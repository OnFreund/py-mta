"""Tests for SubwayFeed class."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from google.transit import gtfs_realtime_pb2
import pytest

from pymta import Arrival, MTAFeedError, SubwayFeed


def test_init_valid_feed_id():
    """Test initialization with valid feed ID."""
    feed = SubwayFeed(feed_id="N")
    assert feed.feed_id == "N"
    assert feed.timeout == 30


def test_init_invalid_feed_id():
    """Test initialization with invalid feed ID."""
    with pytest.raises(ValueError, match="Invalid feed_id"):
        SubwayFeed(feed_id="INVALID")


def test_get_feed_id_for_route():
    """Test getting feed ID for a route."""
    assert SubwayFeed.get_feed_id_for_route("Q") == "N"
    assert SubwayFeed.get_feed_id_for_route("1") == "1"
    assert SubwayFeed.get_feed_id_for_route("F") == "B"


def test_get_feed_id_for_invalid_route():
    """Test getting feed ID for invalid route."""
    with pytest.raises(ValueError, match="Invalid route_id"):
        SubwayFeed.get_feed_id_for_route("INVALID")


@patch("pymta.requests.get")
def test_get_arrivals_success(mock_get):
    """Test getting arrivals successfully."""
    # Create a GTFS-RT FeedMessage
    feed_message = gtfs_realtime_pb2.FeedMessage()
    feed_message.header.gtfs_realtime_version = "2.0"
    feed_message.header.timestamp = int(datetime.now(timezone.utc).timestamp())

    # Create a trip update entity
    entity = feed_message.entity.add()
    entity.id = "trip1"

    trip_update = entity.trip_update
    trip_update.trip.route_id = "Q"

    # Add stop time update for the future
    stop_time = trip_update.stop_time_update.add()
    stop_time.stop_id = "B08S"
    future_time = datetime.now(timezone.utc).timestamp() + 300  # 5 minutes from now
    stop_time.arrival.time = int(future_time)

    # Mock response
    mock_response = Mock()
    mock_response.content = feed_message.SerializeToString()
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Test
    feed = SubwayFeed(feed_id="N")
    arrivals = feed.get_arrivals(route_id="Q", stop_id="B08S")

    assert len(arrivals) == 1
    assert arrivals[0].route_id == "Q"
    assert arrivals[0].stop_id == "B08S"
    assert arrivals[0].destination == "Q train"
    assert isinstance(arrivals[0].arrival_time, datetime)


@patch("pymta.requests.get")
def test_get_arrivals_filters_past_arrivals(mock_get):
    """Test that past arrivals are filtered out."""
    # Create a GTFS-RT FeedMessage
    feed_message = gtfs_realtime_pb2.FeedMessage()
    feed_message.header.gtfs_realtime_version = "2.0"
    feed_message.header.timestamp = int(datetime.now(timezone.utc).timestamp())

    # Create trip with past arrival
    entity = feed_message.entity.add()
    entity.id = "trip1"
    trip_update = entity.trip_update
    trip_update.trip.route_id = "Q"

    stop_time = trip_update.stop_time_update.add()
    stop_time.stop_id = "B08S"
    past_time = datetime.now(timezone.utc).timestamp() - 300  # 5 minutes ago
    stop_time.arrival.time = int(past_time)

    # Mock response
    mock_response = Mock()
    mock_response.content = feed_message.SerializeToString()
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Test
    feed = SubwayFeed(feed_id="N")
    arrivals = feed.get_arrivals(route_id="Q", stop_id="B08S")

    assert len(arrivals) == 0


@patch("pymta.requests.get")
def test_get_arrivals_max_arrivals(mock_get):
    """Test max_arrivals parameter."""
    # Create a GTFS-RT FeedMessage with 5 arrivals
    feed_message = gtfs_realtime_pb2.FeedMessage()
    feed_message.header.gtfs_realtime_version = "2.0"
    feed_message.header.timestamp = int(datetime.now(timezone.utc).timestamp())

    for i in range(5):
        entity = feed_message.entity.add()
        entity.id = f"trip{i}"
        trip_update = entity.trip_update
        trip_update.trip.route_id = "Q"

        stop_time = trip_update.stop_time_update.add()
        stop_time.stop_id = "B08S"
        future_time = datetime.now(timezone.utc).timestamp() + (i + 1) * 60
        stop_time.arrival.time = int(future_time)

    # Mock response
    mock_response = Mock()
    mock_response.content = feed_message.SerializeToString()
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Test
    feed = SubwayFeed(feed_id="N")
    arrivals = feed.get_arrivals(route_id="Q", stop_id="B08S", max_arrivals=3)

    assert len(arrivals) == 3


@patch("pymta.requests.get")
def test_get_arrivals_network_error(mock_get):
    """Test handling of network errors."""
    import requests.exceptions
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    feed = SubwayFeed(feed_id="N")
    with pytest.raises(MTAFeedError, match="Error fetching GTFS-RT feed"):
        feed.get_arrivals(route_id="Q", stop_id="B08S")


def test_arrival_sorting():
    """Test that Arrival objects can be sorted by time."""
    now = datetime.now(timezone.utc)
    arrival1 = Arrival(
        arrival_time=now,
        route_id="Q",
        stop_id="B08S",
        destination="Coney Island",
    )
    arrival2 = Arrival(
        arrival_time=now + timedelta(minutes=5),
        route_id="Q",
        stop_id="B08S",
        destination="Coney Island",
    )

    arrivals = [arrival2, arrival1]
    arrivals.sort()

    assert arrivals[0] == arrival1
    assert arrivals[1] == arrival2
