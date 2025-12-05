# 🔒 CIS Security Configuration

## Required Environment Variables

This document lists all required environment variables and secrets for the CIS application.

### ⚠️ IMPORTANT: Never commit `.env` to version control!

The `.env` file is already in `.gitignore`. Always use `.env.example` as a template.

---

## 🔐 Authentication (Clerk)

### Required for user authentication and session management

```bash
CLERK_PUBLISHABLE_KEY="pk_test_..."
CLERK_SECRET_KEY="sk_test_..."
CLERK_JWT_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
```

**How to get:**

1. Sign up at [clerk.com](https://clerk.com)
2. Create a new application
3. Copy keys from Dashboard → API Keys

---

## 🗄️ Database (Supabase)

### Required for user data and post storage

```bash
SUPABASE_URL="https://your-project-ref.supabase.co"
SUPABASE_KEY="your-supabase-anon-key"
SUPABASE_SERVICE_KEY="your-supabase-service-role-key"
```

**How to get:**

1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → API
4. Copy URL and keys

---

## 🤖 AI Models (Google Gemini)

### Required for content generation and scoring

```bash
GOOGLE_API_KEY="your-google-api-key"
```

**How to get:**

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Enable Gemini API in Google Cloud Console

---

## 📊 Error Tracking (Sentry)

### Required for production error monitoring

```bash
SENTRY_DSN="https://your-sentry-dsn@sentry.io/your-project-id"
```

**How to get:**

1. Sign up at [sentry.io](https://sentry.io)
2. Create a new project (Python/Streamlit)
3. Copy DSN from Settings → Client Keys

---

## 🔗 LinkedIn OAuth (Optional)

### Optional: For LinkedIn post publishing

```bash
LINKEDIN_CLIENT_ID="your-linkedin-client-id"
LINKEDIN_CLIENT_SECRET="your-linkedin-client-secret"
LINKEDIN_REDIRECT_URI="http://localhost:8080/auth/linkedin/callback"
```

**How to get:**

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create an app
3. Add OAuth 2.0 credentials

---

## 🌐 Application URLs

```bash
API_BASE_URL="http://localhost:8080"
FRONTEND_URL="http://localhost:8501"
PORT="8080"
ENVIRONMENT="development"  # or "production"
```

---

## 🛠️ Development Flags

```bash
TEST_MODE="0"  # Set to 1 to enable test mode features
DEBUG="1"      # Set to 1 to enable debug logging
```

---

## ✅ Setup Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all required variables
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test connection to each service
- [ ] Never commit `.env` to git
- [ ] Use environment-specific `.env` files for staging/production

---

## 🔍 Verification

Run this command to verify your setup:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ GOOGLE_API_KEY:', 'SET' if os.getenv('GOOGLE_API_KEY') else '❌ MISSING'); print('✅ CLERK_SECRET_KEY:', 'SET' if os.getenv('CLERK_SECRET_KEY') else '❌ MISSING'); print('✅ SUPABASE_URL:', 'SET' if os.getenv('SUPABASE_URL') else '❌ MISSING'); print('✅ SENTRY_DSN:', 'SET' if os.getenv('SENTRY_DSN') else '❌ MISSING')"
```

---

## 🚨 Security Best Practices

1. **Never hardcode secrets** - Always use environment variables
2. **Rotate keys regularly** - Especially after team member changes
3. **Use different keys** for development, staging, and production
4. **Limit key permissions** - Use least privilege principle
5. **Monitor key usage** - Set up alerts for unusual activity
6. **Backup `.env`** - Store securely (1Password, AWS Secrets Manager, etc.)

---

## 🆘 Troubleshooting

### "Missing API Key" Error

- Check `.env` file exists in project root
- Verify variable names match exactly (case-sensitive)
- Restart application after changing `.env`

### "Invalid Credentials" Error

- Verify keys are copied correctly (no extra spaces)
- Check key hasn't expired or been revoked
- Ensure you're using the correct environment keys

### "Permission Denied" Error

- Check service account has necessary permissions
- Verify API is enabled in cloud console
- Check billing is enabled (for paid services)

---

**Last Updated:** December 5, 2025
**Maintained By:** GNX AIS Team
