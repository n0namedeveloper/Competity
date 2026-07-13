"""FastAPI application factory — main entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.competitors import router as competitors_router
from app.api.reports import router as reports_router
from app.api.webhooks import router as webhooks_router
from app.bot.telegram import telegram_bot
from app.config import settings
from app.database import Base, engine
from app.scheduler import setup_scheduler, shutdown_scheduler

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown."""
    # ── Startup ──
    logger.info("Starting Competity...", env=settings.app_env)

    # Create tables (in dev mode; use Alembic in production)
    if not settings.is_production:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    # Initialize Telegram bot
    try:
        await telegram_bot.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")

    # Start scheduler
    setup_scheduler()

    logger.info("Competity started successfully ✓")

    yield

    # ── Shutdown ──
    logger.info("Shutting down Competity...")
    shutdown_scheduler()
    await telegram_bot.shutdown()
    await engine.dispose()
    logger.info("Competity stopped ✓")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Competity",
        description="Competitive Intelligence Bot — monitor competitors and generate weekly reports",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(competitors_router)
    app.include_router(reports_router)
    app.include_router(webhooks_router)

    # Health check
    @app.get("/health", tags=["system"])
    async def health():
        return {
            "status": "healthy",
            "service": "competity",
            "version": "0.1.0",
        }

    return app


app = create_app()
