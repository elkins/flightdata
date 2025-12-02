# Quick Start Guide

Get started with FlightData in 5 minutes!

## Installation

```bash
cd /Users/georgeelkins/aviation/flightdata
pip install -r requirements.txt
```

## Your First Flight Query

```python
from adsbexchange import get_flights_all

# Get first 5 flights
for i, flight in enumerate(get_flights_all()):
    if i >= 5:
        break
    print(f"{flight.icao} - {flight.flight or 'N/A'}")
```

## Common Tasks

### 1. Find Flights Near You

```python
from flight_logger import FlightLogger

logger = FlightLogger()
# Replace with your coordinates
logger.add_radius_filter(center=(37.7749, -122.4194), radius_m=50000)

flights = list(logger.get_flights())
print(f"Found {len(flights)} flights nearby")
```

### 2. Export to CSV

```python
from flight_logger import FlightLogger
from pathlib import Path

logger = FlightLogger()
logger.add_altitude_filter(min_alt=10000)  # High altitude only
logger.log_to_csv(Path('high_altitude.csv'))
```

### 3. Track Specific Aircraft

```python
from adsbexchange import get_flight_by_icao

flight = get_flight_by_icao('A12345')  # Replace with real ICAO
if flight:
    print(f"Found: {flight.flight} at {flight.lat}, {flight.lon}")
```

## Run Examples

```bash
# Run all examples
python examples.py

# Or use make
make examples
```

## Run Tests

```bash
# Simple test run
make test

# With coverage
make coverage
```

## Configuration (Optional)

For higher rate limits, get a RapidAPI key:

```bash
# Create config file
make config

# Edit .flightdata.json and add your API key
```

Then use it:

```python
from adsbexchange import ADSBExchangeClient

client = ADSBExchangeClient(api_key='your-key', use_rapid_api=True)
for flight in client.get_all_flights():
    print(flight)
```

## Next Steps

- Read [README_NEW.md](README_NEW.md) for complete documentation
- Check [MIGRATION.md](MIGRATION.md) if migrating from old code
- Browse [examples.py](examples.py) for more examples

## Quick Reference

### Import What You Need

```python
# Basic usage
from adsbexchange import get_flights_all, get_flight_by_icao

# Advanced usage
from adsbexchange import ADSBExchangeClient, FlightData

# Logging and filtering
from flight_logger import FlightLogger, calculate_distance
```

### Data Fields

Each `FlightData` object has:
- `icao` - Aircraft identifier
- `flight` - Callsign
- `lat`, `lon` - Position
- `altitude` - Height in meters
- `speed` - Ground speed in m/s
- `track` - Direction in degrees
- `type` - Aircraft type
- `registration` - Aircraft registration

### Filter Methods

```python
logger = FlightLogger()

# Geographic
logger.add_radius_filter(center=(lat, lon), radius_m=50000)

# Altitude
logger.add_altitude_filter(min_alt=5000, max_alt=15000)

# Custom
logger.add_custom_filter(lambda f: f.speed and f.speed > 200)
```

## Troubleshooting

**No data returned?**
- Check internet connection
- Try different geographic area
- Verify ADS-B Exchange status

**Import errors?**
- Run `pip install -r requirements.txt`
- Verify Python 3.8+ installed

**Rate limiting?**
- Get a RapidAPI key (free tier available)
- Add delays between requests

## Help

- Full docs: [README_NEW.md](README_NEW.md)
- Migration guide: [MIGRATION.md](MIGRATION.md)
- Examples: [examples.py](examples.py)
- ADS-B Exchange: https://www.adsbexchange.com/

Happy tracking! ✈️
