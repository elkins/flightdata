#!/usr/bin/env python3
"""
Tests for ADS-B Exchange API client
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import tempfile
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightdata.adsbexchange import (
    FlightData,
    ADSBExchangeClient,
    get_flights_all,
    get_flight_by_icao,
)


class TestFlightData(unittest.TestCase):
    """Test FlightData dataclass."""

    def test_from_api_response_basic(self):
        """Test creating FlightData from basic API response."""
        api_data = {
            "hex": "a12345",
            "flight": "UAL123  ",
            "lat": 37.7749,
            "lon": -122.4194,
            "alt_baro": 35000,  # feet
            "gs": 450,  # knots
            "track": 270,
            "squawk": "1200",
        }

        flight = FlightData.from_api_response(api_data, convert_si=True)

        self.assertEqual(flight.icao, "A12345")
        self.assertEqual(flight.flight, "UAL123")
        self.assertEqual(flight.lat, 37.7749)
        self.assertEqual(flight.lon, -122.4194)
        self.assertIsNotNone(flight.altitude)
        self.assertAlmostEqual(flight.altitude or 0, 35000 * 0.3048, places=2)
        self.assertIsNotNone(flight.speed)
        self.assertAlmostEqual(flight.speed or 0, 450 * 0.514444444, places=2)
        self.assertEqual(flight.track, 270)
        self.assertEqual(flight.squawk, "1200")

    def test_from_api_response_no_conversion(self):
        """Test creating FlightData without unit conversion."""
        api_data = {
            "hex": "a12345",
            "alt_baro": 35000,
            "gs": 450,
            "baro_rate": 1000,  # fpm
        }

        flight = FlightData.from_api_response(api_data, convert_si=False)

        self.assertEqual(flight.altitude, 35000)
        self.assertEqual(flight.speed, 450)
        self.assertEqual(flight.vert_rate, 1000)

    def test_from_api_response_with_timestamp(self):
        """Test timestamp parsing."""
        api_data = {
            "hex": "a12345",
            "now": 1638360000,  # Unix timestamp
        }

        flight = FlightData.from_api_response(api_data)

        self.assertIsInstance(flight.timestamp, datetime)
        self.assertEqual(flight.timestamp, datetime.fromtimestamp(1638360000))

    def test_to_dict(self):
        """Test converting FlightData to dictionary."""
        flight = FlightData(
            icao="A12345",
            flight="UAL123",
            lat=37.7749,
            lon=-122.4194,
        )

        result = flight.to_dict()

        self.assertEqual(result["icao"], "A12345")
        self.assertEqual(result["flight"], "UAL123")
        self.assertEqual(result["lat"], 37.7749)
        self.assertEqual(result["lon"], -122.4194)


class TestADSBExchangeClient(unittest.TestCase):
    """Test ADSBExchangeClient class."""

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        client = ADSBExchangeClient()

        self.assertIsNone(client.api_key)
        self.assertFalse(client.use_rapid_api)

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = ADSBExchangeClient(api_key="test_key", use_rapid_api=True)

        self.assertEqual(client.api_key, "test_key")
        self.assertTrue(client.use_rapid_api)
        self.assertIn("X-RapidAPI-Key", client.session.headers)

    def test_init_rapid_api_without_key_raises(self):
        """Test that using RapidAPI without key raises error."""
        with self.assertRaises(ValueError):
            ADSBExchangeClient(use_rapid_api=True)

    @patch("flightdata.adsbexchange.requests.Session.get")
    def test_get_all_flights(self, mock_get):
        """Test fetching all flights."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "aircraft": [
                {"hex": "a12345", "lat": 37.7749, "lon": -122.4194},
                {"hex": "b67890", "lat": 40.7128, "lon": -74.0060},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = ADSBExchangeClient()
        flights = list(client.get_all_flights())

        self.assertEqual(len(flights), 2)
        self.assertEqual(flights[0].icao, "A12345")
        self.assertEqual(flights[1].icao, "B67890")

    @patch("flightdata.adsbexchange.requests.Session.get")
    def test_get_flight_by_icao(self, mock_get):
        """Test fetching specific flight by ICAO."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "aircraft": [{"hex": "a12345", "flight": "UAL123", "lat": 37.7749}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = ADSBExchangeClient()
        flight = client.get_flight_by_icao("A12345")

        self.assertIsNotNone(flight)
        if flight:
            self.assertEqual(flight.icao, "A12345")
            self.assertEqual(flight.flight, "UAL123")

    @patch("flightdata.adsbexchange.requests.Session.get")
    def test_get_flight_by_icao_not_found(self, mock_get):
        """Test fetching non-existent flight."""
        mock_response = Mock()
        mock_response.json.return_value = {"aircraft": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = ADSBExchangeClient()
        flight = client.get_flight_by_icao("FFFFFF")

        self.assertIsNone(flight)

    @patch("flightdata.adsbexchange.requests.Session.get")
    def test_get_flights_by_bounds(self, mock_get):
        """Test filtering flights by geographic bounds."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "aircraft": [
                {"hex": "a12345", "lat": 37.5, "lon": -122.0},  # Inside
                {"hex": "b67890", "lat": 38.5, "lon": -122.0},  # Inside
                {"hex": "c11111", "lat": 40.0, "lon": -122.0},  # Outside
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = ADSBExchangeClient()
        flights = list(client.get_flights_by_bounds(37.0, 39.0, -123.0, -121.0))

        self.assertEqual(len(flights), 2)
        self.assertEqual(flights[0].icao, "A12345")
        self.assertEqual(flights[1].icao, "B67890")


class TestConvenienceFunctions(unittest.TestCase):
    """Test module-level convenience functions."""

    @patch("flightdata.adsbexchange.ADSBExchangeClient")
    def test_get_flights_all(self, mock_client_class):
        """Test get_flights_all convenience function."""
        mock_client = Mock()
        mock_client.get_all_flights.return_value = iter(
            [
                FlightData(icao="A12345"),
            ]
        )
        mock_client_class.return_value = mock_client

        flights = list(get_flights_all())

        self.assertEqual(len(flights), 1)
        if flights:
            self.assertEqual(flights[0].icao, "A12345")
        mock_client_class.assert_called_once()

    @patch("flightdata.adsbexchange.ADSBExchangeClient")
    def test_get_flight_by_icao_function(self, mock_client_class):
        """Test get_flight_by_icao convenience function."""
        mock_client = Mock()
        mock_client.get_flight_by_icao.return_value = FlightData(icao="A12345")
        mock_client_class.return_value = mock_client

        flight = get_flight_by_icao("A12345")

        self.assertIsNotNone(flight)
        if flight:
            self.assertEqual(flight.icao, "A12345")


if __name__ == "__main__":
    unittest.main()
