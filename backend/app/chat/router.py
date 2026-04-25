from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.chat.schemas import ChatRequest, ChatResponse
from app.chat.service import get_rag_response
from app.models import User

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    _: User = Depends(get_current_user),
):
    result = await get_rag_response(body.question)
    return ChatResponse(**result)
