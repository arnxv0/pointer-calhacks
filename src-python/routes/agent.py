from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import uuid

logger = logging.getLogger("pointer.routes.agent")

router = APIRouter(prefix="/api", tags=["agent"])

# Will be set by main.py
pointer_runner = None


class AgentRequest(BaseModel):
    message: str
    context_parts: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/process-query")
async def process_query(request: dict):
    """Legacy endpoint - converts old format to new /api/agent format."""
    try:
        query = request.get("query", "")
        context = request.get("context", {})
        
        # Convert to Pointer backend format
        agent_request = AgentRequest(
            message=query,
            context_parts=[
                {"type": "text", "content": f"Selected text: {context.get('selected_text', '')}"}
            ] if context.get('selected_text') else None,
            session_id=None
        )
        
        # Forward to Pointer backend
        result = await process_agent_request(agent_request)
        
        return {"success": True, "response": result.response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    """
    Process user message through the Pointer agent and return results.
    
    Args:
        request: AgentRequest containing message, optional context, and session_id
    
    Returns:
        AgentResponse with agent's response and metadata
    """
    if not pointer_runner:
        raise HTTPException(status_code=503, detail="Pointer backend not available")
    
    try:
        from google.genai import types
        
        logger.info("=" * 60)
        logger.info("🚀 POINTER AGENT REQUEST")
        logger.info(f"📝 Message: {request.message}")
        logger.info(f"🔑 Session ID: {request.session_id}")
        logger.info("=" * 60)
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        user_id = "default_user"
        
        # Create or get session
        session = pointer_runner.session_service.get_session(
            app_name=pointer_runner.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if not session:
            session = pointer_runner.session_service.create_session(
                app_name=pointer_runner.app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        # Prepare the message content
        parts = [types.Part(text=request.message)]
        logger.info(f"📝 User message: {request.message}")
        print(f"[DEBUG] User message: {request.message}")
        
        # Add context parts if provided
        if request.context_parts:
            for ctx_part in request.context_parts:
                parts.append(types.Part(text=ctx_part.get("content", "")))
            logger.info(f"📎 Added {len(request.context_parts)} context part(s)")
        else:
            logger.info("📎 No context parts provided")
        
        logger.info(f"📨 Total message parts: {len(parts)}")
        print(f"[DEBUG] Total message parts: {len(parts)}")
        new_message = types.Content(role="user", parts=parts)
        
        # Run the agent and collect the response
        logger.info("🤖 Starting agent execution...")
        print("[DEBUG] Starting agent execution...")
        response_text = ""
        event_count = 0
        
        import time
        start_time = time.time()
        
        async for event in pointer_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            event_count += 1
            elapsed = time.time() - start_time
            logger.info(f"⏱️  Event {event_count} at {elapsed:.2f}s - Type: {type(event).__name__}")
            print(f"[DEBUG] Event {event_count}: {type(event).__name__}")
            
            # Log function calls
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        func_name = part.function_call.name if part.function_call.name else "unknown"
                        print(f"[DEBUG] 🔧 Function call: {func_name}")
                        print(f"[DEBUG] 📋 Arguments: {part.function_call.args}")
                        logger.info(f"🔧 Function call: {func_name}")
                        logger.info(f"📋 Arguments: {part.function_call.args}")
                    elif hasattr(part, 'function_response') and part.function_response:
                        func_name = part.function_response.name if part.function_response.name else "unknown"
                        print(f"[DEBUG] ✅ Function response: {func_name}")
                        print(f"[DEBUG] 📤 Response: {part.function_response.response}")
                        logger.info(f"✅ Function response: {func_name}")
                    elif hasattr(part, 'text') and part.text:
                        response_text += part.text
                        logger.info(f"💬 Agent response chunk: {part.text[:100]}...")
                        print(f"[DEBUG] 💬 Text: {part.text[:200]}...")
        
        total_time = time.time() - start_time
        logger.info(f"✅ Agent execution complete in {total_time:.2f}s. Total events: {event_count}")
        logger.info(f"📤 Final response length: {len(response_text)} characters")
        logger.info(f"📤 Full response: {response_text}")
        print(f"[DEBUG] Full response: {response_text}")

        
        return AgentResponse(
            response=response_text or "No response generated",
            session_id=session_id,
            metadata={"event_count": event_count}
        )
    
    except Exception as e:
        logger.error(f"❌ Error processing agent request: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
