#!/usr/bin/env python3
"""
ADS-B Exchange API Client

A modern Python 3 library to fetch flight data from ADS-B Exchange,
an open-source collaborative flight tracking platform.
"""

from typing import Iterator, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass, asdict
import logging

__all__ = [
    'FlightData',
    'ADSBExchangeClient',
    'get_flights_by_bounds',
    'get_flights_all',
    'get_flight_by_icao',
]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Unit conversion constants
CONV_KT_TO_MPS = 0.514444444
CONV_FPM_TO_MPS = 5.08e-3
CONV_FT_TO_M = 0.3048


@dataclass
class FlightData:
    """Represents a single flight record from ADS-B Exchange."""
    
    icao: str
    flight: Optional[str] = None
    registration: Optional[str] = None
    type: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    altitude: Optional[float] = None  # meters
    speed: Optional[float] = None  # m/s
    track: Optional[float] = None  # degrees
    vert_rate: Optional[float] = None  # m/s
    squawk: Optional[str] = None
    timestamp: Optional[datetime] = None
    category: Optional[str] = None
    emergency: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any], convert_si: bool = True) -> 'FlightData':
        """
        Create FlightData from ADS-B Exchange API response.
        
        Args:
            data: Raw API response dictionary
            convert_si: If True, convert units to SI (meters, m/s)
        
        Returns:
            FlightData instance
        """
        # Handle timestamp
        timestamp = None
        if 'now' in data:
            timestamp = datetime.fromtimestamp(data['now'])
        elif 'postime' in data:
            timestamp = datetime.fromtimestamp(data['postime'] / 1000)  # milliseconds to seconds
        
        # Extract and optionally convert values
        altitude = data.get('alt_baro') or data.get('alt_geom')
        if altitude and convert_si:
            altitude = altitude * CONV_FT_TO_M
        
        speed = data.get('gs')  # ground speed in knots
        if speed and convert_si:
            speed = speed * CONV_KT_TO_MPS
        
        vert_rate = data.get('baro_rate') or data.get('geom_rate')  # ft/min
        if vert_rate and convert_si:
            vert_rate = vert_rate * CONV_FPM_TO_MPS
        
        return cls(
            icao=data.get('hex', '').upper(),
            flight=data.get('flight', '').strip() or None,
            registration=data.get('r') or data.get('registration'),
            type=data.get('t') or data.get('type'),
            lat=data.get('lat'),
            lon=data.get('lon'),
            altitude=altitude,
            speed=speed,
            track=data.get('track'),
            vert_rate=vert_rate,
            squawk=data.get('squawk'),
            timestamp=timestamp,
            category=data.get('category'),
            emergency=data.get('emergency'),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FlightData to dictionary."""
        return asdict(self)


class ADSBExchangeClient:
    """
    Client for interacting with ADS-B Exchange API.
    
    ADS-B Exchange offers multiple API endpoints:
    - v2 API: Real-time data (requires API key for higher limits)
    - RapidAPI: Commercial access with higher rate limits
    """
    
    # API v2 endpoints (free tier available)
    BASE_URL_V2 = "https://adsbexchange-com1.p.rapidapi.com/v2"
    
    # Alternative: Direct API (may have rate limits)
    BASE_URL_DIRECT = "https://globe.adsbexchange.com/data/aircraft.json"
    
    def __init__(self, api_key: Optional[str] = None, use_rapid_api: bool = False):
        """
        Initialize ADS-B Exchange client.
        
        Args:
            api_key: RapidAPI key (required if use_rapid_api=True)
            use_rapid_api: Use RapidAPI endpoint (higher limits, requires key)
        """
        self.api_key = api_key
        self.use_rapid_api = use_rapid_api
        self.session = requests.Session()
        
        if use_rapid_api:
            if not api_key:
                raise ValueError("API key required for RapidAPI access")
            self.session.headers.update({
                'X-RapidAPI-Key': api_key,
                'X-RapidAPI-Host': 'adsbexchange-com1.p.rapidapi.com'
            })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to ADS-B Exchange API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
        
        Returns:
            JSON response as dictionary
        
        Raises:
            requests.RequestException: If request fails
        """
        if self.use_rapid_api:
            url = f"{self.BASE_URL_V2}/{endpoint}"
        else:
            url = self.BASE_URL_DIRECT if endpoint == "all" else f"https://globe.adsbexchange.com/data/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_all_flights(self, convert_si: bool = True) -> Iterator[FlightData]:
        """
        Get all currently tracked flights.
        
        Args:
            convert_si: Convert units to SI (meters, m/s)
        
        Yields:
            FlightData objects for each tracked aircraft
        """
        try:
            data = self._make_request("all")
            
            # Handle different response formats
            aircraft_list = data.get('aircraft') or data.get('ac') or []
            
            for aircraft in aircraft_list:
                try:
                    yield FlightData.from_api_response(aircraft, convert_si=convert_si)
                except Exception as e:
                    logger.warning(f"Failed to parse aircraft data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to fetch all flights: {e}")
            raise
    
    def get_flight_by_icao(self, icao: str, convert_si: bool = True) -> Optional[FlightData]:
        """
        Get flight data for specific aircraft by ICAO address.
        
        Args:
            icao: ICAO 24-bit address (hex)
            convert_si: Convert units to SI
        
        Returns:
            FlightData if found, None otherwise
        """
        endpoint = f"icao/{icao.lower()}"
        
        try:
            data = self._make_request(endpoint)
            aircraft_list = data.get('aircraft') or data.get('ac') or []
            
            if aircraft_list:
                return FlightData.from_api_response(aircraft_list[0], convert_si=convert_si)
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch flight {icao}: {e}")
            return None
    
    def get_flights_by_bounds(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        convert_si: bool = True
    ) -> Iterator[FlightData]:
        """
        Get flights within geographic bounding box.
        
        Args:
            lat_min: Minimum latitude
            lat_max: Maximum latitude
            lon_min: Minimum longitude
            lon_max: Maximum longitude
            convert_si: Convert units to SI
        
        Yields:
            FlightData objects within bounds
        """
        for flight in self.get_all_flights(convert_si=convert_si):
            if (flight.lat is not None and flight.lon is not None and
                lat_min <= flight.lat <= lat_max and
                lon_min <= flight.lon <= lon_max):
                yield flight


# Convenience functions for backward compatibility
def get_flights_all(api_key: Optional[str] = None, convert_si: bool = True) -> Iterator[FlightData]:
    """
    Get all currently tracked flights.
    
    Args:
        api_key: RapidAPI key (optional)
        convert_si: Convert units to SI
    
    Yields:
        FlightData objects
    """
    client = ADSBExchangeClient(api_key=api_key, use_rapid_api=bool(api_key))
    yield from client.get_all_flights(convert_si=convert_si)


def get_flights_by_bounds(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    api_key: Optional[str] = None,
    convert_si: bool = True
) -> Iterator[FlightData]:
    """
    Get flights within geographic bounding box.
    
    Args:
        lat_min: Minimum latitude
        lat_max: Maximum latitude
        lon_min: Minimum longitude
        lon_max: Maximum longitude
        api_key: RapidAPI key (optional)
        convert_si: Convert units to SI
    
    Yields:
        FlightData objects within bounds
    """
    client = ADSBExchangeClient(api_key=api_key, use_rapid_api=bool(api_key))
    yield from client.get_flights_by_bounds(lat_min, lat_max, lon_min, lon_max, convert_si=convert_si)


def get_flight_by_icao(
    icao: str,
    api_key: Optional[str] = None,
    convert_si: bool = True
) -> Optional[FlightData]:
    """
    Get flight data for specific aircraft by ICAO address.
    
    Args:
        icao: ICAO 24-bit address (hex)
        api_key: RapidAPI key (optional)
        convert_si: Convert units to SI
    
    Returns:
        FlightData if found, None otherwise
    """
    client = ADSBExchangeClient(api_key=api_key, use_rapid_api=bool(api_key))
    return client.get_flight_by_icao(icao, convert_si=convert_si)


def main():
    """Example usage of ADS-B Exchange client."""
    print("Fetching current flight data from ADS-B Exchange...")
    
    try:
        client = ADSBExchangeClient()
        
        # Get first 10 flights as a sample
        flights = []
        for i, flight in enumerate(client.get_all_flights()):
            flights.append(flight)
            if i >= 9:
                break
        
        print(f"\nFound {len(flights)} sample flights:")
        print("-" * 80)
        
        for flight in flights:
            print(f"ICAO: {flight.icao}")
            if flight.flight:
                print(f"  Flight: {flight.flight}")
            if flight.registration:
                print(f"  Registration: {flight.registration}")
            if flight.type:
                print(f"  Type: {flight.type}")
            if flight.lat and flight.lon:
                print(f"  Position: {flight.lat:.4f}, {flight.lon:.4f}")
            if flight.altitude:
                print(f"  Altitude: {flight.altitude:.0f} m")
            if flight.speed:
                print(f"  Speed: {flight.speed:.1f} m/s")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: ADS-B Exchange may require an API key for RapidAPI access.")
        print("Visit https://rapidapi.com/adsbx/api/adsbexchange-com1 for details.")


if __name__ == '__main__':
    main()
