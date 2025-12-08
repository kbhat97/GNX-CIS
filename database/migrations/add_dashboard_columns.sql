-- Migration: Add dashboard columns to posts table
-- Date: 2025-12-08
-- Description: Extends posts table with virality scoring, suggestions, and image data

-- Add new columns for GNX dashboard features
ALTER TABLE public.posts 
ADD COLUMN IF NOT EXISTS virality_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS suggestions JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS image_url TEXT,
ADD COLUMN IF NOT EXISTS style VARCHAR(50),
ADD COLUMN IF NOT EXISTS persona TEXT,
ADD COLUMN IF NOT EXISTS improvement_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS previous_score INTEGER;

-- Add index for faster queries by user_id and score
CREATE INDEX IF NOT EXISTS idx_posts_user_score ON public.posts(user_id, virality_score DESC);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts(created_at DESC);

-- Add comment for documentation
COMMENT ON COLUMN public.posts.virality_score IS 'AI-generated engagement score (0-100)';
COMMENT ON COLUMN public.posts.suggestions IS 'AI suggestions for improving the post';
COMMENT ON COLUMN public.posts.image_url IS 'URL to generated AI image';
COMMENT ON COLUMN public.posts.style IS 'Content style: professional, technical, inspirational, thought_leadership, storytelling';
COMMENT ON COLUMN public.posts.persona IS 'Custom persona used for generation';
COMMENT ON COLUMN public.posts.improvement_count IS 'Number of times post was improved';
COMMENT ON COLUMN public.posts.previous_score IS 'Score before last improvement';
