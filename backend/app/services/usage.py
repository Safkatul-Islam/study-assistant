import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.usage_log import UsageAction, UsageLog


async def log_usage(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: UsageAction,
    tokens_used: int,
    document_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> UsageLog:
    """Create a usage log entry."""
    usage_log = UsageLog(
        user_id=user_id,
        action=action,
        tokens_used=tokens_used,
        document_id=document_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(usage_log)
    await db.flush()
    return usage_log
