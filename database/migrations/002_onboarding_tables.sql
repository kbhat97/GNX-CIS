-- ============================================
-- MIGRATION: Onboarding Tables & RLS Policies
-- UPDATED: Uses uuid for user_id to match existing schema
-- Run this in Supabase SQL Editor
-- ============================================

-- ============================================
-- STEP 1: Add missing columns to existing user_profiles table
-- (table already exists, just add new columns)
-- ============================================

-- Add onboarding-specific columns if they don't exist
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS industry text;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS content_style text;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS topics text[];
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS primary_goal text;

-- ============================================
-- STEP 2: Create virality_calibration table
-- (new table for ViralityAgent bias checking)
-- ============================================

CREATE TABLE IF NOT EXISTS public.virality_calibration (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  
  -- Post sample
  post_content text NOT NULL,
  post_industry text,
  post_style text,
  
  -- Scores
  human_score integer NOT NULL,  -- Ground truth score (1-100)
  ai_score integer,              -- ViralityAgent's score
  
  -- Calibration metadata
  calibration_date timestamptz DEFAULT now(),
  score_difference integer GENERATED ALWAYS AS (ai_score - human_score) STORED,
  
  -- Source info
  source_type text,  -- 'internal', 'user_feedback', 'linkedin_sample'
  notes text
);

-- Index for calibration queries
CREATE INDEX IF NOT EXISTS idx_calibration_date ON virality_calibration(calibration_date DESC);

-- ============================================
-- STEP 3: Enable Row Level Security on all tables
-- ============================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE linkedin_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE engagements ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_engagement ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_questionnaire ENABLE ROW LEVEL SECURITY;
ALTER TABLE virality_calibration ENABLE ROW LEVEL SECURITY;

-- ============================================
-- STEP 4: Drop existing policies (clean slate)
-- ============================================

-- Users table
DROP POLICY IF EXISTS "users_select_own" ON users;
DROP POLICY IF EXISTS "users_insert_own" ON users;
DROP POLICY IF EXISTS "users_update_own" ON users;

-- Posts table
DROP POLICY IF EXISTS "posts_select_own" ON posts;
DROP POLICY IF EXISTS "posts_insert_own" ON posts;
DROP POLICY IF EXISTS "posts_update_own" ON posts;
DROP POLICY IF EXISTS "posts_delete_own" ON posts;

-- User profiles table
DROP POLICY IF EXISTS "profiles_select_own" ON user_profiles;
DROP POLICY IF EXISTS "profiles_insert_own" ON user_profiles;
DROP POLICY IF EXISTS "profiles_update_own" ON user_profiles;

-- Content analysis table
DROP POLICY IF EXISTS "content_select_own" ON content_analysis;
DROP POLICY IF EXISTS "content_insert_own" ON content_analysis;
DROP POLICY IF EXISTS "content_update_own" ON content_analysis;

-- LinkedIn tokens table
DROP POLICY IF EXISTS "tokens_select_own" ON linkedin_tokens;
DROP POLICY IF EXISTS "tokens_insert_own" ON linkedin_tokens;
DROP POLICY IF EXISTS "tokens_update_own" ON linkedin_tokens;

-- Engagements table
DROP POLICY IF EXISTS "engagements_select_own" ON engagements;
DROP POLICY IF EXISTS "engagements_insert_own" ON engagements;

-- Agent memory table
DROP POLICY IF EXISTS "memory_select_own" ON agent_memory;
DROP POLICY IF EXISTS "memory_insert_own" ON agent_memory;

-- Post history table
DROP POLICY IF EXISTS "history_select_own" ON post_history;
DROP POLICY IF EXISTS "history_insert_own" ON post_history;

-- Calibration table
DROP POLICY IF EXISTS "calibration_select_all" ON virality_calibration;
DROP POLICY IF EXISTS "calibration_service_manage" ON virality_calibration;

-- ============================================
-- STEP 5: Create helper function to get user's internal ID
-- Maps clerk_id to internal uuid
-- ============================================

CREATE OR REPLACE FUNCTION get_user_id_from_clerk(p_clerk_id text)
RETURNS uuid AS $$
  SELECT id FROM users WHERE clerk_id = p_clerk_id LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ============================================
