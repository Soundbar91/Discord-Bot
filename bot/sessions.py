"""공부 세션 공용 헬퍼. StudySession cog 과 VoiceTracker cog 이 공유합니다.

단일 소스(SQLite)를 통해 active 세션 상태를 관리하므로,
음성 채널 입장과 /공부시작 명령이 중복으로 세션을 만드는 일이 없습니다.
"""
from __future__ import annotations

from datetime import datetime

import aiosqlite

import config


async def get_active_session(user_id: int):
    """현재 진행 중인 세션을 반환. 없으면 None.

    Returns:
        (session_id, started_at_str, subject, source) or None
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute(
            """
            SELECT id, started_at, subject, source
            FROM study_sessions
            WHERE user_id = ? AND ended_at IS NULL
            ORDER BY started_at DESC LIMIT 1
            """,
            (user_id,),
        ) as cursor:
            return await cursor.fetchone()


async def start_session(user_id: int, subject: str, source: str) -> int | None:
    """세션을 시작. 이미 active 세션이 있으면 None 반환."""
    if await get_active_session(user_id):
        return None

    now = datetime.utcnow()
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO study_sessions (user_id, subject, source, started_at) VALUES (?, ?, ?, ?)",
            (user_id, subject, source, now),
        )
        await db.commit()
        return cursor.lastrowid


async def end_session(user_id: int, only_source: str | None = None):
    """active 세션을 종료하고 (subject, duration_seconds, source) 반환. 없으면 None.

    only_source 가 지정되면 해당 source 의 세션만 종료. 다른 source 면 None 반환.
    (음성 트래커가 수동 세션을 실수로 종료하는 걸 방지)
    """
    active = await get_active_session(user_id)
    if not active:
        return None

    session_id, started_at_str, subject, source = active
    if only_source is not None and source != only_source:
        return None

    started_at = datetime.fromisoformat(started_at_str)
    now = datetime.utcnow()
    duration = int((now - started_at).total_seconds())

    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE study_sessions SET ended_at = ?, duration_seconds = ? WHERE id = ?",
            (now, duration, session_id),
        )
        await db.commit()

    return subject, duration, source
