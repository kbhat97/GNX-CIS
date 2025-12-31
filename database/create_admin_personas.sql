-- ============================================
-- ADMIN PERSONAS TABLE
-- Run this in Supabase SQL Editor
-- ============================================

-- Step 1: Create the table
CREATE TABLE IF NOT EXISTS admin_personas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    persona_id TEXT UNIQUE NOT NULL,
    persona_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_admin_personas_persona_id ON admin_personas(persona_id);

-- Step 3: Enable RLS (Row Level Security)
ALTER TABLE admin_personas ENABLE ROW LEVEL SECURITY;

-- Step 4: Allow service role full access (for API)
CREATE POLICY "Service role has full access" ON admin_personas
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Step 5: Allow authenticated users to read (for dashboard)
CREATE POLICY "Authenticated users can read" ON admin_personas
    FOR SELECT
    TO authenticated
    USING (true);

-- ============================================
-- INSERT YOUR ADMIN PERSONA
-- ============================================

INSERT INTO admin_personas (persona_id, persona_data) VALUES (
    'persona_admin_kunal',
    '{
        "id": "persona_admin_kunal",
        "version": "1.1.0",
        "display_name": "Kunal (Admin Persona)",
        "user_id": "kunal_bhat",
        "role": "admin",
        "identity": {
            "name": "Kunal Bhat, PMP",
            "title": "SAP Leader | S/4HANA Implementation Expert | Digital Transformation Strategist",
            "summary": "SAP Leader and Implementation Expert with 10+ years driving enterprise-scale S/4HANA transformations across North America and APAC. Proven track record delivering $3M-$4.5M SAP programs for Fortune 500 clients, specializing in end-to-end implementation lifecycle, change management, and strategic digital transformation. Known for bridging the gap between business requirements and technical execution.",
            "core_expertise": [
                "S/4HANA End-to-End Implementation",
                "SAP Program Leadership",
                "Digital Transformation Strategy",
                "Enterprise Architecture",
                "Change Management",
                "Stakeholder Alignment"
            ]
        },
        "audience_model": {
            "industries": [
                "IT Services and IT Consulting",
                "Manufacturing",
                "Technology",
                "Financial Services"
            ],
            "locations": [
                "Greater Toronto Area, Canada",
                "Greater Delhi Area, India",
                "United States"
            ],
            "seniority_distribution": {
                "Senior": 48,
                "Entry": 21.7,
                "Director": 11.6,
                "Manager": 10,
                "VP": 5
            },
            "company_examples": [
                "Deloitte",
                "Accenture",
                "IBM",
                "SAP",
                "TCS",
                "Infosys",
                "Wipro"
            ]
        },
        "tone_profile": {
            "keywords": [
                "Structured",
                "Authoritative",
                "Practical",
                "Experience-driven",
                "Clear"
            ],
            "writing_patterns": {
                "uses_bullet_points": true,
                "uses_numbered_lists": true,
                "uses_checklists": true,
                "includes_personal_anecdotes": true,
                "avoids_jargon": false,
                "professional_but_approachable": true
            }
        },
        "content_preferences": {
            "main_themes": [
                "S/4HANA Implementation Best Practices",
                "SAP Program Leadership",
                "Digital Transformation Roadmaps",
                "Enterprise System Migration",
                "Change Management in ERP Projects",
                "Cross-functional Team Leadership"
            ],
            "post_types": [
                "Implementation Lessons Learned",
                "Leadership Insights",
                "Technical Deep Dives",
                "Project Success Stories",
                "Industry Trend Analysis"
            ]
        },
        "publishing": {
            "default_channel": "linkedin_member",
            "hashtags": [
                "#SAP",
                "#S4HANA",
                "#DigitalTransformation",
                "#SAPImplementation",
                "#EnterpriseArchitecture"
            ],
            "timezones_primary": [
                "America/Toronto",
                "Asia/Kolkata"
            ]
        }
    }'::jsonb
) ON CONFLICT (persona_id) DO UPDATE SET
    persona_data = EXCLUDED.persona_data,
    updated_at = NOW();

-- Verify the insert
SELECT persona_id, persona_data->>'display_name' as name, created_at FROM admin_personas;
