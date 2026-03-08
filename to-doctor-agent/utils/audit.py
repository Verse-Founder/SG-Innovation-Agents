"""
utils/audit.py
审计日志工具
"""
import logging
from db.session import get_session
from db import crud

logger = logging.getLogger(__name__)


async def audit(action: str, actor_id: str, actor_type: str = "system",
                target_id: str = None, details: str = None):
    """记录审计日志"""
    try:
        async with get_session() as session:
            await crud.log_audit(
                session, action=action, actor_id=actor_id,
                actor_type=actor_type, target_id=target_id, details=details,
            )
            logger.info(f"[Audit] {action} by {actor_type}:{actor_id} target={target_id}")
    except Exception as e:
        logger.error(f"[Audit] 写入失败: {e}")
