"""Tests for SubwayFeed class."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

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


@pytest.mark.asyncio
async def test_get_arrivals_success():
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
    mock_response = AsyncMock()
    mock_response.read = AsyncMock(return_value=feed_message.SerializeToString())
    mock_response.raise_for_status = Mock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Mock session
    mock_session = Mock()
    mock_session.get = Mock(return_value=mock_response)

    # Test
    feed = SubwayFeed(feed_id="N", session=mock_session)
    arrivals = await feed.get_arrivals(route_id="Q", stop_id="B08S")

    assert len(arrivals) == 1
    assert arrivals[0].route_id == "Q"
    assert arrivals[0].stop_id == "B08S"
    assert arrivals[0].destination == "Q train"
    assert isinstance(arrivals[0].arrival_time, datetime)


@pytest.mark.asyncio
async def test_get_arrivals_filters_past_arrivals():
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
    mock_response = AsyncMock()
    mock_response.read = AsyncMock(return_value=feed_message.SerializeToString())
    mock_response.raise_for_status = Mock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Mock session
    mock_session = Mock()
    mock_session.get = Mock(return_value=mock_response)

    # Test
    feed = SubwayFeed(feed_id="N", session=mock_session)
    arrivals = await feed.get_arrivals(route_id="Q", stop_id="B08S")

    assert len(arrivals) == 0


@pytest.mark.asyncio
async def test_get_arrivals_max_arrivals():
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
    mock_response = AsyncMock()
    mock_response.read = AsyncMock(return_value=feed_message.SerializeToString())
    mock_response.raise_for_status = Mock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Mock session
    mock_session = Mock()
    mock_session.get = Mock(return_value=mock_response)

    # Test
    feed = SubwayFeed(feed_id="N", session=mock_session)
    arrivals = await feed.get_arrivals(route_id="Q", stop_id="B08S", max_arrivals=3)

    assert len(arrivals) == 3


@pytest.mark.asyncio
async def test_get_arrivals_network_error():
    """Test handling of network errors."""
    import aiohttp

    # Mock session that raises an error when entering context
    mock_response = Mock()
    mock_response.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Network error"))
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = Mock()
    mock_session.get = Mock(return_value=mock_response)

    feed = SubwayFeed(feed_id="N", session=mock_session)
    with pytest.raises(MTAFeedError, match="Error fetching GTFS-RT feed"):
        await feed.get_arrivals(route_id="Q", stop_id="B08S")


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


@pytest.mark.asyncio
async def test_get_active_stops():
    """Test getting active stops for a route."""
    # Create a GTFS-RT FeedMessage with multiple stops
    feed_message = gtfs_realtime_pb2.FeedMessage()
    feed_message.header.gtfs_realtime_version = "2.0"
    feed_message.header.timestamp = int(datetime.now(timezone.utc).timestamp())

    # Add trip with multiple stops
    entity = feed_message.entity.add()
    entity.id = "trip1"
    trip_update = entity.trip_update
    trip_update.trip.route_id = "Q"

    # Stop 1 - with future arrival
    stop_time1 = trip_update.stop_time_update.add()
    stop_time1.stop_id = "B08N"
    stop_time1.arrival.time = int(datetime.now(timezone.utc).timestamp() + 300)

    # Stop 2 - with future arrival
    stop_time2 = trip_update.stop_time_update.add()
    stop_time2.stop_id = "B08S"
    stop_time2.arrival.time = int(datetime.now(timezone.utc).timestamp() + 600)

    # Add another trip with a different stop
    entity2 = feed_message.entity.add()
    entity2.id = "trip2"
    trip_update2 = entity2.trip_update
    trip_update2.trip.route_id = "Q"

    stop_time3 = trip_update2.stop_time_update.add()
    stop_time3.stop_id = "D20N"
    stop_time3.arrival.time = int(datetime.now(timezone.utc).timestamp() + 900)

    # Mock response
    mock_response = AsyncMock()
    mock_response.read = AsyncMock(return_value=feed_message.SerializeToString())
    mock_response.raise_for_status = Mock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Mock session
    mock_session = Mock()
    mock_session.get = Mock(return_value=mock_response)

    # Test
    feed = SubwayFeed(feed_id="N", session=mock_session)
    stops = await feed.get_active_stops(route_id="Q")

    assert len(stops) == 3
    assert stops[0]["stop_id"] == "B08N"
    assert stops[1]["stop_id"] == "B08S"
    assert stops[2]["stop_id"] == "D20N"
    assert all(stop["has_arrivals"] for stop in stops)
    assert all(stop["stop_name"] is None for stop in stops)
