import os
import httpx
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..database import get_db
from .. import models
from ..schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut

router = APIRouter(prefix="/ai", tags=["ai"])

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

async def _ollama_chat(messages: list[dict]) -> str:
    """
    Call Ollama /api/chat. See https://github.com/ollama/ollama
    messages: list like [{'role':'user','content':'Hi'}, {'role':'assistant','content':'...'}]
    returns: assistant reply text
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            # Ollama returns: { message: { role: 'assistant', content: '...' }, ... }
            return data["message"]["content"]
    except httpx.HTTPError as e:
        # Surface a clean message if Ollama isn't running or the model is missing
        raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db)):
    # 1) find or create conversation
    convo: models.Conversation | None = None
    if body.conversation_id:
        convo = db.get(models.Conversation, body.conversation_id)
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # create a new conversation (title = first user message truncated)
        title = body.message.strip()[:80]
        convo = models.Conversation(title=title)
        db.add(convo)
        db.commit()
        db.refresh(convo)

    # 2) save the user message
    user_msg = models.Message(conversation_id=convo.id, role="user", content=body.message.strip())
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 3) assemble full history for this conversation
    stmt = select(models.Message).where(models.Message.conversation_id == convo.id).order_by(models.Message.created_at.asc())
    history = db.execute(stmt).scalars().all()
    chat_history = [{"role": m.role, "content": m.content} for m in history]

    # 4) call Ollama to get the assistant reply
    reply_text = await _ollama_chat(chat_history)

    # 5) save assistant reply
    bot_msg = models.Message(conversation_id=convo.id, role="assistant", content=reply_text)
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    return {"conversation_id": convo.id, "reply": reply_text}

@router.get("/conversations", response_model=List[ConversationOut])
def list_conversations(db: Session = Depends(get_db)):
    stmt = select(models.Conversation).order_by(models.Conversation.created_at.desc())
    return db.execute(stmt).scalars().all()

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
def list_messages(conversation_id: int, db: Session = Depends(get_db)):
    convo = db.get(models.Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    stmt = (
        select(models.Message)
        .where(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.created_at.asc())
    )
    return db.execute(stmt).scalars().all()
