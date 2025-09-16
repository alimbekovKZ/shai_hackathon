#!/usr/bin/env python3
"""
JIRA MCP HTTP Server - SSE Implementation for Claude Desktop
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime
from typing import Dict, Any

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-mcp-sse")

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
app = FastAPI(title="JIRA MCP SSE Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def format_sse_message(data: dict) -> str:
    """Format message as Server-Sent Event"""
    return f"data: {json.dumps(data)}\n\n"

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
        <title>JIRA MCP SSE Server</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .status {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .status.good {{ background: #d4edda; color: #155724; }}
            .status.bad {{ background: #f8d7da; color: #721c24; }}
            pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 JIRA MCP SSE Server</h1>
            
            <div class="status {'good' if jira_status.startswith('✅') else 'bad'}">
                <strong>JIRA Connection:</strong> {jira_status}<br>
                <strong>User:</strong> {jira_user}<br>
                <strong>Project:</strong> {config.project_key}
            </div>
            
            <h2>Claude Desktop Configuration</h2>
            <p><strong>Method 1:</strong> stdio (рекомендуется)</p>
            <pre>{{
  "mcpServers": {{
    "jira": {{
      "command": "python",
      "args": ["/home/shaijira/jira_mcp_compatible.py"]
    }}
  }}
}}</pre>
            
            <p><strong>Method 2:</strong> HTTP SSE (исправлено)</p>
            <pre>{{
  "mcpServers": {{
    "jira": {{
      "url": "http://134.209.235.31:8000/mcp",
      "headers": {{}},
      "timeout": 50
    }}
  }}
}}</pre>
            
            <h2>Available Endpoints</h2>
            <ul>
                <li><code>GET /</code> - Status page</li>
                <li><code>GET /mcp</code> - MCP SSE endpoint</li>
                <li><code>POST /mcp</code> - MCP JSON-RPC via SSE</li>
                <li><code>GET /health</code> - Health check</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html

async def handle_mcp_message(message: dict) -> dict:
    """Handle MCP JSON-RPC message"""
    
    method = message.get("method", "")
    request_id = message.get("id", 1)
    params = message.get("params", {})
    
    logger.info(f"MCP Request: {method}")
    
    # Handle different methods
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "jira-mcp-sse",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "create_jira_issue",
                        "description": "Create a new JIRA issue",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "summary": {"type": "string", "description": "Issue title"},
                                "description": {"type": "string", "description": "Issue description"},
                                "issue_type": {"type": "string", "description": "Issue type", "default": "Task"}
                            },
                            "required": ["summary", "description"]
                        }
                    },
                    {
                        "name": "get_jira_issue",
                        "description": "Get JIRA issue details",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "issue_key": {"type": "string", "description": "JIRA issue key"}
                            },
                            "required": ["issue_key"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name == "create_jira_issue":
            result = await create_jira_issue(
                summary=arguments["summary"],
                description=arguments["description"],
                issue_type=arguments.get("issue_type", "Task")
            )
            content = f"✅ Created JIRA issue: {result['key']}\n🔗 URL: {config.base_url}/browse/{result['key']}"
            
        elif name == "get_jira_issue":
            result = await get_jira_issue(arguments["issue_key"])
            issue_info = {
                "key": result["key"],
                "summary": result["fields"]["summary"],
                "status": result["fields"]["status"]["name"],
                "url": f"{config.base_url}/browse/{result['key']}"
            }
            content = f"📋 Issue Details:\n{json.dumps(issue_info, indent=2)}"
            
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {name}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": content}]
            }
        }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

async def mcp_sse_stream():
    """Generator for MCP Server-Sent Events stream"""
    # Send initial capabilities
    yield format_sse_message({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False}
            },
            "serverInfo": {
                "name": "jira-mcp-sse",
                "version": "1.0.0"
            }
        }
    })
    
    # Keep connection alive
    while True:
        try:
            await asyncio.sleep(30)  # Send keep-alive every 30 seconds
            yield "data: {\"type\": \"ping\"}\n\n"
        except Exception as e:
            logger.error(f"SSE Stream error: {e}")
            break

@app.get("/mcp")
async def mcp_sse_endpoint():
    """MCP Server-Sent Events endpoint"""
    
    return StreamingResponse(
        mcp_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

@app.post("/mcp")
async def mcp_post_endpoint(request: Request):
    """MCP JSON-RPC endpoint via POST (for direct testing)"""
    
    try:
        # Parse request
        body = await request.body()
        if not body:
            # Empty POST - return capabilities
            response_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "jira-mcp-sse",
                        "version": "1.0.0"
                    }
                }
            }
        else:
            request_data = json.loads(body.decode('utf-8'))
            response_data = await handle_mcp_message(request_data)
        
        # Return as SSE format for Claude Desktop compatibility
        if request.headers.get("accept", "").find("text/event-stream") >= 0:
            return StreamingResponse(
                iter([format_sse_message(response_data)]),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Regular JSON response for testing
            return JSONResponse(response_data)
            
    except Exception as e:
        logger.error(f"MCP Error: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
        
        if request.headers.get("accept", "").find("text/event-stream") >= 0:
            return StreamingResponse(
                iter([format_sse_message(error_response)]),
                media_type="text/event-stream"
            )
        else:
            return JSONResponse(error_response)

@app.get("/health")
async def health_check():
    """Health check"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config_valid": config.is_valid()
    })

if __name__ == "__main__":
    if not config.is_valid():
        logger.error("❌ Incomplete JIRA configuration!")
        exit(1)
    
    logger.info("🚀 Starting JIRA MCP SSE Server...")
    logger.info(f"📍 JIRA URL: {config.base_url}")
    logger.info(f"📋 Project: {config.project_key}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
