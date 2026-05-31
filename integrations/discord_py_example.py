import os
import discord
import requests
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
MODERATION_API_URL = os.getenv("MODERATION_API_URL", "http://localhost:8000/v1/check")
MODERATION_API_KEY = os.getenv("MODERATION_API_KEY", "")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def check_message(text: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if MODERATION_API_KEY:
        headers["X-API-Key"] = MODERATION_API_KEY

    response = requests.post(
        MODERATION_API_URL,
        json={"text": text},
        headers=headers,
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    try:
        result = check_message(message.content)
    except Exception as exc:
        print(f"Moderation API failed: {exc}")
        await bot.process_commands(message)
        return

    if result.get("blocked"):
        try:
            await message.delete()
        except discord.Forbidden:
            pass

        await message.channel.send(
            f"{message.author.mention} 이 서버에서 허용되지 않는 표현이 감지됐어.",
            delete_after=5,
        )
        return

    await bot.process_commands(message)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is required")
    bot.run(DISCORD_TOKEN)
