"""Telegram Bot Service — Pawnia AI Companion via MTProto.

Menghubungkan Telegram user ke Pawnia AI Orchestrator API.
Menggunakan Telethon (MTProto) untuk koneksi langsung ke Telegram DC.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.network import ConnectionTcpFull

logger = logging.getLogger("pawnia.telegram")

# Konfigurasi dari environment
API_ID = int(os.getenv("TELEGRAM_API_ID", "30079012"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "1097317c20c7b0a43f03bd47ab08f813")
APP_TITLE = os.getenv("TELEGRAM_APP_TITLE", "Pawnia")

DC_TEST_HOST = os.getenv("TELEGRAM_DC_TEST_HOST", "149.154.167.40")
DC_TEST_PORT = int(os.getenv("TELEGRAM_DC_TEST_PORT", "443"))
DC_PROD_HOST = os.getenv("TELEGRAM_DC_PROD_HOST", "149.154.167.50")
DC_PROD_PORT = int(os.getenv("TELEGRAM_DC_PROD_PORT", "443"))

PAWNIA_API_BASE = os.getenv("PAWNIA_API_BASE", "http://localhost:8080")
PAWNIA_CHAT_URL = f"{PAWNIA_API_BASE}/api/v1/ai/chat"
PAWNIA_STATUS_URL = f"{PAWNIA_API_BASE}/api/v1/ai/status"

SESSION_DIR = Path(os.getenv("TELEGRAM_SESSION_DIR", "/app/data/telegram"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = SESSION_DIR / "pawnia_bot.session"


async def pawnia_chat(
    message: str,
    session_id: str | None = None,
    user_id: int | None = None,
    pet_context: dict | None = None,
) -> dict[str, Any]:
    """Kirim pesan ke Pawnia AI Orchestrator dan dapatkan response."""
    payload = {
        "message": message,
        "session_id": session_id,
        "user_id": user_id,
        "pet_context": pet_context or {},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(PAWNIA_CHAT_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


async def pawnia_status() -> dict[str, Any]:
    """Cek status Pawnia AI."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(PAWNIA_STATUS_URL)
        resp.raise_for_status()
        return resp.json()


def format_response(data: dict) -> str:
    """Format Pawnia response jadi teks Telegram yang rapi."""
    agent = data.get("agent", "companion")
    risk_level = data.get("risk_level", "low")
    confidence = data.get("confidence", 0)
    response_data = data.get("response", {})
    text = response_data.get("text", "")
    suggestions = response_data.get("suggestions", [])
    cta = response_data.get("cta", [])
    disclaimer = response_data.get("disclaimer", "")
    escalated = data.get("escalated", False)

    risk_icons = {"low": "\U0001f7e2", "medium": "\U0001f7e1", "high": "\U0001f534", "critical": "\U0001f6a8"}
    risk_icon = risk_icons.get(risk_level, "\u26aa")

    lines = [f"{risk_icon} *Pawnia \u2014 {agent.replace(chr(95), chr(32)).title()}*"]
    lines.append(f"Keyakinan: {confidence:.0%}")

    if text:
        lines.append("")
        lines.append(text)

    if suggestions:
        lines.append("")
        lines.append("*\U0001f4a1 Saran:*")
        for s in suggestions:
            lines.append(f"\u2022 {s}")

    if cta:
        lines.append("")
        lines.append("*\U0001f4cb Tindakan:*")
        for c in cta:
            lines.append(f"\u2022 {c}")

    if disclaimer:
        lines.append("")
        lines.append(f"_{disclaimer}_")

    if escalated:
        lines.append("")
        lines.append("\U0001f6a8 *Telah dieskalasi ke dokter hewan*")

    return "\n".join(lines)


