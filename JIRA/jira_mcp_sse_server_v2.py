#!/usr/bin/env python3
"""
JIRA MCP Server (HTTP + SSE + WebSocket)
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-mcp")

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
app = FastAPI(title="JIRA MCP Server", version="1.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ JIRA API ------------------

async def create_jira_issue(summary: str, description: str, issue_type: str = "Task") -> dict:
    """Create a JIRA issue (uses ADF for description)"""

    issue_data = {
        "fields": {
            "project": {"key": config.project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
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

# ------------------ MCP HANDLERS ------------------

async def handle_mcp_message(message: dict) -> dict:
    method = message.get("method", "")
    request_id = message.get("id", 1)
    params = message.get("params", {})

    logger.info(f"MCP Request: method={method}, id={request_id}")

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "jira-mcp-sse", "version": "1.1.0"}
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
                            "description": "Создать новую задачу в JIRA",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "summary": {"type": "string", "description": "Название задачи"},
                                    "description": {"type": "string", "description": "Описание задачи"},
                                    "issue_type": {"type": "string", "description": "Тип задачи", "default": "Task"}
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
                                    "issue_key": {"type": "string", "description": "Ключ задачи JIRA"}
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
                content = f"✅ Создана задача JIRA: {result['key']}\n🔗 URL: {config.base_url}/browse/{result['key']}"

            elif name == "get_jira_issue":
                result = await get_jira_issue(arguments["issue_key"])
                issue_info = {
                    "key": result["key"],
                    "summary": result["fields"]["summary"],
                    "status": result["fields"]["status"]["name"],
                    "url": f"{config.base_url}/browse/{result['key']}"
                }
                content = f"📋 Информация о задаче:\n{json.dumps(issue_info, indent=2, ensure_ascii=False)}"

            else:
                return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Неизвестный инструмент: {name}"}}

            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": content}]}}

        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Метод не найден: {method}"}}

    except Exception as e:
        logger.error(f"Error handling {method}: {e}")
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": f"Внутренняя ошибка: {str(e)}"}}

# ------------------ ROUTES ------------------

@app.get("/")
async def root():
    return {"status": "ok", "jira_configured": config.is_valid()}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config_valid": config.is_valid(),
        "endpoints": {"websocket": "ws://localhost:8000/mcp", "http": "http://localhost:8000/mcp"}
    }

@app.post("/mcp")
async def mcp_post(request: Request):
    body = await request.body()
    try:
        message = json.loads(body.decode("utf-8"))
    except Exception:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
    return await handle_mcp_message(message)

@app.websocket("/mcp")
async def mcp_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            response = await handle_mcp_message(message)
            await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        logger.info("WebSocket closed")

# ------------------ MAIN ------------------

if __name__ == "__main__":
    if not config.is_valid():
        logger.error("❌ Неполная конфигурация JIRA! Проверьте .env (JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN, JIRA_PROJECT_KEY)")
        exit(1)

    logger.info("🚀 Запуск JIRA MCP Server...")
    logger.info(f"📍 JIRA URL: {config.base_url}")
    logger.info(f"📋 Проект: {config.project_key}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
