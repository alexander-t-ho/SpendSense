"""Utility functions for insights computation."""

from datetime import datetime, timedelta
from typing import Tuple
from dateutil.relativedelta import relativedelta


def get_week_start(date: datetime) -> datetime:
    """Get the start of the week (Monday) for a given date.
    
    Args:
        date: The date to get the week start for
    
    Returns:
        datetime: Start of the week (Monday 00:00:00)
    """
    # Get Monday of the week (weekday() returns 0 for Monday, 6 for Sunday)
    days_since_monday = date.weekday()
    return (date - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)


def get_week_end(date: datetime) -> datetime:
    """Get the end of the week (Sunday) for a given date.
    
    Args:
        date: The date to get the week end for
    
    Returns:
        datetime: End of the week (Sunday 23:59:59)
    """
    week_start = get_week_start(date)
    return week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)


def get_month_start(date: datetime) -> datetime:
    """Get the start of the month for a given date.
    
    Args:
        date: The date to get the month start for
    
    Returns:
        datetime: Start of the month (1st day 00:00:00)
    """
    return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_month_end(date: datetime) -> datetime:
    """Get the end of the month for a given date.
    
    Args:
        date: The date to get the month end for
    
    Returns:
        datetime: End of the month (last day 23:59:59)
    """
    # Get first day of next month, then subtract 1 second
    next_month = date.replace(day=1) + relativedelta(months=1)
    return next_month - timedelta(seconds=1)


def get_months_range(start_date: datetime, num_months: int) -> list[Tuple[datetime, datetime]]:
    """Get a list of month ranges (start, end) for the specified number of months.
    
    Args:
        start_date: The starting date
        num_months: Number of months to get
    
    Returns:
        List of tuples (month_start, month_end) for each month
    """
    months = []
    current_date = get_month_start(start_date)
    
    for _ in range(num_months):
        month_start = current_date
        month_end = get_month_end(current_date)
        months.append((month_start, month_end))
        # Move to next month
        current_date = current_date + relativedelta(months=1)
    
    return months


def format_currency(amount: float) -> str:
    """Format amount as currency string.
    
    Args:
        amount: The amount to format
    
    Returns:
        str: Formatted currency string (e.g., "$1,234.56")
    """
    return f"${amount:,.2f}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values.
    
    Args:
        old_value: The old/base value
        new_value: The new value
    
    Returns:
        float: Percentage change (can be negative)
    """
    if old_value == 0:
        return 0.0 if new_value == 0 else 100.0
    return ((new_value - old_value) / old_value) * 100

