#!/bin/bash
# the conductor Email Notification — sends alert when the conductor can't handle something
# Usage: bash notify.sh "subject" "body_text"
#
# Configuration (set in .env or your shell profile):
#   EAIR_SMTP_HOST    SMTP server host (e.g. smtp.example.com)
#   EAIR_SMTP_PORT    SMTP SSL port (default 465)
#   EAIR_SMTP_USER    SMTP account / From address
#   EAIR_SMTP_PASS    SMTP password / app token  # set in .env, never commit
#   EAIR_NOTIFY_EMAIL Recipient address(es), comma-separated
#
# Optionally, a YAML config at $EAIR_MAIL_CONFIG (requires PyYAML) can
# provide the same keys under a top-level `mail:` section; env vars win.

SUBJECT="${1:-the conductor Alert}"
BODY="${2:-the conductor encountered an issue that requires human attention.}"

python3 << PYEOF
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from datetime import datetime
import os

cfg = {
    'host': os.environ.get('EAIR_SMTP_HOST', ''),
    'port': int(os.environ.get('EAIR_SMTP_PORT', '465')),
    'user': os.environ.get('EAIR_SMTP_USER', ''),
    'password': os.environ.get('EAIR_SMTP_PASS', ''),  # set in .env
    'receivers': [r.strip() for r in
                  os.environ.get('EAIR_NOTIFY_EMAIL', '').split(',')
                  if r.strip()],
}

# Optional YAML config file fallback (env vars take precedence).
cfg_path = os.environ.get('EAIR_MAIL_CONFIG', '')
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
        print(f"[the conductor] Mail config load failed: {e}")

if not (cfg['host'] and cfg['user'] and cfg['password'] and cfg['receivers']):
    print("[the conductor] Email not configured — set EAIR_SMTP_HOST/USER/PASS "
          "and EAIR_NOTIFY_EMAIL. Skipping notification.")
    raise SystemExit(0)

subject = """${SUBJECT}"""
body = """${BODY}"""

html = f"""
<html><body>
<h2>the conductor Alert</h2>
<p><b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<hr>
<pre>{body}</pre>
<hr>
<p style="color:gray;font-size:12px">Sent by the EAIR conductor — autonomous research orchestrator</p>
</body></html>
"""

msg = MIMEText(html, 'html', 'utf-8')
msg['Subject'] = Header(f'[the conductor] {subject} - {datetime.now().strftime("%Y-%m-%d %H:%M")}', 'utf-8')
msg['From'] = formataddr(("the conductor", cfg['user']))

try:
    obj = smtplib.SMTP_SSL(cfg['host'], cfg['port'], timeout=10)
    obj.ehlo()
    obj.login(cfg['user'], cfg['password'])
    for r in cfg['receivers']:
        if 'To' in msg: del msg['To']
        msg['To'] = r
        obj.sendmail(cfg['user'], r, msg.as_string())
    obj.quit()
    print("[the conductor] Email sent successfully.")
except Exception as e:
    print(f"[the conductor] Email failed: {e}")
PYEOF
