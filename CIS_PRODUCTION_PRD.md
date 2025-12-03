# Product Requirements Document (PRD)
## LinkedIn Content Intelligence System (CIS) - Production Release

---

## Document Control

| Field | Value |
|-------|-------|
| **Product Name** | LinkedIn Content Intelligence System (CIS) |
| **Version** | 2.0 - Production Release |
| **Status** | In Development |
| **Author** | Product & Engineering Team |
| **Last Updated** | October 29, 2025 |
| **Baseline Reference** | `test_server.py` (100% test pass rate) |
| **Target Release** | Q4 2025 |

---

## Executive Summary

The LinkedIn Content Intelligence System (CIS) is an AI-powered platform that enables professionals to generate, manage, and publish high-quality LinkedIn content. This document outlines the requirements for transforming the validated proof-of-concept (`test_server.py`) into a production-ready SaaS application.

**Current State:** We have a fully validated API contract with 11 endpoints passing 100% of integration tests. The test server demonstrates all core functionality with mock data.

**Target State:** A production system with real authentication (Clerk), persistent storage (Supabase), AI content generation (Gemini), and LinkedIn publishing capabilities, deployed on Google Cloud Run.

**Success Baseline:** All production code must maintain compatibility with the validated test contract. If any component fails, we reference the working `test_server.py` implementation.

---

## Table of Contents

