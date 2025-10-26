"""
ASI One agent management routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
from pathlib import Path
import os

router = APIRouter()

# Agent data model
class Agent(BaseModel):
    id: str
    name: str
    address: str
    description: Optional[str] = ""

class AgentCreate(BaseModel):
    name: str
    address: str
    description: Optional[str] = ""

class ApiKeys(BaseModel):
    asi_one_key: str
    agentverse_key: Optional[str] = ""

def _get_agents_file() -> Path:
    """Get the path to the agents storage file"""
    app_support = Path.home() / "Library" / "Application Support" / "Pointer"
    app_support.mkdir(parents=True, exist_ok=True)
    return app_support / "asi_agents.json"

def _get_keys_file() -> Path:
    """Get the path to the API keys storage file"""
    app_support = Path.home() / "Library" / "Application Support" / "Pointer"
    app_support.mkdir(parents=True, exist_ok=True)
    return app_support / "asi_keys.json"

def _load_agents() -> List[dict]:
    """Load agents from storage"""
    agents_file = _get_agents_file()
    if not agents_file.exists():
        return []
    
    try:
        with open(agents_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading agents: {e}")
        return []

def _save_agents(agents: List[dict]):
    """Save agents to storage"""
    agents_file = _get_agents_file()
    try:
        with open(agents_file, 'w') as f:
            json.dump(agents, f, indent=2)
    except Exception as e:
        print(f"Error saving agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save agents: {str(e)}")

def _load_keys() -> Dict[str, str]:
    """Load API keys from storage"""
    keys_file = _get_keys_file()
    if not keys_file.exists():
        return {}
    
    try:
        with open(keys_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading API keys: {e}")
        return {}

def _save_keys(asi_one_key: str, agentverse_key: str = ""):
    """Save API keys to storage"""
    keys_file = _get_keys_file()
    try:
        with open(keys_file, 'w') as f:
            json.dump({
                "asi_one_key": asi_one_key,
                "agentverse_key": agentverse_key
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save API keys: {str(e)}")

@router.get("/keys")
async def get_keys():
    """Get stored API keys (returns empty strings if not set)"""
    keys = _load_keys()
    return {
        "asi_one_key": keys.get("asi_one_key", ""),
        "agentverse_key": keys.get("agentverse_key", "")
    }

@router.post("/keys")
async def save_keys(api_keys: ApiKeys):
    """Save API keys"""
    _save_keys(api_keys.asi_one_key, api_keys.agentverse_key)
    
    # Also update environment variables for immediate use
    os.environ["ASI_ONE_API_KEY"] = api_keys.asi_one_key
    if api_keys.agentverse_key:
        os.environ["AGENTVERSE_API_KEY"] = api_keys.agentverse_key
    
    return {"success": True}

@router.get("/agents")
async def get_agents():
    """Get all registered ASI agents"""
    agents = _load_agents()
    return {"agents": agents}

@router.post("/agents")
async def add_agent(agent_data: AgentCreate):
    """Add a new ASI agent"""
    agents = _load_agents()
    
    # Check if address already exists
    if any(a["address"] == agent_data.address for a in agents):
        raise HTTPException(status_code=400, detail="Agent with this address already exists")
    
    # Create new agent with unique ID
    new_agent = {
        "id": str(uuid.uuid4()),
        "name": agent_data.name,
        "address": agent_data.address,
        "description": agent_data.description or "",
    }
    
    agents.append(new_agent)
    _save_agents(agents)
    
    return {"success": True, "agent": new_agent}

@router.delete("/agents/{agent_id}")
async def remove_agent(agent_id: str):
    """Remove an ASI agent"""
    agents = _load_agents()
    
    # Find and remove the agent
    original_length = len(agents)
    agents = [a for a in agents if a["id"] != agent_id]
    
    if len(agents) == original_length:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    _save_agents(agents)
    
    return {"success": True}

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific ASI agent"""
    agents = _load_agents()
    
    agent = next((a for a in agents if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


async def process_asi_query(query: str, context: Dict[str, Any]) -> str:
    """
    Process a query using ASI One with automatic Agentverse agent discovery
    
    ASI One's agentic models automatically discover and coordinate with agents
    from the Agentverse marketplace. No separate Agentverse API key needed.
    
    Optional: Users can bookmark favorite agents to help ASI One prioritize them.
    
    Args:
        query: The user's query (without @asi prefix)
        context: Context dict with selected_text, etc.
    
    Returns:
        Response string from ASI One
    """
    try:
        import httpx
    except ImportError:
        raise HTTPException(status_code=500, detail="httpx not installed. Install with: pip install httpx")
    
    # Get API key from storage or environment
    stored_keys = _load_keys()
    asi_api_key = os.environ.get("ASI_ONE_API_KEY") or stored_keys.get("asi_one_key", "")
    
    print(f"[ASI DEBUG] Stored keys: {stored_keys}")
    print(f"[ASI DEBUG] API key loaded: {'Yes' if asi_api_key else 'No'}")
    print(f"[ASI DEBUG] API key length: {len(asi_api_key) if asi_api_key else 0}")
    
    if not asi_api_key:
        return "ASI One API key not configured. Please add your API key in the ASI One settings panel."
    
    # Generate session ID for this request
    session_id = str(uuid.uuid4())
    print(f"[ASI DEBUG] Generated session ID: {session_id}")
    
    # Load agents (optional - ASI One works without them)
    agents = _load_agents()
    
    # Prepare context for ASI One
    full_context = query
    if context.get("selected_text"):
        full_context = f"Selected text: {context['selected_text']}\n\nQuery: {query}"
    
    # Build system prompt with or without favorite agents
    if agents:
        agent_descriptions = []
        for agent in agents:
            desc = f"- {agent['name']}"
            if agent.get('description'):
                desc += f": {agent['description']}"
            desc += f" (Address: {agent['address']})"
            agent_descriptions.append(desc)
        
        agents_info = "\n".join(agent_descriptions)
        system_content = f"""You are an AI assistant powered by ASI One with automatic access to Fetch.ai Agentverse agents.

You can automatically discover and coordinate with agents from the Agentverse marketplace to help answer queries.

The user has bookmarked these favorite agents - prioritize them when relevant:
{agents_info}

When appropriate, leverage the Agentverse ecosystem to find and use the best agents for the task."""
    else:
        system_content = """You are an AI assistant powered by ASI One with automatic access to Fetch.ai Agentverse agents.

You can automatically discover and coordinate with agents from the Agentverse marketplace to help answer queries.

When appropriate, leverage the Agentverse ecosystem to find and use the best agents for the task."""
    
    # Use ASI One API with agentic model (automatically discovers Agentverse agents)
    try:
        print(f"[ASI DEBUG] Making request to ASI One API...")
        print(f"[ASI DEBUG] API key starts with: {asi_api_key[:20]}...")
        print(f"[ASI DEBUG] Session ID: {session_id}")
        print(f"[ASI DEBUG] Query: {full_context[:100]}...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for agent discovery
            print(f"[ASI DEBUG] Sending POST request...")
            response = await client.post(
                "https://api.asi1.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {asi_api_key}",
                    "Content-Type": "application/json",
                    "x-session-id": session_id,  # Required for ASI One agentic model
                },
                json={
                    "model": "asi1-agentic",  # Automatically discovers and calls Agentverse agents
                    "messages": [
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": full_context
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7,
                }
            )
            
            print(f"[ASI DEBUG] Response received!")
            print(f"[ASI DEBUG] Response status: {response.status_code}")
            print(f"[ASI DEBUG] Response body: {response.text[:500]}")
            
            if response.status_code != 200:
                error_text = response.text
                print(f"[ASI DEBUG] Error response: {error_text}")
                return f"ASI One API error ({response.status_code}): {error_text}"
            
            result = response.json()
            print(f"[ASI DEBUG] Parsed JSON response")
            print(f"[ASI DEBUG] Response keys: {result.keys()}")
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"[ASI DEBUG] Returning content: {content[:200]}...")
                
                # ASI One sometimes includes <think> tags for reasoning - strip them for cleaner output
                import re
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                content = content.strip()
                
                return content
            else:
                print(f"[ASI DEBUG] No choices in response")
                return "No response from ASI One"
                
    except httpx.TimeoutException:
        return "Request to ASI One timed out. Please try again."
    except Exception as e:
        return f"Error calling ASI One: {str(e)}"
