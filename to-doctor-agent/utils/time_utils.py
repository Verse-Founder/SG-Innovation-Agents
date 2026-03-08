"""
utils/time_utils.py
时区工具 — 新加坡时区
"""
from datetime import datetime, timezone, timedelta

SGT = timezone(timedelta(hours=8))


def now_sgt() -> datetime:
    return datetime.now(SGT)


def format_date_sgt(dt: datetime) -> str:
    return dt.astimezone(SGT).strftime("%Y-%m-%d")


def format_datetime_sgt(dt: datetime) -> str:
    return dt.astimezone(SGT).strftime("%Y-%m-%d %H:%M")
