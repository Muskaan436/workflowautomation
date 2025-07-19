# Workflow Automation System

A comprehensive workflow automation platform that integrates Notion, Google Calendar, and other services using Celery for background task processing.

## 🚀 Features

- **Multi-Service Integration**: Connect Notion, Google Calendar, and more
- **Background Processing**: Celery-powered task queue with Redis/Upstash
- **User Authentication**: Secure OAuth flows for all integrated services
- **Workflow Management**: Create, activate, and monitor automated workflows
- **Execution Logging**: Track all workflow activities with detailed analytics
- **Real-time Updates**: Live status updates and notifications

## 📋 Available Workflows

### 1. Notion to Google Meet
- **Trigger**: New entries in Notion database marked for scheduling
- **Action**: Automatically create Google Meet events
- **Features**: 
  - Polls Notion database every 5 minutes
  - Creates Google Calendar events with meeting links
  - Updates Notion entries with event IDs
  - Marks entries as "Done" after scheduling



### 3. GMeet to Notion
- **Trigger**: New Google Meet events
- **Action**: Create Notion database entries
- **Features**: Meeting details and attendee tracking

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd workflow_automation
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file with your configuration:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Notion OAuth
NOTION_CLIENT_ID=your_notion_client_id
NOTION_CLIENT_SECRET=your_notion_client_secret

# App Configuration
SECRET_KEY=your_secret_key
REDIS_URL=redis://localhost:6379

# OAuth Redirect URIs (for development)
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

NOTION_REDIRECT_URI=http://localhost:8000/auth/notion/callback
```

### 3. Database Setup

Create the following tables in your Supabase database:

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### User Integrations Table
```sql
CREATE TABLE user_integrations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_in INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Workflow Execution Logs Table
```sql
CREATE TABLE workflow_execution_logs (
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
```

### 4. Run the Application

```bash
# Start the FastAPI server
python -m app.main

# Open the frontend
open index.html  # Or navigate to the file in your browser
```

The API will be available at `http://localhost:8000` and the frontend at `index.html`.

## 📋 Available Workflows

### 1. Notion to Google Meet
- **Trigger**: New entries in Notion database marked for scheduling 