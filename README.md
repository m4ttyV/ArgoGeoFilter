# ArgoGeoFilter

CLI tool for filtering and converting **Argo oceanographic NetCDF profiles** into CSV datasets.

The application processes Argo profile data, applies geographic and temporal filters, calculates depth from pressure using seawater density derived from temperature, salinity and pressure, and exports measurements grouped by observation date.

## Features

- Argo NetCDF profile processing
- Geographic filtering by latitude and longitude
- Time-window filtering by observation date
- File-age filtering
- Support for adjusted Argo variables when available
- Seawater density calculation using the UNESCO 1981 equation
- Iterative depth calculation from pressure, density and local gravity
- Latitude-dependent gravity correction
- Longitude normalization to `[0, 360)`
- CSV export grouped by observation date
- Processed-file tracking to avoid duplicate processing
- Command-line interface for automated workflows

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Xarray | NetCDF dataset processing |
| NumPy | Numerical calculations |
| NetCDF4 | NetCDF backend |
| CSV | Output format |

## Processing Pipeline

```text
Argo NetCDF files
        │
        ▼
      Xarray
        │
        ├── File-age filtering
        ├── Observation-date filtering
        ├── Geographic filtering
        ├── Adjusted/raw variable selection
        │
        ▼
Seawater density calculation
      UNESCO 1981
        │
        ▼
 Iterative depth calculation
   pressure + density + gravity
        │
        ▼
 Longitude normalization
        │
        ▼
 CSV files by observation date
```
