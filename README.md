# TODO
1. User on-boarding
2. If user executes command in server ask user to use dm 


# chattick - AI-Powered Stock Analysis & Discord Bot

chattick is a comprehensive stock market analysis platform that combines real-time market data, technical indicators, and AI-powered natural language processing to provide intelligent trading insights through Discord.

## Features

### 📊 Data Processing & Analysis
- **Real-time Stock Data**: Fetches stock data from Yahoo Finance for Indian markets (NSE)
- **Technical Indicators**: Calculates SMA, EMA, ATR, VWAP, RVOL and other indicators
- **Multi-interval Support**: Supports 1m, 2m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo intervals
- **Corporate Actions**: Handles stock splits, dividends, and other corporate events
- **Nifty-50 Support**: Pre-configured with all major Indian indices

### 🤖 AI-Powered Features
- **Natural Language Queries**: Convert plain English questions into technical analysis queries using GPT-4o
- **Gherkin Query Language**: Structured Given-When-Then syntax for precise market analysis
- **LLM Agent Pipeline**: Multi-stage processing with validation, conversion, and routing

### 💬 Discord Integration
- **Interactive Bot**: Full-featured Discord bot with slash commands
- **Real-time Notifications**: Automatic alerts based on market conditions
- **User Profiles**: Per-user configuration and trading preferences
- **Chart Integration**: TradingView and Zerodha chart links

### ⏰ Intelligent Scheduling
- **Cron-based Jobs**: APScheduler integration for market-hours automation
- **Timezone Support**: Full timezone awareness (default: Asia/Kolkata)
- **Custom Schedules**: Configurable for different analysis intervals

### 📈 Backtesting
- **Historical Analysis**: Configurable iterations for strategy validation
- **Corporate Action Adjustments**: Accurate historical data accounting

## Project Structure

```
pytick/
├── bot/                          # Discord bot implementation
│   ├── discordbot.py            # Main bot class
│   ├── commands.py              # Bot commands
│   └── __init__.py
├── dataframe/                    # Data handling & processing
│   ├── dataframe.py             # Stock data fetching & indicator calculation
│   ├── notification.py          # Notification formatting
│   └── __init__.py
├── llm/                          # AI/LLM integration
│   ├── graph.py                 # LangGraph workflow
│   ├── types.py                 # Type definitions
│   ├── agents/
│   │   ├── converter.py         # Converts English to Gherkin
│   │   ├── router.py            # Routes messages appropriately
│   │   └── validator.py         # Validates Gherkin queries
│   ├── utils/
│   │   └── draw.py              # Graph visualization
│   └── __init__.py
├── query/                        # Query handling & execution
│   ├── query.py                 # Gherkin parser & executor
│   ├── logic.py                 # Query logic implementation
│   ├── steps.py                 # Query step definitions
│   └── __init__.py
├── scheduler/                    # Task scheduling
│   ├── scheduler.py             # APScheduler wrapper
│   └── __init__.py
├── utility/                      # Utility functions
│   ├── utility.py               # Common utilities
│   └── __init__.py
├── test/                         # Test suite
│   ├── test_discordbot.py
│   ├── test_query.py
│   ├── data/                    # Test data (CSV files)
│   └── users/                   # Test user configs
└── setup.py
```

## Installation

