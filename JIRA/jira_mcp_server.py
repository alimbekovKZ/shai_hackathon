#!/usr/bin/env python3
"""
JIRA MCP Server - Совместимая версия для MCP 1.14.0
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from urllib.parse import urljoin

import httpx

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

async def create_jira_issue(config: JIRAConfig, summary: str, description: str, issue_type: str = "Task") -> dict:
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

async def get_jira_issue(config: JIRAConfig, issue_key: str) -> dict:
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

def main():
    """Main entry point"""
    
    # Load configuration
    load_env_file()
    config = JIRAConfig()
    
    if not config.is_valid():
        logger.error("❌ Incomplete JIRA configuration!")
        return
    
    logger.info("✅ JIRA configuration loaded")
    
    # Test connection
    async def test_connection():
        try:
            async with httpx.AsyncClient(
                auth=(config.username, config.api_token),
                timeout=10.0
            ) as client:
                url = f"{config.base_url}/rest/api/3/myself"
                response = await client.get(url)
                response.raise_for_status()
                user_info = response.json()
                logger.info(f"✅ Connected to JIRA as: {user_info.get('displayName', config.username)}")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to JIRA: {e}")
            return False
    
    # Test connection first
    if not asyncio.run(test_connection()):
        return
    
    # Try different MCP server approaches
    
    # Approach 1: Try with modern MCP
    try:
        from mcp.server import Server
        from mcp.types import Tool, TextContent
        from mcp.server.stdio import stdio_server
        from mcp.server.models import InitializationOptions
        
        logger.info("Using MCP Server with proper initialization")
        
        server = Server("jira-mcp")
        
        @server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="create_jira_issue",
                    description="Create a new JIRA issue",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string", "description": "Issue title"},
                            "description": {"type": "string", "description": "Issue description"},
                            "issue_type": {"type": "string", "description": "Issue type", "default": "Task"}
                        },
                        "required": ["summary", "description"]
                    }
                ),
                Tool(
                    name="get_jira_issue",
                    description="Get JIRA issue details",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "issue_key": {"type": "string", "description": "JIRA issue key"}
                        },
                        "required": ["issue_key"]
                    }
                )
            ]
        
        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            try:
                if name == "create_jira_issue":
                    result = await create_jira_issue(
                        config,
                        summary=arguments["summary"],
                        description=arguments["description"],
                        issue_type=arguments.get("issue_type", "Task")
                    )
                    text = f"✅ Created: {result['key']}\n🔗 {config.base_url}/browse/{result['key']}"
                    
                elif name == "get_jira_issue":
                    result = await get_jira_issue(config, arguments["issue_key"])
                    issue_info = {
                        "key": result["key"],
                        "summary": result["fields"]["summary"],
                        "status": result["fields"]["status"]["name"],
                        "url": f"{config.base_url}/browse/{result['key']}"
                    }
                    text = f"📋 Issue Details:\n{json.dumps(issue_info, indent=2)}"
                    
                else:
                    text = f"❌ Unknown tool: {name}"
                
                return [TextContent(type="text", text=text)]
                
            except Exception as e:
                logger.error(f"Error: {e}")
                return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
        
        async def run_server():
            logger.info("🚀 Starting MCP server...")
            
            try:
                # Try with full initialization
                async with stdio_server() as (read_stream, write_stream):
                    await server.run(
                        read_stream,
                        write_stream,
                        InitializationOptions(
                            server_name="jira-mcp",
                            server_version="1.0.0",
                            capabilities=server.get_capabilities(
                                notification_options=server.create_notification_options(),
                                experimental_capabilities={}
                            )
                        )
                    )
            except Exception as e1:
                logger.warning(f"Full initialization failed: {e1}")
                
                try:
                    # Try with minimal initialization
                    async with stdio_server() as (read_stream, write_stream):
                        await server.run(read_stream, write_stream)
                except Exception as e2:
                    logger.error(f"Minimal initialization also failed: {e2}")
                    raise e2
        
        asyncio.run(run_server())
        
    except ImportError as e:
        logger.error(f"Failed to import MCP: {e}")
    except Exception as e:
        logger.error(f"MCP server failed: {e}")
        
        # Approach 2: Manual stdio handling
        logger.info("Falling back to manual stdio handling...")
        
        import sys
        
        async def manual_stdio():
            logger.info("🚀 Starting manual stdio server...")
            
            while True:
                try:
                    # Read from stdin
                    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break
                    
                    try:
                        request = json.loads(line.strip())
                        response = await handle_manual_request(request, config)
                        print(json.dumps(response), flush=True)
                    except json.JSONDecodeError:
                        continue
                        
                except Exception as e:
                    logger.error(f"Manual stdio error: {e}")
                    break
        
        asyncio.run(manual_stdio())

async def handle_manual_request(request: dict, config: JIRAConfig) -> dict:
    """Handle MCP request manually"""
    method = request.get("method", "")
    
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "create_jira_issue",
                        "description": "Create a new JIRA issue",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "summary": {"type": "string"},
                                "description": {"type": "string"},
                                "issue_type": {"type": "string", "default": "Task"}
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
                                "issue_key": {"type": "string"}
                            },
                            "required": ["issue_key"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if name == "create_jira_issue":
                result = await create_jira_issue(
                    config,
                    summary=arguments["summary"],
                    description=arguments["description"],
                    issue_type=arguments.get("issue_type", "Task")
                )
                content = f"✅ Created: {result['key']}\n🔗 {config.base_url}/browse/{result['key']}"
                
            elif name == "get_jira_issue":
                result = await get_jira_issue(config, arguments["issue_key"])
                issue_info = {
                    "key": result["key"],
                    "summary": result["fields"]["summary"],
                    "status": result["fields"]["status"]["name"],
                }
                content = f"📋 Issue: {json.dumps(issue_info, indent=2)}"
                
            else:
                content = f"❌ Unknown tool: {name}"
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{"type": "text", "text": content}]
                }
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}]
                }
            }
    
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "error": {"code": -32601, "message": "Method not found"}
    }

if __name__ == "__main__":
    main()
