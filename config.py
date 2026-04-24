import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
STUDY_VOICE_CHANNEL_ID = int(os.getenv("STUDY_VOICE_CHANNEL_ID", "0"))
STREAK_MIN_MINUTES = int(os.getenv("STREAK_MIN_MINUTES", "30"))
STREAK_MIN_SECONDS = STREAK_MIN_MINUTES * 60
DB_PATH = "study_bot.db"

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN 환경변수가 설정되지 않았습니다 (.env 파일 확인)")
if GUILD_ID == 0:
    raise RuntimeError("GUILD_ID 환경변수가 설정되지 않았습니다 (.env 파일 확인)")
if STUDY_VOICE_CHANNEL_ID == 0:
    raise RuntimeError("STUDY_VOICE_CHANNEL_ID 환경변수가 설정되지 않았습니다 (.env 파일 확인)")
