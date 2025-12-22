-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 003: Add recent_hooks to user_profiles
-- Purpose: Store last 5 hook patterns to prevent content repetition
-- Part of: IMP-003 (Content Variety System)
-- ═══════════════════════════════════════════════════════════════════════════════

-- Add recent_hooks column to user_profiles
-- Stores the last 5 opening lines (hooks) used in generated posts
-- Used by ContentAgent to inject PROHIBITED_HOOKS into prompts
ALTER TABLE public.user_profiles 
ADD COLUMN IF NOT EXISTS recent_hooks TEXT[] DEFAULT '{}';

-- Comment for documentation
COMMENT ON COLUMN public.user_profiles.recent_hooks IS 
  'Last 5 hook patterns used by user, injected as PROHIBITED_HOOKS to prevent repetition';

-- ═══════════════════════════════════════════════════════════════════════════════
-- RPC Function: append_recent_hook
-- Appends a new hook and trims to keep only the last 5
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.append_recent_hook(
    p_user_id UUID,
    p_new_hook TEXT
)
RETURNS VOID AS $$
DECLARE
    current_hooks TEXT[];
    new_hooks TEXT[];
BEGIN
    -- Get current hooks
    SELECT recent_hooks INTO current_hooks
    FROM public.user_profiles
    WHERE user_id = p_user_id;
    
    -- If user_profiles row doesn't exist, create it
    IF NOT FOUND THEN
        INSERT INTO public.user_profiles (user_id, recent_hooks)
        VALUES (p_user_id, ARRAY[p_new_hook])
        ON CONFLICT (user_id) DO UPDATE SET recent_hooks = ARRAY[p_new_hook];
        RETURN;
    END IF;
    
    -- Append new hook and trim to last 5
    new_hooks := array_append(COALESCE(current_hooks, '{}'), p_new_hook);
    
    -- Keep only last 5 hooks (FIFO)
    IF array_length(new_hooks, 1) > 5 THEN
        new_hooks := new_hooks[array_length(new_hooks, 1) - 4 : array_length(new_hooks, 1)];
    END IF;
    
    -- Update the user's recent_hooks
    UPDATE public.user_profiles
    SET recent_hooks = new_hooks,
        updated_at = NOW()
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.append_recent_hook(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.append_recent_hook(UUID, TEXT) TO service_role;

-- ═══════════════════════════════════════════════════════════════════════════════
-- RPC Function: get_recent_hooks
-- Returns the last N hooks for a user (default 5)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.get_recent_hooks(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 5
)
RETURNS TEXT[] AS $$
DECLARE
    hooks TEXT[];
BEGIN
    SELECT recent_hooks INTO hooks
    FROM public.user_profiles
    WHERE user_id = p_user_id;
    
    -- Return empty array if not found
    IF NOT FOUND OR hooks IS NULL THEN
        RETURN '{}';
    END IF;
    
    -- Return last N hooks
    IF array_length(hooks, 1) > p_limit THEN
        RETURN hooks[array_length(hooks, 1) - p_limit + 1 : array_length(hooks, 1)];
    END IF;
    
    RETURN hooks;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.get_recent_hooks(UUID, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_recent_hooks(UUID, INTEGER) TO service_role;

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROLLBACK SCRIPT (run separately if needed)
-- ═══════════════════════════════════════════════════════════════════════════════
-- ALTER TABLE public.user_profiles DROP COLUMN IF EXISTS recent_hooks;
-- DROP FUNCTION IF EXISTS public.append_recent_hook(UUID, TEXT);
-- DROP FUNCTION IF EXISTS public.get_recent_hooks(UUID, INTEGER);
