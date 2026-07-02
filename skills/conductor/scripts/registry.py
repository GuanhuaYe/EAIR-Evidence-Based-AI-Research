"""
the conductor Artifact Registry — mandatory file creation gateway.

Usage:
    from registry import Registry
    reg = Registry(os.path.expandvars("$PROJECT_ROOT/my_project"))

    # Create (auto-registers, archives old version)
    reg.create("results/scores.json", content=json_str,
               producer="scoring_agent", stage="formal_eval",
               description="Per-text detector scores")

    # Read (blocks superseded files)
    content = reg.read("results/scores.json")

    # List / audit / lineage
    reg.list_active(stage="formal_eval")
    reg.audit()
    reg.lineage("results/scores.json")
"""

import json, os, hashlib, uuid, shutil
from datetime import datetime
from pathlib import Path


class Registry:
    REGISTRY_FILE = "FILE_REGISTRY.json"

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.registry_path = self.project_dir / self.REGISTRY_FILE
        self._load_or_create()

    def _load_or_create(self):
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                self.data = json.load(f)
        else:
            self.data = {
                "schema_version": 2,
                "project_id": str(uuid.uuid4())[:12],
                "created": datetime.now().isoformat(),
                "artifacts": {},
            }
            self._save()

    def _save(self):
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def _sha256(self, content):
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()[:16]

    def create(
        self, rel_path: str, content, producer: str, stage: str,
        description: str, parents: list = None,
    ) -> str:
        """Write file + register. Returns artifact_id."""
        abs_path = self.project_dir / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        # Archive old active version if exists
        if rel_path in self.data["artifacts"]:
            old = self.data["artifacts"][rel_path]
            if old["status"] == "active":
                old_v = old["version"]
                stem, suffix = abs_path.stem, abs_path.suffix
                archive_rel = str(Path(rel_path).parent / f"{stem}_v{old_v}{suffix}")
                if abs_path.exists():
                    shutil.copy2(abs_path, self.project_dir / archive_rel)
                old["status"] = "superseded"
                old["superseded_at"] = datetime.now().isoformat()
                self.data["artifacts"][archive_rel] = dict(old)

        # Write file
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(abs_path, mode) as f:
            f.write(content)

        content_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
        artifact_id = str(uuid.uuid4())[:8]

        # Version number
        existing = [
            v.get("version", 0)
            for k, v in self.data["artifacts"].items()
            if Path(k).stem.startswith(Path(rel_path).stem)
            and str(Path(k).parent) == str(Path(rel_path).parent)
        ]
        new_version = max(existing, default=0) + 1

        self.data["artifacts"][rel_path] = {
            "artifact_id": artifact_id,
            "version": new_version,
            "created": datetime.now().isoformat(),
            "producer": producer,
            "stage": stage,
            "status": "active",
            "description": description,
            "checksum": self._sha256(content_bytes),
            "size_bytes": len(content_bytes),
            "parents": parents or [],
        }
        self._save()
        return artifact_id

    def read(self, rel_path: str, strict: bool = True) -> str:
        """Read file, checking registry status. Blocks superseded files."""
        if rel_path not in self.data["artifacts"]:
            if strict:
                raise FileNotFoundError(
                    f"'{rel_path}' NOT in registry. Use reg.list_active()."
                )
            print(f"WARNING: '{rel_path}' not in registry")
        else:
            entry = self.data["artifacts"][rel_path]
            if entry["status"] == "superseded":
                raise ValueError(
                    f"'{rel_path}' is SUPERSEDED. Use reg.list_active() to find current version."
                )
        with open(self.project_dir / rel_path) as f:
            return f.read()

    def list_active(self, stage: str = None) -> list:
        """List active artifacts, optionally filtered by stage."""
        return [
            {"path": k, **v}
            for k, v in self.data["artifacts"].items()
            if v["status"] == "active" and (stage is None or v.get("stage") == stage)
        ]

    def supersede(self, rel_path: str, reason: str = ""):
        if rel_path in self.data["artifacts"]:
            self.data["artifacts"][rel_path]["status"] = "superseded"
            self.data["artifacts"][rel_path]["superseded_at"] = datetime.now().isoformat()
            self.data["artifacts"][rel_path]["supersede_reason"] = reason
            self._save()

    def audit(self) -> dict:
        """Check filesystem vs registry consistency."""
        issues = []
        for path, meta in self.data["artifacts"].items():
            if meta["status"] != "active":
                continue
            if not (self.project_dir / path).exists():
                issues.append({"type": "missing_file", "path": path})
        for subdir in ["code", "latex", "data", "rebuttal"]:
            d = self.project_dir / subdir
            if not d.exists():
                continue
            for f in d.rglob("*"):
                if f.is_file() and f.name != self.REGISTRY_FILE:
                    rel = str(f.relative_to(self.project_dir))
                    if rel not in self.data["artifacts"]:
                        issues.append({"type": "unregistered", "path": rel})
        return {"ok": len(issues) == 0, "issues": issues}

    def lineage(self, rel_path: str, _visited: set = None) -> list:
        if _visited is None:
            _visited = set()
        if rel_path not in self.data["artifacts"] or rel_path in _visited:
            return []
        _visited.add(rel_path)
        entry = self.data["artifacts"][rel_path]
        chain = [{"path": rel_path, **entry}]
        for p in entry.get("parents", []):
            chain.extend(self.lineage(p, _visited))
        return chain

    def summary(self) -> str:
        active = [k for k, v in self.data["artifacts"].items() if v["status"] == "active"]
        superseded = [k for k, v in self.data["artifacts"].items() if v["status"] == "superseded"]
        stages = set(v["stage"] for v in self.data["artifacts"].values() if v["status"] == "active")
        lines = [
            f"=== Artifact Registry: {self.project_dir.name} ===",
            f"Active: {len(active)} | Superseded: {len(superseded)} | Stages: {len(stages)}",
        ]
        for stage in sorted(stages):
            lines.append(f"\n  [{stage}]")
            for k, v in self.data["artifacts"].items():
                if v["status"] == "active" and v["stage"] == stage:
                    lines.append(f"    {k} (v{v['version']}, {v['producer']})")
        return "\n".join(lines)
