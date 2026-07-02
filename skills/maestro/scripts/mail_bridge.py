#!/usr/bin/env python3
"""Escalation mail bridge: send an escalation email, and land the human's
email REPLY on disk where the conductor can read it at the next boundary.

This keeps the supervision topology intact: the human's words never enter a
running agent's context — they arrive as a file.

Env (set in .env):
  MAESTRO_SMTP_HOST / MAESTRO_SMTP_PORT (SSL, default 465)
  MAESTRO_SMTP_USER / MAESTRO_SMTP_PASS   sender account
  MAESTRO_IMAP_HOST                       default: smtp host with imap. prefix
  MAESTRO_NOTIFY_EMAIL                    the human's address

Usage:
  mail_bridge.py send  --project-dir DIR --subject "..." --body "..." [--body-file F]
      sends to MAESTRO_NOTIFY_EMAIL with a token like [ESC-1a2b3c4d] in the
      subject; records escalations/<token>.json (status: pending).
  mail_bridge.py poll  --project-dir DIR
      for every pending token, searches IMAP for a reply (subject contains
      the token and starts with Re:); writes escalations/<token>-reply.md,
      marks the token answered. Exit 0 if any new reply landed, else 3.

Cron the poll (e.g. every 5 min) or run it from a watcher loop.
"""
import argparse, email, imaplib, json, os, smtplib, sys, uuid
from email.header import Header, decode_header
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path


def env(name, default=None, required=False):
    v = os.environ.get(name, default)
    if required and not v:
        sys.exit(f"mail_bridge: {name} not set (see .env.example)")
    return v


def smtp_cfg():
    return {
        "host": env("MAESTRO_SMTP_HOST", required=True),
        "port": int(env("MAESTRO_SMTP_PORT", "465")),
        "user": env("MAESTRO_SMTP_USER", required=True),
        "pass": env("MAESTRO_SMTP_PASS", required=True),
        "to": env("MAESTRO_NOTIFY_EMAIL", required=True),
    }


def cmd_send(args):
    c = smtp_cfg()
    token = "ESC-" + uuid.uuid4().hex[:8]
    subject = f"[{token}] {args.subject}"
    body = args.body or ""
    if args.body_file:
        body += "\n\n" + Path(args.body_file).read_text()
    body += "\n\n--\nReply to this email; your reply text will be delivered to the pipeline at the next experiment boundary."
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = formataddr(("EAIR", c["user"]))
    msg["To"] = c["to"]
    msg["Subject"] = Header(subject, "utf-8")
    s = smtplib.SMTP_SSL(c["host"], c["port"], timeout=30)
    s.login(c["user"], c["pass"])
    s.sendmail(c["user"], [c["to"]], msg.as_string())
    s.quit()
    esc_dir = Path(args.project_dir) / "escalations"
    esc_dir.mkdir(parents=True, exist_ok=True)
    (esc_dir / f"{token}.json").write_text(json.dumps(
        {"token": token, "subject": args.subject, "status": "pending"}, indent=2))
    print(token)


def _imap_connect(c):
    host = env("MAESTRO_IMAP_HOST", c["host"].replace("smtp.", "imap.", 1))
    M = imaplib.IMAP4_SSL(host, 993)
    M.login(c["user"], c["pass"])
    # RFC 2971 ID; some providers (e.g. netease) reject SELECT without it
    imaplib.Commands["ID"] = ("AUTH", "SELECTED")
    try:
        M._simple_command("ID", '("name" "eair" "version" "0.1")')
    except Exception:
        pass
    return M


def _plain_body(m):
    if m.is_multipart():
        for p in m.walk():
            if p.get_content_type() == "text/plain":
                return (p.get_payload(decode=True) or b"").decode("utf-8", "replace")
        return ""
    return (m.get_payload(decode=True) or b"").decode("utf-8", "replace")


def _subject(m):
    out = ""
    for part, enc in decode_header(m.get("Subject", "")):
        out += part.decode(enc or "utf-8", "replace") if isinstance(part, bytes) else part
    return out


def cmd_poll(args):
    c = smtp_cfg()
    esc_dir = Path(args.project_dir) / "escalations"
    pending = []
    for f in sorted(esc_dir.glob("ESC-*.json")) if esc_dir.is_dir() else []:
        rec = json.loads(f.read_text())
        if rec.get("status") == "pending":
            pending.append((f, rec))
    if not pending:
        sys.exit(3)
    M = _imap_connect(c)
    typ, _ = M.select("INBOX")
    if typ != "OK":
        sys.exit("mail_bridge: INBOX select failed (IMAP enabled on the account?)")
    landed = 0
    for f, rec in pending:
        token = rec["token"]
        typ, data = M.search(None, "SUBJECT", f'"{token}"')
        for i in (data[0].split() if typ == "OK" else []):
            typ, md = M.fetch(i, "(RFC822)")
            m = email.message_from_bytes(md[0][1])
            if not _subject(m).lower().startswith("re:"):
                continue
            (esc_dir / f"{token}-reply.md").write_text(
                f"# Reply to {token} — {rec['subject']}\n\n{_plain_body(m)}\n")
            rec["status"] = "answered"
            f.write_text(json.dumps(rec, indent=2))
            landed += 1
            break
    M.logout()
    print(f"replies landed: {landed}")
    sys.exit(0 if landed else 3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("send")
    p1.add_argument("--project-dir", required=True)
    p1.add_argument("--subject", required=True)
    p1.add_argument("--body", default="")
    p1.add_argument("--body-file")
    p2 = sub.add_parser("poll")
    p2.add_argument("--project-dir", required=True)
    args = ap.parse_args()
    {"send": cmd_send, "poll": cmd_poll}[args.cmd](args)
