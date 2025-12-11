-- ============================================
-- MIGRATION: Add improve_post RPC function
-- Tables already exist - just need the atomic function
-- Run this in Supabase SQL Editor
-- ============================================

-- ============================================
-- STEP 1: Clean up any existing functions (handle signature conflicts)
-- ============================================

-- Drop all existing versions of improve_post
DROP FUNCTION IF EXISTS public.improve_post(uuid, uuid, text, text, integer, text, text, integer);
DROP FUNCTION IF EXISTS public.improve_post(uuid, uuid, text, text, integer, text, text, jsonb, integer);
DROP FUNCTION IF EXISTS public.improve_post(uuid, uuid, text, text, integer);

-- Drop existing get_post_history
DROP FUNCTION IF EXISTS public.get_post_history(uuid);

-- ============================================
-- STEP 2: Ensure indexes exist for post_history queries
-- ============================================
CREATE INDEX IF NOT EXISTS idx_post_history_post_created 
  ON post_history(post_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_history_post_version 
  ON post_history(post_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_post_history_author 
  ON post_history(author_id);

-- ============================================
-- STEP 3: Create improve_post RPC function
-- Handles history snapshot + update in one transaction with optimistic locking
-- ============================================

CREATE OR REPLACE FUNCTION public.improve_post(
  p_post_id uuid,
  p_user_id uuid,
  p_new_content text,
  p_new_topic text,
  p_new_score integer,
  p_image_url text DEFAULT NULL,
  p_style text DEFAULT NULL,
  p_suggestions jsonb DEFAULT '[]'::jsonb,
  p_expected_version integer DEFAULT NULL
) RETURNS jsonb AS $$
DECLARE
  v_current_post posts%ROWTYPE;
  v_result jsonb;
BEGIN
  -- Fetch current post (verify ownership)
  SELECT * INTO v_current_post 
  FROM posts 
  WHERE id = p_post_id AND user_id = p_user_id;
  
  IF NOT FOUND THEN
    RETURN jsonb_build_object('success', false, 'error', 'post_not_found');
  END IF;
  
  -- Optimistic locking check (if version provided)
  IF p_expected_version IS NOT NULL AND v_current_post.version != p_expected_version THEN
    RETURN jsonb_build_object(
      'success', false, 
      'error', 'version_mismatch',
      'current_version', v_current_post.version,
      'expected_version', p_expected_version
    );
  END IF;
  
  -- Insert snapshot of CURRENT state into history (before we modify it)
  INSERT INTO post_history (
    post_id, 
    author_id, 
    change_type, 
    payload, 
    previous_score, 
    new_score,
    version
  ) VALUES (
    p_post_id,
    p_user_id,
    'improve',
    to_jsonb(v_current_post),
    v_current_post.virality_score,
    p_new_score,
    v_current_post.version
  );
  
  -- Update canonical post with new improved content
  UPDATE posts SET
    content = p_new_content,
    topic = COALESCE(p_new_topic, topic),
    virality_score = p_new_score,
    previous_score = v_current_post.virality_score,
    improvement_count = COALESCE(improvement_count, 0) + 1,
    version = version + 1,
    image_url = COALESCE(p_image_url, image_url),
    style = COALESCE(p_style, style),
    suggestions = COALESCE(p_suggestions, suggestions),
    updated_at = now()
  WHERE id = p_post_id
  RETURNING jsonb_build_object(
    'success', true,
    'post_id', id,
    'new_version', version,
    'improvement_count', improvement_count,
    'previous_score', previous_score,
    'new_score', virality_score,
    'content', content
  ) INTO v_result;
  
  RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- STEP 4: Create get_post_history helper function
-- ============================================

CREATE OR REPLACE FUNCTION public.get_post_history(p_post_id uuid)
RETURNS TABLE (
  history_id uuid,
  change_type text,
  previous_score integer,
  new_score integer,
  version integer,
  created_at timestamptz,
  original_content text,
  original_topic text
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ph.id as history_id,
    ph.change_type,
    ph.previous_score,
    ph.new_score,
    ph.version,
    ph.created_at,
    (ph.payload->>'content')::text as original_content,
    (ph.payload->>'topic')::text as original_topic
  FROM post_history ph
  WHERE ph.post_id = p_post_id
  ORDER BY ph.created_at DESC
  LIMIT 20;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- STEP 5: Grant permissions
-- ============================================

-- Grant for improve_post (with full signature)
GRANT EXECUTE ON FUNCTION public.improve_post(uuid, uuid, text, text, integer, text, text, jsonb, integer) TO authenticated;
GRANT EXECUTE ON FUNCTION public.improve_post(uuid, uuid, text, text, integer, text, text, jsonb, integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.improve_post(uuid, uuid, text, text, integer, text, text, jsonb, integer) TO anon;

-- Grant for get_post_history
GRANT EXECUTE ON FUNCTION public.get_post_history(uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_post_history(uuid) TO anon;

-- ============================================
-- STEP 6: Add comments
-- ============================================
COMMENT ON FUNCTION public.improve_post(uuid, uuid, text, text, integer, text, text, jsonb, integer) 
  IS 'Atomic post improvement: saves current state to history, then updates canonical post. Uses optimistic locking via version column.';
COMMENT ON FUNCTION public.get_post_history(uuid) 
  IS 'Returns the edit history for a post, showing previous versions.';
