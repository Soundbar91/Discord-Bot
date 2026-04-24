import aiosqlite

import config


async def init_db():
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT,
                source TEXT NOT NULL DEFAULT 'manual',
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                duration_seconds INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON study_sessions(user_id, started_at)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_todos_user ON todos(user_id, done)"
        )

        # 봇 재시작 시 종료되지 않은 세션을 정리 (duration 0으로 마감).
        # 이유: ended_at IS NULL 상태로 남으면 다음 세션 시작이 차단됨.
        await db.execute("""
            UPDATE study_sessions
            SET ended_at = started_at, duration_seconds = 0
            WHERE ended_at IS NULL
        """)
        await db.commit()
