# Email Configuration for Password Reset

## Problem
Emails are not being sent in production because `EMAIL_PROVIDER` is set to `"console"` (prints to stdout instead of sending).

## Solution

Add these to your production `.env` file on the server:

```bash
# Email provider (resend, sendgrid, smtp, or console)
EMAIL_PROVIDER=resend

# Resend API key (get from https://resend.com/api-keys)
RESEND_API_KEY=re_xxxxxxxxxxxxx

# From email and name for password reset emails
SMTP_FROM_EMAIL=noreply@emoratest.com
SMTP_FROM_NAME=EmoraTest
```

## Get a Resend API Key

1. Go to https://resend.com/signup and create an account
2. Go to https://resend.com/api-keys
3. Create a new API key
4. Copy the key and add it to your `.env` file

## Restart Backend

After updating `.env`:

```bash
cd /opt/emoratest
docker compose -f docker-compose.prod.yml restart backend
```

## Test

Try the forgot password form and check your email (and spam folder).
