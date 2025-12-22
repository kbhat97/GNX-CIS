<div align="center">

<img src="docs/cis-hero.png" alt="GNX Content Intelligence System" width="100%">

# GNX Content Intelligence System

### **AI That Remembers You**

_Stop re-explaining yourself to AI every time. CIS learns who you are in 5 questions. The more you post, the smarter it gets._

[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen?style=for-the-badge)](https://cis.gnxautomation.com)
[![Google Cloud](https://img.shields.io/badge/Platform-Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

[**Get Started Free**](https://cis.gnxautomation.com) • [**Documentation**](docs/SYSTEM_ARCHITECTURE.md) • [**Pricing**](https://cis.gnxautomation.com/pricing.html)

</div>

---

## 🎯 What is CIS?

**CIS (Content Intelligence System)** is an AI-powered LinkedIn content generator with **persistent memory**. Unlike ChatGPT or Claude that forget you after every conversation, CIS builds a permanent understanding of your voice, audience, and style.

### **The Problem: Context Fatigue**

Every time you use ChatGPT/Claude/Gemini:

- ❌ "Tell me about your company again..."
- ❌ "Who's your target audience?"
- ❌ "What's your writing style?"
- ❌ You waste 5-10 minutes re-explaining context
- ❌ Output is generic and needs heavy editing

### **The Solution: Persistent Memory**

With CIS:

- ✅ Answer 5 questions once during onboarding
- ✅ CIS remembers forever
- ✅ Every post generated in YOUR voice
- ✅ Gets smarter with every post (learning agent)
- ✅ No more copy-paste context

---

## 🚀 How It Works

### **Three Simple Steps**

```
1. Answer 5 Questions (2 minutes)
   → Industry, audience, style, topics, goals

2. Generate Content
   → CIS remembers your profile automatically
   → Creates posts in YOUR voice, not generic AI

3. It Gets Smarter
   → Learning agent analyzes your patterns
   → After 20 posts, personalization is unstoppable
```

### **What Makes CIS Different**

| Feature             | ChatGPT / Claude          | CIS                                         |
| ------------------- | ------------------------- | ------------------------------------------- |
| **Memory**          | Resets every conversation | Permanent profile saved                     |
| **Learning**        | No improvement over time  | Learns from your post history               |
| **Platform**        | Generic for any use case  | Built specifically for LinkedIn             |
| **Personalization** | Requires manual prompting | Automatic from your saved profile           |
| **Virality**        | No optimization           | Scores posts 0-100 for engagement potential |

---

## ⚡ Key Features

### 🧠 **Persistent Memory**

- Your profile saved forever (industry, audience, style, topics)
- Never re-explain yourself
- Automatic context injection

### 📝 **5 Writing Styles**

- **Professional** - Formal, polished content
- **Technical** - Deep-dive explanations
- **Inspirational** - Motivational messaging
- **Storytelling** - Personal narrative
- **Thought Leadership** - Industry insights

### 📊 \***\*Virality Scoring**

- Every post scored 0-100
- Based on engagement potential
- Actionable improvement suggestions

### 🎨 **AI Image Generation** (Pro+)

- Auto-generate visuals for posts
- Powered by Google Imagen API
- Branded aesthetics

### 📚 **Smart Learning Agent**

- Analyzes your post history
- Identifies successful patterns
- After 20 posts, knows your voice better than you

### 🔗 **LinkedIn Publishing** (Business)

- One-click direct posting
- OAuth integration (secure)
- Scheduled publishing

### 📈 **Post History & Analytics**

- Track all generated posts
- Filter by style, score, status
- Performance insights

---

## 💳 Pricing

| Plan         | Price   | Posts/Month | Features                                         |
| ------------ | ------- | ----------- | ------------------------------------------------ |
| **Free**     | $0      | 5           | 3 styles, persona setup, basic features          |
| **Pro**      | $49/mo  | 30          | All 5 styles, image generation, learning agent   |
| **Business** | $199/mo | 200         | LinkedIn publishing, analytics, priority support |

**All paid plans include:**

- ✅ 30-day free trial (no credit card required)
- ✅ Cancel anytime
- ✅ Unlimited edits
- ✅ Virality scoring

[**View Full Pricing →**](https://cis.gnxautomation.com/pricing.html)

---

## 🛠️ Technology Stack

| Component      | Technology                    |
| -------------- | ----------------------------- |
| **Frontend**   | HTML/CSS/JS (Glassmorphic UI) |
| **Backend**    | FastAPI (Python 3.13)         |
| **AI Engine**  | Google Gemini 2.0 Flash       |
| **Database**   | Supabase (PostgreSQL + RLS)   |
| **Auth**       | Clerk (Enterprise SSO)        |
| **Payments**   | Stripe Checkout               |
| **Images**     | Google Imagen API             |
| **Deployment** | Google Cloud Run              |
| **CI/CD**      | Cloud Build                   |

---

## 📦 Quick Start

### **For Users**

1. **Sign up**: [https://cis.gnxautomation.com](https://cis.gnxautomation.com)
2. **Answer 5 onboarding questions** (2 minutes)
3. **Generate your first post** (topic + style)
4. **Edit, score, and use** (or publish directly)

### **For Developers**

```bash
# Clone repository
git clone https://github.com/kbhat97/GNX-CIS.git
cd GNX-CIS

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your API keys (Clerk, Supabase, Google AI, Stripe)

# Run locally
uvicorn main:app --reload
```

**Required API Keys:**

- `CLERK_SECRET_KEY` - Authentication
- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` - Database
- `GOOGLE_API_KEY` - AI generation
- `STRIPE_SECRET_KEY` - Payments (optional for local dev)

---

## 📚 Documentation

| Document                                                            | Description                                       |
| ------------------------------------------------------------------- | ------------------------------------------------- |
| **[SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)**           | Complete system design, data flows, user journeys |
| **[stripe_secrets_migration.md](docs/stripe_secrets_migration.md)** | GCP Secret Manager setup guide                    |
| **[PRE_COMMIT_REPORT.md](docs/PRE_COMMIT_REPORT.md)**               | Code quality validation                           |

### **Architecture Overview**

```
User → Dashboard (Clerk Auth)
         ↓
      FastAPI Backend
         ↓
    ┌────┴────┐
    │         │
Supabase   Google AI (Gemini 2.0)
(Profile)  (Content Generation)
    │         │
    └────┬────┘
         ↓
  Post Saved + Scored
```

### **Database Schema**

**`users`** - Clerk ID, email, subscription plan  
**`user_profiles`** - Industry, audience, style, topics (your "brain")  
**`posts`** - Generated content, virality scores, status  
**`virality_calibration`** - User feedback for learning

---

## 🔐 Security & Privacy

- ✅ **Clerk JWT authentication** (RS256 signatures)
- ✅ **Row-Level Security (RLS)** on all database tables
- ✅ **GCP Secret Manager** for production credentials
- ✅ **Encrypted at rest** (Supabase PostgreSQL)
- ✅ **HTTPS/TLS 1.3** for all connections
- ✅ **OAuth for LinkedIn** (never store passwords)

**Your data:** Encrypted, private, never sold. Delete anytime.

---

## 🧪 Development

```bash
# Run tests
pytest tests/ -v

# Code quality
ruff check .
mypy main.py

# Local development
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🚀 Deployment

**Production deployment on Google Cloud:**

```bash
git push origin master
# → Triggers Cloud Build
#   1. Build Docker images
#   2. Run tests
#   3. Deploy to Cloud Run
#   4. Inject secrets from GCP Secret Manager
```

**Infrastructure:**

- **Platform:** Google Cloud Run (auto-scaling 0→100 instances)
- **Region:** us-central1
- **Memory:** 2 GB per instance
- **Secrets:** GCP Secret Manager
- **Monitoring:** Cloud Logging

---

## ❓ FAQ

**Q: What's the 20-post learning minimum?**  
A: After 20 posts, the learning agent has enough data about your voice and style. Before that, it's learning. After 20, it's magic.

**Q: Can I try for free?**  
A: Yes! Free tier gives 5 posts/month forever. Pro/Business get 30-day free trials (no credit card).

**Q: Where is my data stored?**  
A: Supabase (encrypted PostgreSQL). Your profile data is only used to improve YOUR content. Never shared or sold.

**Q: Can I cancel anytime?**  
A: Yes. No questions asked. Your data stays on the free tier.

**Q: Is my LinkedIn account safe?**  
A: Yes. We use official LinkedIn OAuth. You control permissions. We never store your password.

**Q: What payment methods?**  
A: Credit cards (Visa, Master card, Amex) via Stripe. Secure and PCI-compliant.

---

## 📞 Contact

**Email:** kunalsbhatt@gmail.com  
**Website:** [https://cis.gnxautomation.com](https://cis.gnxautomation.com)  
**Support:** [support@gnxautomation.com](mailto:support@gnxautomation.com)

---

## 📄 License

**Proprietary Software - All Rights Reserved**

This source code is licensed exclusively for authorized GNX partners and clients. Unauthorized reproduction, reverse engineering, or distribution is prohibited.

See [LICENSE](LICENSE) for full terms.

---

<div align="center">

### _"Your AI finally knows what you actually want"_

**© 2025 GNX Automation. All Rights Reserved.**

Built with ❤️ using Google Gemini 2.0, Supabase, and Clerk

---

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge)](https://cis.gnxautomation.com)
[![Docs](https://img.shields.io/badge/Read-Docs-blue?style=for-the-badge)](docs/SYSTEM_ARCHITECTURE.md)

</div>