-- STEP 6: Create RLS Policies
-- NOTE: Using service_role bypass for backend API calls
-- ============================================

-- USERS TABLE
CREATE POLICY "users_select_own" ON users
  FOR SELECT USING (
    clerk_id = current_setting('request.jwt.claims', true)::json->>'sub'
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "users_insert_own" ON users
  FOR INSERT WITH CHECK (
    clerk_id = current_setting('request.jwt.claims', true)::json->>'sub'
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "users_update_own" ON users
  FOR UPDATE USING (
    clerk_id = current_setting('request.jwt.claims', true)::json->>'sub'
    OR current_setting('role', true) = 'service_role'
  );

-- POSTS TABLE
CREATE POLICY "posts_select_own" ON posts
  FOR SELECT USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "posts_insert_own" ON posts
  FOR INSERT WITH CHECK (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "posts_update_own" ON posts
  FOR UPDATE USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "posts_delete_own" ON posts
  FOR DELETE USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

-- USER PROFILES TABLE
CREATE POLICY "profiles_select_own" ON user_profiles
  FOR SELECT USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "profiles_insert_own" ON user_profiles
  FOR INSERT WITH CHECK (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "profiles_update_own" ON user_profiles
  FOR UPDATE USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

-- CONTENT ANALYSIS TABLE
CREATE POLICY "content_select_own" ON content_analysis
  FOR SELECT USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "content_insert_own" ON content_analysis
  FOR INSERT WITH CHECK (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "content_update_own" ON content_analysis
  FOR UPDATE USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

-- LINKEDIN TOKENS TABLE
CREATE POLICY "tokens_select_own" ON linkedin_tokens
  FOR SELECT USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "tokens_insert_own" ON linkedin_tokens
  FOR INSERT WITH CHECK (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "tokens_update_own" ON linkedin_tokens
  FOR UPDATE USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

-- ENGAGEMENTS TABLE
CREATE POLICY "engagements_select_own" ON engagements
  FOR SELECT USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "engagements_insert_own" ON engagements
  FOR INSERT WITH CHECK (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

-- AGENT MEMORY TABLE
CREATE POLICY "memory_select_own" ON agent_memory
  FOR SELECT USING (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "memory_insert_own" ON agent_memory
  FOR INSERT WITH CHECK (
    user_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

-- POST HISTORY TABLE
CREATE POLICY "history_select_own" ON post_history
  FOR SELECT USING (
    author_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

CREATE POLICY "history_insert_own" ON post_history
  FOR INSERT WITH CHECK (
    author_id IN (SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claims', true)::json->>'sub')
    OR current_setting('role', true) = 'service_role'
  );

-- VIRALITY CALIBRATION TABLE (read-only for users, full access for service)
CREATE POLICY "calibration_select_all" ON virality_calibration
  FOR SELECT USING (true);

CREATE POLICY "calibration_service_manage" ON virality_calibration
  FOR ALL USING (current_setting('role', true) = 'service_role');

-- ============================================
-- STEP 7: Grant permissions
-- ============================================

GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

-- Grant to authenticated users
GRANT SELECT, INSERT, UPDATE ON users TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON posts TO authenticated;
GRANT SELECT, INSERT, UPDATE ON user_profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE ON content_analysis TO authenticated;
GRANT SELECT, INSERT, UPDATE ON linkedin_tokens TO authenticated;
GRANT SELECT, INSERT ON engagements TO authenticated;
GRANT SELECT, INSERT ON agent_memory TO authenticated;
GRANT SELECT, INSERT ON post_history TO authenticated;
GRANT SELECT ON post_engagement TO authenticated;
GRANT SELECT ON virality_calibration TO authenticated;

-- Grant full access to service_role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;

-- Grant function execution
GRANT EXECUTE ON FUNCTION get_user_id_from_clerk(text) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_id_from_clerk(text) TO service_role;

-- ============================================
-- STEP 8: Comments
-- ============================================

COMMENT ON FUNCTION get_user_id_from_clerk IS 'Maps Clerk user ID to internal UUID';
COMMENT ON TABLE virality_calibration IS 'Ground truth dataset for ViralityAgent bias validation';
