# GNX CIS Deployment Checklist

> **Quick reference for deploying to production**  
> **Full guide:** [DEPLOYMENT.md](./DEPLOYMENT.md)  
> **Target URL:** `https://cis.gnxautomation.com`

---

## Pre-Deployment ✈️

### Accounts & Access

- [ ] Google Cloud account with billing enabled
- [ ] Google Cloud CLI installed (`gcloud --version`)
- [ ] Logged into GCloud (`gcloud auth login`)
- [ ] Project selected (`gcloud config set project YOUR_PROJECT`)

### Credentials Ready

- [ ] Clerk Secret Key
- [ ] Clerk Publishable Key
- [ ] Supabase URL
- [ ] Supabase Anon Key
- [ ] Google API Key (Gemini)
- [ ] LinkedIn Client ID/Secret (if using)

---

## Deployment Steps 🚀

### Step 1: Enable APIs (one-time)

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

- [ ] APIs enabled

### Step 2: Deploy GNX CIS (Single Service - API + Dashboard)

Your FastAPI app serves both API endpoints and the static dashboard, so you only need **one service**:

```bash
gcloud run deploy gnx-cis \
  --source . \
  --dockerfile Dockerfile.api \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars="CLERK_SECRET_KEY=xxx,SUPABASE_URL=xxx,..."
```

- [ ] Service deployed
- [ ] Note URL: `https://gnx-cis-xxxxxxxxxx-uc.a.run.app`

### Step 3: Test Raw URL

- [ ] Health check: `https://gnx-cis-xxx.a.run.app/health`
- [ ] Dashboard loads: `https://gnx-cis-xxx.a.run.app`

---

## Custom Domain Setup 🌐

### Step 4: Create Domain Mapping

```bash
gcloud run domain-mappings create \
  --service gnx-cis \
  --domain cis.gnxautomation.com \
  --region us-central1
```

- [ ] Domain mapping created

### Step 5: Add Cloudflare DNS Record

| Type  | Name  | Target                 | Proxy   |
| ----- | ----- | ---------------------- | ------- |
| CNAME | `cis` | `ghs.googlehosted.com` | **OFF** |

- [ ] DNS record added with proxy **OFF** (grey cloud)

### Step 6: Wait for SSL (10-20 min)

```bash
gcloud run domain-mappings describe \
  --domain cis.gnxautomation.com \
  --region us-central1
```

- [ ] Certificate status: `CertificateProvisioned: True`

### Step 7: Enable Cloudflare Proxy

- [ ] Toggle `cis` record to **Proxied** (orange cloud)

### Step 8: Set SSL Mode

- [ ] Cloudflare SSL/TLS → **Full (Strict)**

### Step 9: Create ACME Page Rule (prevents SSL renewal issues)

- URL: `*gnxautomation.com/.well-known/acme-challenge/*`
- [ ] SSL = Off
- [ ] Cache Level = Bypass

---

## Verification ✅

- [ ] `https://cis.gnxautomation.com/health` returns OK
- [ ] `https://cis.gnxautomation.com` loads dashboard
- [ ] Login works via Clerk
- [ ] Content generation works
- [ ] No CORS errors

---

## Post-Deployment 📊

### Set Up Monitoring

- [ ] Cloud Logging enabled
- [ ] Error rate alerts configured
- [ ] Latency alerts configured

### Security Hardening

- [ ] CORS restricted to `https://cis.gnxautomation.com`
- [ ] Rate limiting enabled
- [ ] Secrets in Secret Manager

### Performance Optimization

- [ ] Consider min-instances for reduced cold starts
- [ ] Review Cloudflare caching rules

---

## Zero-Downtime Updates 🔄

### Simple Update

```bash
gcloud run deploy gnx-cis --source . --dockerfile Dockerfile.api
```

### Canary Update (Safer)

```bash
# Deploy without traffic
gcloud run deploy gnx-cis --source . --no-traffic --tag canary

# Test canary URL
# https://canary---gnx-cis-xxx.a.run.app

# Gradual rollout
gcloud run services update-traffic gnx-cis --to-tags canary=10
gcloud run services update-traffic gnx-cis --to-tags canary=50
gcloud run services update-traffic gnx-cis --to-latest
```

### Rollback

```bash
gcloud run revisions list --service gnx-cis
gcloud run services update-traffic gnx-cis --to-revisions REVISION_NAME=100
```

---

## Troubleshooting 🔧

| Issue                   | Solution                                                  |
| ----------------------- | --------------------------------------------------------- |
| SSL errors during setup | Ensure Cloudflare proxy is OFF during cert provisioning   |
| Too many redirects      | Set SSL mode to Full (Strict)                             |
| CORS errors             | Update `allow_origins` in main.py                         |
| Cold start latency      | Add `--min-instances 1` (costs ~$25/month)                |
| 502/503 errors          | Check logs: `gcloud alpha run services logs read gnx-cis` |

---

## Useful Commands 📝

```bash
# View running services
gcloud run services list

# Get service URL
gcloud run services describe gnx-cis --format='value(status.url)'

# Stream logs
gcloud alpha run services logs read gnx-cis --tail=100

# Check traffic distribution
gcloud run services describe gnx-cis --format='yaml(spec.traffic)'

# Update environment variables
gcloud run services update gnx-cis --set-env-vars="KEY=value"

# Delete (careful!)
gcloud run services delete gnx-cis
```

---

**Last Updated:** December 11, 2024
