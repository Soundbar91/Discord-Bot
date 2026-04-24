import discord
from discord import app_commands
from discord.ext import commands

from bot.sessions import end_session, start_session


class StudySession(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="공부시작", description="공부 세션을 시작합니다")
    @app_commands.describe(과목="공부할 과목 (예: 알고리즘, 영어)")
    async def start(self, interaction: discord.Interaction, 과목: str = "기타"):
        session_id = await start_session(interaction.user.id, 과목, source="manual")
        if session_id is None:
            await interaction.response.send_message(
                "⚠️ 이미 진행 중인 세션이 있습니다. `/공부종료` 먼저 해주세요.\n"
                "(음성 채널 입장으로 자동 시작된 세션일 수 있습니다)",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(f"📚 **{과목}** 공부 시작! 화이팅 💪")

    @app_commands.command(name="공부종료", description="진행 중인 공부 세션을 종료합니다")
    async def end(self, interaction: discord.Interaction):
        result = await end_session(interaction.user.id)
        if result is None:
            await interaction.response.send_message(
                "진행 중인 세션이 없습니다.", ephemeral=True
            )
            return

        subject, duration, source = result
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        source_label = "🎤 음성" if source == "voice" else "📝 수동"
        await interaction.response.send_message(
            f"✅ {source_label} — **{subject}** {hours}시간 {minutes}분 완료! 수고했어요 🎉"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(StudySession(bot))
