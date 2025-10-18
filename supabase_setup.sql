-- Supabase Table Setup for Multi-Source Internship Scraper
-- Run this SQL in your Supabase SQL Editor to create the internships table

-- Create internships table
CREATE TABLE IF NOT EXISTS internships (
  id BIGSERIAL PRIMARY KEY,
  logo TEXT,
  title TEXT NOT NULL,
  description TEXT,
  company TEXT NOT NULL,
  location TEXT,
  url TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for faster duplicate checking by URL
CREATE INDEX IF NOT EXISTS idx_internships_url ON internships(url);

-- Add index for searching by company
CREATE INDEX IF NOT EXISTS idx_internships_company ON internships(company);

-- Add index for searching by date
CREATE INDEX IF NOT EXISTS idx_internships_created_at ON internships(created_at DESC);

-- Optional: Enable Row Level Security (RLS)
ALTER TABLE internships ENABLE ROW LEVEL SECURITY;

-- Optional: Create a policy to allow authenticated users to read all internships
CREATE POLICY "Allow authenticated users to read internships"
  ON internships
  FOR SELECT
  TO authenticated
  USING (true);

-- Optional: Create a policy to allow service role to insert/update/delete
CREATE POLICY "Allow service role full access to internships"
  ON internships
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Note: If you're using the anon key, you might want to adjust the policies
-- or disable RLS for testing: ALTER TABLE internships DISABLE ROW LEVEL SECURITY;

