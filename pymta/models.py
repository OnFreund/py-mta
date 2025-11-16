"""Data models for MTA GTFS-RT library."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Arrival:
    """Represents a single train arrival."""

    arrival_time: datetime
    """The datetime when the train will arrive."""

    route_id: str
    """The route/line ID (e.g., '1', 'A', 'Q')."""

    stop_id: str
    """The stop ID including direction (e.g., '127N', 'B08S')."""

    destination: str
    """The trip headsign/destination (e.g., 'Van Cortlandt Park - 242 St')."""

    def __lt__(self, other: "Arrival") -> bool:
        """Allow sorting by arrival time."""
        return self.arrival_time < other.arrival_time
