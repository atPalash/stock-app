# chattick — AI-Powered Stock Analysis & Discord Bot

chattick is a comprehensive, production-grade stock market analysis platform. It integrates real-time market data, calculates advanced technical indicators, and leverages AI-powered natural language processing to deliver trading insights directly through Discord.

---

## 📊 Features

### 1. Data Processing & Technical Indicators
* **Real-time Stock Data**: Fetches and caches historical & live stock data from Yahoo Finance for Indian markets (NSE) and US markets (Nasdaq).
* **Technical Indicators**: Calculates SMA, EMA, ATR, VWAP, RVOL, and other indicators via `pandas-ta`.
* **Multi-interval Support**: Fully supports 1m, 2m, 5m, 15m, 30m, 1h, 1d, 1wk, and 1mo intervals.
* **Corporate Actions**: Seamlessly handles and notifies on stock splits, dividends, and other events.
* **Index Constituents**: Pre-configured with Nifty-50 and Nifty-100 components.

### 2. AI-Powered Workflow (LangGraph)
* **Natural Language Queries**: Transforms conversational queries into structured logical statements using GPT models.
* **Gherkin Query Syntax**: Formulates logic using precise `Given-When-Then` style semantics.
* **LLM Agent Pipeline**: Built on LangGraph, utilizing Validator, Converter, and Router agents to validate inputs and route requests.

### 3. Discord & API Integrations
* **Interactive Bot**: Full-featured Discord bot with rich slash commands, autocomplete support, and interactive text input modals.
* **Real-time Alerts & Subscriptions**: Users can subscribe to custom alerts triggered by market condition checks.
* **FastAPI Server**: Exposes API endpoints for retrieving dataframes, corporate action notifications, Gherkin logic execution, and strategy comparison.

### 4. Backtesting & Comparisons
* **Historical Analysis**: Backtests Gherkin strategies over user-defined lookback windows with custom commissions and stop losses.
* **Multi-Strategy Comparison**: Compares multiple queries simultaneously and generates a comparative performance chart with SQN metrics.

---

## 📂 Project Structure

