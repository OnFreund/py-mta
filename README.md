# py-nymta

Python library for accessing MTA (Metropolitan Transportation Authority) real-time transit data for NYC.

## Features

- Simple, clean API for accessing MTA subway real-time arrival data
- Support for all MTA subway lines
- Compatible with protobuf 6.x
- Type hints for better IDE support
- Extensible design for future bus API support

## Installation

```bash
pip install py-nymta
```

## Usage

### Basic Example

```python
from pymta import SubwayFeed

# Create a feed for the N/Q/R/W lines
feed = SubwayFeed(feed_id="N")

# Get the next 3 arrivals for the Q line at station B08S (southbound)
arrivals = feed.get_arrivals(route_id="Q", stop_id="B08S")

for arrival in arrivals:
    print(f"Route {arrival.route_id} to {arrival.destination}")
    print(f"  Arrives at: {arrival.arrival_time}")
    print(f"  Stop ID: {arrival.stop_id}")
```

### Finding the Feed ID for a Route

```python
from pymta import SubwayFeed

# Get the feed ID for a specific route
feed_id = SubwayFeed.get_feed_id_for_route("Q")
print(f"The Q line is in feed: {feed_id}")  # Output: N

# Create a feed using the discovered feed_id
feed = SubwayFeed(feed_id=feed_id)
```

### Custom Timeout and Max Arrivals

```python
from pymta import SubwayFeed

# Create a feed with custom timeout
feed = SubwayFeed(feed_id="1", timeout=60)

# Get up to 5 arrivals instead of the default 3
arrivals = feed.get_arrivals(
    route_id="1",
    stop_id="127N",  # Times Square - 42 St (northbound)
    max_arrivals=5
)
```

### Error Handling

```python
from pymta import SubwayFeed, MTAFeedError

feed = SubwayFeed(feed_id="A")

try:
    arrivals = feed.get_arrivals(route_id="A", stop_id="A42N")
except MTAFeedError as e:
    print(f"Error fetching arrivals: {e}")
```

## Station IDs and Directions

MTA station IDs include a direction suffix:
- `N` suffix: Northbound/Uptown direction
- `S` suffix: Southbound/Downtown direction

For example:
- `127N`: Times Square - 42 St (northbound)
- `127S`: Times Square - 42 St (southbound)
- `B08N`: DeKalb Av (northbound)
- `B08S`: DeKalb Av (southbound)

**Note**: These are MTA designations and don't always correspond to geographic north/south.

## Feed IDs

The MTA groups subway lines into feeds:

| Feed ID | Lines |
|---------|-------|
| `1` | 1, 2, 3, 4, 5, 6, GS |
| `A` | A, C, E, H, FS |
| `N` | N, Q, R, W |
| `B` | B, D, F, M |
| `L` | L |
| `SI` | SIR (Staten Island Railway) |
| `G` | G |
| `J` | J, Z |
| `7` | 7, 7X |

## API Reference

### `SubwayFeed`

Main class for accessing subway GTFS-RT feeds.

#### `__init__(feed_id: str, timeout: int = 30)`

Initialize the subway feed.

**Parameters:**
- `feed_id`: The feed ID (e.g., '1', 'A', 'N', 'B', 'L', 'SI', 'G', 'J', '7')
- `timeout`: Request timeout in seconds (default: 30)

**Raises:**
- `ValueError`: If feed_id is not valid

#### `get_arrivals(route_id: str, stop_id: str, max_arrivals: int = 3) -> list[Arrival]`

Get upcoming train arrivals for a specific route and stop.

**Parameters:**
- `route_id`: The route/line ID (e.g., '1', 'A', 'Q')
- `stop_id`: The stop ID including direction (e.g., '127N', 'B08S')
- `max_arrivals`: Maximum number of arrivals to return (default: 3)

**Returns:**
- List of `Arrival` objects sorted by arrival time

**Raises:**
- `MTAFeedError`: If feed cannot be fetched or parsed

#### `get_feed_id_for_route(route_id: str) -> str` (static method)

Get the feed ID for a given route.

**Parameters:**
- `route_id`: The route/line ID (e.g., '1', 'A', 'Q')

**Returns:**
- The feed ID for the route

**Raises:**
- `ValueError`: If route_id is not valid

### `Arrival`

Dataclass representing a single train arrival.

**Attributes:**
- `arrival_time` (datetime): The datetime when the train will arrive (UTC)
- `route_id` (str): The route/line ID (e.g., '1', 'A', 'Q')
- `stop_id` (str): The stop ID including direction (e.g., '127N', 'B08S')
- `destination` (str): The trip headsign/destination

### Exceptions

- `MTAError`: Base exception for the library
- `MTAFeedError`: Raised when feed cannot be fetched or parsed

## Development

### Setup

```bash
git clone https://github.com/OnFreund/py-nymta.git
cd py-nymta
pip install -e .
```

### Running Tests

```bash
pytest
```

## License

MIT License - see LICENSE file for details.

## Credits

This library uses the official GTFS-RT protocol buffers from Google's [gtfs-realtime-bindings](https://github.com/MobilityData/gtfs-realtime-bindings) package.

MTA data is provided by the [Metropolitan Transportation Authority](https://www.mta.info/).
