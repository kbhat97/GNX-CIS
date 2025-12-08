# 🚀 GNX CIS - Content Intelligence System

**AI-Powered LinkedIn Content Generation Platform**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.29-red.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://ai.google.dev/gemini-api)
[![Tests](https://img.shields.io/badge/tests-37%20passing-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/tasks-99%25%20complete-success.svg)]()

Generate viral LinkedIn posts with AI, score them for engagement potential, and iteratively improve your content with real-time feedback.

---

## ✨ Features

### 🤖 **AI-Powered Content Generation**

- **Gemini 2.5 Flash** for lightning-fast content creation (5-10s)
- 12 unique hook patterns for variety
- Professional, Technical, Inspirational, Casual, and Thought Leadership styles
- Custom persona integration

### 📊 **Virality Scoring**

- **Gemini 2.0 Flash** for accurate engagement prediction
- 0-100 scoring scale with detailed breakdown
- 8 scoring criteria: Hook Strength, Value Delivery, Emotional Resonance, CTA, Readability, Authority, Shareability, Hashtag Relevance
- Bonus points for metrics, contrarian views, and questions

### 🔄 **Iterative Improvement**

- "Improve This Post" feature with custom feedback
- Side-by-side comparison of different versions
- Track score improvements over iterations
- Full post history with session state

### 📈 **Performance Dashboard**

- Total posts generated
- Average virality score
- Best performing posts
- Excellent posts count (80+ score)

### 🖼️ **Image Generation**

- Branded 1200x675 LinkedIn images
- Custom Poppins typography
- Professional layouts
- **Download/Save generated images** with one click 🆕
- Local storage (no cloud dependencies)

### 💾 **Persistent Storage** 🆕

- **Supabase integration** for database persistence
- Auto-save all generated posts to cloud database
- **Restore posts on page reload** - never lose your work
- User-specific data isolation
- Cross-device access to your content library

### 🔐 **Authentication & Security**

- **Clerk Authentication** for secure login/signup
- Session management with 30-min timeout
- Input sanitization & prompt injection prevention
- Content moderation with profanity/spam detection

### 💎 **Premium UI/UX**

- Glassmorphism dark theme
- GNX branded header with user avatar
- Hamburger sidebar with post history
- WCAG-compliant input contrast
- Mobile responsive design

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              HTML Dashboard (TailwindCSS)                │
│  (dashboard/app.html)                                   │
│  - Glassmorphism UI                                     │
│  - Real-time post generation                            │
│  - Supabase JS client integration                       │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Backend                      │
│  (http://localhost:8080)                                │
│  - RESTful API endpoints                                │
│  - Agent orchestration                                  │
│  - Authentication (Clerk)                               │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                    Agent Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ContentAgent  │  │ViralityAgent │  │ImageGenerator│ │
│  │  (Gemini)    │  │  (Gemini)    │  │    (PIL)     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                Supabase (PostgreSQL) 🆕                 │
│  - User management (users table)                        │
│  - Post storage (posts table)                           │
│  - Persistent state across sessions                     │
│  - Real-time sync                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Google Gemini API Key
- Windows OS (tested) or Linux/macOS

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/kbhat97/GNX-CIS.git
cd GNX-CIS
```

2. **Create virtual environment**

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

5. **Run the application**

**Option 1: Dashboard Only (Recommended for testing)**

```bash
streamlit run dashboard.py
```

Open http://localhost:8501

**Option 2: Full Stack (Dashboard + API)**

```bash
# Terminal 1: Start API
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Start Dashboard
streamlit run dashboard.py
```

---

## 📖 Usage Guide

### **Generate Your First Post**

1. Enter a topic (e.g., "SAP S/4HANA migration with Azure OpenAI")
2. Select a style (Technical, Inspirational, etc.)
3. Click "🚀 Generate Post"
4. Review your post, score, and suggestions

### **Improve a Post**

1. Click "🔄 Improve" on any post in history
2. Enter feedback (e.g., "Make it more technical with specific metrics")
3. Generate improved version
4. Compare scores to see improvement

### **Compare Posts**

1. Enable "📊 Compare Mode" in sidebar
2. Select 2 posts
3. View side-by-side comparison with score differences

### **Pro Tips**

- Generate 3-5 versions of the same topic with different styles
- Use "Improve" to iterate based on AI suggestions
- Aim for 80+ virality score for maximum engagement
- Technical content: Include data, metrics, and specific examples
- Thought leadership: Be contrarian and thought-provoking
- Personal stories: Be vulnerable and authentic

---

## 🎯 Performance Metrics

| Metric               | Target          | Current  |
| -------------------- | --------------- | -------- |
| Generation Speed     | <10s            | 5-10s ✅ |
| Virality Score Range | 70-90           | 70-90 ✅ |
| Hook Variety         | 10+ patterns    | 12 ✅    |
| Stability            | 10+ consecutive | 20+ ✅   |
| Success Rate         | >95%            | ~98% ✅  |

---

## 🛠️ Configuration

### **Model Configuration** (`utils/gemini_config.py`)

```python
CONTENT_MODEL = "gemini-2.5-flash"      # Fast content generation
SCORING_MODEL = "gemini-2.0-flash-exp"  # Fast & accurate scoring
```

### **Environment Variables** (`.env`)

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Supabase (Required for persistent storage) 🆕
SUPABASE_URL=https://ijwmgwirhorksepabgpj.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Optional (for production features)
CLERK_SECRET_KEY=your_clerk_secret
```

### **Supabase Setup** 🆕

1. Run the database migration: `database/migrations/add_dashboard_columns.sql`
2. See full setup guide: `database/SUPABASE_SETUP.md`
3. Posts will auto-save and restore on reload

---

## 📁 Project Structure

```
GNX-CIS/
├── agents/              # AI agents (Content, Virality)
│   ├── content_agent.py
│   ├── virality_agent.py
│   └── base_agent.py
├── utils/               # Utilities
│   ├── gemini_config.py
│   ├── json_parser.py
│   ├── image_generator.py
│   └── logger.py
├── static/              # Static assets
│   └── outputs/         # Generated images
├── logs/                # Application logs
├── dashboard.py         # Streamlit dashboard
├── main.py              # FastAPI backend
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md            # This file
```

---

## 🐛 Troubleshooting

### **Issue: Empty posts or score 50/100**

**Solution**: Check logs for JSON parsing errors. Usually caused by API rate limits.

### **Issue: "Event loop is closed" (FIXED)**

**Solution**: Latest version uses synchronous Gemini calls - no more async issues!

### **Issue: Image generation fails**

**Solution**: Check if PIL and fonts are installed. Images are optional - posts still generate.

### **Issue: Slow generation (>30s)**

**Solution**: Verify you're using `gemini-2.5-flash` not `gemini-3.0-pro`.

---

## 🚧 Roadmap

### **Phase 1: Core Features** ✅ COMPLETE

- [x] Content generation with Gemini
- [x] Virality scoring
- [x] Image generation
- [x] Dashboard UI
- [x] Post history
- [x] Comparison mode
- [x] Iterative improvement

### **Phase 2: Production Ready** ✅ COMPLETE

- [x] User authentication (Clerk)
- [x] Session management
- [x] Input sanitization & security
- [x] Content moderation
- [x] Structured logging
- [x] Error tracking (Sentry-ready)
- [x] Rate limiting
- [x] 37 tests passing (100%)

### **Phase 3: Scale & Polish** ✅ COMPLETE

- [x] Premium glassmorphism UI
- [x] GNX branding throughout
- [x] User profile with avatar
- [x] Accessibility compliance (WCAG)
- [x] Mobile responsive

### **Phase 4: Database & Persistence** ✅ COMPLETE 🆕

- [x] Supabase PostgreSQL integration
- [x] Auto-save posts to database
- [x] Restore state on page reload
- [x] User-specific data isolation
- [x] Download generated images

### **Phase 5: Coming Soon** 📋

- [ ] LinkedIn API integration
- [ ] Analytics dashboard
- [ ] A/B testing mode
- [ ] Multi-user collaboration

---

## 📊 Tech Stack

| Component     | Technology               | Purpose                 |
| ------------- | ------------------------ | ----------------------- |
| **Frontend**  | HTML + TailwindCSS 🆕    | Glassmorphism dashboard |
| **Backend**   | FastAPI                  | RESTful API             |
| **AI Models** | Google Gemini 2.5 Flash  | Content generation      |
| **Scoring**   | Google Gemini 2.0 Flash  | Virality prediction     |
| **Images**    | PIL (Pillow)             | Branded image creation  |
| **Database**  | Supabase (PostgreSQL) 🆕 | Persistent storage      |
| **Auth**      | Clerk (configured)       | User authentication     |

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is part of the GNX AIS ecosystem.

---

## 🙏 Acknowledgments

- **Google Gemini** for powerful AI models
- **Streamlit** for rapid UI development
- **FastAPI** for modern API framework
- **Pillow** for image generation

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/kbhat97/GNX-CIS/issues)
- **Documentation**: See `/docs` folder
- **Email**: support@gnx-ais.com

---

## 🎉 Success Stories

### **Case Study: Enterprise Thought Leadership**

- **Topic**: SAP S/4HANA migration with Azure OpenAI RAG
- **Iterations**: 3
- **Final Score**: 85/100
- **Result**: 2.5% predicted engagement rate

### **Case Study: Career Transition Post**

- **Topic**: Consultant to AI Engineer journey
- **Iterations**: 2
- **Final Score**: 82/100
- **Result**: Authentic, engaging personal narrative

---

## 🔥 Quick Commands

```bash
# Development
open dashboard/app.html                         # Open dashboard (no server needed for UI)
uvicorn main:app --reload                       # Start API backend (optional)

# Testing
python verify_models.py                         # Verify Gemini configuration
python diagnose_empty_posts.py                  # Debug generation issues
python test_dashboard_features.py               # Run feature tests

# Production
uvicorn main:app --host 0.0.0.0 --port 8080     # Production API
# Serve dashboard/app.html via any web server
```

---

**Built with ❤️ by the GNX AIS Team**

**Status**: ✅ Production Ready (Phase 4 Complete - 100%)  
**Version**: 3.0 🆕  
**Tests**: 37 Passing  
**New Features**: Supabase Persistence + Image Download  
**Last Updated**: December 8, 2025
