import os
import aiohttp
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramAlerter:
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_msg_time = 0.0
        has_token = bool(self.token)
        has_chat_id = bool(self.chat_id)
        logger.info(
            "TelegramAlerter init: enabled=%s has_token=%s has_chat_id=%s",
            self.enabled,
            has_token,
            has_chat_id,
        )
        
        if self.enabled:
            logger.info(f"TelegramAlerter enabled for chat_id={self.chat_id}")
        else:
            logger.warning("TelegramAlerter disabled (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)")

    async def start(self):
        if self.enabled and not self.session:
            self.session = aiohttp.ClientSession()

    async def stop(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def send_message(self, text: str):
        if not self.enabled:
            logger.debug("TelegramAlerter send_message skipped: disabled")
            return

        if not self.session:
            await self.start()

        session_closed = self.session.closed if self.session else True
        logger.debug(
            "TelegramAlerter send_message: session_exists=%s session_closed=%s",
            bool(self.session),
            session_closed,
        )

        # Rate limiting: 1 message per second roughly
        now = asyncio.get_running_loop().time()
        delta = now - self.last_msg_time
        if delta < 1.0:
            wait_time = 1.0 - delta
            logger.debug("TelegramAlerter rate limit sleep: %.3fs", wait_time)
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        try:
            # We assume session exists because we called start() or checked above
            # But just in case concurrent close happened:
            if self.session and not self.session.closed:
                async with self.session.post(url, json=payload, timeout=5) as resp:
                    if resp.status != 200:
                        logger.error(f"Telegram send failed: {resp.status} - {await resp.text()}")
                    else:
                        logger.debug("Telegram send success: status=%s", resp.status)
            else:
                logger.error("Telegram send failed: session missing or closed")
            
            self.last_msg_time = asyncio.get_running_loop().time()
            
        except Exception as e:
            logger.error(f"Telegram error: {e}")
