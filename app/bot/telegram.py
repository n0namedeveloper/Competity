"""Telegram bot — delivers reports and handles user commands."""

import structlog
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings

logger = structlog.get_logger()

# Maximum Telegram message length
MAX_MESSAGE_LENGTH = 4096


class TelegramBot:
    """Telegram bot for delivering competitive intelligence reports.

    Commands:
        /start — Welcome message
        /report — Get the latest report
        /collect — Trigger data collection
        /competitors — List monitored competitors
        /help — Show available commands
    """

    def __init__(self) -> None:
        self._app: Application | None = None
        self._bot: Bot | None = None

    async def initialize(self) -> None:
        """Initialize the bot application (without starting polling/webhook)."""
        if not settings.telegram_bot_token:
            logger.warning("No Telegram bot token configured — bot disabled")
            return

        self._app = (
            Application.builder()
            .token(settings.telegram_bot_token)
            .updater(None)  # No updater — we process updates manually via webhook or polling
            .build()
        )

        # Register command handlers
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("help", self._cmd_help))
        self._app.add_handler(CommandHandler("report", self._cmd_report))
        self._app.add_handler(CommandHandler("collect", self._cmd_collect))
        self._app.add_handler(CommandHandler("competitors", self._cmd_competitors))

        await self._app.initialize()
        await self._app.start()
        self._bot = self._app.bot

        logger.info("Telegram bot initialized")

    async def shutdown(self) -> None:
        """Stop the bot."""
        if self._app:
            await self._app.stop()
            await self._app.shutdown()
            logger.info("Telegram bot shut down")

    async def process_update(self, update_data: dict) -> None:
        """Process an incoming Telegram update (from webhook)."""
        if self._app:
            update = Update.de_json(update_data, self._app.bot)
            await self._app.process_update(update)

    async def send_report(self, markdown_text: str, chat_id: str | None = None) -> bool:
        """Send a report to the configured chat.

        Splits long messages into chunks if needed.

        Returns:
            True if sent successfully.
        """
        target_chat = chat_id or settings.telegram_chat_id
        if not self._bot or not target_chat:
            logger.warning("Cannot send report — bot or chat_id not configured")
            return False

        try:
            # Split into chunks if too long
            chunks = self._split_message(markdown_text)

            for chunk in chunks:
                await self._bot.send_message(
                    chat_id=target_chat,
                    text=chunk,
                    parse_mode=ParseMode.MARKDOWN,
                )

            logger.info(f"Report sent to chat {target_chat} ({len(chunks)} messages)")
            return True

        except Exception as e:
            logger.error(f"Failed to send report: {e}")
            # Try sending without markdown formatting as fallback
            try:
                for chunk in self._split_message(markdown_text):
                    await self._bot.send_message(
                        chat_id=target_chat,
                        text=chunk,
                    )
                return True
            except Exception as e2:
                logger.error(f"Fallback send also failed: {e2}")
                return False

    @staticmethod
    def _split_message(text: str) -> list[str]:
        """Split a long message into Telegram-compatible chunks."""
        if len(text) <= MAX_MESSAGE_LENGTH:
            return [text]

        chunks = []
        while text:
            if len(text) <= MAX_MESSAGE_LENGTH:
                chunks.append(text)
                break

            # Try to split at a newline
            split_pos = text.rfind("\n", 0, MAX_MESSAGE_LENGTH)
            if split_pos == -1:
                split_pos = MAX_MESSAGE_LENGTH

            chunks.append(text[:split_pos])
            text = text[split_pos:].lstrip("\n")

        return chunks

    # ── Command Handlers ──

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "🤖 *Competity Bot*\n\n"
            "I monitor your competitors and deliver weekly intelligence reports.\n\n"
            "Use /help to see available commands.",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "📋 *Available Commands:*\n\n"
            "/report — Get the latest intelligence report\n"
            "/collect — Trigger data collection now\n"
            "/competitors — List monitored competitors\n"
            "/help — Show this message",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def _cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Fetch and send the latest report."""
        from app.database import AsyncSessionLocal
        from app.models.report import Report
        from sqlalchemy import select

        await update.message.reply_text("⏳ Fetching latest report...")

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Report).order_by(Report.created_at.desc()).limit(1)
                )
                report = result.scalar_one_or_none()

                if report:
                    await self.send_report(
                        report.content_markdown,
                        chat_id=str(update.effective_chat.id),
                    )
                else:
                    await update.message.reply_text(
                        "📭 No reports generated yet. Use /collect to gather data first."
                    )
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching report: {e}")

    async def _cmd_collect(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Trigger manual data collection."""
        from app.database import AsyncSessionLocal
        from app.services.collector_service import CollectorService

        await update.message.reply_text("🔄 Starting data collection... This may take a few minutes.")

        try:
            async with AsyncSessionLocal() as session:
                service = CollectorService(session)
                summary = await service.collect_all()

                total = summary.get("total_items", 0)
                errors = summary.get("total_errors", 0)

                await update.message.reply_text(
                    f"✅ *Collection complete!*\n\n"
                    f"📊 Items collected: {total}\n"
                    f"⚠️ Errors: {errors}\n\n"
                    f"Use /report to generate an intelligence report.",
                    parse_mode=ParseMode.MARKDOWN,
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Collection failed: {e}")

    async def _cmd_competitors(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all monitored competitors."""
        from app.database import AsyncSessionLocal
        from app.models.competitor import Competitor
        from sqlalchemy import select

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Competitor).order_by(Competitor.name)
                )
                competitors = result.scalars().all()

                if not competitors:
                    await update.message.reply_text(
                        "📭 No competitors configured yet.\n"
                        "Add them via the API: POST /api/v1/competitors"
                    )
                    return

                lines = ["🏢 *Monitored Competitors:*\n"]
                for c in competitors:
                    status = "✅" if c.is_active else "⏸️"
                    lines.append(f"{status} *{c.name}*")
                    if c.domain:
                        lines.append(f"   🌐 {c.domain}")
                    if c.github_org:
                        lines.append(f"   🐙 github.com/{c.github_org}")
                    if c.keywords:
                        lines.append(f"   🔑 {', '.join(c.keywords)}")
                    lines.append("")

                await update.message.reply_text(
                    "\n".join(lines),
                    parse_mode=ParseMode.MARKDOWN,
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")


# Module-level singleton
telegram_bot = TelegramBot()
