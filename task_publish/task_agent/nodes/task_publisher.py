from datetime import date, datetime, time

def end_of_today() -> datetime:
    """Returns 23:59:59 of the current calendar day (server local time or UTC).
    Use a consistent timezone across all services.
    """
    return datetime.combine(date.today(), time(23, 59, 59))
