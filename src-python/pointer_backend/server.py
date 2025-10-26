from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai import types
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

# Initialize the runner
runner = InMemoryRunner(agent=root_agent, app_name="pointer_agent")

app = FastAPI(title="Pointer Agent API")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    message: str
    context_parts: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.post("/api/agent", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    """
    Process user message through the Pointer agent and return results.
    
    Args:
        request: AgentRequest containing message, optional context, and session_id
    
    Returns:
        AgentResponse with agent's response and metadata
    """
    try:
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        user_id = "default_user"
        
        # Create or get session
        session = runner.session_service.get_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if not session:
            session = runner.session_service.create_session(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        # Prepare the message content
        parts = [types.Part(text=request.message)]
        
        # Add context parts if provided
        if request.context_parts:
            for ctx_part in request.context_parts:
                ctx_type = ctx_part.get("type")
                if ctx_type == "text":
                    parts.append(types.Part(text=ctx_part.get("content", "")))
                elif ctx_type == "image":
                    # Handle base64 encoded images
                    import base64
                    mime_type = ctx_part.get("mime_type", "image/jpeg")
                    image_data = ctx_part.get("content")
                    if image_data:
                        parts.append(types.Part(
                            inline_data=types.Blob(
                                mime_type=mime_type,
                                data=base64.b64decode(image_data)
                            )
                        ))
        
        new_message = types.Content(role="user", parts=parts)
        
        # Run the agent and collect the response
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            # Collect the text from events
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        
        return AgentResponse(
            response=response_text or "No response generated",
            session_id=session_id,
            metadata={"status": "success"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "pointer"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
