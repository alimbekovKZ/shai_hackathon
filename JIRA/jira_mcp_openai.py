#!/usr/bin/env python3
"""
JIRA MCP Server - Совместимый с OpenAI MCP
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
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ---------------- Logging ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-mcp")

# ---------------- Load ENV ---------------- #
def load_env_file():
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
    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL", "").strip()
        self.username = os.getenv("JIRA_USERNAME", "").strip()
        self.api_token = os.getenv("JIRA_API_TOKEN", "").strip()
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "").strip()

    def is_valid(self) -> bool:
        return bool(self.base_url and self.username and self.api_token and self.project_key)

load_env_file()
config = JIRAConfig()

# ---------------- FastAPI App ---------------- #
app = FastAPI(title="JIRA MCP Server", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- JIRA Methods ---------------- #
async def create_jira_issue(summary: str, description: str, issue_type: str = "Task") -> dict:
    if not config.is_valid():
        raise HTTPException(status_code=500, detail="JIRA configuration not valid")
        
    issue_data = {
        "fields": {
            "project": {"key": config.project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }

    try:
        async with httpx.AsyncClient(
            auth=(config.username, config.api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0
        ) as client:
            url = urljoin(f"{config.base_url.rstrip('/')}/rest/api/3/", "issue")
            response = await client.post(url, json=issue_data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error creating JIRA issue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create JIRA issue: {str(e)}")

async def get_jira_issue(issue_key: str) -> dict:
    if not config.is_valid():
        raise HTTPException(status_code=500, detail="JIRA configuration not valid")
        
    try:
        async with httpx.AsyncClient(
            auth=(config.username, config.api_token),
            headers={"Accept": "application/json"},
            timeout=30.0
        ) as client:
            url = urljoin(f"{config.base_url.rstrip('/')}/rest/api/3/", f"issue/{issue_key}")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting JIRA issue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get JIRA issue: {str(e)}")

# ---------------- MCP Handler ---------------- #
async def handle_mcp_message(message: Dict[str, Any]) -> Dict[str, Any]:
    method = message.get("method", "")
    request_id = message.get("id")
    params = message.get("params", {})
    
    logger.info(f"Handling MCP message: {method} with id: {request_id}")

    try:
        if method == "initialize":
            result = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "jira-mcp",
                        "version": "2.0.0"
                    }
                }
            }
            logger.info(f"Initialize response: {result}")
            return result

        elif method == "tools/list":
            result = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "create_jira_issue",
                            "description": "Создать новую задачу в JIRA",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "summary": {
                                        "type": "string", 
                                        "description": "Название задачи"
                                    },
                                    "description": {
                                        "type": "string", 
                                        "description": "Описание задачи"
                                    },
                                    "issue_type": {
                                        "type": "string", 
                                        "description": "Тип задачи (Task, Bug, Story)", 
                                        "default": "Task"
                                    }
                                },
                                "required": ["summary", "description"]
                            }
                        },
                        {
                            "name": "get_jira_issue",
                            "description": "Получить информацию о задаче JIRA",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "issue_key": {
                                        "type": "string", 
                                        "description": "Ключ задачи JIRA (например, PROJ-123)"
                                    }
                                },
                                "required": ["issue_key"]
                            }
                        }
                    ]
                }
            }
            logger.info(f"Tools list response: {result}")
            return result

        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            logger.info(f"Calling tool: {name} with arguments: {arguments}")

            if name == "create_jira_issue":
                result = await create_jira_issue(
                    summary=arguments["summary"],
                    description=arguments["description"],
                    issue_type=arguments.get("issue_type", "Task")
                )
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text", 
                                "text": f"✅ Создана задача JIRA: {result['key']}\nURL: {config.base_url}/browse/{result['key']}"
                            }
                        ]
                    }
                }
                logger.info(f"Create issue response: {response}")
                return response

            elif name == "get_jira_issue":
                result = await get_jira_issue(arguments["issue_key"])
                info = {
                    "key": result["key"],
                    "summary": result["fields"]["summary"],
                    "status": result["fields"]["status"]["name"],
                    "assignee": result["fields"]["assignee"]["displayName"] if result["fields"].get("assignee") else "Не назначен",
                    "url": f"{config.base_url}/browse/{result['key']}"
                }
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text", 
                                "text": json.dumps(info, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
                logger.info(f"Get issue response: {response}")
                return response

            else:
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": request_id, 
                    "error": {
                        "code": -32601, 
                        "message": f"Unknown tool: {name}"
                    }
                }
                logger.error(f"Unknown tool error: {error_response}")
                return error_response

        else:
            error_response = {
                "jsonrpc": "2.0", 
                "id": request_id, 
                "error": {
                    "code": -32601, 
                    "message": f"Unknown method: {method}"
                }
            }
            logger.error(f"Unknown method error: {error_response}")
            return error_response
            
    except Exception as e:
        logger.error(f"Error handling MCP message: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": f"Internal server error: {str(e)}"
            }
        }

# ---------------- SSE Endpoint (для совместимости) ---------------- #
@app.get("/mcp")
async def mcp_sse_get():
    """SSE endpoint for streaming MCP protocol (если нужен)"""
    async def event_generator():
        # Отправляем инициализационное сообщение
        init_msg = {
            "jsonrpc": "2.0", 
            "method": "notifications/initialized", 
            "params": {}
        }
        yield f"data: {json.dumps(init_msg)}\n\n"

        # Периодические ping сообщения
        while True:
            await asyncio.sleep(30)
            ping = {
                "jsonrpc": "2.0", 
                "method": "notifications/ping", 
                "params": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            yield f"data: {json.dumps(ping)}\n\n"

    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ---------------- POST Endpoint для MCP ---------------- #
@app.post("/mcp")
async def mcp_post(request: Request):
    """Основной MCP endpoint для обработки JSON-RPC запросов"""
    try:
        body = await request.json()
        logger.info(f"Received MCP request: {body}")
        
        response = await handle_mcp_message(body)
        logger.info(f"Sending MCP response: {response}")
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        }
        return JSONResponse(content=error_response, status_code=400)

# ---------------- Status + Health ---------------- #
@app.get("/")
async def root():
    return HTMLResponse("""
    <h1>✅ JIRA MCP Server is running</h1>
    <p>Endpoints:</p>
    <ul>
        <li><code>GET /health</code> - Health check</li>
        <li><code>POST /mcp</code> - MCP JSON-RPC endpoint</li>
        <li><code>GET /mcp</code> - MCP SSE endpoint</li>
    </ul>
    """)

@app.get("/health")
async def health():
    return {
        "status": "ok", 
        "jira_configured": config.is_valid(),
        "config": {
            "base_url": config.base_url,
            "username": config.username,
            "project_key": config.project_key,
            "api_token_set": bool(config.api_token)
        }
    }

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    if not config.is_valid():
        logger.error("❌ Missing JIRA config. Please check .env file with:")
        logger.error("JIRA_BASE_URL=https://your-domain.atlassian.net")
        logger.error("JIRA_USERNAME=your-email@domain.com")
        logger.error("JIRA_API_TOKEN=your-api-token")
        logger.error("JIRA_PROJECT_KEY=YOUR-PROJECT")
        exit(1)

    logger.info("🚀 Starting JIRA MCP Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
