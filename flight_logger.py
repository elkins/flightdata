#!/usr/bin/env python3
"""
Flight Data Logger

Utilities for logging and filtering flight data from ADS-B Exchange.
"""

from typing import Iterator, Callable, Tuple, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import csv
import json
import numpy as np
import logging

from adsbexchange import FlightData, ADSBExchangeClient

__all__ = [
    'FlightLogger',
    'calculate_distance',
    'filter_by_radius',
    'filter_by_altitude',
    'log_to_csv',
    'log_to_json',
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Earth radius in meters
EARTH_RADIUS_M = 6371000


def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate great circle distance between two coordinates using Haversine formula.
    
    Args:
        coord1: (latitude, longitude) in degrees
        coord2: (latitude, longitude) in degrees
    
    Returns:
        Distance in meters
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    return EARTH_RADIUS_M * c


def filter_by_radius(
    flights: Iterator[FlightData],
    center: Tuple[float, float],
    radius_m: float
) -> Iterator[FlightData]:
    """
    Filter flights within a radius of a center point.
    
    Args:
        flights: Iterator of FlightData objects
        center: (latitude, longitude) center point
        radius_m: Radius in meters
    
    Yields:
        FlightData objects within radius
    """
    for flight in flights:
        if flight.lat is not None and flight.lon is not None:
            distance = calculate_distance(center, (flight.lat, flight.lon))
            if distance <= radius_m:
                yield flight


def filter_by_altitude(
    flights: Iterator[FlightData],
    min_alt: Optional[float] = None,
    max_alt: Optional[float] = None
) -> Iterator[FlightData]:
    """
    Filter flights by altitude range.
    
    Args:
        flights: Iterator of FlightData objects
        min_alt: Minimum altitude in meters (inclusive)
        max_alt: Maximum altitude in meters (inclusive)
    
    Yields:
        FlightData objects within altitude range
    """
    for flight in flights:
        if flight.altitude is not None:
            if min_alt is not None and flight.altitude < min_alt:
                continue
            if max_alt is not None and flight.altitude > max_alt:
                continue
            yield flight


def log_to_csv(
    file_path: Path,
    flights: Iterator[FlightData],
    append: bool = False,
    print_every: int = 100
) -> int:
    """
    Log flight data to CSV file.
    
    Args:
        file_path: Output CSV file path
        flights: Iterator of FlightData objects
        append: If True, append to existing file
        print_every: Print status every N records
    
    Returns:
        Number of records written
    """
    mode = 'a' if append else 'w'
    file_exists = file_path.exists() and append
    
    logger.info(f"Logging to CSV file: {file_path}")
    
    count = 0
    with open(file_path, mode, newline='', encoding='utf-8') as f:
        writer = None
        
        for flight in flights:
            # Initialize writer with first flight's keys
            if writer is None:
                fieldnames = list(flight.to_dict().keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
            
            # Convert datetime to ISO format string
            row = flight.to_dict()
            if row.get('timestamp'):
                row['timestamp'] = row['timestamp'].isoformat()
            
            writer.writerow(row)
            count += 1
            
            if count % print_every == 0:
                logger.info(f"  Wrote {count} records...")
    
    logger.info(f"Done! Total records written: {count}")
    return count


def log_to_json(
    file_path: Path,
    flights: Iterator[FlightData],
    indent: int = 2
) -> int:
    """
    Log flight data to JSON file.
    
    Args:
        file_path: Output JSON file path
        flights: Iterator of FlightData objects
        indent: JSON indentation level
    
    Returns:
        Number of records written
    """
    logger.info(f"Logging to JSON file: {file_path}")
    
    records = []
    for flight in flights:
        record = flight.to_dict()
        # Convert datetime to ISO format string
        if record.get('timestamp'):
            record['timestamp'] = record['timestamp'].isoformat()
        records.append(record)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=indent)
    
    count = len(records)
    logger.info(f"Done! Total records written: {count}")
    return count


class FlightLogger:
    """
    High-level flight data logger with filtering capabilities.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize flight logger.
        
        Args:
            api_key: ADS-B Exchange RapidAPI key (optional)
        """
        self.client = ADSBExchangeClient(api_key=api_key, use_rapid_api=bool(api_key))
        self.filters: List[Callable[[Iterator[FlightData]], Iterator[FlightData]]] = []
    
    def add_radius_filter(self, center: Tuple[float, float], radius_m: float) -> 'FlightLogger':
        """
        Add geographic radius filter.
        
        Args:
            center: (latitude, longitude) center point
            radius_m: Radius in meters
        
        Returns:
            Self for method chaining
        """
        self.filters.append(lambda flights: filter_by_radius(flights, center, radius_m))
        return self
    
    def add_altitude_filter(
        self,
        min_alt: Optional[float] = None,
        max_alt: Optional[float] = None
    ) -> 'FlightLogger':
        """
        Add altitude range filter.
        
        Args:
            min_alt: Minimum altitude in meters
            max_alt: Maximum altitude in meters
        
        Returns:
            Self for method chaining
        """
        self.filters.append(lambda flights: filter_by_altitude(flights, min_alt, max_alt))
        return self
    
    def add_custom_filter(
        self,
        filter_func: Callable[[FlightData], bool]
    ) -> 'FlightLogger':
        """
        Add custom filter function.
        
        Args:
            filter_func: Function that takes FlightData and returns bool
        
        Returns:
            Self for method chaining
        """
        self.filters.append(lambda flights: (f for f in flights if filter_func(f)))
        return self
    
    def clear_filters(self) -> 'FlightLogger':
        """
        Remove all filters.
        
        Returns:
            Self for method chaining
        """
        self.filters.clear()
        return self
    
    def get_flights(self) -> Iterator[FlightData]:
        """
        Get filtered flight data.
        
        Yields:
            FlightData objects after applying all filters
        """
        flights = self.client.get_all_flights()
        
        # Apply all filters in sequence
        for filter_func in self.filters:
            flights = filter_func(flights)
        
        yield from flights
    
    def log_to_csv(
        self,
        file_path: Path,
        append: bool = False,
        print_every: int = 100
    ) -> int:
        """
        Log filtered flights to CSV.
        
        Args:
            file_path: Output CSV file path
            append: If True, append to existing file
            print_every: Print status every N records
        
        Returns:
            Number of records written
        """
        return log_to_csv(file_path, self.get_flights(), append, print_every)
    
    def log_to_json(self, file_path: Path, indent: int = 2) -> int:
        """
        Log filtered flights to JSON.
        
        Args:
            file_path: Output JSON file path
            indent: JSON indentation level
        
        Returns:
            Number of records written
        """
        return log_to_json(file_path, self.get_flights(), indent)


def example_log_nearby_flights():
    """Example: Log flights near a specific location."""
    # Example: Flights near San Francisco
    center = (37.7749, -122.4194)  # SF coordinates
    radius_km = 100
    
    logger_obj = FlightLogger()
    logger_obj.add_radius_filter(center, radius_km * 1000)  # Convert km to meters
    
    output_file = Path('nearby_flights.csv')
    count = logger_obj.log_to_csv(output_file)
    
    print(f"\nLogged {count} flights within {radius_km}km of San Francisco")


def example_log_high_altitude():
    """Example: Log high-altitude flights."""
    min_altitude_ft = 35000
    min_altitude_m = min_altitude_ft * 0.3048  # Convert to meters
    
    logger_obj = FlightLogger()
    logger_obj.add_altitude_filter(min_alt=min_altitude_m)
    
    output_file = Path('high_altitude_flights.csv')
    count = logger_obj.log_to_csv(output_file)
    
    print(f"\nLogged {count} flights above {min_altitude_ft}ft")


def example_custom_filter():
    """Example: Log flights with custom filter (e.g., specific aircraft type)."""
    logger_obj = FlightLogger()
    
    # Filter for Boeing 747s (if type information is available)
    logger_obj.add_custom_filter(lambda f: bool(f.type and 'B74' in f.type))
    
    output_file = Path('b747_flights.json')
    count = logger_obj.log_to_json(output_file)
    
    print(f"\nLogged {count} Boeing 747 flights")


if __name__ == '__main__':
    print("Flight Logger Examples")
    print("=" * 80)
    
    try:
        example_log_nearby_flights()
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print("\nNote: Make sure you have a valid ADS-B Exchange API access.")
