#!/bin/bash
# Maestro Email Notification — sends alert when Maestro can't handle something
# Usage: bash notify.sh "subject" "body_text"
#
# Configuration (set in .env or your shell profile):
#   MAESTRO_SMTP_HOST    SMTP server host (e.g. smtp.example.com)
#   MAESTRO_SMTP_PORT    SMTP SSL port (default 465)
#   MAESTRO_SMTP_USER    SMTP account / From address
#   MAESTRO_SMTP_PASS    SMTP password / app token  # set in .env, never commit
#   MAESTRO_NOTIFY_EMAIL Recipient address(es), comma-separated
#
# Optionally, a YAML config at $MAESTRO_MAIL_CONFIG (requires PyYAML) can
# provide the same keys under a top-level `mail:` section; env vars win.

SUBJECT="${1:-Maestro Alert}"
BODY="${2:-Maestro encountered an issue that requires human attention.}"

python3 << PYEOF
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from datetime import datetime
import os

cfg = {
    'host': os.environ.get('MAESTRO_SMTP_HOST', ''),
    'port': int(os.environ.get('MAESTRO_SMTP_PORT', '465')),
    'user': os.environ.get('MAESTRO_SMTP_USER', ''),
    'password': os.environ.get('MAESTRO_SMTP_PASS', ''),  # set in .env
    'receivers': [r.strip() for r in
                  os.environ.get('MAESTRO_NOTIFY_EMAIL', '').split(',')
                  if r.strip()],
}

# Optional YAML config file fallback (env vars take precedence).
cfg_path = os.environ.get('MAESTRO_MAIL_CONFIG', '')
if cfg_path and os.path.exists(cfg_path):
    try:
        import yaml  # extra dep: PyYAML (only needed for file-based config)
        with open(cfg_path) as f:
            file_cfg = (yaml.safe_load(f) or {}).get('mail', {})
        for k in ('host', 'port', 'user'):
            if not cfg[k] and file_cfg.get(k):
                cfg[k] = file_cfg[k]
        if not cfg['password'] and file_cfg.get('pass_env'):
            cfg['password'] = os.environ.get(file_cfg['pass_env'], '')
        if not cfg['receivers'] and file_cfg.get('receivers'):
            cfg['receivers'] = file_cfg['receivers']
    except Exception as e:
        print(f"[Maestro] Mail config load failed: {e}")

if not (cfg['host'] and cfg['user'] and cfg['password'] and cfg['receivers']):
    print("[Maestro] Email not configured — set MAESTRO_SMTP_HOST/USER/PASS "
          "and MAESTRO_NOTIFY_EMAIL. Skipping notification.")
    raise SystemExit(0)

subject = """${SUBJECT}"""
body = """${BODY}"""

html = f"""
<html><body>
<h2>Maestro Alert</h2>
<p><b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<hr>
<pre>{body}</pre>
<hr>
<p style="color:gray;font-size:12px">Sent by Maestro — Claude Code autonomous orchestrator</p>
</body></html>
"""

msg = MIMEText(html, 'html', 'utf-8')
msg['Subject'] = Header(f'[Maestro] {subject} - {datetime.now().strftime("%Y-%m-%d %H:%M")}', 'utf-8')
msg['From'] = formataddr(("Maestro", cfg['user']))

try:
    obj = smtplib.SMTP_SSL(cfg['host'], cfg['port'], timeout=10)
    obj.ehlo()
    obj.login(cfg['user'], cfg['password'])
    for r in cfg['receivers']:
        if 'To' in msg: del msg['To']
        msg['To'] = r
        obj.sendmail(cfg['user'], r, msg.as_string())
    obj.quit()
    print("[Maestro] Email sent successfully.")
except Exception as e:
    print(f"[Maestro] Email failed: {e}")
PYEOF
