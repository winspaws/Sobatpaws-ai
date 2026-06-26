"""Phase 1: Send OTP request to Telegram."""
from __future__ import annotations
import asyncio, os, sys, json
sys.path.insert(0, "/app/src")
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.network import ConnectionTcpFull
from pathlib import Path

API_ID = int(os.getenv("TELEGRAM_API_ID", "30079012"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "1097317c20c7b0a43f03bd47ab08f813")
PHONE = os.getenv("TELEGRAM_PHONE", "")
SESSION_DIR = Path("/app/data/telegram")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

async def send_code():
    client = TelegramClient(StringSession(), API_ID, API_HASH, connection=ConnectionTcpFull)
    await client.connect()
    result = await client.send_code_request(PHONE)
    data = {
        "phone": PHONE,
        "phone_code_hash": result.phone_code_hash,
        "timeout": result.timeout,
    }
    (SESSION_DIR / "setup_state.json").write_text(json.dumps(data))
    print(f"OTP sent to {PHONE}")
    print(f"phone_code_hash: {result.phone_code_hash}")
    await client.disconnect()

asyncio.run(send_code())
