import re
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def parse_date_range(text: str) -> dict:
    text = text.lower().strip()
    today = date.today()

    # last K days
    match = re.search(r"last (\d+) days", text)
    if match:
        days = int(match.group(1))
        return {
            "start_date": (today - timedelta(days=days)).strftime("%Y-%m-%d"),
            "end_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
        }

    # previous K days
    match = re.search(r"previous (\d+) days", text)
    if match:
        days = int(match.group(1))
        return {
            "start_date": (today - timedelta(days=2 * days)).strftime("%Y-%m-%d"),
            "end_date": (today - timedelta(days=days + 1)).strftime("%Y-%m-%d"),
        }

    if "last month" in text:
        start = today.replace(day=1) - relativedelta(months=1)
        end = today.replace(day=1) - timedelta(days=1)
        return {
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
        }

    if "today" in text:
        return {
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
        }

    # fallback (GA4 accepts relative strings)
    return {
        "start_date": "7daysAgo",
        "end_date": "today"
    }
