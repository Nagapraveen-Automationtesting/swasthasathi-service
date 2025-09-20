from datetime import datetime, date


def convert_date_to_datetime(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time())
