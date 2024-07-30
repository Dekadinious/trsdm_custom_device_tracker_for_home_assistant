# TRSDM Dynamic Device Tracker

## Overview

TRSDM Dynamic Device Tracker is a Home Assistant integration that allows you to easily track custom devices using webhooks. It's designed to be simple and flexible, making it perfect for tracking anything that can send location data via HTTPS requests.

Key features:

-   Easy setup through HACS
-   Tracks latitude and longitude
-   Provides useful attributes like distance from home and direction
-   Allows custom attributes through the payload for maximum flexibility
-   No limit on the number of tracked devices

## Installation

1. Make sure you have [HACS (Home Assistant Community Store)](https://hacs.xyz/) installed.
2. In Home Assistant, go to HACS > Integrations.
3. Click the "+" button and search for "TRSDM Dynamic Device Tracker".
4. Click "Install" on the TRSDM Dynamic Device Tracker integration.
5. Restart Home Assistant.

## Setup

1. In Home Assistant, go to Settings > Devices & Services.
2. Click the "+" button to add a new integration.
3. Search for "TRSDM Dynamic Device Tracker" and select it.
4. Follow the prompts to set up your first device tracker:
    - Give your tracker a name (e.g., "My Car")
    - The integration will generate a unique webhook URL for this tracker

## Using the Integration

### Sending Data

Send a POST request to the webhook URL with JSON data. The only required fields are `latitude` and `longitude`.

Example using curl:

```
curl -X POST https://your-home-assistant-url/api/webhook/your-webhook-id \
 -H "Content-Type: application/json" \
 -d '{"latitude": 37.7749, "longitude": -122.4194, "speed": 30, "battery": 75}'
```

You can include any additional data you want as custom attributes.

### Viewing Tracker Data

-   Go to your Home Assistant dashboard
-   Add a new card and search for your tracker entity (e.g., `device_tracker.my_car`)
-   The card will display the current location and all attributes

### Standard Attributes

-   Distance from home (in meters and miles)
-   Direction relative to home (towards, away_from, stationary)
-   Cardinal direction from home (N, NE, E, SE, S, SW, W, NW)
-   Last updated timestamp
-   Elapsed time since last significant location change (10 meters cumulative)

### Managing Trackers and Attributes

1. Go to Settings > Devices & Services
2. Find "TRSDM Dynamic Device Tracker" and click "Configure"
3. Here you can:
    - Add new trackers
    - View webhook URLs for existing trackers
    - Delete custom attributes you no longer need (remember to remove them from the payload as well)

## Important Notes

-   Attributes are not persisted across Home Assistant restarts. They will be repopulated on the next webhook event.
-   There are no rate limits on webhook calls other than those imposed by your Home Assistant instance.

## Use Cases

-   Track your car using a GPS device like the LilyGo T-SIM7600X
-   Monitor custom IoT devices that can send location data
-   Test and develop location-based automations using tools like Postman or curl

## Support

If you find this integration helpful, please consider donating to a local charity instead of the developer.

Need help? Have questions? Please open an issue on the GitHub repository.

Happy tracking!
