#!/usr/bin/env python3
"""
Pipeline completion notifier — sends email with supervisor log + final PDF.

SMTP config comes from environment variables (set in .env):
    MAESTRO_SMTP_HOST     SMTP server host
    MAESTRO_SMTP_PORT     SMTP SSL port (default 465)
    MAESTRO_SMTP_USER     SMTP account / From address
    MAESTRO_SMTP_PASS     SMTP password / app token  # set in .env, never commit
    MAESTRO_NOTIFY_EMAIL  Recipient address(es), comma-separated

Optionally, MAESTRO_MAIL_CONFIG may point to a YAML file with a `mail:`
section (host/port/user/pass_env/receivers); env vars take precedence.
The YAML fallback needs PyYAML; the env-var path is stdlib-only.

Usage:
    python3 pipeline_notify.py --project-dir $PROJECT_ROOT/<paper>
    python3 pipeline_notify.py --project-dir $PROJECT_ROOT/<paper> --dry-run
"""

import argparse
import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
from email.utils import formataddr
from email import encoders
from pathlib import Path


def load_mail_config():
    cfg = {
        'host': os.environ.get('MAESTRO_SMTP_HOST', ''),
        'port': int(os.environ.get('MAESTRO_SMTP_PORT', '465')),
        'user': os.environ.get('MAESTRO_SMTP_USER', ''),
        'password': os.environ.get('MAESTRO_SMTP_PASS', ''),  # set in .env
        'receivers': [r.strip() for r in
                      os.environ.get('MAESTRO_NOTIFY_EMAIL', '').split(',')
                      if r.strip()],
    }
    cfg_path = os.environ.get('MAESTRO_MAIL_CONFIG', '')
    if cfg_path and os.path.exists(cfg_path):
        import yaml  # extra dep: PyYAML (file-based config only)
        with open(cfg_path) as f:
            file_cfg = (yaml.safe_load(f) or {}).get('mail', {})
        for k in ('host', 'port', 'user'):
            if not cfg[k] and file_cfg.get(k):
                cfg[k] = file_cfg[k]
        if not cfg['password'] and file_cfg.get('pass_env'):
            cfg['password'] = os.environ.get(file_cfg['pass_env'], '')
        if not cfg['receivers'] and file_cfg.get('receivers'):
            cfg['receivers'] = file_cfg['receivers']
    if not (cfg['host'] and cfg['user'] and cfg['password'] and cfg['receivers']):
        raise SystemExit(
            "Mail not configured: set MAESTRO_SMTP_HOST/USER/PASS and "
            "MAESTRO_NOTIFY_EMAIL (or MAESTRO_MAIL_CONFIG).")
    return cfg


