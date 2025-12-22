-- Migration: Add subscription and post limit columns to user_profiles
-- Purpose: Support Stripe subscription management and post limit enforcement
-- Created: 2025-12-19

-- Add subscription management columns
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS subscription_plan TEXT DEFAULT 'free' CHECK (subscription_plan IN ('free', 'pro', 'business')),
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('active', 'canceled', 'past_due', 'trialing')),
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS posts_this_month INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS posts_reset_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMPTZ;

-- Create index on stripe_customer_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_stripe_customer_id 
ON user_profiles(stripe_customer_id) 
WHERE stripe_customer_id IS NOT NULL;

-- Create index on user_id + subscription_plan for queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_subscription 
ON user_profiles(user_id, subscription_plan);

-- Create function to reset monthly post count
CREATE OR REPLACE FUNCTION reset_monthly_post_count()
RETURNS TRIGGER AS $$
BEGIN
  -- If more than 1 month has passed since last reset, reset the counter
  IF NEW.posts_reset_at < NOW() - INTERVAL '1 month' THEN
    NEW.posts_this_month := 0;
    NEW.posts_reset_at := NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-reset monthly count on update
DROP TRIGGER IF EXISTS trigger_reset_monthly_posts ON user_profiles;
CREATE TRIGGER trigger_reset_monthly_posts
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION reset_monthly_post_count();

-- Add comments for documentation
COMMENT ON COLUMN user_profiles.subscription_plan IS 'Current subscription tier: free, pro, business';
COMMENT ON COLUMN user_profiles.subscription_status IS 'Stripe subscription status: active, canceled, past_due, trialing';
COMMENT ON COLUMN user_profiles.stripe_customer_id IS 'Stripe customer ID for subscription management';
COMMENT ON COLUMN user_profiles.posts_this_month IS 'Counter for monthly post limit enforcement';
COMMENT ON COLUMN user_profiles.posts_reset_at IS 'Timestamp when posts_this_month was last reset';
COMMENT ON COLUMN user_profiles.trial_ends_at IS 'Free trial expiration date (null if not on trial)';

-- Grant RLS policies for new columns (inherits existing user_profiles policies)
-- Existing RLS should already cover these columns as they're part of the same table
