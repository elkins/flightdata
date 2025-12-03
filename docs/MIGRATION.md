# Migration Guide: FlightRadar24 → ADS-B Exchange

This guide helps you migrate from the old FlightRadar24-based code to the new ADS-B Exchange implementation.

## Overview of Changes

### Why Migrate?

1. **Open Source Data**: ADS-B Exchange provides truly open data without filtering
2. **Python 3**: Modern Python 3.8+ with type hints and better performance
3. **Better API**: More reliable and ethical data source
4. **More Features**: Built-in filtering, logging, and export capabilities
5. **Testing**: Comprehensive test suite ensures reliability
6. **Maintenance**: Active API that's less likely to break

### Key Differences

| Aspect | Old (FlightRadar24) | New (ADS-B Exchange) |
|--------|-------------------|---------------------|
| Python Version | 2.7 | 3.8+ |
| Data Source | FlightRadar24 (unofficial) | ADS-B Exchange (official) |
| Data Structure | Dictionary | Dataclass (FlightData) |
| Type Hints | None | Full typing support |
| Units | Mixed (ft, knots, etc.) | SI units (m, m/s) |
| Historical Data | Yes (limited) | No (real-time only) |
| Tests | None | Comprehensive suite |
| Documentation | Basic | Extensive |

## Step-by-Step Migration

### 1. Installation

**Old:**
```bash
# Python 2.7
pip install requests
```

**New:**
```bash
# Python 3.8+
pip install -r requirements.txt
```

### 2. Basic Usage

**Old (`flightradar24.py`):**
```python
import flightradar24

# Get current flights
zone = 'full'
data = flightradar24.get_current(zone)

for flight in data:
    print(flight['icao_addr'])
    print(flight['lat'], flight['long'])
    print(flight['alt'])  # feet
    print(flight['speed'])  # knots
```

**New (`adsbexchange.py`):**
```python
from adsbexchange import get_flights_all

# Get current flights
for flight in get_flights_all():
    print(flight.icao)
    print(flight.lat, flight.lon)
    print(flight.altitude)  # meters (SI)
    print(flight.speed)  # m/s (SI)
```

### 3. Field Name Mappings

| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `icao_addr` | `icao` | Now uppercase |
| `long` | `lon` | Standard naming |
| `alt` | `altitude` | Now in meters (was feet) |
| `speed` | `speed` | Now in m/s (was knots) |
| `vert_speed` | `vert_rate` | Now in m/s (was ft/min) |
| `flight_num` | `flight` | Callsign |
| `reg_num` | `registration` | Aircraft registration |
| `type` | `type` | Aircraft type code |
| `time_epoch` | `timestamp` | Now datetime object |
| `src` | N/A | Not available |
| `dest` | N/A | Not available |
| `radar` | N/A | Not available |

### 4. Unit Conversions

If you need the old units, convert them:

```python
from adsbexchange import get_flights_all

for flight in get_flights_all(convert_si=False):
    # Get raw units (feet, knots, etc.)
    altitude_ft = flight.altitude
    speed_kt = flight.speed
```

Or convert SI units:

```python
# Convert meters to feet
altitude_ft = flight.altitude * 3.28084

# Convert m/s to knots
speed_kt = flight.speed * 1.94384

# Convert m/s to ft/min
vert_speed_fpm = flight.vert_rate * 196.85
```

### 5. Historical Data

**Old:**
```python
import flightradar24
import datetime

# Get historical data
start = datetime.datetime(2014, 10, 8, 8, 0)
stop = datetime.datetime(2014, 10, 8, 9, 0)

for flight in flightradar24.get_historical(start, stop):
    print(flight)
```

**New:**
```python
# ADS-B Exchange doesn't provide historical data via API
# For historical data, you need to:
# 1. Log data continuously using FlightLogger
# 2. Use a third-party historical data service
# 3. Set up your own ADS-B receiver and log data locally
```

### 6. Geographic Filtering

**Old:**
```python
import flightradar24
import logger

# Get flights in a zone
zone = 'europe'
flights = flightradar24.get_current(zone)

# Manual radius filtering
coord = (51.5074, -0.1278)  # London
radius = 100000  # meters

filtered = [f for f in flights 
            if logger.distance((f['lat'], f['long']), coord) <= radius]
```

**New:**
```python
from flight_logger import FlightLogger

# Built-in radius filtering
logger = FlightLogger()
logger.add_radius_filter(
    center=(51.5074, -0.1278),  # London
    radius_m=100000
)

# Get filtered flights
flights = list(logger.get_flights())
```

### 7. Logging to CSV

**Old (`logger.py`):**
```python
import flightradar24
import logger
import datetime

time_span = datetime.timedelta(minutes=5)
coord = (35, -39)
radius = 1000e3
file_name = 'flights.csv'

logger.recent_logger(file_name, time_span, coord, radius)
```

