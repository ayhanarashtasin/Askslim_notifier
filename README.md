# Askslim_notifier 📈🔔

Automated 24/7 Telegram notification monitor for askSlim Trade Ideas.

---

## 🚀 Features

- **24/7 Cloud Automation (`.github/workflows/askslim_monitor.yml`)**:
  - Automatically checks askSlim every 5 minutes via GitHub Actions.
  - Runs in the cloud with zero maintenance and no need to keep your computer turned on.
- **Telegram Notifier (`telegram_notifier.py`)**:
  - **New Trade Ideas**: Instant alerts with Symbol, Direction (Long/Short), Price, Target Entry Range, Target Range, Re-Evaluation Level, and Analysis Briefing.
  - **Status Updates**: Alerts when trades hit target zones, hit re-evaluation levels, or close.
  - **State Tracker (`notifier_state.json`)**: Remembers seen ideas to ensure you only get notified on new/updated ideas.

---

## 📁 Repository Structure

```
├── .github/
│   └── workflows/
│       └── askslim_monitor.yml   # 24/7 GitHub Actions Cloud Runner
├── telegram_notifier.py          # Telegram alert watcher
├── notifier_state.json           # Cached tracker state
├── .gitignore
└── README.md
```

---

## ⚙️ Telegram Destination & Setup

- **Supergroup**: Escanor Capital (`chat_id: -1003893592513`)
- **Forum Topic**: Slim Trade Ideas (`message_thread_id: 2`)

### 24/7 GitHub Actions Setup:
1. In this GitHub Repository, navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret** and add:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from [@BotFather](https://t.me/BotFather).
3. The workflow triggers automatically every 5 minutes and routes trade ideas directly to the **Slim Trade Ideas** forum topic in **Escanor Capital**.

---

## 💻 Local Testing (Optional)

```bash
# Verify Telegram bot connection
python telegram_notifier.py --test

# Run once
python telegram_notifier.py --once
```
