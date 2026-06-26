"""Pawnia Telegram Bot — First-time setup & run.

Untuk first run, script ini akan:
1. Login ke Telegram (minta phone + OTP)
2. Simpan session ke file
3. Start bot

Usage:
  python -m ekosistem_satwa.telegram.setup
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.network import ConnectionTcpFull
from pathlib import Path

API_ID = int(os.getenv("TELEGRAM_API_ID", "30079012"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "1097317c20c7b0a43f03bd47ab08f813")

SESSION_DIR = Path("/app/data/telegram")
SESSION_FILE = SESSION_DIR / "pawnia_bot.session"

DC_HOST = os.getenv("TELEGRAM_DC_PROD_HOST", "149.154.167.50")
DC_PORT = int(os.getenv("TELEGRAM_DC_PROD_PORT", "443"))


async def setup():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(
        StringSession(),
        API_ID,
        API_HASH,
        connection=ConnectionTcpFull,
    )

    await client.connect()

    phone = os.getenv("TELEGRAM_PHONE", "")
    if not phone:
        phone = input("Nomor telepon (format +628xxx): ").strip()

    await client.send_code_request(phone)

    code = input("Kode OTP dari Telegram: ").strip()
    try:
        await client.sign_in(phone, code)
    except Exception as e:
        print(f"Login error: {e}")
        pwd = input("Password 2FA (jika ada): ").strip()
        if pwd:
            await client.sign_in(password=pwd)

    session_str = client.session.save()
    SESSION_FILE.write_text(session_str)
    print(f"Session saved to {SESSION_FILE}")

    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username or 'N/A'})")

    await client.disconnect()
    print("Setup complete! Bot siap dijalankan.")


if __name__ == "__main__":
    asyncio.run(setup())
