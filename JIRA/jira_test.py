#!/usr/bin/env python3
"""
JIRA MCP Server - Исправленная версия с поддержкой ADF
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

# ---------------- ADF Support ---------------- #
def text_to_adf(text: str) -> dict:
    """Конвертация текста в Atlassian Document Format"""
    if not text:
        return {
            "type": "doc",
            "version": 1,
            "content": []
        }
    
    # Разбиваем текст на параграфы
    paragraphs = text.split('\n\n')
    content = []
    
    for paragraph in paragraphs:
        if paragraph.strip():
            # Обработка списков
            lines = paragraph.split('\n')
            list_items = []
            regular_text = []
            
            for line in lines:
                line = line.strip()
                if line.startswith(('•', '-', '*', '- ')):
                    # Если у нас есть обычный текст, добавляем его как параграф
                    if regular_text:
                        content.append({
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": '\n'.join(regular_text)
                                }
                            ]
                        })
                        regular_text = []
                    
                    # Добавляем элемент списка
                    item_text = line[1:].strip() if line.startswith(('•', '-', '*')) else line[2:].strip()
                    if item_text:
                        list_items.append({
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": item_text
                                        }
                                    ]
                                }
                            ]
                        })
                else:
                    # Добавляем к обычному тексту
                    if list_items:
                        # Сначала добавляем список
                        content.append({
                            "type": "bulletList",
                            "content": list_items
                        })
                        list_items = []
                    
                    regular_text.append(line)
            
            # Добавляем оставшиеся элементы
            if list_items:
                content.append({
                    "type": "bulletList",
                    "content": list_items
                })
            elif regular_text:
                content.append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": '\n'.join(regular_text)
                        }
                    ]
                })
    
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }

# ---------------- FastAPI App ---------------- #
app = FastAPI(title="JIRA MCP Server", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- JIRA Methods (Updated) ---------------- #
async def create_jira_issue(summary: str, description: str, issue_type: str = "Task") -> dict:
    """Создание JIRA задачи с поддержкой ADF формата"""
    if not config.is_valid():
        raise HTTPException(status_code=500, detail="JIRA configuration not valid")
    
    # Конвертируем описание в ADF формат
    adf_description = text_to_adf(description)
    
    issue_data = {
        "fields": {
            "project": {"key": config.project_key},
            "summary": summary,
            "description": adf_description,  # ADF формат
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
            
            logger.info(f"Creating JIRA issue: {summary}")
            logger.debug(f"Issue data: {json.dumps(issue_data, indent=2)}")
            
            response = await client.post(url, json=issue_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ JIRA issue created: {result.get('key')}")
            return result
            
    except httpx.HTTPStatusError as e:
        error_msg = f"JIRA API Error {e.response.status_code}: {e.response.text}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to create JIRA issue: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

async def get_jira_issue(issue_key: str) -> dict:
    """Получение информации о JIRA задаче"""
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

# ---------------- MCP Handler (Updated) ---------------- #
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
                        "version": "2.1.0"
                    }
                }
            }
            return result

        elif method == "tools/list":
            result = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "create_jira_issue",
                            "description": "Создать новую задачу в JIRA с поддержкой ADF формата",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "summary": {
                                        "type": "string", 
                                        "description": "Название задачи"
                                    },
                                    "description": {
                                        "type": "string", 
                                        "description": "Описание задачи (поддерживает списки с •, -, *)"
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
                
                issue_key = result.get('key')
                issue_url = f"{config.base_url}/browse/{issue_key}" if issue_key else ""
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text", 
                                "text": f"✅ JIRA задача создана успешно!\n\n🔑 Ключ: {issue_key}\n🔗 Ссылка: {issue_url}\n\nЗадача готова для работы!"
                            }
                        ]
                    }
                }
                return response

            elif name == "get_jira_issue":
                result = await get_jira_issue(arguments["issue_key"])
                fields = result.get("fields", {})
                
                info = {
                    "key": result["key"],
                    "summary": fields.get("summary", ""),
                    "status": fields.get("status", {}).get("name", ""),
                    "assignee": fields.get("assignee", {}).get("displayName", "Не назначен") if fields.get("assignee") else "Не назначен",
                    "priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else "Не указан",
                    "url": f"{config.base_url}/browse/{result['key']}"
                }
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text", 
                                "text": f"📋 Информация о задаче {info['key']}:\n\n" +
                                       f"📝 Название: {info['summary']}\n" +
                                       f"📊 Статус: {info['status']}\n" +
                                       f"👤 Исполнитель: {info['assignee']}\n" +
                                       f"⚡ Приоритет: {info['priority']}\n" +
                                       f"🔗 Ссылка: {info['url']}"
                            }
                        ]
                    }
                }
                return response

            else:
                return {
                    "jsonrpc": "2.0", 
                    "id": request_id, 
                    "error": {
                        "code": -32601, 
                        "message": f"Unknown tool: {name}"
                    }
                }

        else:
            return {
                "jsonrpc": "2.0", 
                "id": request_id, 
                "error": {
                    "code": -32601, 
                    "message": f"Unknown method: {method}"
                }
            }
            
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

# ---------------- Endpoints ---------------- #
@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
    <head>
        <title>JIRA MCP Server v2.1</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status { color: #28a745; font-size: 24px; }
            .feature { background: #e7f3ff; padding: 10px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007bff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="status">✅ JIRA MCP Server v2.1 - ADF Support</h1>
            
            <div class="feature">
                <h3>🆕 Новые возможности:</h3>
                <ul>
                    <li>✅ Поддержка Atlassian Document Format (ADF)</li>
                    <li>✅ Автоматическое форматирование списков</li>
                    <li>✅ Улучшенная обработка ошибок</li>
                    <li>✅ Совместимость с JIRA Cloud</li>
                </ul>
            </div>
            
            <h3>Доступные инструменты MCP:</h3>
            <ul>
                <li><strong>create_jira_issue</strong> - Создание задач с ADF поддержкой</li>
                <li><strong>get_jira_issue</strong> - Получение информации о задачах</li>
            </ul>
            
            <h3>Использование с OpenAI:</h3>
            <p><code>https://134.209.235.31/mcp</code></p>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.1.0", 
        "jira_configured": config.is_valid(),
        "features": ["ADF_support", "error_handling", "JIRA_Cloud_compatible"],
        "config": {
            "base_url": config.base_url,
            "username": config.username,
            "project_key": config.project_key,
            "api_token_set": bool(config.api_token)
        }
    }

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

@app.get("/mcp")
async def mcp_sse_get():
    """SSE endpoint for streaming MCP protocol"""
    async def event_generator():
        init_msg = {
            "jsonrpc": "2.0", 
            "method": "notifications/initialized", 
            "params": {}
        }
        yield f"data: {json.dumps(init_msg)}\n\n"

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

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    if not config.is_valid():
        logger.error("❌ Missing JIRA config. Please check .env file with:")
        logger.error("JIRA_BASE_URL=https://your-domain.atlassian.net")
        logger.error("JIRA_USERNAME=your-email@domain.com")
        logger.error("JIRA_API_TOKEN=your-api-token")
        logger.error("JIRA_PROJECT_KEY=YOUR-PROJECT")
        exit(1)

    logger.info("🚀 Starting JIRA MCP Server v2.1 with ADF support...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
