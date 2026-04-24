import discord
from discord.ext import commands

import config
from bot.sessions import end_session, get_active_session, start_session


class VoiceTracker(commands.Cog):
    """공부방 음성 채널 입·퇴장에 맞춰 세션을 자동으로 시작/종료합니다."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return

        target = config.STUDY_VOICE_CHANNEL_ID
        was_in = before.channel is not None and before.channel.id == target
        now_in = after.channel is not None and after.channel.id == target

        if not was_in and now_in:
            # 공부방 입장
            active = await get_active_session(member.id)
            if active is not None:
                # 이미 수동 세션 중이면 중복 시작 안 함 (그대로 두기)
                return
            await start_session(member.id, subject="음성공부방", source="voice")

        elif was_in and not now_in:
            # 공부방 퇴장 — voice 로 시작된 세션만 종료
            await end_session(member.id, only_source="voice")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceTracker(bot))
