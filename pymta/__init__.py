"""py-nymta library for accessing NYC transit real-time data."""

from datetime import datetime, timezone

from google.protobuf.message import DecodeError
from google.transit import gtfs_realtime_pb2
import requests

from .constants import FEED_URLS, LINE_TO_FEED
from .models import Arrival

__version__ = "0.1.1"
__all__ = ["SubwayFeed", "Arrival", "MTAError", "MTAFeedError"]


class MTAError(Exception):
    """Base exception for py-nymta library."""


class MTAFeedError(MTAError):
    """Exception raised when feed cannot be fetched or parsed."""


class SubwayFeed:
    """Interface for MTA subway real-time feeds."""

    def __init__(self, feed_id: str, timeout: int = 30) -> None:
        """Initialize the subway feed.

        Args:
            feed_id: The feed ID (e.g., '1', 'A', 'N', 'B', 'L', 'SI', 'G', 'J', '7').
            timeout: Request timeout in seconds (default: 30).

        Raises:
            ValueError: If feed_id is not valid.
        """
        if feed_id not in FEED_URLS:
            raise ValueError(
                f"Invalid feed_id '{feed_id}'. "
                f"Must be one of: {', '.join(FEED_URLS.keys())}"
            )

        self.feed_id = feed_id
        self.feed_url = FEED_URLS[feed_id]
        self.timeout = timeout

    def get_arrivals(
        self,
        route_id: str,
        stop_id: str,
        max_arrivals: int = 3,
    ) -> list[Arrival]:
        """Get upcoming train arrivals for a specific route and stop.

        Args:
            route_id: The route/line ID (e.g., '1', 'A', 'Q').
            stop_id: The stop ID including direction (e.g., '127N', 'B08S').
            max_arrivals: Maximum number of arrivals to return (default: 3).

        Returns:
            List of Arrival objects sorted by arrival time.

        Raises:
            MTAFeedError: If feed cannot be fetched or parsed.
        """
        # Fetch the GTFS-RT feed
        try:
            response = requests.get(self.feed_url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            raise MTAFeedError(f"Error fetching GTFS-RT feed: {err}") from err

        # Parse the protobuf
        feed = gtfs_realtime_pb2.FeedMessage()
        try:
            feed.ParseFromString(response.content)
        except DecodeError as err:
            raise MTAFeedError(f"Error parsing GTFS-RT feed: {err}") from err

        arrivals: list[Arrival] = []
        now = datetime.now(timezone.utc)

        # Get base station ID (without direction suffix) for flexible matching
        base_station_id = stop_id.rstrip("NS")
        direction_suffix = stop_id[-1] if stop_id and stop_id[-1] in ("N", "S") else ""

        # Process each entity in the feed
        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            trip_update = entity.trip_update
            trip = trip_update.trip

            # Filter by route/line
            if trip.route_id != route_id:
                continue

            # Process stop time updates
            for stop_time_update in trip_update.stop_time_update:
                current_stop_id = stop_time_update.stop_id

                # Match on base station ID and direction suffix
                if (
                    current_stop_id
                    and current_stop_id.startswith(base_station_id)
                    and current_stop_id.endswith(direction_suffix)
                    and stop_time_update.HasField("arrival")
                ):
                    # Get the arrival time
                    arrival_timestamp = stop_time_update.arrival.time
                    arrival_time = datetime.fromtimestamp(
                        arrival_timestamp, tz=timezone.utc
                    )

                    # Only include future arrivals
                    if arrival_time > now:
                        # Get trip headsign if available
                        destination = "Unknown"
                        if stop_time_update.HasField("stop_headsign"):
                            destination = stop_time_update.stop_headsign

                        arrivals.append(
                            Arrival(
                                arrival_time=arrival_time,
                                route_id=trip.route_id,
                                stop_id=current_stop_id,
                                destination=destination,
                            )
                        )

        # Sort by arrival time and limit to max_arrivals
        arrivals.sort()
        return arrivals[:max_arrivals]

    @staticmethod
    def get_feed_id_for_route(route_id: str) -> str:
        """Get the feed ID for a given route.

        Args:
            route_id: The route/line ID (e.g., '1', 'A', 'Q').

        Returns:
            The feed ID for the route.

        Raises:
            ValueError: If route_id is not valid.
        """
        if route_id not in LINE_TO_FEED:
            raise ValueError(
                f"Invalid route_id '{route_id}'. "
                f"Must be one of: {', '.join(LINE_TO_FEED.keys())}"
            )
        return LINE_TO_FEED[route_id]
