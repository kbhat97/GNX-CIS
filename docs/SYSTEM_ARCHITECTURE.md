# GNX CIS - System Architecture & User Flow

**Date:** 2025-12-22  
**Version:** 2.0.0

---

## 🎯 High-Level Overview

**GNX CIS (Content Intelligence System)** is an AI-native, multi-agent platform that transforms thought leadership ideas into high-impact LinkedIn content. The system orchestrates specialized AI agents to create, score, refine, and publish content automatically.

---

## 🏗️ System Architecture

### **Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │   Dashboard (SPA) - Glassmorphic UI                        │    │
│  │   - Onboarding  - Generate  - History  - Settings          │    │
│  └──────────────────────┬─────────────────────────────────────┘    │
└─────────────────────────┼───────────────────────────────────────────┘
                          │ HTTPS (Clerk JWT Auth)
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (main.py)                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  API Routes:                                             │      │
│  │  /health, /auth/*, /onboarding/*, /api/generate,        │      │
│  │  /api/posts/*, /api/settings/*, /api/create-checkout    │      │
│  └──────────────────────┬───────────────────────────────────┘      │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   CLERK      │ │   SUPABASE   │ │   STRIPE     │
│   (Auth)     │ │  (Database)  │ │  (Payment)   │
└──────────────┘ └──────────────┘ └──────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │     MULTI-AGENT SYSTEM          │
        │  ┌─────────────────────────┐   │
        │  │  1. Content Agent       │   │
        │  │  2. Virality Agent      │   │
        │  │  3. History Agent       │   │
        │  │  4. Publisher Agent     │   │
        │  │  5. Reflector Agent     │   │
        │  │  6. Engagement Agent    │   │
        │  └─────────────────────────┘   │
        └─────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ GOOGLE       │ │   GOOGLE     │ │   IMAGEN     │
│ GEMINI API   │ │  AI PLATFORM │ │     API      │
│ (2.0 Flash)  │ │  (Embedding) │ │  (Images)    │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 📂 System Components

### **1. Frontend - Dashboard** (`/dashboard`)

**Technology:** Vanilla HTML + CSS + JavaScript (Glassmorphic Design)

**Pages:**

- `app.html` - Main dashboard SPA (all-in-one interface)
- `pricing.html` - Subscription pricing page

**Key Features:**

- ✅ Glassmorphic UI with modern animations
- ✅ Real-time post generation with loading states
- ✅ Post history with filtering and search
- ✅ Settings panel (LinkedIn integration, admin controls)
- ✅ Responsive design

---

### **2. Backend - FastAPI** (`main.py`)

**Technology:** Python 3.13 + FastAPI + Uvicorn

**Core Responsibilities:**

- Authentication via Clerk JWT
- API endpoint orchestration
- Agent coordination
- Supabase database operations
- Stripe payment processing
- Rate limiting (10 posts/hour)

**Key Modules:**

```python
main.py (2768 lines)
├── Authentication (Clerk JWT validation)
├── Onboarding endpoints
├── Post generation (multi-agent orchestration)
├── Post management (CRUD operations)
├── Subscription management (Stripe)
├── Settings & LinkedIn integration
└── Health checks & error handling
```

---

### **3. Multi-Agent System** (`/agents`)

Each agent is a specialized AI with a specific responsibility:

#### **🎯 1. Content Agent** (`content_agent.py`)

- **Role:** Primary content creator
- **Capabilities:**
  - Analyzes user's industry, audience, and voice
  - Applies psychological hooks (FOMO, Pattern Interrupt, Authority, etc.)
  - Generates LinkedIn posts in various styles (Story, Data-Driven, How-To, etc.)
  - Uses hook history to avoid repetition
  - Integrates persona data (for admin mode)
- **AI Model:** Google Gemini 2.0 Flash

#### **📊 2. Virality Agent** (`virality_agent.py`)

- **Role:** Unbiased content scorer
- **Capabilities:**
  - Scores posts from 0-100 based on virality potential
  - Evaluates: hook strength, readability, emotional resonance
  - Provides actionable improvement suggestions
  - Prevents LLM self-evaluation bias
- **AI Model:** Google Gemini 2.0 Flash

#### **📚 3. History Agent** (`history_agent.py`)

- **Role:** Context provider and learning engine
- **Capabilities:**
  - Fetches user's post history from Supabase
  - Identifies patterns and successful hooks
  - Provides personalized writing insights
  - Feeds context to Content Agent
- **Data Source:** Supabase `posts` table

#### **📤 4. Publisher Agent** (`publisher_agent.py`)

- **Role:** LinkedIn publishing automation
- **Capabilities:**
  - Posts content directly to LinkedIn
  - Handles image uploads
  - Manages OAuth tokens
  - Error handling and retries
- **Integration:** LinkedIn Marketing API

#### **🔄 5. Reflector Agent** (`reflector_agent.py`)

- **Role:** Content improvement specialist
- **Capabilities:**
  - Analyzes underperforming content
  - Suggests specific improvements
  - Re-writes posts based on feedback
  - Iterative refinement loop

#### **💬 6. Engagement Agent** (`engagement_agent.py`)

- **Role:** Response generator
- **Capabilities:**
  - Generates contextual comment replies
  - Maintains brand voice consistency
  - Suggests engagement strategies

---

### **4. Database - Supabase** (`/database`)

**Technology:** PostgreSQL via Supabase

**Schema Overview:**

```sql
users
├── id (uuid, PK)
├── clerk_id (text, unique) -- Links to Clerk auth
├── email (text)
├── full_name (text)
├── onboarding_completed (boolean)
├── subscription_status (text) -- free, pro, business
└── created_at (timestamp)

user_profiles
├── id (uuid, PK)
├── user_id (uuid, FK → users.id)
├── writing_tone (text)
├── target_audience (text)
├── key_values (text[])
├── personality_traits (text[])
├── content_focus (text)
└── brand_voice_summary (text)

posts
├── id (uuid, PK)
├── user_id (uuid, FK → users.id)
├── topic (text)
├── style (text)
├── content (text)
├── virality_score (numeric)
├── improvement_suggestions (text)
├── hook (text) -- Psychological hook used
├── image_url (text)
├── status (text) -- draft, published
├── linkedin_post_id (text) -- For published posts
├── created_at (timestamp)
└── updated_at (timestamp)

virality_calibration
├── id (uuid, PK)
├── user_id (uuid, FK → users.id)
├── post_id (uuid, FK → posts.id)
├── feedback_score (integer) -- User's rating
└── created_at (timestamp)

subscriptions (via Stripe webhook)
├── user_id (uuid)
├── stripe_customer_id (text)
├── stripe_subscription_id (text)
├── plan (text) -- pro, business
├── status (text) -- active, canceled, past_due
└── current_period_end (timestamp)
```

**Row-Level Security (RLS):** ✅ Enabled on all tables

---

### **5. Authentication - Clerk**

**Technology:** Clerk (Enterprise SSO)

**Flow:**

1. User signs up/logs in via Clerk hosted UI
2. Clerk issues JWT token
3. Frontend stores token in `localStorage`
4. Backend validates JWT via JWKS (no API calls to Clerk)
5. Creates/retrieves user in Supabase via `clerk_id`

**Admin Roles:**

- Admin emails defined in `config.py`
- Admins can use persona mode (pre-configured voice profiles)

---

### **6. Payment System - Stripe**

**Technology:** Stripe Checkout + Webhooks

**Plans:**
| Plan | Price | Post Limit | Features |
|------|-------|------------|----------|
| Free | $0 | 5/month | Basic generation |
| Pro | $29/mo | 30/month | All features + analytics |
| Business | $99/mo | 200/month | Priority support + white-label |

**Webhook Events:**

- `checkout.session.completed` → Activate subscription
- `invoice.payment_succeeded` → Renew subscription
- `customer.subscription.deleted` → Cancel subscription

**Secrets:** Stored in GCP Secret Manager (see `docs/stripe_secrets_migration.md`)

---

### **7. Utilities** (`/utils`)

**Key Utilities:**

| File                 | Purpose                              |
| -------------------- | ------------------------------------ |
| `rate_limiter.py`    | Post generation limits (10/hour)     |
| `image_generator.py` | AI image generation via Imagen API   |
| `cache.py`           | Redis-like caching for API responses |
| `hook_history.py`    | Track used hooks to avoid repetition |
| `secret_manager.py`  | GCP Secret Manager integration       |
| `sanitizer.py`       | Content safety and validation        |
| `health_check.py`    | System health monitoring             |

---

## 👤 User Flow

### **🚀 1. Onboarding Flow**

```
┌─────────────┐
│  Sign Up    │ → Clerk Authentication
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Questionnaire  │ → Save to user_profiles table
└──────┬──────────┘   - Writing tone
       │               - Target audience
       │               - Key values
       │               - Content focus
       ▼
┌─────────────────┐
│  Dashboard      │ → onboarding_completed = true
└─────────────────┘
```

**Questionnaire Fields:**

1. **Writing Tone:** Professional, Conversational, Thought-Leadership
2. **Target Audience:** Industry, seniority, interests
3. **Core Values:** Innovation, Integrity, Growth, etc.
4. **Personality:** Analytical, Creative, Direct
5. **Posting Frequency:** Daily, Weekly, As-needed
6. **Content Focus:** Topic areas

---

### **📝 2. Post Generation Flow**

```
┌──────────────────┐
│  User Input      │
│  - Topic         │
│  - Style (opt)   │
│  - Image? (bool) │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  BACKEND: Rate Limiter Check           │
│  - Free: 5/month                       │
│  - Pro: 30/month                       │
│  - Business: 200/month                 │
└────────┬───────────────────────────────┘
         │ ✅ Within limit
         ▼
┌────────────────────────────────────────┐
│  STEP 1: History Agent                 │
│  - Fetch user's post history           │
│  - Identify successful hooks           │
│  - Build context for Content Agent     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  STEP 2: Content Agent                 │
│  - Load user profile (audience, tone)  │
│  - Select psychological hook           │
│  - Generate post content               │
│  - Apply style-specific formatting     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  STEP 3: Virality Agent                │
│  - Score content (0-100)               │
│  - Analyze hook effectiveness          │
│  - Provide improvement suggestions     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  STEP 4: Image Generation (Optional)   │
│  - Extract headline from post          │
│  - Generate AI image via Imagen        │
│  - Return public URL                   │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  STEP 5: Save to Database              │
│  - Insert into posts table             │
│  - Store hook used (for history)       │
│  - Status = "draft"                    │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  RESPONSE TO FRONTEND                  │
│  {                                     │
│    content: "...",                     │
│    virality_score: 85,                 │
│    suggestions: [...],                 │
│    image_url: "https://...",           │
│    post_id: "uuid"                     │
│  }                                     │
└────────────────────────────────────────┘
```

**Timing:**

- ⏱️ Total: ~8-12 seconds
- History retrieval: ~500ms
- Content generation: ~4-6s
- Virality scoring: ~2-3s
- Image generation: ~3-5s (if enabled)

---

### **📊 3. Post Management Flow**

#### **View History**

```
GET /api/posts?user_id={id}&limit=50
  ↓
Fetch from Supabase posts table (with RLS)
  ↓
Return sorted by created_at DESC
```

#### **Improve Post**

```
POST /api/improve/{post_id}
  ↓
Fetch original post + suggestions
  ↓
Reflector Agent re-writes content
  ↓
Virality Agent re-scores
  ↓
Update existing post (version tracking)
```

#### **Publish to LinkedIn**

```
POST /api/publish/{post_id}
  ↓
Check LinkedIn token validity
  ↓
Publisher Agent posts via LinkedIn API
  ↓
Update post.status = "published"
  ↓
Store linkedin_post_id for tracking
```

---

### **💳 4. Subscription Flow**

```
┌──────────────────┐
│  User clicks     │
│  "Upgrade to Pro"│
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  POST /api/create-checkout             │
│  {                                     │
│    plan: "pro",                        │
│    promo_code: "LAUNCH50" (optional)   │
│  }                                     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  Stripe Checkout Session Created       │
│  - 30-day free trial                   │
│  - Return URL: /dashboard?checkout=ok  │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  User completes payment on Stripe      │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  Stripe Webhook: checkout.completed    │
│  → Update users.subscription_status    │
│  → Log in subscriptions table          │
└────────────────────────────────────────┘
```

---

### **⚙️ 5. Settings & Integrations**

#### **LinkedIn Integration**

```
1. User clicks "Connect LinkedIn"
2. OAuth flow → LinkedIn auth screen
3. User approves → Redirect with auth code
4. Backend exchanges code for access_token
5. Save token to user_profiles.linkedin_token
6. Publisher Agent can now post directly
```

#### **Admin Persona Mode**

```
1. Admin user logs in
2. System detects email in ADMIN_EMAILS
3. UI shows "Persona Mode" toggle
4. When enabled:
   - Load persona from /personas/persona_admin_kunal.json
   - Content Agent uses persona data instead of user_profile
   - Generates content in pre-defined voice
```

---

## 🔐 Security Architecture

### **Authentication Layers**

```
┌─────────────────────────────────────────┐
│  Layer 1: Clerk JWT Validation          │
│  - RS256 signature verification         │
│  - JWKS public key rotation             │
│  - Audience validation                  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Layer 2: Supabase RLS                  │
│  - Row-Level Security enabled           │
│  - user_id = auth.uid() filters         │
│  - Service role bypass for admin        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Layer 3: Rate Limiting                 │
│  - 10 posts/hour per user               │
│  - Subscription tier enforcement        │
│  - DDoS protection via Cloud Armor      │
└─────────────────────────────────────────┘
```

### **Secret Management**

- ✅ All production secrets in GCP Secret Manager
- ✅ Secrets mounted as env vars in Cloud Run
- ✅ No secrets in codebase
- ✅ Automatic rotation supported

---

## 🚀 Deployment Architecture

### **Infrastructure**

```
┌─────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD                         │
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │  Cloud Build (CI/CD)                          │    │
│  │  - Triggered by: git push origin master       │    │
│  │  - Build Docker images (API + Frontend)       │    │
│  │  - Run tests                                  │    │
│  │  - Deploy to Cloud Run                        │    │
│  └───────────────────────────────────────────────┘    │
│                         │                              │
│                         ▼                              │
│  ┌───────────────────────────────────────────────┐    │
│  │  Cloud Run                                    │    │
│  │  ┌─────────────────┐  ┌──────────────────┐   │    │
│  │  │  cis-api        │  │  cis-frontend    │   │    │
│  │  │  (FastAPI)      │  │  (Static Nginx)  │   │    │
│  │  │  Port: 8080     │  │  Port: 8080      │   │    │
│  │  └─────────────────┘  └──────────────────┘   │    │
│  │                                               │    │
│  │  Auto-scaling: 0 → 100 instances             │    │
│  │  Region: us-central1                         │    │
│  └───────────────────────────────────────────────┘    │
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │  Secret Manager                               │    │
│  │  - STRIPE_SECRET_KEY                          │    │
│  │  - GOOGLE_API_KEY                             │    │
│  │  - SUPABASE_SERVICE_KEY                       │    │
│  │  - All production secrets                     │    │
│  └───────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘

         External Services (SaaS)
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Clerk   │  │ Supabase │  │  Stripe  │
    │  (Auth)  │  │   (DB)   │  │ (Payment)│
    └──────────┘  └──────────┘  └──────────┘
```

---

## 📊 Data Flow Summary

### **Typical Request Lifecycle**

```
1. Frontend → Request with Clerk JWT
                ↓
2. FastAPI → Validate JWT via JWKS
                ↓
3. FastAPI → Check rate limiter (Supabase query)
                ↓
4. FastAPI → Orchestrate agents
                ├→ History Agent (Supabase)
                ├→ Content Agent (Gemini API)
                ├→ Virality Agent (Gemini API)
                └→ Image Gen (Imagen API)
                ↓
5. FastAPI → Save to Supabase (posts table)
                ↓
6. Frontend ← JSON response (content + score + image)
```

**Average Latency:** 8-12 seconds (mostly AI generation)

---

## 🎯 Key Differentiators

### **What Makes GNX CIS Unique?**

1. **Multi-Agent Orchestration**

   - Not a single AI, but a coordinated team
   - Each agent specializes in one task
   - Agents share context and collaborate

2. **Unbiased Scoring**

   - Separate Virality Agent prevents LLM self-evaluation bias
   - Content Agent generates, Virality Agent scores
   - Reflector Agent improves based on feedback

3. **Learning Engine**

   - History Agent tracks successful patterns
   - Hook history prevents repetition
   - Continuous improvement via user feedback

4. **Enterprise-Grade**

   - JWT authentication + RLS
   - Rate limiting + subscription tiers
   - Cloud Run auto-scaling
   - 99.9% uptime SLA

5. **AI-Native Design**
   - Built for AI workflows from day one
   - Human-in-the-loop only when needed
   - Autonomous quality control

---

## 📈 Future Roadmap

### **Planned Features**

- [ ] **Multi-platform support** (Twitter/X, Medium, Substack)
- [ ] **Team collaboration** (shared personas, approval workflows)
- [ ] **Analytics dashboard** (engagement tracking, A/B testing)
- [ ] **Voice cloning** (audio content generation)
- [ ] **Advanced personalization** (ML-based voice modeling)
- [ ] **API access** (headless CMS integration)

---

## 📞 Contact & Support

**Email:** kunalsbhatt@gmail.com  
**Documentation:** `/docs` folder  
**Issues:** Contact admin for bug reports

---

**© 2025 GNX. All Rights Reserved.**

_Building the AI-native future, one agent at a time._
