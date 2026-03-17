# Email Service Setup Guide for Password Reset

## Overview
The application now includes a complete password reset email system using Gmail SMTP. Users can securely reset their passwords when they forget them.

## Features
✅ Secure password reset tokens (32-byte hex)  
✅ Token expiration (60 minutes)  
✅ Beautiful HTML emails  
✅ Console logging for debugging  
✅ Development mode with fallback tokens  
✅ Password validation (minimum 8 characters)  
✅ Bcrypt password hashing  

## How It Works

### User Workflow
1. User clicks "Forgot Password" on login page
2. Enters their email address
3. System generates a secure reset token
4. Email is sent with reset link: `http://localhost:5173/reset-password?token=<token>`
5. User clicks link in email
6. User enters new password (minimum 8 characters)
7. Password is updated and token is invalidated

### Backend Flow
- **FastAPI Route**: `/api/auth/forgot-password` (POST)
- **Email Service**: Sends via Gmail SMTP
- **Token Storage**: Database (expires after 1 hour)
- **Password Reset**: `/api/auth/reset-password` (POST)

## Setup Instructions

### Step 1: Get Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. You may need to:
   - Verify your identity (2FA)
   - Login to your Google account first
3. Select platform: **Windows Computer**
4. Select app: **Mail**
5. Google will generate a 16-character password that looks like: `xxxx-xxxx-xxxx-xxxx`
6. **Copy this password** (you'll need it)

### Step 2: Update .env File

Open `.env` file in the project root:

```env
# Email Service for Password Reset (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**Important Notes:**
- `EMAIL_USER`: Your full Gmail address (e.g., nilay.yala@gmail.com)
- `EMAIL_PASSWORD`: The 16-character App Password you just generated (NOT your regular Gmail password)
- Do NOT use your regular Gmail password - it will fail

### Step 3: Restart Backend Services

Kill the running FastAPI server and restart it:

```powershell
cd backend
python -m uvicorn app.main_optimized:app --reload --port 8000
```

### Step 4: Test Email Service

#### Option 1: Test via Frontend UI
1. Go to `http://localhost:5173`
2. Click on "Login"
3. Click "Forgot Password?"
4. Enter your email address
5. Check your email inbox and spam folder
6. Click the reset link
7. Enter new password (minimum 8 characters)

#### Option 2: Test via API (cURL or Postman)

**Send reset email:**
```bash
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@gmail.com"}'
```

**Expected Success Response:**
```json
{
  "success": true,
  "message": "Password reset link sent to your email. Check your inbox and spam folder.",
  "email": "your-email@gmail.com"
}
```

## Troubleshooting

### Problem: Email not sending - "Email service not configured"

**Solution:**
1. Verify `EMAIL_USER` and `EMAIL_PASSWORD` are set in `.env`
2. Restart the FastAPI server
3. Check terminal logs for error messages
4. Ensure it's an **App Password**, not your Gmail password

### Problem: "Invalid Email address" error

**Solution:**
- Use a valid email format: `user@domain.com`
- The email doesn't need to be registered in the system yet

### Problem: "SMTP authentication failed"

**Possible Causes:**
1. Wrong App Password - regenerate it from https://myaccount.google.com/apppasswords
2. Email address is wrong - verify against your Google account
3. 2FA not enabled - Gmail App Passwords require 2-factor authentication
4. App Password expired - regenerate a new one

**Fix:**
1. Go to https://myaccount.google.com/apppasswords
2. Select Mail / Windows / Generate
3. Copy the new 16-character password
4. Update `EMAIL_PASSWORD` in `.env`
5. Restart the server

### Problem: Email received but link doesn't work

**Check:**
1. Copy the full URL from email: `http://localhost:5173/reset-password?token=...`
2. Verify the token is complete (should be 64 characters)
3. Ensure you're accessing via http://localhost:5173 (not a different domain)
4. Token expires after 60 minutes - generate a new one if needed

## Console Logging

When email service is working, you should see logs like:

```
✅ Email service configured successfully
📧 Attempting to send reset email to user@gmail.com...
   SMTP Server: smtp.gmail.com:587
   ✅ TLS connection established
   ✅ Authenticated as your-email@gmail.com
   ✅ Email sent successfully to user@gmail.com
```

### Debug: Email service not configured
```
⚠️  Email credentials not configured in .env
   Set EMAIL_USER and EMAIL_PASSWORD to enable email sending
```

### Debug: Authentication failed
```
❌ Email authentication failed: b'5.7.8 ...invalid password'
   Check EMAIL_USER and EMAIL_PASSWORD in .env file
   For Gmail: Use 'App Password' from https://myaccount.google.com/apppasswords
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_HOST` | SMTP server address | smtp.gmail.com |
| `EMAIL_PORT` | SMTP port (usually 587 for TLS) | 587 |
| `EMAIL_USER` | Your email address | nilay@gmail.com |
| `EMAIL_PASSWORD` | Gmail App Password (16 chars) | xxxx-xxxx-xxxx-xxxx |

## Testing in Development Mode

If email service is not configured, the API returns:
```json
{
  "success": false,
  "message": "Email service not configured.",
  "testing_token": "abc123def456..."
}
```

Use the `testing_token` to manually construct the reset link for development:
```
http://localhost:5173/reset-password?token=abc123def456...
```

## Database Migrations

The `users` table includes these columns for password reset:
- `reset_password_token` - Secure token (32-byte hex)
- `reset_password_expires` - Token expiration timestamp

These are automatically created by `init_db.py`.

## Security Notes

✅ **Bcrypt Hashing**: Passwords are hashed with 12 rounds of bcrypt  
✅ **Secure Tokens**: 32-byte random hex tokens (256-bit entropy)  
✅ **Token Expiration**: Reset tokens expire after 60 minutes  
✅ **No Email Exposure**: Login doesn't reveal if email exists  
✅ **TLS Encryption**: Gmail connection uses TLS encryption  

## API Endpoints Reference

### POST /api/auth/register
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123"
}
```

### POST /api/auth/login
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123"
}
```

### POST /api/auth/forgot-password
```json
{
  "email": "john@example.com"
}
```

### POST /api/auth/reset-password
```json
{
  "token": "abc123def456...",
  "password": "NewPassword123"
}
```

### GET /api/auth/verify-token/{token}
Verifies if a reset token is still valid.

## Need Help?

1. Check the FastAPI logs: Look for error messages in terminal
2. Check .env file: Ensure EMAIL_USER and EMAIL_PASSWORD are set
3. Test Gmail App Password: Try logging into Gmail with the app password (it won't work, but you'll see a clear error)
4. Generator new App Password: Go to https://myaccount.google.com/apppasswords and generate a new one
