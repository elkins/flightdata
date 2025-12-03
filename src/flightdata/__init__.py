"""
FlightData - Modern Python library for ADS-B Exchange flight tracking

This package provides a modern Python interface to the ADS-B Exchange API,
offering real-time flight tracking data with comprehensive filtering and logging capabilities.
"""

from flightdata.adsbexchange import (
    FlightData,
    ADSBExchangeClient,
    get_flights_all,
    get_flight_by_icao,
    get_flights_by_bounds,
)
from flightdata.flight_logger import FlightLogger, calculate_distance
from flightdata.config import Config

__version__ = "2.0.0"
__all__ = [
    "FlightData",
    "ADSBExchangeClient",
    "FlightLogger",
    "Config",
    "get_flights_all",
    "get_flight_by_icao",
    "get_flights_by_bounds",
    "calculate_distance",
]