1. [Product Vision & Objectives](#1-product-vision--objectives)
2. [User Personas & Use Cases](#2-user-personas--use-cases)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Technical Architecture](#5-technical-architecture)
6. [API Specification](#6-api-specification)
7. [Data Model](#7-data-model)
8. [Security & Compliance](#8-security--compliance)
9. [Phase-by-Phase Implementation Plan](#9-phase-by-phase-implementation-plan)
10. [Testing Strategy](#10-testing-strategy)
11. [Deployment Strategy](#11-deployment-strategy)
12. [Success Metrics](#12-success-metrics)
13. [Risk Assessment](#13-risk-assessment)
14. [Appendix](#14-appendix)

---

## 1. Product Vision & Objectives

### 1.1 Vision Statement
Empower professionals to maintain a consistent, high-quality LinkedIn presence through AI-powered content generation that learns and adapts to their unique voice and expertise.

### 1.2 Product Objectives

**Primary Objectives:**
1. **Reduce Content Creation Time:** From 30 minutes to <5 minutes per post
2. **Improve Content Quality:** Achieve average virality score >7/10
3. **Increase Posting Consistency:** Enable 3-5 posts per week sustainably
4. **Maintain Authenticity:** Generate content indistinguishable from user's writing

**Secondary Objectives:**
1. Provide actionable content improvement suggestions
2. Enable data-driven content strategy decisions
3. Simplify LinkedIn publishing workflow
4. Build user confidence in AI-assisted content

### 1.3 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| System Uptime | >99.5% | Cloud monitoring |
| Content Generation Time | <30 seconds | API response time |
| User Satisfaction | >4.5/5 | In-app survey |
| Test Pass Rate | 100% | CI/CD pipeline |
| Error Rate | <1% | Error tracking |
| API Response Time (p95) | <500ms | APM tools |

---

## 2. User Personas & Use Cases

### 2.1 Primary Persona: "The Expert Practitioner"

**Profile:**
- **Name:** Sarah Chen
- **Role:** Senior SAP Consultant / Technical Lead
- **Age:** 35-50
- **LinkedIn Activity:** Posts 1-2x per week, 2000+ connections
- **Pain Points:**
  - "I have expertise but struggle to articulate it consistently"
  - "I don't have time to write thoughtful posts regularly"
  - "I'm not sure what content will resonate with my network"
  - "I want to maintain my authentic voice, not sound like AI"

**Goals:**
- Build thought leadership in SAP/Enterprise AI space
- Attract consulting opportunities and talent
- Share learnings from real projects
- Engage meaningfully with industry peers

### 2.2 Use Cases

#### UC-001: First-Time User Onboarding
**Actor:** New user  
**Precondition:** User has signed up via Clerk  
**Flow:**
1. User completes onboarding questionnaire (tone, audience, values, focus)
2. System creates user profile and analyzes style preferences
3. User connects LinkedIn account (OAuth)
4. System welcomes user and suggests first topic
5. User generates first draft post

**Success Criteria:** User generates first post within 5 minutes of signup

---

#### UC-002: Weekly Content Generation
**Actor:** Active user  
**Precondition:** User is authenticated and onboarded  
**Flow:**
1. User navigates to "Generate" tab
2. User enters topic (e.g., "SAP S/4HANA migration challenges")
3. System generates personalized content using AI agents
4. System scores content for virality potential
5. System displays draft with image and suggestions
6. User reviews, optionally edits
7. User clicks "Publish to LinkedIn"
8. System publishes post and confirms success

**Success Criteria:** End-to-end flow completes in <2 minutes

---

#### UC-003: Content Improvement Loop
**Actor:** Active user  
**Precondition:** User has published posts  
**Flow:**
1. System fetches engagement metrics from LinkedIn
2. System analyzes what content performed well
3. System updates user's style profile based on performance
4. Future content incorporates learnings
5. User sees improved engagement over time

**Success Criteria:** Measurable improvement in average engagement after 10 posts

---

## 3. Functional Requirements

### 3.1 Authentication & Authorization (MUST HAVE)

| Req ID | Requirement | Baseline Reference | Priority |
|--------|-------------|-------------------|----------|
| AUTH-001 | Users must authenticate via Clerk (email/password or Google OAuth) | `test_server.py` - JWT validation | P0 |
| AUTH-002 | System must validate JWT tokens on every API request | Lines 95-115 | P0 |
| AUTH-003 | Unauthenticated requests must return 401 Unauthorized | Test case validation | P0 |
| AUTH-004 | Tokens must auto-refresh before expiration | New requirement | P1 |
| AUTH-005 | Users can log out and invalidate sessions | Dashboard requirement | P1 |

**Acceptance Criteria:**
- ✅ User can sign up with email/password
- ✅ User can sign in with Google
- ✅ Invalid tokens are rejected with 401
- ✅ All authenticated endpoints require valid JWT
- ✅ Token refresh happens automatically

---

### 3.2 User Profile Management (MUST HAVE)

| Req ID | Requirement | Baseline Reference | Priority |
|--------|-------------|-------------------|----------|
| PROF-001 | System must create user record in Supabase on first login | `test_server.py` - GET /user/profile | P0 |
| PROF-002 | Users must complete onboarding questionnaire | POST /onboarding/questionnaire | P0 |
| PROF-003 | System must store user preferences (tone, audience, values) | Database schema | P0 |
| PROF-004 | Users can update their profile at any time | New endpoint needed | P1 |
| PROF-005 | System must link Clerk user ID to Supabase user record | User mapping logic | P0 |

**Acceptance Criteria:**
- ✅ New user completes questionnaire
- ✅ Profile data stored in `user_profiles` table
- ✅ User can view their profile
- ✅ User can edit profile settings
- ✅ Clerk ID correctly maps to Supabase user

---

### 3.3 Content Generation (MUST HAVE)

| Req ID | Requirement | Baseline Reference | Priority |
|--------|-------------|-------------------|----------|
| CONT-001 | System must generate post content from user-provided topic | `test_server.py` - POST /posts/generate | P0 |
| CONT-002 | Generated content must match user's writing style | ContentAgent integration | P0 |
| CONT-003 | System must score content for virality (0-10) | ViralityAgent | P0 |
| CONT-004 | System must provide actionable improvement suggestions | ViralityAgent output | P0 |
| CONT-005 | System must generate branded image for each post | ImageGenerator utility | P1 |
| CONT-006 | Generation must complete within 30 seconds | Performance requirement | P0 |
| CONT-007 | System must save all drafts to database | POST /posts/generate response | P0 |
| CONT-008 | Users can specify optional style (professional, casual, etc.) | Request parameter | P1 |

**Acceptance Criteria:**
- ✅ User enters topic, receives AI-generated content
- ✅ Content reflects user's profile preferences
- ✅ Virality score (0-10) displayed
- ✅ Suggestions for improvement shown
- ✅ Branded image generated and displayed
- ✅ Draft saved to database
- ✅ Generation completes in <30 seconds

---

### 3.4 Post Management (MUST HAVE)

| Req ID | Requirement | Baseline Reference | Priority |
|--------|-------------|-------------------|----------|
| POST-001 | Users can view all pending draft posts | GET /posts/pending | P0 |
| POST-002 | Users can view all published posts | GET /posts/published | P0 |
| POST-003 | Users can edit draft post content | PUT /posts/{id} | P0 |
| POST-004 | Users can delete draft posts | DELETE /posts/{id} (new) | P1 |
| POST-005 | System must track post status (draft, published) | Database field | P0 |
| POST-006 | System must timestamp all post actions | created_at, updated_at, published_at | P0 |

**Acceptance Criteria:**
- ✅ Pending drafts displayed in dashboard
- ✅ Published posts displayed separately
- ✅ User can edit draft content inline
- ✅ User can delete unwanted drafts
- ✅ All posts have correct timestamps

---

### 3.5 LinkedIn Integration (MUST HAVE)

| Req ID | Requirement | Baseline Reference | Priority |
|--------|-------------|-------------------|----------|
| LI-001 | Users can connect LinkedIn account via OAuth 2.0 | GET /auth/linkedin/authorize | P0 |
| LI-002 | System must store LinkedIn access token securely | Database - linkedin_tokens table | P0 |
| LI-003 | System must handle OAuth callback and token exchange | POST /auth/linkedin/callback | P0 |
| LI-004 | Users can publish posts to LinkedIn from dashboard | POST /posts/publish/{id} | P0 |
| LI-005 | System must upload post image to LinkedIn | LinkedIn UGC API | P1 |
| LI-006 | System must store LinkedIn post ID after publishing | Database field | P0 |
| LI-007 | Users can view published post on LinkedIn (link) | Dashboard feature | P1 |
| LI-008 | System must refresh expired LinkedIn tokens | Token refresh logic | P1 |
| LI-009 | Users can disconnect LinkedIn account | POST /auth/linkedin/disconnect | P1 |

**Acceptance Criteria:**
- ✅ User clicks "Connect LinkedIn", completes OAuth
- ✅ LinkedIn token stored in database
- ✅ User clicks "Publish", post appears on LinkedIn
- ✅ Image uploaded to LinkedIn post
- ✅ LinkedIn post ID stored in database
- ✅ "View on LinkedIn" link works
- ✅ User can disconnect LinkedIn account

---

### 3.6 Analytics & Insights (SHOULD HAVE)

| Req ID | Requirement | Baseline Reference | Priority |
|--------|-------------|-------------------|----------|
| ANLZ-001 | System should fetch engagement metrics from LinkedIn | LinkedIn API | P2 |
| ANLZ-002 | System should display post performance (views, likes, comments) | Dashboard metrics | P2 |
| ANLZ-003 | System should identify top-performing content topics | HistoryAgent | P2 |
| ANLZ-004 | System should suggest topics based on past performance | New AI feature | P3 |

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

| Req ID | Requirement | Target | Measurement |
|--------|-------------|--------|-------------|
| PERF-001 | API response time (p50) | <200ms | APM monitoring |
| PERF-002 | API response time (p95) | <500ms | APM monitoring |
| PERF-003 | Content generation time | <30 seconds | Timed endpoint |
| PERF-004 | Dashboard page load time | <2 seconds | Browser metrics |
| PERF-005 | Database query time | <100ms | Query logs |
| PERF-006 | Concurrent users supported | 100+ | Load testing |

---

### 4.2 Reliability Requirements

| Req ID | Requirement | Target | Measurement |
|--------|-------------|--------|-------------|
| REL-001 | System uptime | >99.5% | Uptime monitoring |
| REL-002 | API error rate | <1% | Error tracking |
| REL-003 | Graceful degradation on AI failures | Fallback templates | Error handling |
| REL-004 | Database backup frequency | Every 24 hours | Automated backups |
| REL-005 | Recovery Time Objective (RTO) | <1 hour | Incident response |
| REL-006 | Recovery Point Objective (RPO) | <24 hours | Backup validation |

---

### 4.3 Security Requirements

| Req ID | Requirement | Implementation | Priority |
|--------|-------------|----------------|----------|
| SEC-001 | All data in transit must be encrypted (TLS 1.3) | HTTPS only | P0 |
| SEC-002 | All data at rest must be encrypted | Supabase encryption | P0 |
| SEC-003 | No credentials stored in code or version control | Environment variables + Secret Manager | P0 |
| SEC-004 | SQL injection prevention | Parameterized queries | P0 |
| SEC-005 | XSS protection | Input sanitization | P0 |
| SEC-006 | Rate limiting on all API endpoints | 100 req/min per user | P0 |
| SEC-007 | LinkedIn tokens encrypted in database | Supabase encryption | P0 |
| SEC-008 | Regular security audits | Quarterly | P1 |
| SEC-009 | Dependency vulnerability scanning | Weekly (automated) | P1 |

---

### 4.4 Scalability Requirements

| Req ID | Requirement | Implementation |
|--------|-------------|----------------|
| SCAL-001 | Support 1000+ registered users | Multi-tenant architecture |
| SCAL-002 | Support 10,000+ posts in database | Database indexing |
| SCAL-003 | Horizontal scaling capability | Stateless API design |
| SCAL-004 | Auto-scaling based on load | Cloud Run auto-scaling |

---

### 4.5 Usability Requirements

| Req ID | Requirement | Implementation |
|--------|-------------|----------------|
| UX-001 | User can complete first post in <5 minutes | Streamlined onboarding |
| UX-002 | Dashboard must be intuitive (no training needed) | User testing |
| UX-003 | Error messages must be actionable | Clear error copy |
| UX-004 | Loading states shown for all async operations | UI spinners |
| UX-005 | Mobile-responsive design | Responsive Streamlit components |

---

## 5. Technical Architecture

### 5.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌──────────────┐                      ┌──────────────┐         │
│  │   Browser    │◄────────────────────►│   LinkedIn   │         │
│  │  (Desktop/   │                      │   Platform   │         │
│  │   Mobile)    │                      │              │         │
│  └──────┬───────┘                      └──────────────┘         │
│         │                                                         │
└─────────┼─────────────────────────────────────────────────────────┘
          │
          │ HTTPS
          │
┌─────────▼─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                             │
│  ┌────────────────────────────────────────────────────────┐      │
│  │           Streamlit Frontend (Cloud Run)                │      │
│  │  - User Interface                                       │      │
│  │  - Session Management                                   │      │
│  │  - Clerk Auth Component                                 │      │
│  └────────────────────────────────────────────────────────┘      │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            │ REST API (HTTPS)
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                     APPLICATION LAYER                             │
│  ┌────────────────────────────────────────────────────────┐      │
│  │            FastAPI Backend (Cloud Run)                  │      │
│  │  ┌──────────────────────────────────────────────┐      │      │
│  │  │         API Gateway & Middleware              │      │      │
│  │  │  - CORS                                       │      │      │
│  │  │  - Rate Limiting                              │      │      │
│  │  │  - Request Logging                            │      │      │
│  │  │  - JWT Validation                             │      │      │
│  │  └──────────────────────────────────────────────┘      │      │
│  │  ┌──────────────────────────────────────────────┐      │      │
│  │  │          Business Logic Layer                 │      │      │
│  │  │  - PostOrchestrator                           │      │      │
│  │  │  - UserService                                │      │      │
│  │  │  - LinkedInService                            │      │      │
│  │  └──────────────────────────────────────────────┘      │      │
│  │  ┌──────────────────────────────────────────────┐      │      │
│  │  │            AI Agent Layer                     │      │      │
│  │  │  - ContentAgent (Gemini)                      │      │      │
│  │  │  - ViralityAgent (Gemini)                     │      │      │
│  │  │  - HistoryAgent (Analysis)                    │      │      │
│  │  └──────────────────────────────────────────────┘      │      │
│  └────────────────────────────────────────────────────────┘      │
└───────────┬─────────────────────┬─────────────────────────────────┘
            │                     │
            │                     │
    ┌───────▼────────┐    ┌──────▼────────┐
    │                │    │               │
┌───┴────────────────▼────▼───────────────▼───┐
│              INFRASTRUCTURE LAYER            │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Supabase   │  │    Clerk     │         │
│  │  (Database)  │  │    (Auth)    │         │
│  │  - Users     │  │  - User Mgmt │         │
│  │  - Posts     │  │  - JWT       │         │
│  │  - Profiles  │  │  - OAuth     │         │
│  │  - Tokens    │  └──────────────┘         │
│  └──────────────┘                            │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Google     │  │  LinkedIn    │         │
│  │   Gemini     │  │     API      │         │
│  │  (AI Model)  │  │  (Publish)   │         │
│  └──────────────┘  └──────────────┘         │
└──────────────────────────────────────────────┘
```

---

### 5.2 Component Specifications

#### 5.2.1 Frontend (Streamlit)
**Technology:** Python 3.11 + Streamlit  
**Deployment:** Google Cloud Run  
**Responsibilities:**
- User interface rendering
- Session state management
- Clerk authentication integration
- API communication
- File uploads (future: bulk post uploads)

**Key Files:**
- `dashboard.py` - Main application
- `components/` - Reusable UI components
- `styles/` - Custom CSS

---

#### 5.2.2 Backend API (FastAPI)
**Technology:** Python 3.11 + FastAPI + Uvicorn  
**Deployment:** Google Cloud Run  
**Responsibilities:**
- RESTful API endpoints
- Request validation (Pydantic)
- JWT authentication
- Business logic orchestration
- Error handling and logging

**Key Files:**
- `main_v2.py` - API application (follows `test_server.py` structure)
- `api/routes/` - Endpoint definitions
- `api/middleware/` - CORS, logging, rate limiting

---

#### 5.2.3 AI Agent System
**Technology:** Python 3.11 + Google Gemini API  
**Responsibilities:**
- Content generation (ContentAgent)
- Virality scoring (ViralityAgent)
- Style learning (HistoryAgent)
- Image generation (ImageGenerator)

**Key Files:**
- `agents/content_agent.py`
- `agents/virality_agent.py`
- `agents/history_agent.py`
- `utils/image_generator.py`

---

#### 5.2.4 Database Layer (Supabase)
**Technology:** PostgreSQL (managed by Supabase)  
**Responsibilities:**
- Persistent data storage
- Row-level security (RLS)
- Real-time subscriptions (future)
- Automatic backups

**Tables:** See Section 7 (Data Model)

---

#### 5.2.5 Authentication (Clerk)
**Technology:** Clerk (SaaS)  
**Responsibilities:**
- User sign-up/sign-in
- OAuth providers (Google)
- JWT token issuance
- User management

---

#### 5.2.6 External Services

**Google Gemini API**
- Content generation
- Text analysis
- Style matching

**LinkedIn API**
- OAuth 2.0 authentication
- UGC Post creation
- Image upload
- Analytics (future)

---

### 5.3 Data Flow Diagrams

#### 5.3.1 Authentication Flow
```
User                 Frontend              Backend              Clerk              Supabase
 │                      │                     │                    │                   │
 ├─1. Click Login──────►│                     │                    │                   │
 │                      │                     │                    │                   │
 │                      ├─2. Redirect to Clerk────────────────────►│                   │
 │                      │                     │                    │                   │
 │◄─3. Clerk Sign-In────┤                     │                    │                   │
 │                      │                     │                    │                   │
 ├─4. Complete Auth────►│                     │                    │                   │
 │                      │                     │                    │                   │
 │                      │◄─5. JWT Token───────┤                    │                   │
 │                      │                     │                    │                   │
 │                      ├─6. Store JWT in Session                  │                   │
 │                      │                     │                    │                   │
 │                      ├─7. API Call (with JWT)──────────────────►│                   │
 │                      │                     │                    │                   │
 │                      │                     ├─8. Validate JWT────►│                   │
 │                      │                     │                    │                   │
 │                      │                     │◄─9. User Claims────┤                   │
 │                      │                     │                    │                   │
 │                      │                     ├─10. Get/Create User────────────────────►│
 │                      │                     │                    │                   │
 │                      │                     │◄─11. User Data─────┤                   │
 │                      │                     │                    │                   │
 │                      │◄─12. API Response───┤                    │                   │
 │                      │                     │                    │                   │
 │◄─13. Display Dashboard──                   │                    │                   │
```

---

#### 5.3.2 Content Generation Flow
```
User          Frontend        Backend         ContentAgent    ViralityAgent   ImageGen    Supabase
 │               │               │                  │               │            │            │
 ├─1. Enter Topic───────►│               │                  │               │            │            │
 │               │               │                  │               │            │            │
 │               ├─2. POST /posts/generate──────────►│                  │               │            │            │
 │               │               │                  │               │            │            │
 │               │               ├─3. Validate JWT  │               │            │            │
 │               │               │                  │               │            │            │
 │               │               ├─4. Get User Profile────────────────────────────────────────►│
 │               │               │                  │               │            │            │
 │               │               │◄─5. Profile Data─┤               │            │            │
 │               │               │                  │               │            │            │
 │               │               ├─6. Generate Content──────────────►│               │            │            │
 │               │               │                  │               │            │            │
 │               │               │                  ├─7. Call Gemini API               │            │            │
 │               │               │                  │               │            │            │
 │               │               │◄─8. AI Content───┤               │            │            │
 │               │               │                  │               │            │            │
 │               │               ├─9. Score Content────────────────────────────►│            │            │
 │               │               │                  │               │            │            │
 │               │               │                  │               ├─10. Call Gemini API            │            │
 │               │               │                  │               │            │            │
 │               │               │◄─11. Virality Score & Suggestions─┤            │            │
 │               │               │                  │               │            │            │
 │               │               ├─12. Generate Image──────────────────────────────────────►│            │
 │               │               │                  │               │            │            │
 │               │               │◄─13. Image Path──┤               │            │            │
 │               │               │                  │               │            │            │
 │               │               ├─14. Save Draft Post──────────────────────────────────────────────────►│
 │               │               │                  │               │            │            │
 │               │               │◄─15. Post ID─────┤               │            │            │
 │               │               │                  │               │            │            │
 │               │◄─16. {post_id, content, score, image}────────┤                  │               │            │            │
 │               │               │                  │               │            │            │
 │◄─17. Display Post─────┤               │                  │               │            │            │
```

---

## 6. API Specification

### 6.1 API Design Principles

1. **RESTful Design:** All endpoints follow REST conventions
2. **Consistency:** Response format matches `test_server.py` baseline
3. **Versioning:** API versioned at `/v1/` (future-proofing)
4. **Authentication:** All authenticated endpoints require `Authorization: Bearer <JWT>` header
5. **Error Handling:** Standard HTTP status codes + consistent error response format

### 6.2 Standard Response Format

**Success Response:**
```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-10-29T12:34:56.789Z"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "timestamp": "2025-10-29T12:34:56.789Z"
}
```

---

### 6.3 Endpoint Specifications

#### 6.3.1 Health Check

**Endpoint:** `GET /health`  
**Authentication:** Not required  
**Baseline Reference:** `test_server.py` lines 95-105  

**Response (200 OK):**
```json
{
  "status": "healthy",
  "api": true,
  "clerk": true,
  "supabase": true,
  "timestamp": "2025-10-29T12:34:56.789Z"
}
```

**Use Case:** Health monitoring, CI/CD validation

---

#### 6.3.2 Authentication Verification

**Endpoint:** `GET /auth/verify`  
**Authentication:** Required (JWT)  
**Baseline Reference:** `test_server.py` lines 124-133  

**Response (200 OK):**
```json
{
  "status": "authenticated",
  "user": {
    "clerk_id": "user_2Xy...",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Invalid or expired token"
}
```

---

#### 6.3.3 Get User Profile

**Endpoint:** `GET /user/profile`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 136-147  

**Response (200 OK):**
```json
{
  "status": "success",
  "id": "uuid-user-id",
  "email": "user@example.com",
  "full_name": "John Doe",
  "onboarding_completed": true,
  "writing_tone": "Professional & Formal",
  "target_audience": "SAP Consultants",
  "key_values": ["Innovation", "Leadership"]
}
```

---

#### 6.3.4 Submit Onboarding Questionnaire

**Endpoint:** `POST /onboarding/questionnaire`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 150-157  

**Request Body:**
```json
{
  "writing_tone": "Professional & Formal",
  "audience": "SAP Project Managers",
  "values": ["Innovation", "Leadership", "Growth"],
  "personality": "Thought leader sharing practical insights",
  "frequency": 3,
  "focus": "SAP S/4HANA Migration"
}
```

**Response (200 OK):**
```json
{
  "status": "profile_created",
  "message": "Onboarding questionnaire saved successfully"
}
```

---

#### 6.3.5 Generate Post

**Endpoint:** `POST /posts/generate`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 160-179  

**Request Body:**
```json
{
  "topic": "SAP S/4HANA Cloud vs On-Premise",
  "style": "Professional"  // optional
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "post_id": "uuid-post-id",
  "content": "In my 15 years of SAP consulting...",
  "virality_score": 8.5,
  "suggestions": [
    "Add a personal anecdote in the opening",
    "Include 2-3 concrete metrics"
  ],
  "image_path": "/static/outputs/uuid-post-id.png",
  "reasoning": "Content generated based on user profile..."
}
```

---

#### 6.3.6 Get Pending Drafts

**Endpoint:** `GET /posts/pending`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 182-192  

**Response (200 OK):**
```json
{
  "status": "success",
  "posts": [
    {
      "id": "uuid-1",
      "topic": "SAP BTP Overview",
      "content": "...",
      "virality_score": 7.5,
      "image_path": "/static/outputs/uuid-1.png",
      "created_at": "2025-10-29T10:00:00Z"
    }
  ],
  "count": 1
}
```

---

#### 6.3.7 Get Published Posts

**Endpoint:** `GET /posts/published`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 195-205  

**Response (200 OK):**
```json
{
  "status": "success",
  "posts": [
    {
      "id": "uuid-2",
      "topic": "AI in SAP",
      "content": "...",
      "linkedin_post_id": "urn:li:share:12345",
      "published_at": "2025-10-28T14:00:00Z",
      "analytics": {
        "views": 1250,
        "likes": 45,
        "comments": 8
      }
    }
  ],
  "count": 1
}
```

---

#### 6.3.8 Update Post

**Endpoint:** `PUT /posts/{post_id}`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 218-234  

**Request Body:**
```json
{
  "content": "Updated post content...",
  "topic": "Updated Topic"  // optional
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "post": {
    "id": "uuid-post-id",
    "content": "Updated post content...",
    "topic": "Updated Topic",
    "updated_at": "2025-10-29T12:34:56Z"
  }
}
```

---

#### 6.3.9 Publish Post to LinkedIn

**Endpoint:** `POST /posts/publish/{post_id}`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 237-251  

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Post published successfully",
  "linkedin_post_id": "urn:li:share:67890",
  "linkedin_url": "https://www.linkedin.com/feed/update/urn:li:share:67890"
}
```

**Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": {
    "code": "LINKEDIN_NOT_CONNECTED",
    "message": "Please connect your LinkedIn account first"
  }
}
```

---

#### 6.3.10 LinkedIn Authorization

**Endpoint:** `GET /auth/linkedin/authorize`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 260-270  

**Response (200 OK):**
```json
{
  "auth_url": "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=...&redirect_uri=...&state=...&scope=..."
}
```

**Frontend Action:** Redirect user to `auth_url`

---

#### 6.3.11 LinkedIn OAuth Callback

**Endpoint:** `GET /auth/linkedin/callback`  
**Authentication:** Not required (OAuth flow)  
**Query Parameters:**
- `code` (string, required): Authorization code from LinkedIn
- `state` (string, required): User ID for validation

**Response (302 Redirect):**
- Success: Redirect to `{FRONTEND_URL}?linkedin=connected`
- Error: Redirect to `{FRONTEND_URL}?linkedin=error`

**Backend Actions:**
1. Exchange `code` for access token with LinkedIn
2. Store token in `linkedin_tokens` table
3. Redirect user back to frontend

---

#### 6.3.12 LinkedIn Connection Status

**Endpoint:** `GET /auth/linkedin/status`  
**Authentication:** Required  
**Baseline Reference:** `test_server.py` lines 254-258  

**Response (200 OK - Connected):**
```json
{
  "status": "connected",
  "linkedin_email": "user@example.com"
}
```

**Response (200 OK - Not Connected):**
```json
{
  "status": "not_connected"
}
```

---

## 7. Data Model

### 7.1 Database Schema (Supabase/PostgreSQL)

#### Table: `users`
Stores core user account information linked to Clerk.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Internal user ID |
| `clerk_id` | VARCHAR(255) | UNIQUE, NOT NULL | Clerk user ID |
| `email` | VARCHAR(255) | NOT NULL | User email |
| `full_name` | VARCHAR(255) | | User's full name |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |
| `onboarding_completed` | BOOLEAN | DEFAULT FALSE | Onboarding status |
| `onboarding_path` | VARCHAR(50) | | 'questionnaire' or 'content_analysis' |

**Indexes:**
- `idx_users_clerk_id` ON `clerk_id`
- `idx_users_email` ON `email`

**RLS Policies:**
```sql
-- Users can only read their own data
CREATE POLICY "Users can read own data"
ON users FOR SELECT
USING (clerk_id = auth.uid());

-- Service role can do everything
CREATE POLICY "Service role full access"
ON users FOR ALL
USING (auth.jwt() ->> 'role' = 'service_role');
```

---

#### Table: `user_profiles`
Stores detailed user preferences and content style information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Profile ID |
| `user_id` | UUID | FOREIGN KEY (users.id), UNIQUE, NOT NULL | Reference to users table |
| `writing_tone` | VARCHAR(100) | NOT NULL | User's preferred writing tone |
| `target_audience` | TEXT | NOT NULL | Description of target audience |
| `key_values` | TEXT[] | NOT NULL | Array of user's key values |
| `personality_traits` | TEXT[] | | Array of personality descriptors |
| `posting_frequency` | INTEGER | | Desired posts per week |
| `content_focus` | TEXT | NOT NULL | Primary content focus area |
| `brand_voice_summary` | TEXT | | AI-generated summary of user's voice |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Profile creation timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `idx_user_profiles_user_id` ON `user_id`

---

#### Table: `onboarding_questionnaire`
Stores raw questionnaire responses for auditing and analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Response ID |
| `user_id` | UUID | FOREIGN KEY (users.id), NOT NULL | Reference to users table |
| `question_1_writing_tone` | VARCHAR(100) | NOT NULL | Q1: Writing tone selection |
| `question_2_audience` | TEXT | NOT NULL | Q2: Target audience |
| `question_3_values` | TEXT[] | NOT NULL | Q3: Key values selected |
| `question_4_personality` | TEXT | NOT NULL | Q4: Personality description |
| `question_5_frequency` | INTEGER | NOT NULL | Q5: Posting frequency |
| `question_6_focus` | TEXT | NOT NULL | Q6: Content focus area |
| `completed_at` | TIMESTAMPTZ | DEFAULT NOW() | Completion timestamp |

---

#### Table: `posts`
Stores all generated and published posts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Post ID |
| `user_id` | UUID | FOREIGN KEY (users.id), NOT NULL | Reference to users table |
| `topic` | TEXT | NOT NULL | User-provided topic |
| `content` | TEXT | NOT NULL | Generated post content |
| `reasoning` | TEXT | | AI agent's reasoning for content |
| `virality_score` | DECIMAL(3,1) | CHECK (virality_score >= 0 AND virality_score <= 10) | Virality score (0-10) |
| `suggestions` | JSONB | | Improvement suggestions array |
| `status` | VARCHAR(20) | DEFAULT 'draft' | 'draft' or 'published' |
| `image_path` | VARCHAR(500) | | Path to generated image |
| `linkedin_post_id` | VARCHAR(500) | | LinkedIn post URN after publishing |
| `linkedin_url` | VARCHAR(1000) | | Direct URL to LinkedIn post |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Draft creation timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |
| `published_at` | TIMESTAMPTZ | | Publishing timestamp |

**Indexes:**
- `idx_posts_user_id` ON `user_id`
- `idx_posts_status` ON `status`
- `idx_posts_created_at` ON `created_at DESC`

**RLS Policies:**
```sql
-- Users can only access their own posts
CREATE POLICY "Users can read own posts"
ON posts FOR SELECT
USING (user_id IN (SELECT id FROM users WHERE clerk_id = auth.uid()));

CREATE POLICY "Users can create own posts"
ON posts FOR INSERT
WITH CHECK (user_id IN (SELECT id FROM users WHERE clerk_id = auth.uid()));

CREATE POLICY "Users can update own posts"
ON posts FOR UPDATE
USING (user_id IN (SELECT id FROM users WHERE clerk_id = auth.uid()));
```

---

#### Table: `linkedin_tokens`
Stores encrypted LinkedIn OAuth tokens.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Token record ID |
| `user_id` | UUID | FOREIGN KEY (users.id), UNIQUE, NOT NULL | Reference to users table |
| `access_token` | TEXT | NOT NULL | Encrypted LinkedIn access token |
| `refresh_token` | TEXT | | Encrypted LinkedIn refresh token |
| `expires_at` | TIMESTAMPTZ | | Token expiration timestamp |
| `linkedin_email` | VARCHAR(255) | | LinkedIn account email |
| `linkedin_user_id` | VARCHAR(255) | | LinkedIn user ID |
| `scope` | VARCHAR(500) | | OAuth scope granted |
| `token_type` | VARCHAR(50) | DEFAULT 'Bearer' | Token type |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Token creation timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last refresh timestamp |

**Security Note:** Supabase encrypts this table at rest.

---

#### Table: `post_analytics` (Future - Phase 2)
Stores engagement metrics fetched from LinkedIn.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Analytics record ID |
| `post_id` | UUID | FOREIGN KEY (posts.id), NOT NULL | Reference to posts table |
| `views` | INTEGER | DEFAULT 0 | Post view count |
| `likes` | INTEGER | DEFAULT 0 | Post like count |
| `comments` | INTEGER | DEFAULT 0 | Post comment count |
| `shares` | INTEGER | DEFAULT 0 | Post share count |
| `engagement_rate` | DECIMAL(5,2) | | Calculated engagement rate |
| `fetched_at` | TIMESTAMPTZ | DEFAULT NOW() | Timestamp of metric fetch |

---

### 7.2 Entity Relationship Diagram

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ clerk_id (UQ)   │───┐
│ email           │   │
│ full_name       │   │
│ onboarding_...  │   │
└─────────────────┘   │
                      │
         ┌────────────┼────────────┬────────────┐
         │            │            │            │
         ▼            ▼            ▼            ▼
┌─────────────┐ ┌──────────┐ ┌────────┐ ┌──────────────┐
│user_profiles│ │onboarding│ │ posts  │ │linkedin_     │
│             │ │_question │ │        │ │tokens        │
├─────────────┤ │_naire    │ ├────────┤ ├──────────────┤
│id (PK)      │ ├──────────┤ │id (PK) │ │id (PK)       │
│user_id (FK) │ │id (PK)   │ │user_id │ │user_id (FK)  │
│writing_tone │ │user_id   │ │  (FK)  │ │access_token  │
│target_aud...│ │  (FK)    │ │topic   │ │refresh_token │
│key_values   │ │question_1│ │content │ │expires_at    │
│...          │ │...       │ │virality│ │...           │
└─────────────┘ └──────────┘ │_score  │ └──────────────┘
                              │status  │
                              │image...│
                              │linkedin│
                              │_post_id│
                              └────────┘
                                  │
                                  │ (Future)
                                  ▼
                            ┌──────────────┐
                            │post_analytics│
                            ├──────────────┤
                            │id (PK)       │
                            │post_id (FK)  │
                            │views         │
                            │likes         │
                            │comments      │
                            │engagement_...│
                            └──────────────┘
```

---

## 8. Security & Compliance

### 8.1 Authentication & Authorization

**Authentication Provider:** Clerk  
**Method:** JWT (JSON Web Tokens)  

**Token Validation Process:**
1. User authenticates via Clerk (frontend)
2. Clerk issues JWT token
3. Frontend includes token in all API requests (`Authorization: Bearer <token>`)
4. Backend validates token using Clerk's JWKS (public keys)
5. Backend extracts `clerk_id` from validated token
6. Backend maps `clerk_id` to internal `user_id` in Supabase
7. All database queries filtered by `user_id` (tenant isolation)

---

### 8.2 Data Security

**Encryption at Rest:**
- All Supabase data encrypted using AES-256
- LinkedIn tokens stored in encrypted table

**Encryption in Transit:**
- All API traffic over HTTPS/TLS 1.3
- Certificate management via Google Cloud Load Balancer

**Secret Management:**
- Environment variables stored in Google Secret Manager
- Secrets injected into Cloud Run at runtime
- No secrets in code or version control
- Automatic secret rotation (quarterly)

---

### 8.3 Row-Level Security (RLS)

All Supabase tables implement RLS policies ensuring:
- Users can only access their own data
- No cross-tenant data leakage
- Service role (backend) has full access
- Queries automatically filtered by `user_id`

**Example Policy:**
```sql
CREATE POLICY "users_select_own"
ON posts FOR SELECT
USING (user_id IN (
  SELECT id FROM users WHERE clerk_id = auth.uid()
));
```

---

### 8.4 API Security

**Rate Limiting:**
- 100 requests per minute per user
- 1000 requests per hour per user
- Implemented using FastAPI middleware

**Input Validation:**
- All requests validated using Pydantic models
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)
- CSRF protection (stateless API)

**Error Handling:**
- No sensitive data in error messages
- Generic error responses for security failures
- Detailed errors logged server-side only

---

### 8.5 Compliance

**Data Privacy:**
- GDPR-ready (user data deletion capability)
- Clear data retention policies
- User consent for LinkedIn publishing

**LinkedIn API Compliance:**
- OAuth 2.0 strictly followed
- Respects LinkedIn API rate limits
- Stores minimum required user data

**Audit Logging:**
- All critical actions logged (post creation, publishing, profile updates)
- Logs retained for 90 days
- Searchable via Google Cloud Logging

---

## 9. Phase-by-Phase Implementation Plan

### 9.1 Implementation Philosophy

**Guiding Principles:**
1. **Test-Driven Development:** `test_server.py` is our validated baseline. Every production feature must pass equivalent tests.
2. **Incremental Delivery:** Each phase delivers working, testable functionality.
3. **No Regressions:** All tests from previous phases must continue passing.
4. **Production Readiness:** Each phase ends with deployable, documented code.

**Success Gate for Each Phase:**
- ✅ All code follows `test_server.py` patterns
- ✅ All tests passing (unit + integration)
- ✅ Documentation updated
- ✅ Code reviewed and approved
- ✅ Deployed to staging and validated

---

## Phase 1: Foundation - Backend Reconstruction
**Duration:** 3-4 days  
**Objective:** Build a production backend that matches `test_server.py` reliability with real integrations

---

### Phase 1.1: Configuration Management System
**Duration:** 0.5 days  
**Baseline:** `test_server.py` lines 1-50 (imports and setup)

**Deliverables:**
- [ ] `config_v2.py` - Centralized configuration module
- [ ] Environment variable validation on startup
- [ ] Configuration validation tests
- [ ] `.env.example` template file

**Implementation Steps:**
```python
# 1. Create config_v2.py
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Production configuration with validation"""
    
    # API Configuration
    API_BASE_URL: str = Field(default="http://localhost:8080")
    FRONTEND_URL: str = Field(default="http://localhost:8501")
    PORT: int = Field(default=8080)
    
    # Authentication (Clerk)
    CLERK_PUBLISHABLE_KEY: str = Field(...)
    CLERK_SECRET_KEY: str = Field(...)
    CLERK_JWKS_URL: str = Field(...)
    
    # Database (Supabase)
    SUPABASE_URL: str = Field(...)
    SUPABASE_KEY: str = Field(...)
    SUPABASE_SERVICE_KEY: Optional[str] = Field(default=None)
    
    # AI (Google Gemini)
    GEMINI_API_KEY: str = Field(...)
    
    # LinkedIn API
    LINKEDIN_CLIENT_ID: Optional[str] = Field(default=None)
    LINKEDIN_CLIENT_SECRET: Optional[str] = Field(default=None)
    
    # Feature Flags
    TEST_MODE: bool = Field(default=False)
    DEBUG: bool = Field(default=False)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def is_production(self) -> bool:
        return not self.TEST_MODE and not self.DEBUG
    
    def validate_required_for_production(self):
        """Validate all required secrets are present for production"""
        if self.is_production:
            assert self.LINKEDIN_CLIENT_ID, "LinkedIn Client ID required for production"
            assert self.LINKEDIN_CLIENT_SECRET, "LinkedIn Client Secret required"
        
# Global settings instance
settings = Settings()

# 2. Create tests/test_config.py
import pytest
from config_v2 import Settings

def test_config_loads_from_env():
    config = Settings()
    assert config.API_BASE_URL is not None
    assert config.SUPABASE_URL is not None

def test_production_validation():
    config = Settings(TEST_MODE=False)
    # Should not raise if all required fields present
    config.validate_required_for_production()

# 3. Create .env.example
"""
# API Configuration
API_BASE_URL=http://localhost:8080
FRONTEND_URL=http://localhost:8501
PORT=8080

# Clerk Authentication
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Google Gemini AI
GEMINI_API_KEY=your_gemini_key

# LinkedIn API
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret

# Feature Flags
TEST_MODE=false
DEBUG=false
"""
```

**Acceptance Criteria:**
- ✅ `python -c "from config_v2 import settings; print(settings.SUPABASE_URL)"` prints URL
- ✅ Missing required env var raises clear error on startup
- ✅ All config tests pass: `pytest tests/test_config.py -v`

**Tools Required:**
- `pydantic-settings==2.1.0`
- `python-dotenv==1.0.0`

---

### Phase 1.2: Database Layer (Supabase Client)
**Duration:** 1 day  
**Baseline:** `test_server.py` data operations (lines 60-90)

**Deliverables:**
- [ ] `database/client_v2.py` - Production-ready Supabase client
- [ ] Connection health checks
- [ ] Graceful error handling
- [ ] Database client unit tests

**Implementation Steps:**
```python
# 1. Create database/client_v2.py
import logging
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential
from config_v2 import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Production-ready Supabase client with retry logic and health checks"""
    
    def __init__(self):
        """Initialize Supabase client"""
        try:
            # Use service key for backend operations
            key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
            self.client: Client = create_client(settings.SUPABASE_URL, key)
            logger.info("✓ Supabase client initialized")
        except Exception as e:
            logger.error(f"✗ Supabase initialization failed: {e}")
            self.client = None
            if settings.is_production:
                raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check database connection health"""
        if not self.client:
            return {"healthy": False, "error": "Client not initialized"}
        
        try:
            # Simple query to test connection
            result = self.client.table("users").select("count", count="exact").limit(1).execute()
            return {
                "healthy": True,
                "total_users": getattr(result, 'count', 0)
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_user_by_clerk_id(self, clerk_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Clerk ID with automatic retry"""
        result = self.client.table("users").select("*").eq("clerk_id", clerk_id).execute()
        return result.data[0] if result.data else None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_user(self, clerk_id: str, email: str, full_name: str) -> Dict[str, Any]:
        """Create new user"""
        user_data = {
            "clerk_id": clerk_id,
            "email": email,
            "full_name": full_name,
            "onboarding_completed": False
        }
        result = self.client.table("users").insert(user_data).execute()
        if not result.data:
            raise Exception("User creation failed")
        return result.data[0]
    
    # ... (add methods for posts, profiles, tokens following same pattern)

# Global client instance
db = SupabaseClient()

# 2. Create tests/test_database.py
import pytest
from database.client_v2 import SupabaseClient

@pytest.fixture
def db_client():
    return SupabaseClient()

def test_health_check(db_client):
    health = db_client.health_check()
    assert health["healthy"] is True

def test_get_user_by_clerk_id(db_client):
    # Should not raise
    user = db_client.get_user_by_clerk_id("test_clerk_id")
    assert user is None or isinstance(user, dict)
```

**Acceptance Criteria:**
- ✅ `python -c "from database.client_v2 import db; print(db.health_check())"` shows healthy
- ✅ All database tests pass: `pytest tests/test_database.py -v`
- ✅ Retry logic tested with temporary network failure simulation

**Tools Required:**
- `supabase==2.0.3`
- `tenacity==8.2.3`

---

### Phase 1.3: Authentication Layer (Clerk JWT)
**Duration:** 1 day  
**Baseline:** `test_server.py` lines 95-115 (get_current_user)

**Deliverables:**
- [ ] `auth/clerk_jwt.py` - JWT validation module
- [ ] JWKS public key fetching and caching
- [ ] FastAPI authentication dependency
- [ ] Auth unit tests with real/mock tokens

**Implementation Steps:**
```python
# 1. Create auth/clerk_jwt.py
import logging
import requests
from typing import Dict, Any
from jose import jwt, JWTError
from fastapi import HTTPException, Header, Depends
from cachetools import TTLCache
from config_v2 import settings

logger = logging.getLogger(__name__)

# Cache JWKS keys for 1 hour
jwks_cache = TTLCache(maxsize=10, ttl=3600)

def get_jwks_keys() -> List[Dict]:
    """Fetch Clerk's public keys for JWT validation (with caching)"""
    if "keys" in jwks_cache:
        return jwks_cache["keys"]
    
    try:
        response = requests.get(settings.CLERK_JWKS_URL, timeout=5)
        response.raise_for_status()
        keys = response.json()["keys"]
        jwks_cache["keys"] = keys
        logger.info("✓ JWKS keys fetched and cached")
        return keys
    except Exception as e:
        logger.error(f"✗ Failed to fetch JWKS keys: {e}")
        raise HTTPException(status_code=500, detail="Authentication service unavailable")

def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Validate JWT token and return claims"""
    try:
        # Get unverified header to extract 'kid'
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise ValueError("No 'kid' in token header")
        
        # Find matching public key
        keys = get_jwks_keys()
        public_key = next((k for k in keys if k["kid"] == kid), None)
        
        if not public_key:
            raise ValueError(f"No matching key for kid: {kid}")
        
        # Verify and decode token
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.CLERK_PUBLISHABLE_KEY
        )
        
        return claims
    
    except JWTError as e:
        logger.error(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(authorization: str = Header(None)) -> Dict[str, Any]:
    """FastAPI dependency: Extract and validate user from JWT"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
        
        claims = validate_jwt_token(token)
        
        return {
            "clerk_id": claims.get("sub"),
            "email": claims.get("email", ""),
            "full_name": claims.get("name", "")
        }
    
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# 2. Create tests/test_auth.py
import pytest
from auth.clerk_jwt import validate_jwt_token

def test_invalid_token_raises_error():
    with pytest.raises(Exception):
        validate_jwt_token("invalid.token.here")

# Note: Real token testing requires a test Clerk instance
```

**Acceptance Criteria:**
- ✅ Invalid token raises 401
- ✅ Valid Clerk JWT passes validation
- ✅ JWKS keys cached (verified in logs)
- ✅ All auth tests pass: `pytest tests/test_auth.py -v`

**Tools Required:**
- `python-jose[cryptography]==3.3.0`
- `cachetools==5.3.2`

---

### Phase 1.4: Core API Application (main_v2.py)
**Duration:** 1 day  
**Baseline:** `test_server.py` (entire structure)

**Deliverables:**
- [ ] `main_v2.py` - Production FastAPI app
- [ ] All 11 endpoints from test server
- [ ] Request logging middleware
- [ ] OpenAPI documentation
- [ ] Integration tests against main_v2

**Implementation Steps:**
```python
# 1. Create main_v2.py
import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
    except (AttributeError, TypeError):
        pass

from fastapi import FastAPI, Depends, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

from config_v2 import settings
from auth.clerk_jwt import get_current_user
from database.client_v2 import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CIS Content Intelligence System API",
    description="AI-powered LinkedIn content generation - Production",
    version="2.0.0",
)

# CORS Configuration
ALLOWED_ORIGINS = [
    settings.FRONTEND_URL,
    "http://localhost:8501",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for images)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# ========================================
# DEPENDENCY: GET DATABASE USER
# ========================================

async def get_db_user(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get or create user in database linked to Clerk ID"""
    clerk_id = current_user["clerk_id"]
    
    # Try to get existing user
    user = db.get_user_by_clerk_id(clerk_id)
    
    if not user:
        # Create new user
        logger.info(f"Creating new user for Clerk ID: {clerk_id}")
        user = db.create_user(
            clerk_id=clerk_id,
            email=current_user["email"],
            full_name=current_user["full_name"]
        )
    
    return user

# ========================================
# ENDPOINTS (MATCH test_server.py)
# ========================================

@app.get("/health")
async def health_check():
    """System health check"""
    db_health = db.health_check()
    
    return {
        "status": "healthy" if db_health["healthy"] else "degraded",
        "api": True,
        "clerk": bool(settings.CLERK_SECRET_KEY),
        "supabase": db_health["healthy"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "CIS Content Intelligence System API",
        "version": "2.0.0",
        "status": "running",
        "auth": "Clerk (JWT)",
        "database": "Supabase",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/auth/verify")
async def verify_auth(current_user: Dict = Depends(get_current_user)):
    """Verify user is authenticated"""
    return {
        "status": "authenticated",
        "user": current_user
    }

@app.get("/user/profile")
async def get_user_profile(db_user: Dict = Depends(get_db_user)):
    """Get user's profile"""
    # Get full profile from database
    profile = db.get_user_profile(db_user["id"])
    
    if not profile:
        return {
            "status": "no_profile",
            "message": "User has not completed onboarding",
            "id": db_user["id"],
            "onboarding_completed": db_user["onboarding_completed"]
        }
    
    return {
        "status": "success",
        "id": db_user["id"],
        **profile
    }

@app.post("/onboarding/questionnaire")
async def save_questionnaire(
    payload: Dict[str, Any] = Body(...),
    db_user: Dict = Depends(get_db_user)
):
    """Save onboarding questionnaire responses"""
    user_id = db_user["id"]
    
    # Save questionnaire
    db.save_questionnaire(user_id, payload)
    
    # Create user profile
    db.create_user_profile(user_id, payload)
    
    # Mark onboarding complete
    db.update_user(user_id, {"onboarding_completed": True})
    
    logger.info(f"Onboarding completed for user: {user_id}")
    
    return {
        "status": "profile_created",
        "message": "Onboarding questionnaire saved successfully"
    }

@app.post("/posts/generate")
async def generate_post(
    payload: Dict[str, Any] = Body(...),
    db_user: Dict = Depends(get_db_user)
):
    """Generate a LinkedIn post"""
    user_id = db_user["id"]
    topic = payload.get("topic")
    style = payload.get("style")
    
    # TODO: Replace with real AI generation (Phase 2)
    # For now, use simple template
    content = f"This is a generated post about: {topic}\n\nGenerated by CIS AI System"
    
    # Save draft
    post = db.create_post(
        user_id=user_id,
        topic=topic,
        content=content,
        status="draft"
    )
    
    return {
        "status": "success",
        "post_id": post["id"],
        "content": content
    }

# ... (implement remaining endpoints: /posts/pending, /posts/published, /posts/{id}, /posts/publish/{id}, LinkedIn endpoints)

# ========================================
# STARTUP
# ========================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("🚀 Starting CIS API v2.0")
    logger.info(f"✓ Environment: {'PRODUCTION' if settings.is_production else 'DEVELOPMENT'}")
    logger.info(f"✓ Database: {db.health_check()['healthy']}")
    logger.info("=" * 50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_v2:app", host="0.0.0.0", port=settings.PORT, reload=True)
```

**Acceptance Criteria:**
- ✅ Server starts: `python main_v2.py`
- ✅ Health check works: `curl http://localhost:8080/health`
- ✅ All integration tests pass: `python test_integration.py` (update BASE_URL)
- ✅ OpenAPI docs accessible: `http://localhost:8080/docs`

---

### Phase 1 Completion Checklist

- [ ] All code follows `test_server.py` patterns
- [ ] Config system validated and documented
- [ ] Database client tested with real Supabase
- [ ] JWT authentication working with Clerk test tokens
- [ ] All 11 endpoints functional
- [ ] **Integration tests pass: 11/11** ✅
- [ ] Documentation updated in README
- [ ] Code reviewed
- [ ] Deployed to staging environment

**Phase 1 Exit Criteria:**
```bash
# Must pass before moving to Phase 2
pytest tests/ -v --cov=. --cov-report=term-missing
python test_integration.py  # 100% pass rate
curl http://localhost:8080/health  # Returns healthy
```

---

## Phase 2: Intelligence Layer - AI Agent Integration
**Duration:** 3-4 days  
**Objective:** Replace mock content generation with real AI

---

### Phase 2.1: Agent Dependency Resolution
**Duration:** 0.5 days

**Deliverables:**
- [ ] `requirements_agents.txt` - Isolated agent dependencies
- [ ] Fixed circular imports in agents/
- [ ] Agent initialization tests
- [ ] Graceful fallback for agent failures

**Implementation Steps:**
```bash
# 1. Create requirements_agents.txt
google-generativeai==0.3.2
pillow==10.1.0
# (add any other agent-specific dependencies)

# 2. Fix imports
# Ensure agents/ modules don't import from each other circularly
# Move shared utilities to utils/

# 3. Test agents can initialize
python -c "from agents.content_agent import ContentAgent; agent = ContentAgent()"
```

**Acceptance Criteria:**
- ✅ All agents import without errors
- ✅ `ContentAgent()` initializes successfully
- ✅ Agent tests pass: `pytest tests/test_agents/ -v`

---

### Phase 2.2: Content Agent Integration
**Duration:** 1.5 days

**Deliverables:**
- [ ] Real AI content generation in `/posts/generate`
- [ ] Timeout protection (30s max)
- [ ] Fallback templates if AI fails
- [ ] Content generation performance metrics

**Implementation Steps:**
```python
# Update main_v2.py /posts/generate endpoint

from agents.content_agent import ContentAgent
from tenacity import retry, stop_after_attempt, wait_fixed
import asyncio

content_agent = ContentAgent()

@app.post("/posts/generate")
async def generate_post(
    payload: Dict[str, Any] = Body(...),
    db_user: Dict = Depends(get_db_user)
):
    """Generate a LinkedIn post using AI"""
    user_id = db_user["id"]
    topic = payload.get("topic")
    
    # Get user profile for personalization
    profile = db.get_user_profile(user_id)
    
    try:
        # Call AI agent with timeout
        content_result = await asyncio.wait_for(
            content_agent.generate_post_text(
                topic=topic,
                profile=profile,
                use_history=True,
                user_id=user_id
            ),
            timeout=30.0  # 30 second max
        )
        
        content = content_result["post_text"]
        reasoning = content_result.get("reasoning", "")
        
    except asyncio.TimeoutError:
        logger.error("Content generation timed out")
        # Fallback to template
        content = f"[FALLBACK] Content about {topic}..."
        reasoning = "AI generation timed out; using fallback template"
    
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        # Fallback
        content = f"[FALLBACK] Content about {topic}..."
        reasoning = f"AI generation error: {str(e)}"
    
    # Save draft
    post = db.create_post(
        user_id=user_id,
        topic=topic,
        content=content,
        reasoning=reasoning,
        status="draft"
    )
    
    return {
        "status": "success",
        "post_id": post["id"],
        "content": content,
        "reasoning": reasoning
    }
```

**Acceptance Criteria:**
- ✅ `/posts/generate` returns AI-generated content
- ✅ Content matches user's style profile
- ✅ Generation completes in <30s
- ✅ Fallback template used if AI fails
- ✅ All integration tests still pass

---

### Phase 2.3: Virality Agent Integration
**Duration:** 1 day

**Deliverables:**
- [ ] Virality scoring on all generated posts
- [ ] Scores stored in database
- [ ] Actionable suggestions returned to user

**Implementation Steps:**
```python
# Update /posts/generate to include virality scoring

from agents.virality_agent import ViralityAgent

virality_agent = ViralityAgent()

@app.post("/posts/generate")
async def generate_post(...):
    # ... (content generation logic)
    
    # Score content for virality
    try:
        score_result = await virality_agent.score_post(content)
        virality_score = score_result.get("score", 0.0)
        suggestions = score_result.get("suggestions", [])
    except Exception as e:
        logger.error(f"Virality scoring failed: {e}")
        virality_score = 0.0
        suggestions = []
    
    # Save draft with score
    post = db.create_post(
        user_id=user_id,
        topic=topic,
        content=content,
        reasoning=reasoning,
        virality_score=virality_score,
        suggestions=json.dumps(suggestions),
        status="draft"
    )
    
    return {
        "status": "success",
        "post_id": post["id"],
        "content": content,
        "virality_score": virality_score,
        "suggestions": suggestions
    }
```

**Acceptance Criteria:**
- ✅ Every generated post has virality score (0-10)
- ✅ Suggestions array returned in API response
- ✅ Scores stored in database

---

### Phase 2.4: Image Generation Integration
**Duration:** 0.5 days

**Deliverables:**
- [ ] Branded image generated for each post
- [ ] Image path returned in API response
- [ ] Images served via `/static/` endpoint

**Implementation Steps:**
```python
# Update /posts/generate to include image generation

from utils.image_generator import create_branded_image

@app.post("/posts/generate")
async def generate_post(...):
    # ... (content + virality scoring)
    
    # Generate branded image
    try:
        image_path = create_branded_image(content, db_user["full_name"])
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        image_path = None
    
    # Save draft with image
    post = db.create_post(
        user_id=user_id,
        topic=topic,
        content=content,
        reasoning=reasoning,
        virality_score=virality_score,
        suggestions=json.dumps(suggestions),
        image_path=image_path,
        status="draft"
    )
    
    return {
        "status": "success",
        "post_id": post["id"],
        "content": content,
        "virality_score": virality_score,
        "suggestions": suggestions,
        "image_path": image_path  # e.g., "/static/outputs/{uuid}.png"
    }
```

**Acceptance Criteria:**
- ✅ Image generated for each post
- ✅ Image path returned in API
- ✅ Images accessible via `/static/outputs/{id}.png`

---

### Phase 2 Completion Checklist

- [ ] All AI agents integrated and functional
- [ ] Real content generation working
- [ ] Virality scoring operational
- [ ] Images generated and served
- [ ] **All integration tests still pass: 11/11** ✅
- [ ] Performance benchmarks met (<30s generation)
- [ ] Error handling and fallbacks tested
- [ ] Documentation updated

---

## Phase 3: Frontend Integration
**Duration:** 2-3 days  
**Objective:** Connect working frontend to working backend with real authentication

---

### Phase 3.1: Clerk Frontend Integration
**Duration:** 1 day

**Deliverables:**
- [ ] Clerk sign-in component in Streamlit
- [ ] JWT token capture and storage
- [ ] Session management
- [ ] Logout functionality

**Implementation Steps:**
```python
# Update dashboard.py

import streamlit as st
import streamlit.components.v1 as components
import requests

API_BASE_URL = "http://localhost:8080"
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")

# Initialize session state
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user" not in st.session_state:
    st.session_state.user = None

def show_clerk_auth():
    """Embed Clerk sign-in component"""
    components.html(
        f"""
        <div id="clerk-sign-in"></div>
        <script src="https://cdn.jsdelivr.net/npm/@clerk/clerk-js@latest/dist/clerk.browser.js"></script>
        <script>
            const clerk = Clerk.load('{CLERK_PUBLISHABLE_KEY}');
            
            clerk.on('session.created', async (session) => {{
                const token = await session.getToken();
                window.parent.postMessage({{
                    type: 'clerk-auth-success',
                    token: token,
                    user: {{
                        id: clerk.user.id,
                        email: clerk.user.primaryEmailAddress.emailAddress,
                        name: clerk.user.fullName
                    }}
                }}, '*');
            }});
            
            clerk.mountSignIn(document.getElementById('clerk-sign-in'));
        </script>
        """,
        height=600,
    )

def main():
    if not st.session_state.auth_token:
        show_clerk_auth()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
```

**Acceptance Criteria:**
- ✅ User can sign in via Clerk
- ✅ JWT token stored in session
- ✅ API calls include token
- ✅ Logout clears session

---

### Phase 3.2: Frontend-Backend Connection
**Duration:** 1 day

**Deliverables:**
- [ ] All dashboard tabs functional
- [ ] API calls use real backend
- [ ] Loading states implemented
- [ ] Error handling in UI

**Implementation Steps:**
```python
# Update all API calls in dashboard.py

def get_headers():
    return {
        "Authorization": f"Bearer {st.session_state.auth_token}",
        "Content-Type": "application/json"
    }

def generate_post(topic: str):
    with st.spinner("Generating post..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/posts/generate",
                json={"topic": topic},
                headers=get_headers(),
                timeout=35  # Slightly more than backend timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                st.success("✅ Post generated!")
                return data
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                return None
        
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
```

**Acceptance Criteria:**
- ✅ Generate tab creates real AI content
- ✅ Posts tab shows drafts from database
- ✅ All API calls authenticated
- ✅ Error messages displayed to user

---

### Phase 3.3: Image Display Integration
**Duration:** 0.5 days

**Deliverables:**
- [ ] Images display in Generate tab
- [ ] Images display in Posts tab
- [ ] Image download functionality

**Implementation Steps:**
```python
# In dashboard.py

def show_generate_tab():
    # ... (after post generation)
    
    if data:
        st.markdown("### 📝 Generated Content")
        st.text_area("", value=data["content"], height=200, disabled=True)
        
        st.markdown(f"**Virality Score:** {data['virality_score']}/10")
        
        if data.get("image_path"):
            image_url = f"{API_BASE_URL}{data['image_path']}"
            st.markdown("### 🖼️ Generated Image")
            st.image(image_url)
            
            if st.button("⬇️ Download Image"):
                # Trigger download
                st.markdown(f"[Download Image]({image_url})", unsafe_allow_html=True)
```

**Acceptance Criteria:**
- ✅ Generated images display correctly
- ✅ Images viewable in draft list

### Phase 3 Completion Checklist

- [ ] Clerk authentication fully integrated
- [ ] All dashboard tabs functional with real backend
- [ ] Images display and download working
- [ ] Error handling implemented across UI
- [ ] **All integration tests still pass: 11/11** ✅
- [ ] User can complete full flow: sign-in → generate → publish
- [ ] Documentation updated

---

## Phase 4: LinkedIn Publishing Integration
**Duration:** 2-3 days  
**Objective:** Enable real LinkedIn post publishing via UGC API

---

### Phase 4.1: LinkedIn UGC API Integration
**Duration:** 1.5 days

**Deliverables:**
- [ ] LinkedIn UGC Post creation working
- [ ] Image upload to LinkedIn
- [ ] Post ID tracking
- [ ] Error handling for API failures

**Implementation Steps:**
```python
# Update tools/linkedin_publisher.py

from linkedin import linkedin
import requests

class LinkedInPublisher:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    
    async def publish_post(self, post_content: str, image_url: Optional[str] = None):
        """Publish post to LinkedIn UGC"""
        try:
            # Get user's profile URN
            profile_result = await self._get_profile_urn()
            author_urn = profile_result["elements"][0]["id"]
            
            # Upload image if provided
            image_urn = None
            if image_url:
                image_urn = await self._upload_image(image_url)
            
            # Create UGC post
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_content},
                        "shareMediaCategory": "NONE" if not image_urn else "IMAGE",
                        "media": [{"media": image_urn}] if image_urn else []
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            
            response = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=self.headers,
                json=post_data
            )
            response.raise_for_status()
            
            post_id = response.headers.get("X-LinkedIn-Id")
            return {"success": True, "post_id": post_id}
            
        except Exception as e:
            logger.error(f"LinkedIn publish error: {e}")
            return {"success": False, "error": str(e)}
```

**Acceptance Criteria:**
- ✅ Post successfully publishes to LinkedIn
- ✅ Image uploads correctly
- ✅ Post ID stored in database
- ✅ Error messages user-friendly

---

### Phase 4.2: Publishing Endpoint Enhancement
**Duration:** 0.5 days

**Deliverables:**
- [ ] Real LinkedIn publish in `/posts/publish/{id}` endpoint
- [ ] Polling for publish status
- [ ] Retry logic for transient failures

**Implementation Steps:**
```python
# Update main_v2.py /posts/publish/{post_id}

from tools.linkedin_publisher import LinkedInPublisher
from tenacity import retry, stop_after_attempt

@app.post("/posts/publish/{post_id}")
async def publish_post(post_id: str, db_user: Dict = Depends(get_db_user)):
    """Publish post to LinkedIn"""
    user_id = db_user["id"]
    
    # Get post and LinkedIn token
    post = db.get_post(post_id, user_id)
    token_record = db.get_linkedin_token(user_id)
    
    # Initialize publisher
    publisher = LinkedInPublisher(token_record["access_token"])
    
    # Publish
    result = await publisher.publish_post(
        post_content=post["content"],
        image_url=post.get("image_path")
    )
    
    if result["success"]:
        # Update post status
        db.update_post(post_id, {
            "status": "published",
            "linkedin_post_id": result["post_id"],
            "published_at": datetime.now()
        })
        return {"status": "success", "linkedin_post_id": result["post_id"]}
    else:
        return {"status": "error", "message": result["error"]}
```

**Acceptance Criteria:**
- ✅ Real LinkedIn posts created
- ✅ Publishing tracked in database
- ✅ Errors handled gracefully

---

### Phase 4 Completion Checklist

- [ ] LinkedIn UGC API fully integrated
- [ ] Image upload working
- [ ] Publishing flow end-to-end functional
- [ ] **All integration tests still pass: 11/11** ✅
- [ ] Documentation updated

---

## Phase 5: Testing & Quality Assurance
**Duration:** 2 days  
**Objective:** Comprehensive test coverage and quality gates

---

### Phase 5.1: Automated Testing Suite
**Duration:** 1 day

**Deliverables:**
- [ ] Unit tests for all modules (>80% coverage)
- [ ] Integration tests for all endpoints
- [ ] E2E tests for critical user flows
- [ ] Performance tests

**Test Structure:**
```
tests/
├── unit/
│   ├── test_config.py
│   ├── test_auth.py
│   ├── test_database.py
│   └── test_agents.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_linkedin_integration.py
│   └── test_ai_generation.py
├── e2e/
│   ├── test_user_onboarding.py
│   ├── test_content_generation.py
│   └── test_publishing_flow.py
└── performance/
    ├── test_load.py
    └── test_stress.py
```

**Acceptance Criteria:**
- ✅ >80% code coverage
- ✅ All tests passing in CI
- ✅ Tests run in <5 minutes

---

### Phase 5.2: Manual QA & User Acceptance Testing
**Duration:** 1 day

**Deliverables:**
- [ ] Test cases documented
- [ ] UAT with real users (3-5 testers)
- [ ] Bug tracking and resolution
- [ ] Performance benchmarks validated

**UAT Test Cases:**
1. User can sign up and authenticate
2. User completes onboarding successfully
3. User generates content on first attempt
4. Generated content is relevant and personalized
5. User can edit draft posts
6. User publishes to LinkedIn successfully
7. Published posts appear on LinkedIn
8. User can view published posts in dashboard
9. Error messages are clear and actionable
10. System handles network failures gracefully

**Acceptance Criteria:**
- ✅ All UAT test cases passed
- ✅ Critical bugs resolved
- ✅ Performance targets met
- ✅ Test report documented

---

## Phase 6: Deployment & DevOps
**Duration:** 1 day  
**Objective:** Production deployment on Google Cloud Run

---

### Phase 6.1: Cloud Run Setup
**Duration:** 0.5 days

**Deliverables:**
- [ ] Backend deployed to Cloud Run
- [ ] Frontend deployed to Cloud Run
- [ ] Environment variables configured via Secret Manager
- [ ] Custom domains configured
- [ ] SSL certificates provisioned

**Implementation Steps:**
```bash
# 1. Build and deploy backend
gcloud builds submit --config cloudbuild.api.yaml
gcloud run deploy cis-api \
  --image gcr.io/[PROJECT_ID]/cis-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# 2. Build and deploy frontend
gcloud builds submit --config cloudbuild.frontend.yaml
gcloud run deploy cis-frontend \
  --image gcr.io/[PROJECT_ID]/cis-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# 3. Configure secrets
gcloud secrets create clerk-secret-key --data-file=secrets/clerk_key.txt
gcloud secrets create supabase-url --data-file=secrets/supabase_url.txt
```

**Acceptance Criteria:**
- ✅ Backend accessible at api.cis.example.com
- ✅ Frontend accessible at cis.example.com
- ✅ Health check passing
- ✅ All secrets encrypted

---

### Phase 6.2: CI/CD Pipeline
**Duration:** 0.5 days

**Deliverables:**
- [ ] GitHub Actions workflow
- [ ] Automated testing on PR
- [ ] Automated deployment on merge to main
- [ ] Rollback capability

**Implementation Steps:**
```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest tests/ -v --cov=.

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Cloud Run
        run: |
          gcloud builds submit --config cloudbuild.api.yaml
          gcloud run deploy cis-api --image ...

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Cloud Run
        run: |
          gcloud builds submit --config cloudbuild.frontend.yaml
          gcloud run deploy cis-frontend --image ...
```

**Acceptance Criteria:**
- ✅ Tests run automatically on PR
- ✅ Deployments triggered on merge to main
- ✅ Rollback procedure tested

---

## Phase 7: Monitoring & Observability
**Duration:** 1 day  
**Objective:** Production monitoring and alerting

---

### Phase 7.1: Logging & Tracing
**Duration:** 0.5 days

**Deliverables:**
- [ ] Structured logging configured
- [ ] Log aggregation in Cloud Logging
- [ ] Request tracing enabled
- [ ] Performance metrics captured

**Implementation Steps:**
```python
# Enhanced logging in main_v2.py

import structlog
import uuid

logger = structlog.get_logger()

@app.middleware("http")
async def add_request_id(request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.post("/posts/generate")
async def generate_post(...):
    logger.info("post_generation_started", 
                user_id=user_id, 
                topic=topic,
                request_id=request.state.request_id)
    # ... generation logic
    logger.info("post_generation_completed",
                post_id=post_id,
                duration_ms=duration)
```

**Acceptance Criteria:**
- ✅ All logs in Cloud Logging
- ✅ Request IDs traceable
- ✅ Performance metrics visible

---

### Phase 7.2: Alerting & Dashboards
**Duration:** 0.5 days

**Deliverables:**
- [ ] Cloud Monitoring dashboards
- [ ] Alert policies configured
- [ ] PagerDuty/Opsgenie integration
- [ ] On-call runbook

**Alert Policies:**
1. Error rate >5%
2. API response time p95 >1000ms
3. Database connection failures
4. LinkedIn API failures
5. AI generation failures >10%

**Acceptance Criteria:**
- ✅ Alerts triggering correctly
- ✅ Dashboard shows key metrics
- ✅ Runbook documented

---

## 10. Testing Strategy

### 10.1 Test Pyramid

```
                    /\                E2E Tests (10%)
                   /  \                 
                  /____\              Integration Tests (30%)
                 /      \             
                /________\            Unit Tests (60%)
```

### 10.2 Test Types

| Test Type | Coverage | Execution | Purpose |
|-----------|----------|-----------|---------|
| **Unit Tests** | >80% | Every commit | Validate individual functions |
| **Integration Tests** | All endpoints | Every commit | Validate API contracts |
| **E2E Tests** | Critical flows | Daily | Validate user journeys |
| **Performance Tests** | Core endpoints | Weekly | Validate SLAs |
| **Security Tests** | Authentication | Weekly | Validate security |

### 10.3 Test Automation

**Continuous Integration:**
- Run unit and integration tests on every PR
- Block merge if tests fail
- Generate coverage reports

**Continuous Deployment:**
- Run E2E tests in staging
- Automated deployment to production
- Smoke tests in production

---

## 11. Deployment Strategy

### 11.1 Environments

| Environment | Purpose | URL | Data |
|-------------|---------|-----|------|
| **Development** | Local development | localhost:8080 | Mock data |
| **Staging** | Pre-production testing | staging.cis.example.com | Real services |
| **Production** | Live system | cis.example.com | Production data |

### 11.2 Deployment Process

**Staging Deployment:**
1. Merge feature branch to staging
2. Run full test suite
3. Deploy to staging environment
4. Run smoke tests
5. Monitor for 24 hours
6. Approved for production

**Production Deployment:**
1. Merge staging to main
2. Create release tag
3. Deploy to Cloud Run (canary 10%)
4. Monitor metrics for 15 minutes
5. Rollout to 100%
6. Verify all systems operational

**Rollback Procedure:**
1. Identify failing deployment version
2. Revert to previous working version
3. Deploy previous image
4. Verify health checks
5. Post-mortem investigation

---

## 12. Success Metrics

### 12.1 Technical Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| API Uptime | >99.5% | TBD | 🔄 |
| Error Rate | <1% | TBD | 🔄 |
| P95 Response Time | <500ms | TBD | 🔄 |
| Test Coverage | >80% | TBD | 🔄 |
| Deployment Frequency | Daily | TBD | 🔄 |

### 12.2 Business Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| User Sign-ups | 100/month | TBD | 🔄 |
| Content Generation | 500/month | TBD | 🔄 |
| Publishing Rate | 70% | TBD | 🔄 |
| User Retention | 40% @ 30 days | TBD | 🔄 |
| NPS Score | >50 | TBD | 🔄 |

### 12.3 Product Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Time to First Post | <5 min | TBD | 🔄 |
| Content Quality Score | >7/10 | TBD | 🔄 |
| Avg Posts/User/Week | 3-5 | TBD | 🔄 |
| User Satisfaction | >4.5/5 | TBD | 🔄 |

---

## 13. Risk Assessment

### 13.1 Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LinkedIn API changes | High | Medium | Monitor API, version pinning |
| AI model rate limits | High | Medium | Implement queueing, caching |
| Database performance | Medium | Low | Indexing, query optimization |
| Authentication failures | High | Low | JWKS caching, fallback logic |
| Cloud service outage | High | Low | Multi-region deployment (future) |

### 13.2 Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Low user adoption | High | Medium | Beta testing, user feedback |
| Content quality issues | High | Medium | AI prompt tuning, user ratings |
| Compliance violations | High | Low | GDPR compliance, data encryption |
| Competitor launch | Medium | Medium | Faster feature delivery |

### 13.3 Operational Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Key person dependency | Medium | Medium | Documentation, knowledge sharing |
| Budget overrun | Medium | Low | Phased rollout, cost monitoring |
| Security breach | High | Low | Regular audits, penetration testing |

---

## 14. Appendix

### 14.1 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Frontend | Streamlit | 1.28+ | Web UI |
| Backend | FastAPI | 0.104+ | REST API |
| Database | Supabase (PostgreSQL) | Latest | Data persistence |
| Auth | Clerk | Latest | Authentication |
| AI | Google Gemini | Latest | Content generation |
| Infrastructure | Google Cloud Run | Latest | Container hosting |
| CI/CD | GitHub Actions | Latest | Automation |
| Monitoring | Cloud Monitoring | Latest | Observability |

### 14.2 Dependencies

**Backend:**
```
fastapi==0.104+
uvicorn==0.24+
pydantic==2.5+
python-dotenv==1.0+
supabase==2.0+
python-jose[cryptography]==3.3+
requests==2.31+
google-generativeai==0.3+
pillow==10.1+
tenacity==8.2+
```

**Frontend:**
```
streamlit==1.28+
requests==2.31+
```

### 14.3 API Contract Reference

**Baseline Endpoints (from test_server.py):**
1. `GET /health` - Health check
2. `GET /auth/verify` - Verify authentication
3. `GET /user/profile` - Get user profile
4. `POST /onboarding/questionnaire` - Submit onboarding
5. `POST /posts/generate` - Generate post
6. `GET /posts/pending` - Get draft posts
7. `GET /posts/published` - Get published posts
8. `PUT /posts/{id}` - Update post
9. `POST /posts/publish/{id}` - Publish post
10. `GET /auth/linkedin/authorize` - LinkedIn OAuth
11. `GET /auth/linkedin/status` - Check LinkedIn status

### 14.4 Glossary

| Term | Definition |
|------|------------|
| **UGC** | User-Generated Content (LinkedIn API) |
| **JWKS** | JSON Web Key Set (Clerk public keys) |
| **RLS** | Row-Level Security (Supabase) |
| **SaaS** | Software as a Service |
| **NPS** | Net Promoter Score |
| **SLA** | Service Level Agreement |
| **p95** | 95th percentile response time |

### 14.5 References

- [LinkedIn UGC API Documentation](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/ugc-post-api)
- [Clerk Authentication Docs](https://clerk.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Streamlit Documentation](https://docs.streamlit.io)

---

## 15. Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-10-29 | 1.0 | Product Team | Initial PRD draft |
| 2025-10-29 | 2.0 | Engineering Team | Complete production PRD |

---

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Tech Lead | | | |
| Security Lead | | | |
| Operations Lead | | | |

---

**END OF DOCUMENT**