# Askslim_notifier 📈🔔

Automated fetcher, JSON dataset builder, and 24/7 Telegram notification monitor for askSlim Trade Ideas.

---

## 🚀 Features

- **Automated Data Fetcher (`fetch_trade_ideas.py`)**:
  - Fetches the complete database of 1,000+ active and historical trade ideas from askSlim.
  - Automatically parses and decodes enums (Status, Position Bias, Outlook Period, Outcomes).
  - Exports clean, structured **JSON** (`trade_ideas.json`) and **CSV** (`trade_ideas.csv`).

- **Telegram 24/7 Notifier (`telegram_notifier.py`)**:
  - **New Trade Ideas**: Instant alerts with Symbol, Direction (Long/Short), Price, Target Entry Range, Target Range, Re-Evaluation Level, and Analysis Briefing.
  - **Status Updates**: Alerts when trades hit target zones, hit re-evaluation levels, or close.
  - **State Persistence**: Tracks seen trade ideas via `notifier_state.json` to prevent duplicate alerts.

- **Cloud Automation (`.github/workflows/askslim_monitor.yml`)**:
  - Automatically runs every 15 minutes via GitHub Actions 24/7 for free with zero maintenance.

---

## 📁 Repository Structure

```
├── .github/
│   └── workflows/
│       └── askslim_monitor.yml   # 24/7 GitHub Actions Cloud Runner
├── fetch_trade_ideas.py          # Standalone scraper & JSON/CSV builder
├── telegram_notifier.py          # Telegram alert watcher
├── notifier_state.json           # Cached tracker state
├── trade_ideas.json              # Processed trade ideas dataset (JSON)
├── trade_ideas_raw.json          # Raw API response (JSON)
├── trade_ideas.csv               # Processed trade ideas dataset (CSV)
└── README.md
```

---

## ⚙️ 24/7 GitHub Actions Setup

1. In this GitHub Repository, navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret** and add:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from [@BotFather](https://t.me/BotFather).
   - `TELEGRAM_CHAT_ID`: Your chat ID from [@userinfobot](https://t.me/userinfobot).
3. The workflow will automatically trigger every 15 minutes and send alerts directly to your Telegram.

---

## 💻 Local Usage

### 1. Fetch & Update JSON Dataset
```bash
python fetch_trade_ideas.py
```

### 2. Test Telegram Alert Connection
```bash
python telegram_notifier.py --test
```

### 3. Run Continuous Local Monitor
```bash
python telegram_notifier.py --interval 300
```
