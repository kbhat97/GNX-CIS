# GNX Content Intelligence System - Production Deployment Guide

> **Last Updated:** December 11, 2024  
> **Stack:** GoDaddy + Cloudflare + Google Cloud Run  
> **Domain:** gnxautomation.com

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Current Infrastructure](#current-infrastructure)
3. [Prerequisites](#prerequisites)
4. [Phase 1: Google Cloud Setup](#phase-1-google-cloud-setup)
5. [Phase 2: Deploy to Cloud Run](#phase-2-deploy-to-cloud-run)
6. [Phase 3: Custom Domain Setup](#phase-3-custom-domain-setup)
7. [Phase 4: Cloudflare Configuration](#phase-4-cloudflare-configuration)
8. [Phase 5: SSL/TLS Setup](#phase-5-ssltls-setup)
9. [Zero-Downtime Deployments](#zero-downtime-deployments)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Monitoring & Observability](#monitoring--observability)
12. [Troubleshooting](#troubleshooting)
13. [Cost Estimation](#cost-estimation)
14. [Security Checklist](#security-checklist)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GODADDY (Domain Registrar)                       │
│                      Nameservers → Cloudflare                            │
│                      apollo.ns.cloudflare.com                            │
│                      joan.ns.cloudflare.com                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLOUDFLARE                                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │    DNS     │  │    CDN     │  │    WAF     │  │    SSL     │         │
│  │ Resolution │  │   Cache    │  │ Protection │  │ Termination│         │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘         │
│                                                                          │
│  app.gnxautomation.com ─────────────────► Frontend Service               │
│  api.gnxautomation.com ─────────────────► API Service                    │
│  dev.gnxautomation.com ─────────────────► Cloudflare Tunnel (Dev)        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (Full Strict SSL)
┌─────────────────────────────────────────────────────────────────────────┐
│                        GOOGLE CLOUD RUN                                  │
│                                                                          │
│  ┌───────────────────────────┐    ┌───────────────────────────┐         │
│  │      cis-api Service       │    │    cis-frontend Service    │         │
│  │  ┌─────────┐ ┌─────────┐  │    │  ┌─────────────────────┐  │         │
│  │  │Rev v1   │ │Rev v2   │  │    │  │   Dashboard (HTML)   │  │         │
│  │  │(stable) │ │(canary) │  │    │  │   Static Assets      │  │         │
│  │  └─────────┘ └─────────┘  │    │  └─────────────────────┘  │         │
│  │                           │    │                           │         │
│  │  FastAPI + Uvicorn        │    │  Python HTTP Server       │         │
│  │  Port 8080                │    │  Port 8080                │         │
│  └───────────────────────────┘    └───────────────────────────┘         │
│                   │                            │                         │
└───────────────────┼────────────────────────────┼─────────────────────────┘
                    │                            │
                    ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │  Supabase  │  │   Clerk    │  │   Gemini   │  │  LinkedIn  │         │
│  │  Database  │  │    Auth    │  │     AI     │  │    API     │         │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Current Infrastructure

### Domain Configuration (as of December 2024)

| Component            | Service                                              | Status                                  |
| -------------------- | ---------------------------------------------------- | --------------------------------------- |
| **Domain Registrar** | GoDaddy                                              | ✅ Active                               |
| **DNS Provider**     | Cloudflare                                           | ✅ Active                               |
| **Nameservers**      | `apollo.ns.cloudflare.com`, `joan.ns.cloudflare.com` | ✅ Configured                           |
| **SSL/TLS Mode**     | Full                                                 | ⚠️ Upgrade to Full (Strict) recommended |

### Current DNS Records

| Type  | Name                | Content             | Proxy    | Purpose                 |
| ----- | ------------------- | ------------------- | -------- | ----------------------- |
| A     | `gnxautomation.com` | `13.248.243.5`      | Proxied  | AWS Global Accelerator  |
| A     | `gnxautomation.com` | `76.223.105.230`    | Proxied  | AWS Global Accelerator  |
| CNAME | `dev`               | Cloudflare Tunnel   | Proxied  | Development environment |
| CNAME | `www`               | `gnxautomation.com` | Proxied  | WWW redirect            |
| MX    | `gnxautomation.com` | Outlook.com         | DNS Only | Microsoft 365 Email     |

### Planned DNS Records (Cloud Run)

| Type  | Name  | Content                | Proxy   | Purpose            |
| ----- | ----- | ---------------------- | ------- | ------------------ |
| CNAME | `app` | `ghs.googlehosted.com` | Proxied | Frontend Dashboard |
| CNAME | `api` | `ghs.googlehosted.com` | Proxied | Backend API        |

---

## Prerequisites

### Required Accounts

- [ ] **Google Cloud Platform account** with billing enabled
- [ ] **Cloudflare account** (already have: Omsrilakshmi888@gmail.com)
- [ ] **GoDaddy account** (domain registrar)

### Required Tools

```bash
# 1. Google Cloud CLI
# Download: https://cloud.google.com/sdk/docs/install
gcloud --version

# 2. Docker (for local testing)
docker --version

# 3. Git
git --version
```

### Environment Variables Required

Create a `.env.production` file (DO NOT commit to git):

```bash
# Authentication (Clerk)
CLERK_SECRET_KEY=sk_live_xxxxxxxxxxxxx
CLERK_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxx

# Database (Supabase)
SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI Services
GOOGLE_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxx

# LinkedIn Integration
LINKEDIN_CLIENT_ID=xxxxxxxx
LINKEDIN_CLIENT_SECRET=xxxxxxxx

# Application URLs (update after deployment)
API_BASE_URL=https://api.gnxautomation.com
FRONTEND_URL=https://app.gnxautomation.com
```

---

## Phase 1: Google Cloud Setup

### 1.1 Create or Select Project

```bash
# Login to Google Cloud
gcloud auth login

# Create new project (if needed)
gcloud projects create gnx-cis-production --name="GNX CIS Production"

# Set as active project
gcloud config set project gnx-cis-production

# Verify
gcloud config get-value project
```

### 1.2 Enable Required APIs

```bash
# Enable Cloud Run
gcloud services enable run.googleapis.com

# Enable Cloud Build
gcloud services enable cloudbuild.googleapis.com

# Enable Artifact Registry
gcloud services enable artifactregistry.googleapis.com

# Enable Secret Manager (for secure env vars)
gcloud services enable secretmanager.googleapis.com
```

### 1.3 Set Default Region

```bash
gcloud config set run/region us-central1
```

---

## Phase 2: Deploy to Cloud Run

### 2.1 Deploy API Service

```bash
# From project root directory
gcloud run deploy cis-api \
  --source . \
  --dockerfile Dockerfile.api \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars="CLERK_SECRET_KEY=xxx,CLERK_PUBLISHABLE_KEY=xxx,SUPABASE_URL=xxx,SUPABASE_KEY=xxx,GOOGLE_API_KEY=xxx,API_BASE_URL=https://api.gnxautomation.com,FRONTEND_URL=https://app.gnxautomation.com"
```

### 2.2 Deploy Frontend Service

```bash
gcloud run deploy cis-frontend \
  --source . \
  --dockerfile Dockerfile.frontend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars="API_BASE_URL=https://api.gnxautomation.com"
```

### 2.3 Verify Deployments

```bash
# List services
gcloud run services list

# Get service URLs
gcloud run services describe cis-api --format='value(status.url)'
gcloud run services describe cis-frontend --format='value(status.url)'
```

**Expected Output:**

- `https://cis-api-xxxxxxxxxx-uc.a.run.app`
- `https://cis-frontend-xxxxxxxxxx-uc.a.run.app`

---

## Phase 3: Custom Domain Setup

### 3.1 Map Custom Domains in Cloud Run

```bash
# Map API domain
gcloud run domain-mappings create \
  --service cis-api \
  --domain api.gnxautomation.com \
  --region us-central1

# Map Frontend domain
gcloud run domain-mappings create \
  --service cis-frontend \
  --domain app.gnxautomation.com \
  --region us-central1
```

### 3.2 Get Required DNS Records

```bash
# View domain mapping status and required DNS records
gcloud run domain-mappings describe \
  --domain api.gnxautomation.com \
  --region us-central1

gcloud run domain-mappings describe \
  --domain app.gnxautomation.com \
  --region us-central1
```

**Typical output will show DNS records like:**

```
resourceRecords:
- name: api
  type: CNAME
  rrdata: ghs.googlehosted.com.
```

---

## Phase 4: Cloudflare Configuration

### 4.1 Add DNS Records

In Cloudflare Dashboard → DNS → Records → Add Record:

| Type  | Name  | Target                 | Proxy Status             | TTL  |
| ----- | ----- | ---------------------- | ------------------------ | ---- |
| CNAME | `api` | `ghs.googlehosted.com` | **DNS Only** (initially) | Auto |
| CNAME | `app` | `ghs.googlehosted.com` | **DNS Only** (initially) | Auto |

> ⚠️ **CRITICAL:** Keep proxy status as "DNS Only" (grey cloud) initially!

### 4.2 Wait for SSL Certificate Provisioning

Google Cloud Run needs to verify domain ownership and provision SSL certificates:

```bash
# Check domain mapping status
gcloud run domain-mappings describe \
  --domain api.gnxautomation.com \
  --region us-central1 \
  --format='value(status.conditions)'
```

Wait for status to show `CertificateProvisioned: True` (typically 10-20 minutes).

### 4.3 Enable Cloudflare Proxy

Once certificates are provisioned:

1. Go to Cloudflare Dashboard → DNS
2. Find the `api` and `app` records
3. Click the proxy status toggle to change from grey cloud to **orange cloud** (Proxied)
4. Save changes

### 4.4 Create Page Rule for SSL Certificate Renewal

To prevent future SSL renewal issues:

1. Go to Cloudflare Dashboard → Rules → Page Rules
2. Create new rule:
   - URL: `*gnxautomation.com/.well-known/acme-challenge/*`
   - Setting: **SSL = Off** (or Disable Security)
   - Setting: **Cache Level = Bypass**
3. Save and deploy

---

## Phase 5: SSL/TLS Setup

### 5.1 Configure SSL Mode

1. Go to Cloudflare Dashboard → SSL/TLS → Overview
2. Change encryption mode from **Full** to **Full (Strict)**

### 5.2 Enable Additional Security

1. **Edge Certificates → Always Use HTTPS:** ON
2. **Edge Certificates → Automatic HTTPS Rewrites:** ON
3. **Edge Certificates → Minimum TLS Version:** TLS 1.2

---

## Zero-Downtime Deployments

### Strategy: Traffic Splitting with Revisions

Cloud Run automatically creates new revisions for each deployment. Use traffic splitting for zero-downtime updates.

### Option 1: Simple Deployment (Automatic Rollout)

```bash
# Deploy new version - automatically receives 100% traffic
gcloud run deploy cis-api \
  --source . \
  --dockerfile Dockerfile.api \
  --region us-central1
```

### Option 2: Canary Deployment (Gradual Rollout)

```bash
# Step 1: Deploy new revision with NO traffic
gcloud run deploy cis-api \
  --source . \
  --dockerfile Dockerfile.api \
  --region us-central1 \
  --no-traffic \
  --tag canary

# Step 2: Test canary at unique URL
# https://canary---cis-api-xxxxxxxxxx-uc.a.run.app

# Step 3: Route 10% traffic to canary
gcloud run services update-traffic cis-api \
  --region us-central1 \
  --to-tags canary=10

# Step 4: Monitor metrics, then increase traffic
gcloud run services update-traffic cis-api \
  --region us-central1 \
  --to-tags canary=50

# Step 5: Full rollout
gcloud run services update-traffic cis-api \
  --region us-central1 \
  --to-latest
```

### Instant Rollback

```bash
# List revisions
gcloud run revisions list --service cis-api --region us-central1

# Rollback to specific revision
gcloud run services update-traffic cis-api \
  --region us-central1 \
  --to-revisions cis-api-00005-abc=100
```

---

## CI/CD Pipeline

### Cloud Build Configuration

The project includes `cloudbuild.yaml` for automated deployments.

### Setup Automated Deployments

#### 1. Connect Repository

```bash
# Create Cloud Build trigger
gcloud builds triggers create github \
  --repo-name=Linkedin_agent \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml \
  --substitutions=_CLERK_SECRET_KEY=xxx,_SUPABASE_URL=xxx,...
```

#### 2. Store Secrets in Secret Manager

```bash
# Create secrets
echo -n "your-clerk-secret-key" | gcloud secrets create CLERK_SECRET_KEY --data-file=-
echo -n "your-supabase-url" | gcloud secrets create SUPABASE_URL --data-file=-

# Grant Cloud Build access
gcloud secrets add-iam-policy-binding CLERK_SECRET_KEY \
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Enhanced cloudbuild.yaml (with traffic splitting)

```yaml
steps:
  # Build API container
  - name: "gcr.io/cloud-builders/docker"
    args:
      [
        "build",
        "-t",
        "gcr.io/$PROJECT_ID/cis-api:$COMMIT_SHA",
        "-f",
        "Dockerfile.api",
        ".",
      ]

  # Build Frontend container
  - name: "gcr.io/cloud-builders/docker"
    args:
      [
        "build",
        "-t",
        "gcr.io/$PROJECT_ID/cis-frontend:$COMMIT_SHA",
        "-f",
        "Dockerfile.frontend",
        ".",
      ]

  # Push containers
  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "gcr.io/$PROJECT_ID/cis-api:$COMMIT_SHA"]
  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "gcr.io/$PROJECT_ID/cis-frontend:$COMMIT_SHA"]

  # Deploy API as canary (no traffic initially)
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: gcloud
    args:
      - "run"
      - "deploy"
      - "cis-api"
      - "--image=gcr.io/$PROJECT_ID/cis-api:$COMMIT_SHA"
      - "--region=us-central1"
      - "--platform=managed"
      - "--no-traffic"
      - "--tag=canary"

  # Route 10% traffic to canary for testing
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: gcloud
    args:
      - "run"
      - "services"
      - "update-traffic"
      - "cis-api"
      - "--region=us-central1"
      - "--to-tags=canary=10"

  # Deploy Frontend (simple rollout - frontend is safer)
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: gcloud
    args:
      - "run"
      - "deploy"
      - "cis-frontend"
      - "--image=gcr.io/$PROJECT_ID/cis-frontend:$COMMIT_SHA"
      - "--region=us-central1"
      - "--platform=managed"
      - "--allow-unauthenticated"

images:
  - "gcr.io/$PROJECT_ID/cis-api:$COMMIT_SHA"
  - "gcr.io/$PROJECT_ID/cis-frontend:$COMMIT_SHA"

options:
  logging: CLOUD_LOGGING_ONLY
```

---

## Monitoring & Observability

### Google Cloud Monitoring

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cis-api" --limit=50

# Stream logs in real-time
gcloud alpha run services logs read cis-api --tail=50
```

### Set Up Alerts

1. Go to Google Cloud Console → Monitoring → Alerting
2. Create alerting policies for:
   - **Request latency > 2s** (95th percentile)
   - **Error rate > 1%**
   - **Instance count approaching max**
   - **Memory utilization > 80%**

### Cloudflare Analytics

1. Go to Cloudflare Dashboard → Analytics
2. Monitor:
   - Request volume
   - Cached vs uncached requests
   - Security threats blocked
   - Geographic distribution

---

## Troubleshooting

### Common Issues and Solutions

#### SSL Certificate Not Provisioning

**Symptom:** `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`

**Solution:**

1. Ensure Cloudflare proxy is OFF (DNS Only) for new records
2. Wait 10-20 minutes for Google to provision certificates
3. Check domain mapping status:
   ```bash
   gcloud run domain-mappings describe --domain api.gnxautomation.com
   ```

#### Too Many Redirects

**Symptom:** `ERR_TOO_MANY_REDIRECTS`

**Solution:**

1. Set Cloudflare SSL mode to "Full (Strict)"
2. Disable "Always Use HTTPS" temporarily to test
3. Check if both Cloudflare and Cloud Run are forcing HTTPS

#### CORS Errors

**Symptom:** `Access-Control-Allow-Origin` errors

**Solution:**
Ensure `main.py` has correct CORS configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.gnxautomation.com", "https://gnxautomation.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Cold Start Latency

**Symptom:** First request takes 5-10 seconds

**Solution:**
Set minimum instances:

```bash
gcloud run services update cis-api --min-instances 1
```

Note: This incurs costs (~$25/month for 1 always-on instance)

---

## Cost Estimation

### Google Cloud Run (Pay-per-use)

| Resource       | Free Tier                  | Beyond Free Tier        |
| -------------- | -------------------------- | ----------------------- |
| **Requests**   | 2 million/month            | $0.40/million           |
| **CPU**        | 180,000 vCPU-seconds/month | $0.00002400/vCPU-second |
| **Memory**     | 360,000 GiB-seconds/month  | $0.00000250/GiB-second  |
| **Networking** | 1 GB egress/month          | $0.12/GB                |

### Estimated Monthly Costs

| Scenario                             | API    | Frontend | Total      |
| ------------------------------------ | ------ | -------- | ---------- |
| **Low traffic** (1K users/month)     | $0     | $0       | **$0**     |
| **Medium traffic** (10K users/month) | $5-10  | $2-5     | **$7-15**  |
| **High traffic** (100K users/month)  | $30-50 | $10-20   | **$40-70** |
| **With min instances**               | +$25   | +$12     | **+$37**   |

### Other Costs

| Service                        | Cost      |
| ------------------------------ | --------- |
| Cloudflare Free Plan           | $0        |
| GoDaddy Domain Renewal         | ~$20/year |
| Cloud Build (120 min/day free) | $0        |

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets stored in Secret Manager, not in code
- [ ] `.env` files in `.gitignore`
- [ ] CORS configured for production domains only
- [ ] Rate limiting enabled on API
- [ ] Input validation on all endpoints

### Cloudflare Security

- [ ] WAF rules enabled
- [ ] Bot protection enabled
- [ ] DDoS protection (automatic)
- [ ] SSL/TLS mode set to Full (Strict)
- [ ] HSTS enabled

### Google Cloud Security

- [ ] IAM roles follow least privilege principle
- [ ] Cloud Run services use dedicated service accounts
- [ ] VPC connector for private database access (if needed)
- [ ] Cloud Armor (optional, for advanced WAF)

### Application Security

- [ ] Clerk authentication on protected endpoints
- [ ] HTTPS only (HTTP redirected)
- [ ] Secure headers configured (CSP, X-Frame-Options, etc.)
- [ ] API keys rotated regularly
- [ ] Logs don't contain sensitive data

---

## Quick Reference Commands

```bash
# Deploy
gcloud run deploy cis-api --source . --dockerfile Dockerfile.api

# Check status
gcloud run services describe cis-api

# View logs
gcloud alpha run services logs read cis-api --tail=100

# Update traffic
gcloud run services update-traffic cis-api --to-latest

# Rollback
gcloud run services update-traffic cis-api --to-revisions=REVISION_NAME=100

# Scale
gcloud run services update cis-api --min-instances=1 --max-instances=20

# Delete (careful!)
gcloud run services delete cis-api
```

---

## Support & Resources

- **Google Cloud Run Docs:** https://cloud.google.com/run/docs
- **Cloudflare Docs:** https://developers.cloudflare.com
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/

---

_Document Version: 1.0_  
_Created: December 11, 2024_  
_Author: GNX AIS Development Team_