class PawniaTelegramBot:
    """Telegram Bot untuk Pawnia AI Companion."""

    def __init__(self, use_test_dc: bool = False):
        self.use_test_dc = use_test_dc
        self.client: TelegramClient | None = None
        self._sessions: dict[int, str] = {}

    async def start(self):
        """Start the Telegram client."""
        host = DC_TEST_HOST if self.use_test_dc else DC_PROD_HOST
        port = DC_TEST_PORT if self.use_test_dc else DC_PROD_PORT

        logger.info(
            "Starting Pawnia Telegram Bot (DC=%s:%d, test=%s)",
            host, port, self.use_test_dc,
        )

        session_str = None
        if SESSION_FILE.exists():
            session_str = SESSION_FILE.read_text().strip()
            logger.info("Loaded existing session from %s", SESSION_FILE)

        self.client = TelegramClient(
            StringSession(session_str) if session_str else StringSession(),
            API_ID,
            API_HASH,
            connection=ConnectionTcpFull,
            request_retries=5,
            connection_retries=3,
        )

        await self.client.connect()

        if not await self.client.is_user_authorized():
            logger.info("Bot not authorized. Requesting phone number...")
            print("\n\u26a0\ufe0f  Telegram Bot belum login!")
            print("Silakan login sebagai user bot atau akun Telegram.")
            phone = input("\U0001f4f1 Nomor telepon (format +628xxx): ").strip()
            await self.client.send_code_request(phone)
            code = input("\U0001f511 Kode OTP dari Telegram: ").strip()
            try:
                await self.client.sign_in(phone, code)
            except Exception as e:
                logger.warning("Sign in failed: %s", e)
                pwd = input("\U0001f510 Password 2FA (jika ada): ").strip()
                if pwd:
                    await self.client.sign_in(password=pwd)

        session_str = self.client.session.save()
        SESSION_FILE.write_text(session_str)
        logger.info("Session saved to %s", SESSION_FILE)

        self._register_handlers()

        me = await self.client.get_me()
        logger.info("Logged in as: %s (ID: %d)", me.username or me.first_name, me.id)

        await self.client.run_until_disconnected()

    def _register_handlers(self):
        """Register event handlers."""
        if not self.client:
            return

        @self.client.on(events.NewMessage(pattern=r"^/start$"))
        async def start_handler(event):
            await event.reply(
                "\U0001f43e *Halo! Saya Pawnia \u2014 AI Companion untuk hewan kesayangan Anda!*\n\n"
                "Saya bisa membantu:\n"
                "\u2022 \U0001fa79 Konsultasi kesehatan hewan\n"
                "\u2022 \U0001f37d\ufe0f Saran nutrisi & makan\n"
                "\u2022 \U0001f9e0 Analisis perilaku\n"
                "\u2022 \U0001f4f8 Analisis gambar (luka, kulit)\n\n"
                "Cukup kirim pesan atau foto, saya akan bantu!\n\n"
                "\u26a0\ufe0f *Saya bukan pengganti dokter hewan.*\n"
                "Untuk keadaan darurat, segera bawa ke klinik terdekat.",
                parse_mode="markdown",
            )

        @self.client.on(events.NewMessage(pattern=r"^/status$"))
        async def status_handler(event):
            msg = await event.reply("\u23f3 Mengecek status sistem...")
            try:
                st = await pawnia_status()
                agents = ", ".join(st.get("agents", []))
                status_text = (
                    f"*\U0001f916 Pawnia Status*\n\n"
                    f"Status: {chr(10004) if st.get('pawnia_available') else chr(10060)} {'Aktif' if st.get('pawnia_available') else 'Tidak Aktif'}\n"
                    f"LLM: {chr(10004) if st.get('llm_available') else chr(10060)}\n"
                    f"Memory: {chr(10004) if st.get('memory_available') else chr(10060)}\n"
                    f"Knowledge: {chr(10004) if st.get('knowledge_available') else chr(10060)}\n"
                    f"Agent: {agents}\n"
                    f"Versi: {st.get('version', 'N/A')}"
                )
                await msg.edit(status_text, parse_mode="markdown")
            except Exception as e:
                await msg.edit(f"\u274c Gagal cek status: {e}")

        @self.client.on(events.NewMessage(pattern=r"^/help$"))
        async def help_handler(event):
            await event.reply(
                "*\U0001f4d6 Bantuan Pawnia*\n\n"
                "\u2022 `/start` \u2014 Mulai\n"
                "\u2022 `/status` \u2014 Cek status sistem\n"
                "\u2022 `/help` \u2014 Bantuan ini\n"
                "\u2022 `/clear` \u2014 Reset sesi percakapan\n\n"
                "Atau langsung kirim pesan untuk konsultasi!",
                parse_mode="markdown",
            )

        @self.client.on(events.NewMessage(pattern=r"^/clear$"))
        async def clear_handler(event):
            user_id = event.sender_id
            if user_id and user_id in self._sessions:
                del self._sessions[user_id]
            await event.reply("\u2705 Sesi percakapan direset. Mulai lagi ya!")

        @self.client.on(events.NewMessage)
        async def message_handler(event):
            """Handle all text messages."""
            if event.text.startswith("/"):
                return

            user_id = event.sender_id
            message = event.text.strip()
            if not message:
                return

            async with self.client.action(event.chat_id, "typing"):
                session_id = self._sessions.get(user_id)

                try:
                    data = await pawnia_chat(
                        message=message,
                        session_id=session_id,
                        user_id=user_id,
                    )

                    conv_id = data.get("conversation_id")
                    if conv_id and user_id:
                        self._sessions[user_id] = conv_id

                    reply = format_response(data)
                    await event.reply(reply, parse_mode="markdown")

                except httpx.HTTPStatusError as e:
                    await event.reply(
                        f"\u274c Maaf, terjadi kesalahan pada sistem ({e.response.status_code}). "
                        "Silakan coba lagi nanti."
                    )
                except httpx.RequestError:
                    await event.reply(
                        "\u274c Tidak dapat terhubung ke Pawnia AI. "
                        "Pastikan server sedang berjalan."
                    )
                except Exception as e:
                    logger.exception("Error processing message")
                    await event.reply("\u274c Terjadi kesalahan. Silakan coba lagi.")

        @self.client.on(events.NewMessage)
        async def photo_handler(event):
            """Handle photo messages."""
            if not event.message.photo:
                return

            user_id = event.sender_id
            session_id = self._sessions.get(user_id)

            async with self.client.action(event.chat_id, "typing"):
                try:
                    photo_path = await event.message.download_media(
                        file=SESSION_DIR / f"photo_{user_id}.jpg"
                    )

                    async with httpx.AsyncClient(timeout=60.0) as client:
                        with open(photo_path, "rb") as f:
                            resp = await client.post(
                                f"{PAWNIA_API_BASE}/api/vision/analyze/upload",
                                files={"image": f},
                                data={
                                    "focus_mode": "general",
                                    "session_id": session_id or "",
                                    "user_id": user_id or 0,
                                },
                            )
                            resp.raise_for_status()
                            vision_data = resp.json()

                    Path(photo_path).unlink(missing_ok=True)

                    vision_text = vision_data.get("description", "")
                    diagnosis = vision_data.get("diagnosis", "")
                    confidence = vision_data.get("confidence", 0)

                    reply = (
                        f"\U0001f4f8 *Analisis Gambar*\n\n"
                        f"{vision_text}\n"
                    )
                    if diagnosis:
                        reply += f"\n*Diagnosis:* {diagnosis}\n"
                    reply += f"*Keyakinan:* {confidence:.0%}\n\n"
                    reply += "Ada yang ingin ditanyakan lebih lanjut?"

                    await event.reply(reply, parse_mode="markdown")

                except Exception as e:
                    logger.exception("Error processing photo")
                    await event.reply(
                        "\u274c Gagal memproses gambar. Pastikan formatnya JPEG/PNG."
                    )

    async def stop(self):
        """Stop the Telegram client."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    use_test = os.getenv("TELEGRAM_USE_TEST_DC", "false").lower() == "true"
    bot = PawniaTelegramBot(use_test_dc=use_test)

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
