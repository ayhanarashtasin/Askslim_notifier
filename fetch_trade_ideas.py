import json
import ssl
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


def fetch_trade_ideas(
    output_json: str = "trade_ideas.json",
    output_raw_json: str = "trade_ideas_raw.json",
    output_csv: str = "trade_ideas.csv",
):
  """Fetches trade ideas from askSlim (trade-ideas.slimulator.net) and exports them into JSON and CSV formats."""
  url = "https://trade-ideas.slimulator.net/ti/trade_idea"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json, text/plain, */*",
      "Referer": "https://trade-ideas.slimulator.net/app/",
  }

  print(f"Fetching trade ideas from {url}...")
  ctx = ssl.create_default_context()
  req = urllib.request.Request(url, headers=headers)

  try:
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
      raw_text = response.read().decode("utf-8")
      raw_json = json.loads(raw_text)
  except Exception as e:
    print(f"Error fetching data: {e}", file=sys.stderr)
    raise

  # Save raw JSON
  if output_raw_json:
    raw_path = Path(output_raw_json)
    with open(raw_path, "w", encoding="utf-8") as f:
      json.dump(raw_json, f, indent=2, ensure_ascii=False)
    print(f"Saved raw API response to: {raw_path.resolve()}")

  ideas_dict = raw_json.get("data", {})
  print(f"Parsing {len(ideas_dict)} trade ideas...")

  # Mappings based on askSlim application definitions
  status_map = {1: "Inactive", 2: "Active"}

  period_map = {
      1: "Near-Term (1-5 days)",
      2: "Short-Term (1-3 weeks)",
      3: "Intermediate-Term (3-8 weeks)",
      4: "Long-Term (2-6 months)",
      5: "Intraday",
  }

  bias_map = {1: "Short", 2: "Long"}

  directional_bias_map = {
      0: "None",
      1: "Bearish",
      2: "Slightly Bearish",
      3: "Neutral",
      4: "Slightly Bullish",
      5: "Bullish",
  }

  outcome_map = {
      0: "Pending / Inactive",
      1: "Re-evaluation Level Hit",
      2: "Target Zone Reached",
      3: "Target Zone Reached (Early / Missed Entry)",
  }

  parsed_records = []

  for idea_id, item in ideas_dict.items():
    # 1. Entry ranges
    entry_ranges = item.get("entry_ranges", [])
    entry_range_display = (
        ", ".join([
            f"{r[0]} - {r[1]}" if len(r) == 2 else str(r) for r in entry_ranges
        ])
        if entry_ranges
        else None
    )

    # 2. Target ranges
    target_ranges = item.get("target_ranges", [])
    target_range_display = (
        ", ".join([
            f"{r[0]} - {r[1]}" if len(r) == 2 else str(r)
            for r in target_ranges
        ])
        if target_ranges
        else None
    )

    # 3. Re-evaluation level
    re_eval_num = item.get("re_eval_point_number")
    re_eval_cond = item.get("re_eval_point_condition")
    cond_symbol = (
        "< " if re_eval_cond == -1 else ("> " if re_eval_cond == 1 else "")
    )
    re_eval_display = (
        f"{cond_symbol}{re_eval_num}" if re_eval_num is not None else None
    )

    # Status
    status_code = item.get("status")
    status_label = status_map.get(status_code, str(status_code))

    # Period
    period_code = item.get("market_outlook_period")
    period_label = period_map.get(period_code, str(period_code))

    # Bias
    bias_code = item.get("position_bias")
    bias_label = bias_map.get(bias_code, str(bias_code))

    # Directional Bias
    dir_bias_code = item.get("directional_bias", 0)
    dir_bias_label = directional_bias_map.get(
        dir_bias_code, str(dir_bias_code)
    )

    # Outcome
    outcome_code = item.get("idea_outcome")
    outcome_label = (
        outcome_map.get(outcome_code, str(outcome_code))
        if outcome_code is not None
        else None
    )

    record = {
        "id": idea_id,
        "symbol": item.get("symbol"),
        "status": status_label,
        "status_code": status_code,
        "date": item.get("creation_date"),
        "period": period_label,
        "period_code": period_code,
        "price_at_analysis": item.get("current_price"),
        "position_bias": bias_label,
        "position_bias_code": bias_code,
        "directional_bias": dir_bias_label,
        "entry_range": entry_range_display,
        "entry_ranges_raw": entry_ranges,
        "target_range": target_range_display,
        "target_ranges_raw": target_ranges,
        "re_evaluation_level": re_eval_display,
        "re_evaluation_level_number": re_eval_num,
        "re_evaluation_condition": (
            "below"
            if re_eval_cond == -1
            else ("above" if re_eval_cond == 1 else None)
        ),
        "briefing_notes": item.get("briefing"),
        "result_text": item.get("result_text"),
        "outcome": outcome_label,
        "outcome_code": outcome_code,
        "inactive_datetime": item.get("inactive_datetime"),
    }

    parsed_records.append(record)

  # Sort records by date descending (newest first)
  def parse_date(rec):
    dt_str = rec.get("date")
    if not dt_str:
      return datetime.min
    try:
      # handle ISO timestamp
      return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
      return datetime.min

  parsed_records.sort(key=parse_date, reverse=True)

  # Save formatted JSON
  if output_json:
    json_path = Path(output_json)
    with open(json_path, "w", encoding="utf-8") as f:
      json.dump(parsed_records, f, indent=2, ensure_ascii=False)
    print(f"Saved formatted JSON ({len(parsed_records)} records) to: {json_path.resolve()}")

  # Save CSV for easy viewing in Excel or data tools
  if output_csv:
    try:
      import csv

      csv_path = Path(output_csv)
      fieldnames = [
          "id",
          "symbol",
          "status",
          "date",
          "period",
          "price_at_analysis",
          "position_bias",
          "directional_bias",
          "entry_range",
          "target_range",
          "re_evaluation_level",
          "briefing_notes",
          "result_text",
          "outcome",
          "inactive_datetime",
      ]
      with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in parsed_records:
          writer.writerow(row)
      print(f"Saved CSV export to: {csv_path.resolve()}")
    except Exception as ex:
      print(f"Could not export CSV: {ex}")

  return parsed_records


if __name__ == "__main__":
  fetch_trade_ideas(
      output_json="trade_ideas.json",
      output_raw_json="trade_ideas_raw.json",
      output_csv="trade_ideas.csv",
  )
