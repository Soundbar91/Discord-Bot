import asyncio
import discord
from discord.ext import commands

import config
from bot.database import init_db

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "bot.cogs.study_session",
    "bot.cogs.voice_tracker",
    "bot.cogs.todo",
    "bot.cogs.ranking",
]


@bot.event
async def on_ready():
    print(f"[ready] {bot.user} 온라인")
    guild = discord.Object(id=config.GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    print(f"[ready] 슬래시 커맨드 {len(synced)}개 동기화 완료")


async def main():
    await init_db()
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
