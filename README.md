# osmtag-explorer

> Web-based tool for browsing and filtering OpenStreetMap tag usage statistics with live Overpass API queries.

## Overview

osmtag-explorer lets you interactively explore how OpenStreetMap tags are used across the world. Search for keys and values, filter by region, and run live Overpass API queries directly from your browser.

## Installation

```bash
pip install osmtag-explorer
```

Or install from source:

```bash
git clone https://github.com/yourusername/osmtag-explorer.git
cd osmtag-explorer
pip install -e .
```

## Usage

Start the local web server:

```bash
osmtag-explorer serve
```

Then open `http://localhost:8080` in your browser.

**Example — query all nodes tagged `amenity=cafe` in a bounding box:**

```python
from osmtag_explorer import OverpassClient

client = OverpassClient()
results = client.query_tag("amenity", "cafe", bbox=(48.8, 2.3, 48.9, 2.4))
print(results.summary())
```

You can also filter and export tag statistics as CSV or JSON from the web interface.

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `OVERPASS_API_URL` | `https://overpass-api.de/api` | Overpass API endpoint |
| `OST_PORT` | `8080` | Local server port |

## Requirements

- Python 3.9+
- requests
- flask

## License

This project is licensed under the [MIT License](LICENSE).

---

Contributions welcome! Please open an issue or pull request on GitHub.