- [main.py](file:///home/palash/dev/stock-app/main.py): Entrypoint file that initializes the FastAPI server, APScheduler, and the Discord bot.
- [setup.py](file:///home/palash/dev/stock-app/setup.py): Distribution setup for the `pytick` Python package.
- [requirements.txt](file:///home/palash/dev/stock-app/requirements.txt): Core Python dependencies.
- [config.yaml](file:///home/palash/dev/stock-app/config.yaml): Main application configuration file containing index listings, indicators, and scheduled task rules.
- [pytick/](file:///home/palash/dev/stock-app/pytick):
  - [bot/](file:///home/palash/dev/stock-app/pytick/bot): Discord bot command handlers, user preferences, and message flows.
  - [dataframe/](file:///home/palash/dev/stock-app/pytick/dataframe): Data downloading, caching, indicator calculations, and notification formatting.
  - [llm/](file:///home/palash/dev/stock-app/pytick/llm): LangGraph workflows, validator/converter agents, and system prompt generation.
  - [query/](file:///home/palash/dev/stock-app/pytick/query): Gherkin parser, strategy executor, and step logic verification.
  - [scheduler/](file:///home/palash/dev/stock-app/pytick/scheduler): Timezone-aware wrapper around APScheduler.

---

## 🚀 Installation & Setup

### Prerequisites
* Python 3.10+
* Discord Bot Token (obtainable via the [Discord Developer Portal](https://discord.com/developers/applications))
* OpenAI API Key (or access to custom LLMs)
* Redis (for persistent conversation tracking and subscription caching)

---

### Option A: Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stock-app
   ```

2. **Set up a Virtual Environment & Install Dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Configure Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token
   OPENAI_API_KEY=your_openai_api_key
   CONFIG_FILE=config.yaml
   REDIS_URL=redis://localhost:6379/0
   APP_PORT=8000
   ```

4. **Run the Application**
   ```bash
   python main.py
   ```

---

### Option B: Containerized Setup (Docker & Podman)

This repository includes a multi-stage [Dockerfile](file:///home/palash/dev/stock-app/Dockerfile) and a [docker-compose.yml](file:///home/palash/dev/stock-app/docker-compose.yml) configured to run the FastAPI service, Discord bot, and a backing Redis database.

#### Using Docker Compose
```bash
# Start all services (Redis + Dev application)
docker compose up -d --build
```

#### Using Podman Compose (Rootless Setup)
Podman runs rootless containers by default. The configuration features `userns_mode: keep-id` to mount the source code directory without file ownership conflicts:
```bash
# Start all services using Podman
podman compose up -d --build
```

* **Development Target (`stockappdev`)**: Starts on port `9000` and mounts the local folder into `/home/palash/stock-app` for live edits.
* **Release Target (`stockapprel`)**: Starts on port `8000` with the production setup.

---

## ⚙️ Configuration

1. **[.env](file:///home/palash/dev/stock-app/.env)**: Houses secrets like `DISCORD_BOT_TOKEN`, `OPENAI_API_KEY`, `REDIS_URL`, and `APP_PORT`.
2. **[config.yaml](file:///home/palash/dev/stock-app/config.yaml)**: Contains global parameters:
   * `tz`: Active timezone (default: `Asia/Kolkata`).
   * `admin_ids`: List of Discord user IDs authorized to run administrative debug options.
   * `indexes`: Lists of stock symbols grouped by index (e.g., `nifty50`, `nifty100`).
   * `indicators`: Configuration definitions for indicators like `sma`, `ema`, `atr`, `vwap`.
   * `cron_schedules`: Execution intervals and rules for background data-fetching jobs.

---

## 💬 Bot Commands

The Discord bot integrates slash commands for ease of use:

| Command | Description |
| :--- | :--- |
| `/analyze` | Formulate a natural language query (e.g. *"Show me stocks where Close is above 20 SMA"*). |
| `/quote` | Get a real-time price snapshot and info card for a specific ticker symbol. |
| `/schedule` | Manage recurring alerts and schedules for analysis queries. |
| `/backtest` | Runs a historical performance evaluation on a strategy query. |
| `/config` | Updates user-specific links, defaults, and notification settings. |
| `/subscribe` | Subscribe to automated alerts on strategy executions. Supports `/subscribe ls` to view current subscriptions. |
| `/debug` | **Admin Only** (Restricted to user IDs specified in `admin_ids` config). Run development tools. |

### 🛠️ Administrative `/debug` Command Options
The `/debug` command accepts the following options:
* `--command health`: Tests endpoint connectivity and logs API server health.
* `--command df --endpoint <TICKER>`: Fetches and uploads the last 10 rows of the processed dataframe for `<TICKER>` as a CSV.
* `--command gherkin --queries "<GHERKIN_QUERY>"`: Executes a Gherkin query directly on historical data and returns results in CSV format.
* `--command backtest --queries "<GHERKIN_QUERY>" --start <START_WINDOW> --stop <STOP_WINDOW> --stop_loss <STOP_LOSS_PCT> --commission <COMMISSION_PCT>`: Triggers a comparative backtest report for administrators.

---

## 📈 Query Syntax (Gherkin Format)

Strategies can be queried explicitly using Gherkin's `Given-When-Then` style:

```gherkin
Given ticker [SYMBOL] and interval [INTERVAL]
When [TECHNICAL_CONDITION]
Then [ACTION]
```

### Example
```gherkin
Given ticker SBIN and interval 1d
When Close > SMA(20)
Then Generate buy signal
```

---

## 🧪 Development & Testing

### Running Unit Tests
To execute the test suite, ensure the development dependencies are installed and run:
```bash
pytest pytick/test/
```

### Adding Technical Indicators
1. Declare your indicator parameters in the `indicators:` block inside [config.yaml](file:///home/palash/dev/stock-app/config.yaml).
2. Code the calculation logic inside [pytick/dataframe/dataframe.py](file:///home/palash/dev/stock-app/pytick/dataframe/dataframe.py#L130).
3. Validate by writing a new unit test or loading indicator outputs.

---

**Last Updated**: July 2026  
**Version**: 0.2.0  
**Status**: Active Development  
