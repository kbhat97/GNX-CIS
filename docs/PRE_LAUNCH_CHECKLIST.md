# GNX CIS Pre-Launch Checklist

## Last Updated: 2025-12-10

---

## 🔴 CRITICAL: Security Fixes (MUST DO BEFORE LAUNCH)

### ✅ COMPLETED

- [x] **API_BASE made runtime-configurable** - Uses `window.__RUNTIME_CONFIG__.API_BASE` or auto-detects from `window.location.origin`
- [x] **Supabase URL/Key made runtime-configurable** - Uses `window.__RUNTIME_CONFIG__.SUPABASE_URL` and `SUPABASE_ANON_KEY`
- [x] **CORS origins now configurable** - Via `ALLOWED_ORIGINS` environment variable (comma-separated)
- [x] **LinkedIn publish endpoint secured** - Now requires JWT auth via `get_db_user` dependency, verifies admin from database
- [x] **Admin email check moved server-side** - `ADMIN_EMAILS` configurable via env var, not exposed to client
- [x] **Test hooks gated to dev mode only** - `gnx_test_role` localStorage hook only works on localhost
- [x] **Frontend publish switched to safe flow** - Copies content + opens LinkedIn instead of direct API call

### ⏳ PENDING (User Action Required)

- [ ] **Set ADMIN_EMAILS in production .env** - Add your admin email: `ADMIN_EMAILS=your@email.com`
- [ ] **Rotate Supabase anon key if concerned** - The key in code IS the safe anon key (role: "anon"), but if you prefer fresh keys for production, rotate in Supabase dashboard → Settings → API
- [ ] **Add production subdomain to CORS** - Update `.env` with `ALLOWED_ORIGINS=https://gnx-cis.yourdomain.com,...`
- [ ] **Review demo auth flows** - The login still accepts any password for demo; consider integrating proper Clerk auth for production

---

## 🟡 Infrastructure Setup

### Domain & DNS (GoDaddy + Cloudflare + GCP)

- [ ] **Verify GoDaddy nameservers point to Cloudflare**

  ```
  ns1.cloudflare.com
  ns2.cloudflare.com
  ```

- [ ] **Create subdomain in Cloudflare DNS**

  ```
  Type: CNAME
  Name: gnx-cis
  Target: [Your Cloud Run service URL].run.app
  Proxy: OFF initially (for Cloud Run cert provisioning)
  ```

- [ ] **Map custom domain in Cloud Run**

  ```bash
  gcloud run domain-mappings create \
    --service=gnx-cis-api \
    --domain=gnx-cis.yourdomain.com \
    --region=us-central1
  ```

- [ ] **Wait for SSL certificate provisioning** (usually 15-30 min)

- [ ] **Enable Cloudflare proxy** (orange cloud) after cert is provisioned

- [ ] **Set Cloudflare SSL to "Full (strict)"**

---

## 🟢 Code Quality

### Linting & Static Analysis

- [ ] Run `ruff check .` and fix all errors
- [ ] Run `mypy api/ main.py` and resolve type issues
- [ ] Run `bandit -r . -x ./tests,./venv,./.venv` for security scan

### Testing

- [ ] All pytest tests pass: `python -m pytest tests/ -v`
- [ ] E2E tests pass (if applicable)
- [ ] Manual smoke test: Navigate to `/health` endpoint

### Code Cleanup

- [ ] Remove all `console.log` debug statements (except error logging)
- [ ] Remove all `print()` debug statements in Python
- [ ] Ensure no TODO comments that block launch

---

## 🔧 Environment Configuration

### Production `.env` Requirements

