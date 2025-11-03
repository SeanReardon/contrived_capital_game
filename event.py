"""
Base Event class for timeline-based game events.
"""

from abc import ABC
from typing import Optional
from datetime import datetime


class Event(ABC):
    """
    Base class for all timeline events in the game.
    
    All events must have a date that can be converted to datetime for sorting.
    
    Attributes:
        event_date: The date string for this event (format may vary by subclass)
    """
    
    def __init__(self, event_date: Optional[str] = None):
        """
        Initialize an Event.
        
        Args:
            event_date: Date string for this event (format depends on subclass)
        """
        self.event_date = event_date
    
    def get_date_as_datetime(self) -> Optional[datetime]:
        """
        Convert the event_date string to a datetime object for sorting/comparison.
        
        Must be implemented by subclasses to handle their specific date formats.
        
        Returns:
            datetime object or None if date is invalid or not set
        """
        if not self.event_date:
            return None
        
        # Try common date formats
        formats = [
            "%Y-%m-%d",  # YYYY-MM-DD
            "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 with Z
            "%Y-%m-%dT%H:%M:%S",  # ISO 8601 without timezone
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(self.event_date, fmt)
            except ValueError:
                continue
        
        return None
    
    def __lt__(self, other):
        """Allow sorting events by date."""
        self_dt = self.get_date_as_datetime()
        other_dt = other.get_date_as_datetime() if hasattr(other, 'get_date_as_datetime') else None
        
        if self_dt is None and other_dt is None:
            return False
        if self_dt is None:
            return True  # None dates come first
        if other_dt is None:
            return False
        
        return self_dt < other_dt

