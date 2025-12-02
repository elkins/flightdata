#!/usr/bin/env python3
"""
Example scripts demonstrating how to use the flightdata library.
"""

from adsbexchange import get_flights_all, ADSBExchangeClient
from flight_logger import FlightLogger, calculate_distance
from datetime import datetime


def example_1_basic_usage():
    """Example 1: Basic usage - Get all flights."""
    print("=" * 80)
    print("Example 1: Fetching all current flights")
    print("=" * 80)
    
    try:
        count = 0
        for flight in get_flights_all():
            if count >= 5:  # Just show first 5
                break
            
            print(f"\nFlight {count + 1}:")
            print(f"  ICAO: {flight.icao}")
            if flight.flight:
                print(f"  Callsign: {flight.flight}")
            if flight.registration:
                print(f"  Registration: {flight.registration}")
            if flight.type:
                print(f"  Aircraft Type: {flight.type}")
            if flight.lat and flight.lon:
                print(f"  Position: {flight.lat:.4f}°, {flight.lon:.4f}°")
            if flight.altitude:
                print(f"  Altitude: {flight.altitude:.0f} m ({flight.altitude * 3.28084:.0f} ft)")
            if flight.speed:
                print(f"  Speed: {flight.speed:.1f} m/s ({flight.speed * 1.94384:.1f} knots)")
            
            count += 1
        
        print(f"\n✓ Successfully fetched {count} flights")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def example_2_geographic_filter():
    """Example 2: Filter flights by geographic radius."""
    print("\n" + "=" * 80)
    print("Example 2: Flights near San Francisco")
    print("=" * 80)
    
    try:
        logger = FlightLogger()
        sf_coords = (37.7749, -122.4194)
        radius_km = 50
        
        logger.add_radius_filter(sf_coords, radius_km * 1000)
        
        print(f"\nSearching for flights within {radius_km}km of San Francisco...")
        
        flights = list(logger.get_flights())
        
        print(f"\n✓ Found {len(flights)} flights near SF:")
        for i, flight in enumerate(flights[:10], 1):  # Show first 10
            if flight.lat and flight.lon:
                dist = calculate_distance(sf_coords, (flight.lat, flight.lon))
                print(f"  {i}. {flight.icao} ({flight.flight or 'N/A'}) - {dist/1000:.1f}km away")
        
        if len(flights) > 10:
            print(f"  ... and {len(flights) - 10} more")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def example_3_altitude_filter():
    """Example 3: Filter flights by altitude."""
    print("\n" + "=" * 80)
    print("Example 3: High-altitude flights")
    print("=" * 80)
    
    try:
        logger = FlightLogger()
        min_altitude_ft = 35000
        min_altitude_m = min_altitude_ft * 0.3048
        
        logger.add_altitude_filter(min_alt=min_altitude_m)
        
        print(f"\nSearching for flights above {min_altitude_ft} feet...")
        
        flights = list(logger.get_flights())
        
        print(f"\n✓ Found {len(flights)} high-altitude flights:")
        for i, flight in enumerate(flights[:10], 1):
            if flight.altitude:
                alt_ft = flight.altitude * 3.28084
                print(f"  {i}. {flight.icao} ({flight.flight or 'N/A'}) - {alt_ft:.0f} ft")
        
        if len(flights) > 10:
            print(f"  ... and {len(flights) - 10} more")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def example_4_combined_filters():
    """Example 4: Combine multiple filters."""
    print("\n" + "=" * 80)
    print("Example 4: Combined filters - Low altitude flights near NYC")
    print("=" * 80)
    
    try:
        logger = FlightLogger()
        nyc_coords = (40.7128, -74.0060)
        
        # Flights near NYC, at low altitude (landing/departing)
        logger.add_radius_filter(nyc_coords, 30000)  # 30km radius
        logger.add_altitude_filter(max_alt=3000)      # Below 3000m
        
        print(f"\nSearching for landing/departing flights near NYC...")
        
        flights = list(logger.get_flights())
        
        print(f"\n✓ Found {len(flights)} flights:")
        for i, flight in enumerate(flights[:10], 1):
            if flight.lat and flight.lon and flight.altitude:
                dist = calculate_distance(nyc_coords, (flight.lat, flight.lon))
                alt_ft = flight.altitude * 3.28084
                print(f"  {i}. {flight.icao} ({flight.flight or 'N/A'}) - "
                      f"{dist/1000:.1f}km away, {alt_ft:.0f} ft")
        
        if len(flights) > 10:
            print(f"  ... and {len(flights) - 10} more")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def example_5_custom_filter():
    """Example 5: Custom filter function."""
    print("\n" + "=" * 80)
    print("Example 5: Boeing 777 flights")
    print("=" * 80)
    
    try:
        logger = FlightLogger()
        
        # Filter for Boeing 777 aircraft (type codes: B77W, B77L, B772, B773, etc.)
        logger.add_custom_filter(lambda f: bool(f.type and 'B77' in f.type))
        
        print(f"\nSearching for Boeing 777 flights...")
        
        flights = list(logger.get_flights())
        
        print(f"\n✓ Found {len(flights)} B777 flights:")
        for i, flight in enumerate(flights[:10], 1):
            print(f"  {i}. {flight.icao} - {flight.flight or 'N/A'} "
                  f"({flight.type}) - {flight.registration or 'N/A'}")
        
        if len(flights) > 10:
            print(f"  ... and {len(flights) - 10} more")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def example_6_export_to_csv():
    """Example 6: Export data to CSV."""
    print("\n" + "=" * 80)
    print("Example 6: Export flights to CSV")
    print("=" * 80)
    
    try:
        from pathlib import Path
        
        logger = FlightLogger()
        
        # Get flights over the Atlantic (example bounding box)
        atlantic_center = (35.0, -40.0)
        logger.add_radius_filter(atlantic_center, 1000000)  # 1000km radius
        
        output_file = Path('atlantic_flights.csv')
        
        print(f"\nExporting flights to {output_file}...")
        count = logger.log_to_csv(output_file, print_every=50)
        
        print(f"\n✓ Exported {count} flights to {output_file}")
        print(f"  File size: {output_file.stat().st_size} bytes")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def example_7_track_specific_aircraft():
    """Example 7: Track a specific aircraft."""
    print("\n" + "=" * 80)
    print("Example 7: Track specific aircraft by ICAO")
    print("=" * 80)
    
    try:
        client = ADSBExchangeClient()
        
        # Note: Replace with an actual ICAO address you want to track
        # This is just an example
        icao = 'A12345'
        
        print(f"\nLooking for aircraft {icao}...")
        
        flight = client.get_flight_by_icao(icao)
        
        if flight:
            print(f"\n✓ Found aircraft:")
            print(f"  ICAO: {flight.icao}")
            print(f"  Callsign: {flight.flight or 'N/A'}")
            print(f"  Position: {flight.lat}, {flight.lon}")
            print(f"  Altitude: {flight.altitude}m")
        else:
            print(f"\n✗ Aircraft {icao} not found (may not be airborne)")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "FlightData Examples" + " " * 39 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\nThese examples demonstrate the flightdata library capabilities.")
    print("Note: Some examples may take a moment to fetch data from ADS-B Exchange.")
    
    examples = [
        example_1_basic_usage,
        example_2_geographic_filter,
        example_3_altitude_filter,
        example_4_combined_filters,
        example_5_custom_filter,
        example_6_export_to_csv,
        # example_7_track_specific_aircraft,  # Uncomment to track specific aircraft
    ]
    
    for example in examples:
        try:
            example()
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
    
    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80)
    print("\nFor more information, see README_NEW.md")


if __name__ == '__main__':
    main()
