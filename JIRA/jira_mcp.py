import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# ==== JIRA CONFIG ====
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://dsmlkz.atlassian.net")
JIRA_USER = os.getenv("JIRA_USER", "you@example.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "your_api_token")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SCRUM")

# ==== TOOLS LIST ====
TOOLS = [
    {
        "name": "create_jira_issue",
        "description": "Создать новую задачу в JIRA",
        "inputSchema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Название задачи"},
                "description": {"type": "string", "description": "Описание задачи"},
                "issue_type": {
                    "type": "string",
                    "description": "Тип задачи",
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
                "issue_key": {"type": "string", "description": "Ключ задачи JIRA"}
            },
            "required": ["issue_key"]
        }
    }
]


@app.post("/mcp")
async def mcp_handler(request: Request):
    data = await request.json()
    method = data.get("method")
    req_id = data.get("id", 1)

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    elif method == "tools/call":
        params = data.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "create_jira_issue":
            return await handle_create_issue(req_id, args)

        elif tool_name == "get_jira_issue":
            return await handle_get_issue(req_id, args)

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool {tool_name}"}
            }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method {method}"}
        }


# ==== HANDLERS ====

async def handle_create_issue(req_id, args):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    auth = (JIRA_USER, JIRA_API_TOKEN)

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": args.get("summary"),
            "description": args.get("description"),
            "issuetype": {"name": args.get("issue_type", "Task")}
        }
    }

    resp = requests.post(url, json=payload, auth=auth, headers={"Content-Type": "application/json"})

    if resp.status_code == 201:
        issue_key = resp.json().get("key")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ Создана задача JIRA: {issue_key}\n🔗 URL: {JIRA_BASE_URL}/browse/{issue_key}"
                    }
                ]
            }
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32603,
                "message": f"Ошибка при создании задачи: {resp.status_code} {resp.text}"
            }
        }


async def handle_get_issue(req_id, args):
    issue_key = args.get("issue_key")
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    auth = (JIRA_USER, JIRA_API_TOKEN)

    resp = requests.get(url, auth=auth, headers={"Accept": "application/json"})

    if resp.status_code == 200:
        issue = resp.json()
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": f"📌 Задача {issue_key}: {issue['fields']['summary']}"}
                ]
            }
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32603,
                "message": f"Ошибка при получении задачи: {resp.status_code} {resp.text}"
            }
        }