### Prerequisites
- Python 3.8+
- Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
- OpenAI API Key (for GPT-4o)
- Zerodha/TradingView access (optional, for chart links)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd app
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
Create a `.env` file in the root directory:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
CONFIG_FILE=config.yaml
USERS_DIR=users/
```

5. **Configure application**
Edit `config.yaml` to set:
- Timezone (default: `Asia/Kolkata`)
- Stock indicators
- Cron schedules for market hours
- Chart link preferences (TradingView or Zerodha)
- Backtesting iterations

## Usage

### Running the Application

```bash
python main.py
```

This starts:
- FastAPI server for HTTP endpoints
- Discord bot for chat interactions
- APScheduler for market analysis jobs

### Bot Commands

The Discord bot supports slash commands for:
- `/analyze` - Analyze stock using natural language
- `/quote` - Get live price quotes
- `/schedule` - Set up recurring analysis
- `/backtest` - Run historical validation
- `/config` - User-specific settings

### Query Syntax (Gherkin Format)

```gherkin
Given ticker [SYMBOL] and interval [INTERVAL]
When [CONDITION] occurs
Then [ACTION] should be taken
```

Example:
```gherkin
Given ticker SBIN and interval 1d
When Close > SMA(20)
Then Generate alert
```

### Configuration Files

- **config.yaml**: Global application settings
- **instruments.csv**: Zerodha instrument tokens
- **ind_nifty50list.csv**: Nifty-50 constituents
- **users/*.yaml**: Per-user bot preferences

## Key Components

### DataFrameHandler (`dataframe/dataframe.py`)
- Downloads stock data from Yahoo Finance
- Calculates technical indicators using `pandas-ta`
- Handles multi-timeframe data
- Processes corporate actions

### QueryHandler (`query/query.py`)
- Parses and validates Gherkin queries
- Executes analysis logic
- Returns formatted results

### Graph (`llm/graph.py`)
- LangGraph-based workflow
- Multi-stage LLM processing:
  1. **Validator**: Validates user input
  2. **Converter**: Converts English to Gherkin
  3. **Router**: Routes to appropriate handler

### DiscordBot (`bot/discordbot.py`)
- Discord.py integration
- Command handling
- User preference management
- Scheduled notifications

### Scheduler (`scheduler/scheduler.py`)
- APScheduler backend
- Market-hours automation
- Timezone-aware cron triggers

## Dependencies

Key packages:
- **discord.py**: Discord bot framework
- **fastapi**: Web framework
- **pandas**: Data manipulation
- **yfinance**: Stock data
- **langgraph**: LLM workflow orchestration
- **langchain**: LLM integration
- **apscheduler**: Task scheduling
- **pydantic**: Data validation

See `requirements.txt` for complete list.

## Development

### Running Tests

```bash
pytest pytick/test/
```

### Adding New Indicators

1. Update `config.yaml` with indicator settings
2. Extend `DataFrameHandler.calculate_indicators()`
3. Add test data in `pytick/test/data/`

### Extending Bot Commands

1. Add command in `bot/commands.py`
2. Update `BotConfig` if needed
3. Add tests in `pytick/test/test_discordbot.py`

## Architecture Diagram

```
User Input (Discord)
        ↓
    LLM Graph
    ├── Validator (Input validation)
    ├── Converter (English→Gherkin)
    └── Router (Route to handler)
        ↓
   Query Handler
    ├── Parse Gherkin
    ├── Execute Logic
    └── Format Response
        ↓
  Data Handler
    ├── Fetch Data
    ├── Calculate Indicators
    └── Process Results
        ↓
  Notification Handler
        ↓
Discord Bot → User
```

## Performance Considerations

- **Data Caching**: Stock data cached per interval
- **Batch Processing**: Multi-process ticker downloads
- **Async Scheduling**: Non-blocking market analysis jobs
- **Message Batching**: Notification consolidation via `NotificationHandler`

## Troubleshooting

### Bot Not Responding
- Check Discord bot token in `.env`
- Verify bot has correct server permissions
- Check logs in `log.txt`

### LLM Conversion Issues
- Verify OpenAI API key
- Check model availability (requires GPT-4o)
- Review agent validation logs

### Data Fetch Failures
- Verify ticker symbols (use `.NS` suffix for NSE)
- Check Yahoo Finance availability
- Review corporate actions handling

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push branch: `git push origin feature/your-feature`
5. Submit pull request

## License

[Specify your license here]

## Support

For issues, questions, or suggestions:
- Open a GitHub issue
- Contact the development team
- Check documentation in `README.md`

## Future Roadmap

- [ ] Resubscribe user subscriptions
- [ ] Check user registration 
    - [ ] New user guidelines
    - [ ] New user licensing    
- [ ] Fix LLM converter

---

**Last Updated**: February 2026
**Version**: 0.1.0
**Status**: Active Development
