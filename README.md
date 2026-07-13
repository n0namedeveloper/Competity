# 🕵️ Competity — Competitive Intelligence Bot

**Система мониторинга конкурентов** — собирает данные из 5 источников, анализирует через DeepSeek V4, доставляет structured еженедельные отчёты через Telegram.

## Архитектура

```
📡 Sources                    ⚙️ Core (FastAPI)           📬 Delivery
┌──────────┐                 ┌─────────────┐            ┌──────────┐
│ Websites │──┐              │ Collectors  │            │ Telegram │
│ GitHub   │──┤    ┌─────┐   │ Service     │────────┐   │ Bot      │
│ PH       │──┼───→│ API │──→│             │        │   └──────────┘
│ HN       │──┤    └─────┘   │ DeepSeek V4 │        │
│ Reddit   │──┘              │ Analyzer    │────────┼──→ 📊 Reports
                             │             │        │
                             │ APScheduler │        │   ┌──────────┐
                             └─────────────┘        └──→│PostgreSQL│
                                                        └──────────┘
```

## Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI + uvicorn |
| Database | PostgreSQL 16 + async SQLAlchemy |
| Web Scraping | Playwright (async, headless Chromium) |
| AI Analysis | DeepSeek V4 (OpenAI-compatible API) |
| Scheduling | APScheduler |
| Delivery | python-telegram-bot |
| Orchestration | n8n (webhook-ready) |
| Containerization | Docker + Docker Compose |

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** on port `5432`
- **Competity API** on port `8000`
- **n8n** on port `5678`

### 3. Add competitors

```bash
curl -X POST http://localhost:8000/api/v1/competitors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI",
    "domain": "openai.com",
    "github_org": "openai",
    "keywords": ["openai", "chatgpt", "gpt-4"]
  }'
```

### 4. Trigger collection

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/collect
```

### 5. Generate report

```bash
curl -X POST http://localhost:8000/api/v1/reports/generate
```

## Local Development (without Docker)

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Start PostgreSQL (must be running)
# Configure .env with your DATABASE_URL

# Run
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/competitors` | List competitors |
| `POST` | `/api/v1/competitors` | Add competitor |
| `PUT` | `/api/v1/competitors/{id}` | Update competitor |
| `DELETE` | `/api/v1/competitors/{id}` | Delete competitor |
| `GET` | `/api/v1/reports` | List reports |
| `GET` | `/api/v1/reports/{id}` | Get report |
| `POST` | `/api/v1/reports/generate` | Generate report |
| `POST` | `/api/v1/webhooks/collect` | Trigger collection |
| `POST` | `/api/v1/webhooks/report` | Trigger report |
| `POST` | `/api/v1/webhooks/telegram` | Telegram webhook |

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show commands |
| `/report` | Get latest report |
| `/collect` | Trigger data collection |
| `/competitors` | List monitored competitors |

## Data Sources

- **🌐 Websites** — Playwright scrapes `/`, `/pricing`, `/changelog`, `/blog`
- **🐙 GitHub** — REST API for repos, releases, star counts
- **🚀 Product Hunt** — GraphQL API for new launches
- **📰 HackerNews** — Algolia Search API for mentions
- **💬 Reddit** — AsyncPRAW searches target subreddits

## Schedule

| Job | Schedule | Default |
|-----|----------|---------|
| Data Collection | Daily | 03:00 UTC |
| Report Generation | Weekly | Monday 09:00 UTC |

Configure via `.env`:
```
COLLECT_CRON_HOUR=3
REPORT_CRON_DAY_OF_WEEK=mon
REPORT_CRON_HOUR=9
```

## n8n Integration

n8n is available at `http://localhost:5678` (login: admin/competity).

Use these webhook URLs in your n8n workflows:
- `http://app:8000/api/v1/webhooks/collect` — trigger collection
- `http://app:8000/api/v1/webhooks/report` — trigger report generation
