#!/usr/bin/env python3
"""
JIRA HTTP Server для тестирования и мониторинга
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-http")

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        logger.info(f"Loading .env file from {env_path}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

class JIRAConfig:
    """JIRA configuration"""
    
    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL", "").strip()
        self.username = os.getenv("JIRA_USERNAME", "").strip()
        self.api_token = os.getenv("JIRA_API_TOKEN", "").strip()
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "").strip()
    
    def is_valid(self) -> bool:
        return bool(self.base_url and self.username and self.api_token and self.project_key)

# Load configuration
load_env_file()
config = JIRAConfig()

# FastAPI app
app = FastAPI(title="JIRA MCP Server Monitor", version="1.0.0")

# Stats
stats = {
    "started_at": datetime.now().isoformat(),
    "requests_count": 0,
    "errors_count": 0,
    "last_request": None
}

async def create_jira_issue(summary: str, description: str, issue_type: str = "Task") -> dict:
    """Create a JIRA issue"""
    
    issue_data = {
        "fields": {
            "project": {"key": config.project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            },
            "issuetype": {"name": issue_type}
        }
    }
    
    async with httpx.AsyncClient(
        auth=(config.username, config.api_token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=30.0
    ) as client:
        url = urljoin(f"{config.base_url.rstrip('/')}/rest/api/3/", "issue")
        response = await client.post(url, json=issue_data)
        response.raise_for_status()
        return response.json()

async def get_jira_issue(issue_key: str) -> dict:
    """Get JIRA issue details"""
    
    async with httpx.AsyncClient(
        auth=(config.username, config.api_token),
        headers={"Accept": "application/json"},
        timeout=30.0
    ) as client:
        url = urljoin(f"{config.base_url.rstrip('/')}/rest/api/3/", f"issue/{issue_key}")
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

@app.get("/", response_class=HTMLResponse)
async def status_page():
    """Status page"""
    
    # Test JIRA connection
    jira_status = "❌ Not Connected"
    jira_user = "Unknown"
    
    try:
        async with httpx.AsyncClient(
            auth=(config.username, config.api_token),
            timeout=10.0
        ) as client:
            url = f"{config.base_url}/rest/api/3/myself"
            response = await client.get(url)
            response.raise_for_status()
            user_info = response.json()
            jira_status = "✅ Connected"
            jira_user = user_info.get('displayName', config.username)
    except Exception as e:
        jira_status = f"❌ Error: {str(e)}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>JIRA MCP Server Status</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 2px solid #007cba; padding-bottom: 10px; }}
            .status {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .status.good {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
            .status.bad {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
            .info {{ background: #e2e3e5; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .button {{ display: inline-block; padding: 10px 20px; background: #007cba; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }}
            .button:hover {{ background: #005a87; }}
            pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        </style>
        <script>
            function refreshPage() {{ location.reload(); }}
            setInterval(refreshPage, 30000); // Refresh every 30 seconds
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🎯 JIRA MCP Server Monitor</h1>
            
            <div class="status {'good' if jira_status.startswith('✅') else 'bad'}">
                <strong>JIRA Connection:</strong> {jira_status}<br>
                <strong>User:</strong> {jira_user}<br>
                <strong>Base URL:</strong> {config.base_url}<br>
                <strong>Project:</strong> {config.project_key}
            </div>
            
            <div class="info">
                <strong>Server Started:</strong> {stats['started_at']}<br>
                <strong>Total Requests:</strong> {stats['requests_count']}<br>
                <strong>Errors:</strong> {stats['errors_count']}<br>
                <strong>Last Request:</strong> {stats['last_request'] or 'None'}
            </div>
            
            <h2>🛠️ Test API</h2>
            <a href="/health" class="button">Health Check</a>
            <a href="/jira/test" class="button">Test JIRA Connection</a>
            <a href="/tools" class="button">List Available Tools</a>
            
            <h2>📝 Usage Examples</h2>
            <pre>
# Create a JIRA issue
curl -X POST http://your-server:8000/jira/issues \\
  -H "Content-Type: application/json" \\
  -d '{{"summary": "Test Issue", "description": "Test Description", "issue_type": "Task"}}'

# Get issue details  
curl http://your-server:8000/jira/issues/SCRUM-123

# Health check
curl http://your-server:8000/health
            </pre>
            
            <p><em>Auto-refresh every 30 seconds</em></p>
        </div>
    </body>
    </html>
    """
    
    return html

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    stats["requests_count"] += 1
    stats["last_request"] = datetime.now().isoformat()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config_valid": config.is_valid(),
        "stats": stats
    }

@app.get("/jira/test")
async def test_jira_connection():
    """Test JIRA connection"""
    stats["requests_count"] += 1
    stats["last_request"] = datetime.now().isoformat()
    
    try:
        async with httpx.AsyncClient(
            auth=(config.username, config.api_token),
            timeout=10.0
        ) as client:
            url = f"{config.base_url}/rest/api/3/myself"
            response = await client.get(url)
            response.raise_for_status()
            user_info = response.json()
            
            return {
                "status": "success",
                "user": user_info.get('displayName'),
                "email": user_info.get('emailAddress'),
                "jira_url": config.base_url
            }
    except Exception as e:
        stats["errors_count"] += 1
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    stats["requests_count"] += 1
    stats["last_request"] = datetime.now().isoformat()
    
    return {
        "tools": [
            {
                "name": "create_jira_issue",
                "description": "Create a new JIRA issue",
                "parameters": ["summary", "description", "issue_type"]
            },
            {
                "name": "get_jira_issue", 
                "description": "Get JIRA issue details",
                "parameters": ["issue_key"]
            }
        ]
    }

@app.post("/jira/issues")
async def create_issue_endpoint(request: dict):
    """Create JIRA issue via HTTP"""
    stats["requests_count"] += 1
    stats["last_request"] = datetime.now().isoformat()
    
    try:
        result = await create_jira_issue(
            summary=request["summary"],
            description=request["description"],
            issue_type=request.get("issue_type", "Task")
        )
        
        return {
            "status": "success",
            "issue_key": result["key"],
            "url": f"{config.base_url}/browse/{result['key']}",
            "result": result
        }
    except Exception as e:
        stats["errors_count"] += 1
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jira/issues/{issue_key}")
async def get_issue_endpoint(issue_key: str):
    """Get JIRA issue details via HTTP"""
    stats["requests_count"] += 1
    stats["last_request"] = datetime.now().isoformat()
    
    try:
        result = await get_jira_issue(issue_key)
        
        return {
            "status": "success",
            "issue": {
                "key": result["key"],
                "summary": result["fields"]["summary"],
                "status": result["fields"]["status"]["name"],
                "priority": result["fields"]["priority"]["name"],
                "assignee": result["fields"]["assignee"]["displayName"] if result["fields"]["assignee"] else "Unassigned",
                "created": result["fields"]["created"],
                "updated": result["fields"]["updated"],
                "url": f"{config.base_url}/browse/{result['key']}"
            }
        }
    except Exception as e:
        stats["errors_count"] += 1
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    if not config.is_valid():
        logger.error("❌ Incomplete JIRA configuration!")
        exit(1)
    
    logger.info("🚀 Starting JIRA HTTP Server...")
    logger.info(f"📍 Base URL: {config.base_url}")
    logger.info(f"👤 User: {config.username}")
    logger.info(f"📋 Project: {config.project_key}")
    
    # Run on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
