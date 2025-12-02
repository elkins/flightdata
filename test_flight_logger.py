#!/usr/bin/env python3
"""
Tests for flight_logger module
"""

import unittest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import tempfile
import csv
import json

from adsbexchange import FlightData
from flight_logger import (
    calculate_distance,
    filter_by_radius,
    filter_by_altitude,
    log_to_csv,
    log_to_json,
    FlightLogger,
)


class TestCalculateDistance(unittest.TestCase):
    """Test distance calculation function."""
    
    def test_same_point(self):
        """Test distance between same point is zero."""
        coord = (37.7749, -122.4194)
        distance = calculate_distance(coord, coord)
        self.assertAlmostEqual(distance, 0, places=1)
    
    def test_known_distance(self):
        """Test known distance between two cities."""
        # SF to LA (approximately 559 km)
        sf = (37.7749, -122.4194)
        la = (34.0522, -118.2437)
        distance = calculate_distance(sf, la)
        
        # Should be around 559 km (with some tolerance)
        self.assertGreater(distance, 500000)  # > 500 km
        self.assertLess(distance, 600000)     # < 600 km
    
    def test_antipodal_points(self):
        """Test distance between opposite points on Earth."""
        coord1 = (0, 0)
        coord2 = (0, 180)
        distance = calculate_distance(coord1, coord2)
        
        # Should be approximately half Earth's circumference
        earth_circumference = 2 * 3.14159 * 6371000
        expected = earth_circumference / 2
        self.assertAlmostEqual(distance, expected, delta=100000)


class TestFilterByRadius(unittest.TestCase):
    """Test radius filtering."""
    
    def test_filter_within_radius(self):
        """Test filtering flights within radius."""
        flights = [
            FlightData(icao='A12345', lat=37.7749, lon=-122.4194),  # SF
            FlightData(icao='B67890', lat=37.8, lon=-122.4),         # Near SF
            FlightData(icao='C11111', lat=34.0522, lon=-118.2437),  # LA (far)
        ]
        
        center = (37.7749, -122.4194)
        radius = 10000  # 10 km
        
        filtered = list(filter_by_radius(iter(flights), center, radius))
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].icao, 'A12345')
        self.assertEqual(filtered[1].icao, 'B67890')
    
    def test_filter_no_position(self):
        """Test filtering flights without position data."""
        flights = [
            FlightData(icao='A12345', lat=None, lon=None),
            FlightData(icao='B67890', lat=37.7749, lon=-122.4194),
        ]
        
        center = (37.7749, -122.4194)
        radius = 10000
        
        filtered = list(filter_by_radius(iter(flights), center, radius))
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].icao, 'B67890')


class TestFilterByAltitude(unittest.TestCase):
    """Test altitude filtering."""
    
    def test_filter_min_altitude(self):
        """Test filtering with minimum altitude."""
        flights = [
            FlightData(icao='A12345', altitude=1000),
            FlightData(icao='B67890', altitude=5000),
            FlightData(icao='C11111', altitude=10000),
        ]
        
        filtered = list(filter_by_altitude(iter(flights), min_alt=5000))
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].icao, 'B67890')
        self.assertEqual(filtered[1].icao, 'C11111')
    
    def test_filter_max_altitude(self):
        """Test filtering with maximum altitude."""
        flights = [
            FlightData(icao='A12345', altitude=1000),
            FlightData(icao='B67890', altitude=5000),
            FlightData(icao='C11111', altitude=10000),
        ]
        
        filtered = list(filter_by_altitude(iter(flights), max_alt=5000))
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].icao, 'A12345')
        self.assertEqual(filtered[1].icao, 'B67890')
    
    def test_filter_altitude_range(self):
        """Test filtering with altitude range."""
        flights = [
            FlightData(icao='A12345', altitude=1000),
            FlightData(icao='B67890', altitude=5000),
            FlightData(icao='C11111', altitude=10000),
        ]
        
        filtered = list(filter_by_altitude(iter(flights), min_alt=2000, max_alt=8000))
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].icao, 'B67890')
    
    def test_filter_no_altitude(self):
        """Test filtering flights without altitude data."""
        flights = [
            FlightData(icao='A12345', altitude=None),
            FlightData(icao='B67890', altitude=5000),
        ]
        
        filtered = list(filter_by_altitude(iter(flights), min_alt=1000))
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].icao, 'B67890')