**New (`flight_logger.py`):**
```python
from flight_logger import FlightLogger
from pathlib import Path

# Modern approach with FlightLogger
logger = FlightLogger()
logger.add_radius_filter(center=(35, -39), radius_m=1000000)

# Export to CSV (single call, no loops needed)
logger.log_to_csv(Path('flights.csv'))
```

### 8. Complete Migration Example

**Old Code:**
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import flightradar24
import logger
import datetime

def get_nearby_flights():
    # Get recent flights
    time_span = datetime.timedelta(minutes=10)
    flights = list(flightradar24.get_recent(time_span))
    
    # Filter by location
    coord = (37.7749, -122.4194)  # SF
    radius = 50e3  # 50 km
    
    nearby = []
    for f in flights:
        dist = logger.distance((f['lat'], f['long']), coord)
        if dist <= radius:
            nearby.append(f)
    
    # Log to CSV
    logger.log_to_csv('nearby.csv', iter(nearby), print_every=10)
    
    return nearby

if __name__ == '__main__':
    flights = get_nearby_flights()
    print 'Found {} flights'.format(len(flights))
```

**New Code:**
```python
#!/usr/bin/env python3

from flight_logger import FlightLogger
from pathlib import Path

def get_nearby_flights():
    """Get and log flights near San Francisco."""
    # Create logger with filters
    logger = FlightLogger()
    logger.add_radius_filter(
        center=(37.7749, -122.4194),  # SF
        radius_m=50000  # 50 km
    )
    
    # Log to CSV (automatically fetches and filters)
    count = logger.log_to_csv(Path('nearby.csv'))
    
    return count

if __name__ == '__main__':
    count = get_nearby_flights()
    print(f'Found {count} flights')
```

## Common Migration Patterns

### Pattern 1: Iterator to List

**Old:**
```python
data = flightradar24.get_current('full')
flights = list(data)
print len(flights)
```

**New:**
```python
from adsbexchange import get_flights_all

flights = list(get_flights_all())
print(len(flights))
```

### Pattern 2: Filtering

**Old:**
```python
flights = [f for f in data if f['alt'] > 30000]  # feet
```

**New:**
```python
from flight_logger import filter_by_altitude

flights = list(filter_by_altitude(
    get_flights_all(),
    min_alt=30000 * 0.3048  # Convert to meters
))
```

### Pattern 3: Distance Calculation

**Old:**
```python
from logger import distance

coord1 = (37.7749, -122.4194)
coord2 = (flight['lat'], flight['long'])
dist = distance(coord1, coord2)
```

**New:**
```python
from flight_logger import calculate_distance

coord1 = (37.7749, -122.4194)
coord2 = (flight.lat, flight.lon)
dist = calculate_distance(coord1, coord2)
```

## Testing Your Migration

After migration, test your code:

```bash
# Run tests
make test

# Or manually
python -m pytest test_adsbexchange.py test_flight_logger.py -v

# Test with examples
python examples.py
```

## Troubleshooting

### Issue: "No module named 'adsbexchange'"

**Solution:**
```bash
# Make sure you're in the correct directory
cd /path/to/flightdata

# Install dependencies
pip install -r requirements.txt
```

### Issue: "TypeError: 'FlightData' object is not subscriptable"

**Old Code:**
```python
print(flight['icao_addr'])  # Dictionary access
```

**Solution:**
```python
print(flight.icao)  # Attribute access
```

### Issue: API rate limiting

**Solution:**
```python
# Use RapidAPI with an API key
from adsbexchange import ADSBExchangeClient

client = ADSBExchangeClient(
    api_key='your-rapidapi-key',
    use_rapid_api=True
)

for flight in client.get_all_flights():
    print(flight)
```

### Issue: Historical data not available

**Solution:**
ADS-B Exchange API provides real-time data only. For historical data:
1. Set up continuous logging using `FlightLogger`
2. Use a different data source for historical queries
3. Consider setting up your own ADS-B receiver

## Performance Considerations

### Old Code Performance Issues
- Sequential processing
- No caching
- Repeated API calls

### New Code Improvements
- Iterator-based processing (memory efficient)
- Single API call with filtering
- Better error handling

## Additional Resources

- [README_NEW.md](README_NEW.md) - Full documentation
- [examples.py](examples.py) - Working examples
- [ADS-B Exchange](https://www.adsbexchange.com/) - Data source
- [RapidAPI Documentation](https://rapidapi.com/adsbx/api/adsbexchange-com1) - API docs

## Need Help?

If you encounter issues during migration:

1. Check the [examples.py](examples.py) for working code
2. Run the tests to verify your installation
3. Review [README_NEW.md](README_NEW.md) for detailed API docs
4. Open an issue on GitHub

## Conclusion

The migration to ADS-B Exchange provides:
- ✅ Better data quality (unfiltered, community-driven)
- ✅ Modern Python 3 with type safety
- ✅ More robust and maintainable code
- ✅ Better filtering and logging capabilities
- ✅ Comprehensive testing

Happy migrating! 🚀
