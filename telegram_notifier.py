import html
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# ==========================================================
# CONFIGURATION
# 1. Get Bot Token from @BotFather on Telegram
# 2. Get your Chat ID from @userinfobot on Telegram
# ==========================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE")

API_URL = "https://trade-ideas.slimulator.net/ti/trade_idea"
STATE_FILE = Path(__file__).parent / "notifier_state.json"
CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes (default)

# Enums & Mappings
STATUS_MAP = {1: "Inactive", 2: "Active"}
PERIOD_MAP = {
    1: "Near-Term (1-5 days)",
    2: "Short-Term (1-3 weeks)",
    3: "Intermediate-Term (3-8 weeks)",
    4: "Long-Term (2-6 months)",
    5: "Intraday",
}
BIAS_MAP = {1: "Short", 2: "Long"}
OUTCOME_MAP = {
    0: "Pending / Inactive",
    1: "Re-evaluation Level Hit",
    2: "Target Zone Reached",
    3: "Target Zone Reached (Early / Missed Entry)",
}


def send_telegram_message(
    text: str, bot_token: str = None, chat_id: str = None
):
  """Sends an HTML-formatted message to Telegram via Bot API."""
  token = bot_token or TELEGRAM_BOT_TOKEN
  cid = chat_id or TELEGRAM_CHAT_ID

  if token == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not token:
    print(" [!] Telegram credentials not configured. Message preview:")
    print("-" * 50)
    # encode safe for windows console print
    print(text.encode("ascii", "replace").decode("ascii"))
    print("-" * 50)
    return False

  url = f"https://api.telegram.org/bot{token}/sendMessage"
  payload = {
      "chat_id": cid,
      "text": text,
      "parse_mode": "HTML",
      "disable_web_page_preview": True,
  }

  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
      url, data=data, headers={"Content-Type": "application/json"}
  )
  ctx = ssl.create_default_context()

  try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as res:
      return res.status == 200
  except Exception as e:
    print(f" [!] Failed to send Telegram message: {e}", file=sys.stderr)
    return False


