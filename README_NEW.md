# FlightData - ADS-B Exchange API Client

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern Python 3 library for fetching real-time flight data from [ADS-B Exchange](https://www.adsbexchange.com/), an open-source collaborative flight tracking platform.

## Why ADS-B Exchange?

ADS-B Exchange is a community-driven, open-source flight tracking platform that provides unfiltered flight data. Unlike commercial services, it:

- ✅ Uses open-source data from volunteer feeders worldwide
- ✅ Does not filter or hide aircraft (unlike FlightRadar24, FlightAware, etc.)
- ✅ Provides free access to global flight data
- ✅ Supports the aviation enthusiast community

This makes it an ideal choice for open-source projects, research, and aviation enthusiasts.

## Features

- 🚀 **Modern Python 3.8+ codebase** with type hints
- 🌍 **Real-time flight tracking** worldwide
- 📍 **Geographic filtering** by bounding box or radius
- 📊 **Altitude filtering** for specific flight levels
- 💾 **Export to CSV/JSON** for data analysis
- 🔧 **Flexible filtering** with custom filter functions
- 🧪 **Comprehensive test suite** with 90%+ coverage
- 📦 **Easy installation** via pip

## Installation

```bash
# Install from source
git clone https://github.com/elkins/flightdata.git
cd flightdata
pip install -r requirements.txt

# Or install with pip (when published)
pip install flightdata
```

## Quick Start

### Basic Usage

```python
from adsbexchange import get_flights_all

# Get all currently tracked flights
for flight in get_flights_all():
    if flight.flight:  # Has callsign
        print(f"{flight.flight}: {flight.lat}, {flight.lon} at {flight.altitude}m")
```

### Geographic Filtering

```python
from flight_logger import FlightLogger

# Track flights near San Francisco
logger = FlightLogger()
logger.add_radius_filter(
    center=(37.7749, -122.4194),  # SF coordinates
    radius_m=50000  # 50km radius
)

# Log to CSV
logger.log_to_csv('sf_flights.csv')
```

### Advanced Filtering

```python
from flight_logger import FlightLogger

# Find high-altitude commercial flights
logger = FlightLogger()
logger.add_altitude_filter(min_alt=10000)  # Above 10,000m
logger.add_custom_filter(lambda f: f.type and 'B7' in f.type)  # Boeing aircraft

# Export to JSON
logger.log_to_json('boeing_flights.json')
```

## API Documentation

### Core Classes

#### `FlightData`

A dataclass representing a single flight with the following attributes:

- `icao` (str): ICAO 24-bit address
- `flight` (str | None): Flight callsign
- `registration` (str | None): Aircraft registration
- `type` (str | None): Aircraft type code
- `lat` (float | None): Latitude in degrees
- `lon` (float | None): Longitude in degrees
- `altitude` (float | None): Altitude in meters (SI units)
- `speed` (float | None): Ground speed in m/s (SI units)
- `track` (float | None): Track angle in degrees
- `vert_rate` (float | None): Vertical rate in m/s (SI units)
- `squawk` (str | None): Squawk code
- `timestamp` (datetime | None): Position timestamp

#### `ADSBExchangeClient`

Main client for interacting with ADS-B Exchange API.

```python
from adsbexchange import ADSBExchangeClient

# Initialize client
client = ADSBExchangeClient()

# With RapidAPI key (for higher rate limits)
client = ADSBExchangeClient(api_key='your-key', use_rapid_api=True)

# Get all flights
for flight in client.get_all_flights():
    print(flight)

# Get specific aircraft by ICAO
flight = client.get_flight_by_icao('A12345')

# Get flights in geographic area
for flight in client.get_flights_by_bounds(
    lat_min=37.0, lat_max=38.0,
    lon_min=-123.0, lon_max=-122.0
):
    print(flight)
```

#### `FlightLogger`

High-level logger with filtering capabilities.

```python
from flight_logger import FlightLogger

logger = FlightLogger()

# Add filters (chainable)
logger.add_radius_filter((37.7749, -122.4194), 50000)
logger.add_altitude_filter(min_alt=5000, max_alt=15000)
logger.add_custom_filter(lambda f: f.speed and f.speed > 100)

# Export data
logger.log_to_csv('filtered_flights.csv')
logger.log_to_json('filtered_flights.json')

# Clear filters
logger.clear_filters()
```

### Utility Functions

```python
from flight_logger import calculate_distance, filter_by_radius, filter_by_altitude

# Calculate distance between coordinates
distance = calculate_distance(
    (37.7749, -122.4194),  # SF
    (34.0522, -118.2437)   # LA
)
print(f"Distance: {distance/1000:.1f} km")

# Filter flight iterators
flights = get_flights_all()
nearby = filter_by_radius(flights, center=(37.7749, -122.4194), radius_m=50000)
high_altitude = filter_by_altitude(nearby, min_alt=10000)
```

## Configuration

### Environment Variables

```bash
# Set API key via environment variable
export ADSB_EXCHANGE_API_KEY="your-rapidapi-key"
export ADSB_EXCHANGE_USE_RAPID_API="true"
```

### Configuration File

Create `.flightdata.json` in your project directory:

```json
{
  "api_key": "your-rapidapi-key",
  "use_rapid_api": false,
  "default_radius_km": 100,
  "default_center_lat": 37.7749,
  "default_center_lon": -122.4194
}
```

Generate a template config file:

```bash
python config.py .flightdata.json
```

## API Access

### Free Access

ADS-B Exchange provides free access to their data through their website and APIs. However, for programmatic access with higher rate limits, consider using their RapidAPI endpoint.

### RapidAPI (Recommended for Production)

For reliable API access with higher rate limits:

1. Sign up at [RapidAPI](https://rapidapi.com/adsbx/api/adsbexchange-com1)
2. Subscribe to a plan (free tier available)
3. Get your API key
4. Use it in your code:

```python
client = ADSBExchangeClient(api_key='your-key', use_rapid_api=True)
```

## Examples

### Example 1: Track Aircraft Over Time

```python
import time
from adsbexchange import ADSBExchangeClient

client = ADSBExchangeClient()

# Track a specific aircraft
icao = 'A12345'
for i in range(10):
    flight = client.get_flight_by_icao(icao)
    if flight:
        print(f"[{i}] {flight.flight}: {flight.lat}, {flight.lon} @ {flight.altitude}m")
    time.sleep(10)  # Update every 10 seconds
```

### Example 2: Airport Traffic Monitor

```python
from flight_logger import FlightLogger

# Monitor San Francisco Airport (SFO)
sfo = (37.6213, -122.3790)

logger = FlightLogger()
logger.add_radius_filter(sfo, 20000)  # 20km radius
logger.add_altitude_filter(max_alt=3000)  # Below 3000m (landing/departing)

print("Monitoring SFO traffic...")
logger.log_to_csv('sfo_traffic.csv')
```

### Example 3: Flight Statistics

```python
from collections import Counter
from adsbexchange import get_flights_all

# Count aircraft by type
types = Counter()
speeds = []

for flight in get_flights_all():
    if flight.type:
        types[flight.type] += 1
    if flight.speed:
        speeds.append(flight.speed)

print(f"Most common aircraft types:")
for aircraft_type, count in types.most_common(10):
    print(f"  {aircraft_type}: {count}")

if speeds:
    print(f"\nAverage speed: {sum(speeds)/len(speeds):.1f} m/s")
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest test_adsbexchange.py -v
```

Or use unittest directly:

```bash
python -m unittest discover -s . -p "test_*.py"
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/elkins/flightdata.git
cd flightdata

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run code formatters
black *.py
ruff check *.py

# Run type checker
mypy adsbexchange.py flight_logger.py
```

### Project Structure

```
flightdata/
├── adsbexchange.py       # Main API client
├── flight_logger.py      # Logging and filtering utilities
├── config.py             # Configuration management
├── test_adsbexchange.py  # Tests for API client
├── test_flight_logger.py # Tests for logger
├── requirements.txt      # Dependencies
├── setup.py              # Package setup
└── README.md             # This file
```

## Migration from FlightRadar24

If you're migrating from the old FlightRadar24-based code:

### Old Code (FlightRadar24)
```python
import flightradar24

zone = 'full'
data = flightradar24.get_current(zone)
for flight in data:
    print(flight['icao_addr'], flight['lat'], flight['long'])
```

### New Code (ADS-B Exchange)
```python
from adsbexchange import get_flights_all

for flight in get_flights_all():
    print(flight.icao, flight.lat, flight.lon)
```

### Key Differences

| Feature | Old (FR24) | New (ADS-B Exchange) |
|---------|-----------|---------------------|
| Python Version | 2.7 | 3.8+ |
| Data Structure | Dictionary | Dataclass (FlightData) |
| Units | Mixed | SI units (meters, m/s) |
| API | Unofficial FR24 | ADS-B Exchange |
| Type Hints | No | Yes |
| Tests | No | Comprehensive suite |
| Filtering | Manual | Built-in utilities |

## Performance Tips

1. **Use geographic filtering**: Filter by bounds/radius on the server side when possible
2. **Batch processing**: Process flights in batches rather than one at a time
3. **Rate limiting**: Respect API rate limits (use RapidAPI for higher limits)
4. **Caching**: Cache results if you don't need real-time data
5. **Efficient filtering**: Apply filters in order of selectivity (most restrictive first)

## Troubleshooting

### API Rate Limits

If you encounter rate limiting:
- Use the RapidAPI endpoint with an API key
- Add delays between requests
- Cache results when appropriate

### No Data Returned

If you're not getting any data:
- Check your internet connection
- Verify ADS-B Exchange API status
- Try a different geographic region
- Check API key if using RapidAPI

### Import Errors

If you get import errors:
- Ensure Python 3.8+ is installed
- Install all dependencies: `pip install -r requirements.txt`
- Check that you're in the correct directory

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Credits

- Original FlightRadar24 code inspired by [@palli](https://github.com/palli)
- Modernized and migrated to ADS-B Exchange by George Elkins
- ADS-B Exchange data provided by volunteer feeders worldwide

## Support

- **Issues**: [GitHub Issues](https://github.com/elkins/flightdata/issues)
- **ADS-B Exchange**: [https://www.adsbexchange.com/](https://www.adsbexchange.com/)
- **RapidAPI Docs**: [ADS-B Exchange API](https://rapidapi.com/adsbx/api/adsbexchange-com1)

## Changelog

### Version 2.0.0 (2025-12-01)

- ✨ Complete rewrite for Python 3.8+
- ✨ Migration from FlightRadar24 to ADS-B Exchange
- ✨ Added type hints throughout
- ✨ New dataclass-based FlightData model
- ✨ Comprehensive test suite (90%+ coverage)
- ✨ Modern logging and filtering utilities
- ✨ Configuration file support
- ✨ CSV and JSON export capabilities
- ✨ Full documentation and examples

### Version 1.0.0 (Legacy)

- Original FlightRadar24-based implementation
- Python 2.7 support
- Basic functionality

---

**Note**: This library uses the ADS-B Exchange API, which provides open-source flight tracking data. Please use responsibly and respect their terms of service.