class TestLogToCSV(unittest.TestCase):
    """Test CSV logging functionality."""
    
    def test_log_to_csv(self):
        """Test logging flights to CSV file."""
        flights = [
            FlightData(icao='A12345', flight='UAL123', lat=37.7749, lon=-122.4194),
            FlightData(icao='B67890', flight='DAL456', lat=40.7128, lon=-74.0060),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / 'test.csv'
            count = log_to_csv(file_path, iter(flights), print_every=1)
            
            self.assertEqual(count, 2)
            self.assertTrue(file_path.exists())
            
            # Verify CSV content
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['icao'], 'A12345')
            self.assertEqual(rows[0]['flight'], 'UAL123')
            self.assertEqual(rows[1]['icao'], 'B67890')
    
    def test_log_to_csv_append(self):
        """Test appending to existing CSV file."""
        flights1 = [FlightData(icao='A12345')]
        flights2 = [FlightData(icao='B67890')]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / 'test.csv'
            
            # First write
            log_to_csv(file_path, iter(flights1), print_every=1)
            # Append
            log_to_csv(file_path, iter(flights2), append=True, print_every=1)
            
            # Verify both records exist
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            self.assertEqual(len(rows), 2)


class TestLogToJSON(unittest.TestCase):
    """Test JSON logging functionality."""
    
    def test_log_to_json(self):
        """Test logging flights to JSON file."""
        flights = [
            FlightData(icao='A12345', flight='UAL123'),
            FlightData(icao='B67890', flight='DAL456'),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / 'test.json'
            count = log_to_json(file_path, iter(flights))
            
            self.assertEqual(count, 2)
            self.assertTrue(file_path.exists())
            
            # Verify JSON content
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['icao'], 'A12345')
            self.assertEqual(data[1]['icao'], 'B67890')


class TestFlightLogger(unittest.TestCase):
    """Test FlightLogger class."""
    
    def test_init(self):
        """Test logger initialization."""
        logger = FlightLogger()
        self.assertEqual(len(logger.filters), 0)
    
    def test_add_radius_filter(self):
        """Test adding radius filter."""
        logger = FlightLogger()
        result = logger.add_radius_filter((37.7749, -122.4194), 10000)
        
        self.assertEqual(result, logger)  # Check chaining
        self.assertEqual(len(logger.filters), 1)
    
    def test_add_altitude_filter(self):
        """Test adding altitude filter."""
        logger = FlightLogger()
        result = logger.add_altitude_filter(min_alt=5000, max_alt=10000)
        
        self.assertEqual(result, logger)
        self.assertEqual(len(logger.filters), 1)
    
    def test_add_custom_filter(self):
        """Test adding custom filter."""
        logger = FlightLogger()
        result = logger.add_custom_filter(lambda f: f.icao == 'A12345')
        
        self.assertEqual(result, logger)
        self.assertEqual(len(logger.filters), 1)
    
    def test_clear_filters(self):
        """Test clearing filters."""
        logger = FlightLogger()
        logger.add_radius_filter((0, 0), 1000)
        logger.add_altitude_filter(min_alt=5000)
        
        self.assertEqual(len(logger.filters), 2)
        
        logger.clear_filters()
        self.assertEqual(len(logger.filters), 0)
    
    def test_method_chaining(self):
        """Test method chaining."""
        logger = FlightLogger()
        result = (logger
                  .add_radius_filter((37.7749, -122.4194), 10000)
                  .add_altitude_filter(min_alt=5000)
                  .add_custom_filter(lambda f: bool(f.flight)))
        
        self.assertEqual(result, logger)
        self.assertEqual(len(logger.filters), 3)
    
    @patch('flight_logger.ADSBExchangeClient')
    def test_get_flights_with_filters(self, mock_client_class):
        """Test getting filtered flights."""
        # Create mock flights
        mock_flights = [
            FlightData(icao='A12345', lat=37.7749, lon=-122.4194, altitude=10000),
            FlightData(icao='B67890', lat=37.8, lon=-122.4, altitude=5000),
            FlightData(icao='C11111', lat=40.0, lon=-122.0, altitude=10000),  # Far away
        ]
        
        mock_client = Mock()
        mock_client.get_all_flights.return_value = iter(mock_flights)
        mock_client_class.return_value = mock_client
        
        logger = FlightLogger()
        logger.add_radius_filter((37.7749, -122.4194), 20000)  # 20km radius
        logger.add_altitude_filter(min_alt=8000)
        
        filtered = list(logger.get_flights())
        
        # Should only get the first flight (close and high altitude)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].icao, 'A12345')


if __name__ == '__main__':
    unittest.main()
