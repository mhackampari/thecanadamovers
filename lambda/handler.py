import json
import html
import re
import os
import urllib.request
import urllib.parse
import urllib.error
import boto3

TURNSTILE_SECRET = os.environ.get("TURNSTILE_SECRET", "")
SES_FROM = os.environ.get("SES_FROM", "noreply@the-canada-movers.com")
SES_TO = os.environ.get("SES_TO", "thecanadamovers@gmail.com")
SES_BCC = os.environ.get("SES_BCC", "nico.mkhatvari@gmail.com")
MAX_LEN = 500

_ses = None


def get_ses():
    global _ses
    if _ses is None:
        _ses = boto3.client("ses", region_name="us-east-2")
    return _ses


def ok(message="ok"):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"ok": True, "message": message}),
    }


def err(status, message):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"ok": False, "message": message}),
    }


def verify_turnstile(token, remote_ip):
    if not TURNSTILE_SECRET:
        return True  # skip in dev when secret not configured
    data = urllib.parse.urlencode({
        "secret": TURNSTILE_SECRET,
        "response": token,
        "remoteip": remote_ip,
    }).encode()
    req = urllib.request.Request(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=data,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            return result.get("success", False)
    except Exception:
        return False


def handler(event, context):
    # 1. Parse body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return err(400, "Invalid JSON")

    # 2. Honeypot — silently drop bot submissions
    if body.get("middle_name"):
        return ok("received")

    # 3. Turnstile
    token = body.get("cf-turnstile-response", "")
    remote_ip = (event.get("requestContext") or {}).get("http", {}).get("sourceIp", "")
    if not verify_turnstile(token, remote_ip):
        return err(400, "Human verification failed")

    # 4. XSS escape all string fields
    for key in list(body.keys()):
        if isinstance(body[key], str):
            body[key] = html.escape(body[key])

    # 5. Validate email and phone
    email = body.get("email", "")
    phone = body.get("phone", "")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return err(400, "Invalid email address")
    if not re.match(r"^\+?[\d\s\-\(\)]{7,20}$", phone):
        return err(400, "Invalid phone number")

    # 6. Max-length enforcement
    for key in list(body.keys()):
        if isinstance(body[key], str) and len(body[key]) > MAX_LEN:
            body[key] = body[key][:MAX_LEN]
    email = body.get("email", "")
    phone = body.get("phone", "")

    # 7. Build email content
    services = body.get("services", [])
    if isinstance(services, list):
        services_str = ", ".join(services)
    else:
        services_str = str(services)

    lead_body = f"""New quote request submitted via the-canada-movers.com

Name:      {body.get('name', '')}
Email:     {body.get('email', '')}
Phone:     {body.get('phone', '')}
Move Date: {body.get('move_date', '')}

Services:  {services_str}
Box Count: {body.get('box_count', 'N/A')}
Pool Refurb: {'Yes' if body.get('pool_refurb') else 'No'}
Heavy Items: {body.get('heavy_count', 'N/A')}
Has Stairs: {'Yes' if body.get('has_stairs') else 'No'}
Stair Count: {body.get('stair_count', 'N/A')}

Origin:    {body.get('origin_city', '')}, {body.get('origin_postal', '')}
Dest:      {body.get('dest_city', '')}, {body.get('dest_postal', '')}

Notes:     {body.get('instructions', '')}
"""

    confirm_body = f"""Hi {body.get('name', '')},

Thank you for choosing The Canada Movers - fully insured and experienced moving company in Toronto GTA, Canada, and the US.

We have successfully received your quote enquiry.

We will get back to you soon with an estimate.

Best regards,
The Canada Movers team
"""

    confirm_html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;">
          <tr>
            <td style="background-color:#D52B1E;padding:20px 32px;">
              <span style="color:#ffffff;font-size:20px;font-weight:bold;">The Canada Movers</span>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;color:#1A1A1A;font-size:15px;line-height:1.6;">
              <p>Dear {body.get('name', 'customer')},</p>
              <p>Thank you for choosing The Canada Movers &mdash; fully insured and experienced moving company in Toronto GTA, Canada, and the US.</p>
              <p>We have successfully received your quote enquiry.</p>
              <p>We will get back to you soon with an estimate.</p>
              <p>Best regards,<br>The Canada Movers team</p>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f4f4f4;padding:16px 32px;color:#666666;font-size:12px;">
              1-647-885-0450 &nbsp;|&nbsp; the-canada-movers.com
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    ses = get_ses()

    # Send lead notification to the business
    ses.send_email(
        Source=SES_FROM,
        Destination={"ToAddresses": [SES_TO], "BccAddresses": [SES_BCC]},
        Message={
            "Subject": {"Data": f"New Quote Request — {body.get('name', 'Unknown')}"},
            "Body": {"Text": {"Data": lead_body}},
        },
    )

    # Send auto-confirm to the client (best-effort — lead is already captured above)
    try:
        ses.send_email(
            Source=SES_FROM,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "We received your quote request — The Canada Movers"},
                "Body": {
                    "Text": {"Data": confirm_body},
                    "Html": {"Data": confirm_html},
                },
            },
        )
    except Exception:
        pass

    return ok("Quote request received")
