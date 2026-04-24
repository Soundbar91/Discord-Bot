import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

import config


class Todo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="할일추가", description="할 일을 추가합니다")
    @app_commands.describe(내용="추가할 할 일")
    async def add(self, interaction: discord.Interaction, 내용: str):
        async with aiosqlite.connect(config.DB_PATH) as db:
            await db.execute(
                "INSERT INTO todos (user_id, content) VALUES (?, ?)",
                (interaction.user.id, 내용),
            )
            await db.commit()
        await interaction.response.send_message(f"📝 추가됨: {내용}", ephemeral=True)

    @app_commands.command(name="할일목록", description="내 할 일 목록을 봅니다")
    async def list(self, interaction: discord.Interaction):
        async with aiosqlite.connect(config.DB_PATH) as db:
            async with db.execute(
                "SELECT id, content, done FROM todos WHERE user_id = ? ORDER BY done, id",
                (interaction.user.id,),
            ) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message(
                "할 일이 없습니다. 잠깐 쉬어가세요 😌", ephemeral=True
            )
            return

        lines = [
            f"{'✅' if done else '⬜'} `#{todo_id}` {content}"
            for todo_id, content, done in rows
        ]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="할일완료", description="할 일을 완료 처리합니다")
    @app_commands.describe(번호="완료할 할 일 번호 (/할일목록 에서 확인)")
    async def done(self, interaction: discord.Interaction, 번호: int):
        async with aiosqlite.connect(config.DB_PATH) as db:
            cursor = await db.execute(
                "UPDATE todos SET done = 1 WHERE id = ? AND user_id = ?",
                (번호, interaction.user.id),
            )
            await db.commit()
            changed = cursor.rowcount

        if changed == 0:
            await interaction.response.send_message(
                "해당 번호의 할 일을 찾을 수 없습니다.", ephemeral=True
            )
        else:
            await interaction.response.send_message(f"🎉 `#{번호}` 완료!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Todo(bot))