def fetch_current_trade_ideas():
  """Fetches live trade ideas from the askSlim API."""
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json, text/plain, */*",
      "Referer": "https://trade-ideas.slimulator.net/app/",
  }

  ctx = ssl.create_default_context()
  req = urllib.request.Request(API_URL, headers=headers)

  with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
    data = json.loads(response.read().decode("utf-8"))
    return data.get("data", {})


def load_previous_state():
  """Loads the previously saved state to detect changes."""
  if STATE_FILE.exists():
    try:
      with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception as e:
      print(f" [!] Error reading state file: {e}")
  return {}


def save_current_state(state):
  """Saves the current state to disk."""
  with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)


PERIOD_SHORT_MAP = {
    1: "N-T",
    2: "S-T",
    3: "I-T",
    4: "L-T",
    5: "Intraday",
}


def format_new_idea_message(idea_id: str, item: dict) -> str:
  """Builds a rich Telegram notification matching the website table fields."""
  symbol = html.escape(str(item.get("symbol", "N/A")), quote=False)
  status_code = item.get("status")
  status_display = "🟢 Active" if status_code == 2 else "🔴 Inactive"

  # Format date as MM/DD/YY to match website
  raw_date = item.get("creation_date", "")
  try:
    if raw_date:
      # e.g. 2026-08-19 -> 08/19/26
      dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
      date_str = dt.strftime("%m/%d/%y")
    else:
      date_str = "N/A"
  except Exception:
    date_str = raw_date[:10] if raw_date else "N/A"

  period_code = item.get("market_outlook_period")
  period_short = PERIOD_SHORT_MAP.get(period_code, "N/A")
  period_full = PERIOD_MAP.get(period_code, "")
  period_display = f"{period_short} ({period_full})" if period_full else period_short

  price = item.get("current_price", "N/A")

  bias = BIAS_MAP.get(item.get("position_bias"), "N/A")
  bias_emoji = "📈" if bias == "Long" else ("📉" if bias == "Short" else "⚖️")

  # Entry Ranges
  entry_ranges = item.get("entry_ranges", [])
  entry_str = (
      ", ".join([
          f"{r[0]} - {r[1]}" if len(r) == 2 else str(r) for r in entry_ranges
      ])
      if entry_ranges
      else "N/A"
  )
  entry_str = html.escape(entry_str, quote=False)

  # Target Ranges with Projection label
  target_ranges = item.get("target_ranges", [])
  projections = item.get("projections", [])
  proj_prefix = f"{PERIOD_SHORT_MAP.get(projections[0], 'Target')} Projection: " if projections else ""
  if target_ranges:
    target_str = proj_prefix + ", ".join([
        f"{r[0]} - {r[1]}" if len(r) == 2 else str(r)
        for r in target_ranges
    ])
  else:
    target_str = "—"
  target_str = html.escape(target_str, quote=False)

  # Re-evaluation level (e.g. Daily Close < 71.25)
  re_eval_num = item.get("re_eval_point_number")
  re_eval_cond = item.get("re_eval_point_condition")
  cond_symbol = "&lt; " if re_eval_cond == -1 else ("&gt; " if re_eval_cond == 1 else "")
  re_eval_str = (
      f"Daily Close {cond_symbol}{re_eval_num}" if re_eval_num is not None else "N/A"
  )

  briefing = html.escape(item.get("briefing", "").strip(), quote=False)

  msg = (
      f"🚨 <b>NEW ASKSILM TRADE IDEA: ${symbol}</b>\n\n"
      f"• <b>Status:</b> {status_display}\n"
      f"• <b>Date:</b> {date_str}\n"
      f"• <b>Period:</b> {period_display}\n"
      f"• <b>Symbol:</b> <b>${symbol}</b>\n"
      f"• <b>Price at Time of Analysis:</b> ${price}\n"
      f"• <b>Position Bias:</b> {bias_emoji} <b>{bias}</b>\n"
      f"• <b>Entry Range:</b> {entry_str}\n"
      f"• <b>Target Range:</b> {target_str}\n"
      f"• <b>Re-Evaluation Level:</b> {re_eval_str}\n\n"
  )

  if briefing:
    msg += f"📝 <b>Briefing Notes:</b>\n<i>{briefing}</i>\n\n"

  msg += f"🔗 <a href='https://trade-ideas.slimulator.net/app/'>View on askSlim</a>"
  return msg


def format_status_update_message(
    idea_id: str, old_item: dict, new_item: dict
) -> str:
  """Builds a notification when an existing trade idea is updated."""
  symbol = html.escape(str(new_item.get("symbol", "N/A")), quote=False)
  old_status = STATUS_MAP.get(old_item.get("status"), str(old_item.get("status")))
  new_status = STATUS_MAP.get(new_item.get("status"), str(new_item.get("status")))

  raw_date = new_item.get("creation_date", "")
  date_str = raw_date[:10] if raw_date else "N/A"
  period = PERIOD_MAP.get(new_item.get("market_outlook_period"), "N/A")
  price = new_item.get("current_price", "N/A")
  bias = BIAS_MAP.get(new_item.get("position_bias"), "N/A")

  outcome = OUTCOME_MAP.get(new_item.get("idea_outcome"), "N/A")
  result_text = html.escape(new_item.get("result_text", "").strip(), quote=False)

  msg = (
      f"🔔 <b>TRADE IDEA UPDATE: ${symbol}</b>\n\n"
      f"• <b>Status:</b> {old_status} ➔ <b>{new_status}</b>\n"
      f"• <b>Date:</b> {date_str}\n"
      f"• <b>Period:</b> {period}\n"
      f"• <b>Symbol:</b> <b>${symbol}</b>\n"
      f"• <b>Price at Analysis:</b> ${price}\n"
      f"• <b>Position Bias:</b> <b>{bias}</b>\n"
      f"• <b>Outcome:</b> <b>{outcome}</b>\n"
  )

  if result_text:
    msg += f"• <b>Result Commentary:</b>\n<i>{result_text}</i>\n\n"

  msg += f"🔗 <a href='https://trade-ideas.slimulator.net/app/'>View on askSlim</a>"
  return msg


def check_for_updates():
  """Checks askSlim for changes, sends notifications, and updates the local state."""
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"[{timestamp}] Checking askSlim for updates...")

  current_ideas = fetch_current_trade_ideas()
  if not current_ideas or not isinstance(current_ideas, dict):
    print(" [!] No trade data received from askSlim API. Skipping state update to protect data.")
    return

  previous_state = load_previous_state()

  if not previous_state:
    print(
        f" [+] Initializing state with {len(current_ideas)} existing trade"
        " ideas..."
    )
    save_current_state(current_ideas)
    print(" [+] Initial state saved. Monitoring is now active!")
    return

  new_count = 0
  update_count = 0

  # Check for brand new ideas
  for idea_id, item in current_ideas.items():
    if idea_id not in previous_state:
      new_count += 1
      print(f" [+] Found NEW trade idea: {item.get('symbol')} (ID: {idea_id})")
      msg = format_new_idea_message(idea_id, item)
      send_telegram_message(msg)
      time.sleep(1)

    else:
      # Check for status / result updates on existing ideas
      old_item = previous_state[idea_id]
      status_changed = old_item.get("status") != item.get("status")
      outcome_changed = (
          old_item.get("idea_outcome") != item.get("idea_outcome")
          and item.get("idea_outcome") is not None
      )
      result_changed = (
          old_item.get("result_text") != item.get("result_text")
          and item.get("result_text")
      )

      if status_changed or outcome_changed or result_changed:
        update_count += 1
        print(
            f" [~] Found UPDATE for trade idea: {item.get('symbol')} (ID:"
            f" {idea_id})"
        )
        msg = format_status_update_message(idea_id, old_item, item)
        send_telegram_message(msg)
        time.sleep(1)

  if new_count == 0 and update_count == 0:
    print(" [OK] No new updates found. Everything is up to date.")

  # Save updated state
  save_current_state(current_ideas)


def run_continuous_monitor(interval_seconds: int = CHECK_INTERVAL_SECONDS):
  """Runs the watcher continuously in a background loop."""
  print(
      f"[*] askSlim Telegram Notifier is running. Checking every"
      f" {interval_seconds}s..."
  )
  while True:
    try:
      check_for_updates()
    except Exception as e:
      print(f" [!] Unexpected error during check: {e}", file=sys.stderr)
    time.sleep(interval_seconds)


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description="askSlim Telegram Notifier")
  parser.add_argument(
      "--once",
      action="store_true",
      help="Run once and exit (ideal for Task Scheduler / Cron)",
  )
  parser.add_argument(
      "--interval",
      type=int,
      default=CHECK_INTERVAL_SECONDS,
      help="Check interval in seconds (default: 300)",
  )
  parser.add_argument(
      "--test",
      action="store_true",
      help="Send a test message to Telegram to verify credentials",
  )

  args = parser.parse_args()

  if args.test:
    test_msg = (
        "✅ <b>askSlim Telegram Notifier Connected!</b>\n\nYou will receive"
        " instant alerts here whenever a new trade idea is posted or updated."
    )
    success = send_telegram_message(test_msg)
    if success:
      print("[OK] Test message sent successfully!")
    else:
      print(
          "[!] Test message failed. Please check your TELEGRAM_BOT_TOKEN and"
          " TELEGRAM_CHAT_ID."
      )
  elif args.once:
    check_for_updates()
  else:
    run_continuous_monitor(args.interval)