```bash
# Required for production
ENVIRONMENT=production
API_BASE_URL=https://gnx-cis-api.yourdomain.com
FRONTEND_URL=https://gnx-cis.yourdomain.com
ALLOWED_ORIGINS=https://gnx-cis.yourdomain.com

# Supabase (production project)
SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_KEY=your-prod-anon-key
SUPABASE_SERVICE_KEY=your-prod-service-key

# Clerk (production keys)
CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...

# LinkedIn (production app)
LINKEDIN_CLIENT_ID=your-prod-linkedin-id
LINKEDIN_CLIENT_SECRET=your-prod-linkedin-secret
LINKEDIN_REDIRECT_URI=https://gnx-cis-api.yourdomain.com/auth/linkedin/callback

# Google Gemini
GOOGLE_API_KEY=your-gemini-api-key
```

### Cloud Run Secrets

- [ ] All secrets stored in Google Secret Manager
- [ ] Cloud Run service configured to read from Secret Manager
- [ ] No secrets in Cloud Build substitution variables (use secretManager)

---

## 🚀 Deployment

### CI/CD Pipeline

- [ ] `cloudbuild.yaml` triggers on push to `main`
- [ ] Build includes: lint → test → build image → deploy
- [ ] Smoke test step added (calls `/health` after deploy)
- [ ] Rollback strategy documented

### Cloud Run Configuration

```bash
# Recommended settings
gcloud run services update gnx-cis-api \
  --region=us-central1 \
  --min-instances=1 \        # Avoid cold starts ($$$)
  --max-instances=10 \       # Cap costs
  --memory=512Mi \
  --cpu=1 \
  --timeout=60s
```

---

## 📋 Git Hygiene

- [ ] All sensitive files in `.gitignore` (`.env`, keys, certs)
- [ ] No secrets in git history (run `git log -p | grep -i "key\|secret"`)
- [ ] Create release tag: `git tag -a v1.0.0 -m "Production release"`
- [ ] Update `README.md` with production deployment instructions
- [ ] Create `CHANGELOG.md` for version tracking

---

## 📊 Monitoring & Observability

- [ ] Cloud Run logs enabled and accessible
- [ ] Error alerting configured (Cloud Monitoring or Sentry)
- [ ] Health check monitoring (uptime check on `/health`)
- [ ] Cost alerts set in GCP Billing

---

## 🎯 Final Verification

### Pre-Launch Testing

- [ ] Access frontend at `https://gnx-cis.yourdomain.com`
- [ ] Login flow works
- [ ] Generate a test post
- [ ] API health endpoint returns `"status": "healthy"`
- [ ] No CORS errors in browser console
- [ ] LinkedIn integration works (if enabled)

### Rollback Plan

1. Keep previous working container image tagged
2. To rollback: `gcloud run services update-traffic gnx-cis-api --to-revisions=PREVIOUS_REVISION=100`
3. Document current working revision ID

---

## 📁 Files Modified in This Session

| File                                     | Change                                                                      |
| ---------------------------------------- | --------------------------------------------------------------------------- |
| `dashboard/app.html`                     | Runtime config, secured isAdminUser(), safe publish flow                    |
| `dashboard/runtime-config.template.html` | Template for production config injection                                    |
| `main.py`                                | Secured `/api/linkedin/publish` with JWT auth, CORS + ADMIN_EMAILS env vars |
| `.env.example`                           | Added ALLOWED_ORIGINS and ADMIN_EMAILS documentation                        |
| `docs/PRE_LAUNCH_CHECKLIST.md`           | This file                                                                   |

---

## Commands Reference

### Deploy to Cloud Run

```bash
# Build and deploy API
gcloud builds submit --tag gcr.io/YOUR_PROJECT/gnx-cis-api:latest
gcloud run deploy gnx-cis-api \
  --image gcr.io/YOUR_PROJECT/gnx-cis-api:latest \
  --region=us-central1 \
  --allow-unauthenticated

# Map custom domain
gcloud run domain-mappings create \
  --service=gnx-cis-api \
  --domain=gnx-cis.yourdomain.com
```

### Test Health Endpoint

```bash
curl https://gnx-cis-api.yourdomain.com/health
```

### Check Cloud Run Logs

```bash
gcloud logs read --service=gnx-cis-api --limit=100
```
