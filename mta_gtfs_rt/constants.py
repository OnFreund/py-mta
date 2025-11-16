"""Constants for MTA GTFS-RT library."""

# MTA GTFS-RT feed URLs
FEED_URLS = {
    "1": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "A": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "N": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "B": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "L": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "SI": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
    "G": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "J": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "7": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-7",
}

# Mapping of subway lines to feed IDs
LINE_TO_FEED = {
    # Feed 1: 1, 2, 3, 4, 5, 6, GS (Grand Central Shuttle)
    "1": "1",
    "2": "1",
    "3": "1",
    "4": "1",
    "5": "1",
    "6": "1",
    "GS": "1",
    # Feed A: A, C, E, H (Rockaway Shuttle), FS (Franklin Av Shuttle)
    "A": "A",
    "C": "A",
    "E": "A",
    "H": "A",
    "FS": "A",
    # Feed N: N, Q, R, W
    "N": "N",
    "Q": "N",
    "R": "N",
    "W": "N",
    # Feed B: B, D, F, M
    "B": "B",
    "D": "B",
    "F": "B",
    "M": "B",
    # Feed L: L
    "L": "L",
    # Feed SI: SIR (Staten Island Railway)
    "SI": "SI",
    # Feed G: G
    "G": "G",
    # Feed J: J, Z
    "J": "J",
    "Z": "J",
    # Feed 7: 7, 7X (7 Express)
    "7": "7",
}
