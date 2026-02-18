from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_token_claims, llm_usage_limiter
from app.db.session import get_db
from app.models import AIConversation, AIMessage, LLMUsageDaily, User
from app.schemas.schemas import (
    CopilotConversationDetailResponse,
    CopilotConversationListItem,
    CopilotConversationMessageRequest,
    CopilotConversationMessageResponse,
)
from app.services.audit_service import audit_service
from app.services.metabolic_copilot_service import metabolic_copilot_service

copilot_router = APIRouter(prefix="/copilot", tags=["copilot"], dependencies=[Depends(get_current_token_claims)])


def _increment_llm_daily_usage(db: Session, user_id: int, route: str, ip_address: str) -> bool:
    usage = db.scalar(select(LLMUsageDaily).where(LLMUsageDaily.user_id == user_id, LLMUsageDaily.usage_date == date.today()))
    if not usage:
        usage = LLMUsageDaily(user_id=user_id, usage_date=date.today(), request_count=0)
        db.add(usage)
        db.flush()

    if usage.request_count >= settings.llm_requests_per_day:
        audit_service.log_event(
            db,
            event_type="excess_llm_calls",
            severity="warning",
            user_id=user_id,
            ip_address=ip_address,
            route=route,
            details={"daily_count": usage.request_count, "daily_limit": settings.llm_requests_per_day},
        )
        return False

    usage.request_count += 1
    usage.updated_at = datetime.utcnow()
    return True


@copilot_router.post("/message", response_model=CopilotConversationMessageResponse)
async def copilot_message(
    payload: CopilotConversationMessageRequest,
    request: Request,
    claims: dict = Depends(get_current_token_claims),
    db: Session = Depends(get_db),
):
    user_id = int(claims["sub"])
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    client_ip = request.client.host if request.client else "unknown"
    if not llm_usage_limiter.is_allowed(f"copilot:{user_id}"):
        raise HTTPException(status_code=429, detail="Hourly LLM usage limit reached")
    if not _increment_llm_daily_usage(db, user_id, "/copilot/message", client_ip):
        db.commit()
        raise HTTPException(status_code=429, detail="Daily LLM usage limit reached")

    try:
        result = await metabolic_copilot_service.process_message(
            db=db,
            user_id=user_id,
            user_message=payload.message,
            conversation_id=payload.conversation_id,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    return CopilotConversationMessageResponse(**result)


@copilot_router.get("/conversations", response_model=list[CopilotConversationListItem])
def list_conversations(
    claims: dict = Depends(get_current_token_claims),
    db: Session = Depends(get_db),
):
    user_id = int(claims["sub"])
    rows = db.scalars(
        select(AIConversation).where(AIConversation.user_id == user_id).order_by(AIConversation.updated_at.desc(), AIConversation.id.desc())
    ).all()
    return [
        CopilotConversationListItem(
            id=row.id,
            title=row.title,
            summary=row.summary,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@copilot_router.get("/conversations/{conversation_id}", response_model=CopilotConversationDetailResponse)
def get_conversation(
    conversation_id: int,
    claims: dict = Depends(get_current_token_claims),
    db: Session = Depends(get_db),
):
    user_id = int(claims["sub"])
    conversation = db.scalar(
        select(AIConversation).where(AIConversation.id == conversation_id, AIConversation.user_id == user_id)
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.scalars(
        select(AIMessage).where(AIMessage.conversation_id == conversation.id).order_by(AIMessage.created_at.asc(), AIMessage.id.asc())
    ).all()
    return CopilotConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[{"role": item.role.value, "content": item.content, "created_at": item.created_at} for item in messages],
    )
