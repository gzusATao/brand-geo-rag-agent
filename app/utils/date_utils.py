from datetime import datetime, timedelta, timezone


def timestamp():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
