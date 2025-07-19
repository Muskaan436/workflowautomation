-- Database setup for Workflow Automation System
-- Run this in your Supabase SQL editor

-- 1. Users table (if not already created)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. User Integrations table
CREATE TABLE IF NOT EXISTS user_integrations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',  -- Store additional data like database IDs
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- 4. User Workflows table
CREATE TABLE IF NOT EXISTS user_workflows (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, workflow_id)
);

-- 5. Workflow Execution Logs table
CREATE TABLE IF NOT EXISTS workflow_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    workflow_id INT NOT NULL,
    step_id INT,
    step_type TEXT,
    app TEXT,
    description TEXT,
    success BOOLEAN,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default workflows
INSERT INTO workflows (id, name) VALUES 
    (1, 'Notion to Google Meet'),
    (3, 'GMeet to Notion'),
    (4, 'Slack to Notion')
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_integrations_user_id ON user_integrations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_integrations_provider ON user_integrations(provider);
CREATE INDEX IF NOT EXISTS idx_user_workflows_user_id ON user_workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_user_workflows_workflow_id ON user_workflows(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_logs_user_id ON workflow_execution_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_logs_workflow_id ON workflow_execution_logs(workflow_id);

-- Verify the setup
SELECT 'Tables created successfully' as status;
SELECT COUNT(*) as workflows_count FROM workflows; 