from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

import config

KST = timezone(timedelta(hours=9))


def calculate_xp(duration_seconds: int) -> int:
    """공부 시간(초)을 XP로 환산.

    기본 구현: 5분 미만은 0 XP, 그 외에는 1분당 1 XP.

    TODO(학습): 본인의 보상 철학에 맞게 바꿔보세요.
      - 장시간 보너스: 2시간 이상 세션은 1.5배 (몰입 장려)
      - 상한선: 하루 6시간 이상 공부는 추가 XP 없음 (번아웃 방지)
      - 과목 가중치: 어려운 과목은 1.2배 등
    """
    if duration_seconds < 300:
        return 0
    return duration_seconds // 60


async def calculate_streak(user_id: int) -> tuple[int, int]:
    """(현재 스트릭, 최장 스트릭)을 일 단위로 반환.

    규칙:
      - "하루" = KST 기준 (UTC+9)
      - 해당 일의 공부 시간 합계가 STREAK_MIN_SECONDS 이상이어야 스트릭 인정
      - 현재 스트릭은 가장 최근 인정일이 '오늘' 또는 '어제'(KST) 여야 살아있음
        → 오늘 아직 공부 전이어도 어제까지 이어졌다면 자정까지는 유예
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute(
            """
            SELECT date(started_at, '+9 hours') AS day,
                   SUM(duration_seconds) AS total
            FROM study_sessions
            WHERE user_id = ? AND ended_at IS NOT NULL
            GROUP BY day
            HAVING total >= ?
            ORDER BY day DESC
            """,
            (user_id, config.STREAK_MIN_SECONDS),
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return 0, 0

    qualifying = [date.fromisoformat(day) for day, _ in rows]  # 최신순
    today_kst = datetime.now(KST).date()

    # 현재 스트릭
    current = 0
    most_recent = qualifying[0]
    if most_recent == today_kst or most_recent == today_kst - timedelta(days=1):
        expected = most_recent
        for day in qualifying:
            if day == expected:
                current += 1
                expected -= timedelta(days=1)
            else:
                break

    # 최장 스트릭
    longest = 1
    run = 1
    for i in range(1, len(qualifying)):
        if qualifying[i - 1] - qualifying[i] == timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    return current, longest


class Ranking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="랭킹", description="최근 7일 공부 시간 랭킹")
    async def weekly(self, interaction: discord.Interaction):
        async with aiosqlite.connect(config.DB_PATH) as db:
            async with db.execute(
                """
                SELECT user_id, SUM(duration_seconds) AS total
                FROM study_sessions
                WHERE ended_at IS NOT NULL
                  AND started_at >= datetime('now', '-7 days')
                GROUP BY user_id
                ORDER BY total DESC
                LIMIT 10
                """
            ) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message(
                "이번 주 기록이 없습니다.", ephemeral=True
            )
            return

        lines = ["🏆 **주간 공부 랭킹** (최근 7일)"]
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for rank, (user_id, total) in enumerate(rows, 1):
            member = interaction.guild.get_member(user_id) if interaction.guild else None
            name = member.display_name if member else f"User {user_id}"
            hours = total // 3600
            minutes = (total % 3600) // 60
            prefix = medals.get(rank, f"{rank}.")
            lines.append(f"{prefix} {name} — {hours}시간 {minutes}분")

        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="내기록", description="내 누적 공부 기록을 봅니다")
    async def mine(self, interaction: discord.Interaction):
        async with aiosqlite.connect(config.DB_PATH) as db:
            async with db.execute(
                """
                SELECT COUNT(*), COALESCE(SUM(duration_seconds), 0)
                FROM study_sessions
                WHERE user_id = ? AND ended_at IS NOT NULL
                """,
                (interaction.user.id,),
            ) as cursor:
                count, total = await cursor.fetchone()

        hours = total // 3600
        minutes = (total % 3600) // 60
        current_streak, longest_streak = await calculate_streak(interaction.user.id)
        xp = calculate_xp(total) if total > 0 else 0

        await interaction.response.send_message(
            f"📊 **{interaction.user.display_name}** 의 공부 기록\n"
            f"• 총 세션: {count}회\n"
            f"• 누적 시간: {hours}시간 {minutes}분\n"
            f"• 🔥 현재 스트릭: {current_streak}일 (최장 {longest_streak}일)\n"
            f"• 누적 XP: {xp}",
            ephemeral=True,
        )

    @app_commands.command(name="스트릭", description="연속 공부 일수를 봅니다")
    async def streak(self, interaction: discord.Interaction):
        current, longest = await calculate_streak(interaction.user.id)
        min_minutes = config.STREAK_MIN_MINUTES

        if current == 0:
            msg = (
                f"🔥 현재 스트릭: **0일**\n"
                f"하루 **{min_minutes}분 이상** 공부하면 스트릭이 시작됩니다. 오늘부터 가보자구요!"
            )
        else:
            msg = (
                f"🔥 현재 스트릭: **{current}일 연속**\n"
                f"최장 기록: {longest}일\n"
                f"_(하루 {min_minutes}분 이상 공부 기준, KST)_"
            )
        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Ranking(bot))