def build_body(project_dir):
    """Build HTML email body from pipeline state and review history."""
    project = Path(project_dir)

    # Load pipeline state
    state_file = project / "PIPELINE_STATE.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
    else:
        state = {"stage_name": "unknown", "ideas": []}

    # Load pipeline report
    report_file = project / "PIPELINE_REPORT.md"
    report_text = report_file.read_text() if report_file.exists() else "No report found."

    # Collect review scores
    reviews = []
    for i in range(1, 10):
        rf = project / f"REVIEW_R{i}.md"
        if rf.exists():
            content = rf.read_text()
            # Extract score
            for line in content.split('\n'):
                if line.startswith('## Score:'):
                    score = line.split(':')[1].strip().split('/')[0].strip()
                    reviews.append((f"R{i}", score))
                    break

    idea = state.get('ideas', [{}])[0]
    title = idea.get('title', 'Unknown')
    venue = state.get('venue', 'unknown')
    stage = state.get('stage_name', 'unknown')

    review_rows = ''.join(
        f'<tr><td>{r}</td><td>{s}/10</td></tr>' for r, s in reviews
    )

    html = f"""
    <html><body style="font-family: -apple-system, Arial, sans-serif; max-width: 700px; margin: 0 auto;">
    <h2 style="color: #2e7d32;">Pipeline Complete: {title}</h2>
    <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
        <tr style="background: #f5f5f5;"><td style="padding: 8px; font-weight: bold;">Venue</td><td style="padding: 8px;">{venue}</td></tr>
        <tr><td style="padding: 8px; font-weight: bold;">Stage</td><td style="padding: 8px;">{stage}</td></tr>
        <tr style="background: #f5f5f5;"><td style="padding: 8px; font-weight: bold;">Paper Status</td><td style="padding: 8px;">{idea.get('paper_status', 'unknown')}</td></tr>
    </table>

    <h3>Review Trajectory</h3>
    <table style="border-collapse: collapse; border: 1px solid #ddd;">
        <tr style="background: #e8f5e9;"><th style="padding: 6px 16px;">Round</th><th style="padding: 6px 16px;">Score</th></tr>
        {review_rows}
    </table>

    <h3>Pipeline Report</h3>
    <pre style="background: #f8f8f8; padding: 12px; border-radius: 4px; font-size: 13px; overflow-x: auto; white-space: pre-wrap;">{report_text}</pre>

    <p style="color: #888; font-size: 12px; margin-top: 24px;">
    Sent by Maestro &mdash; {title} ({venue})
    </p>
    </body></html>
    """
    return html, title, venue


def collect_attachments(project_dir, title=None, venue=None):
    """Collect PDF and supervisor logs as attachments."""
    project = Path(project_dir)
    attachments = []

    # Final PDF -- name by title+venue from PIPELINE_STATE
    pdf = project / "latex" / "main.pdf"
    if pdf.exists():
        safe_title = (title or "paper").replace(" ", "_").replace("/", "_")[:40]
        safe_venue = (venue or "venue").replace(" ", "_")[:20]
        attachments.append((f"{safe_title}_{safe_venue}.pdf", pdf))

    # Pipeline report
    report = project / "PIPELINE_REPORT.md"
    if report.exists():
        attachments.append(("PIPELINE_REPORT.md", report))

    # All review files
    for i in range(1, 10):
        rf = project / f"REVIEW_R{i}.md"
        if rf.exists():
            attachments.append((f"REVIEW_R{i}.md", rf))

    return attachments


def send_email(mail_cfg, subject, html_body, attachments, dry_run=False):
    mail_pass = mail_cfg['password']

    msg = MIMEMultipart()
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr(("Maestro", mail_cfg['user']))

    # HTML body
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    # Attachments
    for filename, filepath in attachments:
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)

    if dry_run:
        print(f"[DRY RUN] Would send to: {mail_cfg['receivers']}")
        print(f"[DRY RUN] Subject: {subject}")
        print(f"[DRY RUN] Attachments: {[a[0] for a in attachments]}")
        print(f"[DRY RUN] Body length: {len(html_body)} chars")
        return True

    smtp = smtplib.SMTP_SSL(mail_cfg['host'], mail_cfg['port'], timeout=15)
    smtp.ehlo()
    smtp.login(mail_cfg['user'], mail_pass)
    try:
        for receiver in mail_cfg['receivers']:
            if 'To' in msg:
                del msg['To']
            msg['To'] = receiver
            smtp.sendmail(mail_cfg['user'], receiver, msg.as_string())
            print(f"Sent to {receiver}")
    finally:
        smtp.quit()
    return True


def main():
    parser = argparse.ArgumentParser(description="Pipeline completion email notifier")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Print without sending")
    args = parser.parse_args()

    mail_cfg = load_mail_config()
    html_body, title, venue = build_body(args.project_dir)
    attachments = collect_attachments(args.project_dir, title=title, venue=venue)

    subject = f"[Maestro] Pipeline Complete: {title} ({venue})"

    success = send_email(mail_cfg, subject, html_body, attachments, dry_run=args.dry_run)
    if success:
        print("Pipeline notification sent successfully.")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
