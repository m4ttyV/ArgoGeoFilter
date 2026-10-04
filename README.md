# ArgoGeoFilter

CLI tool for filtering and converting **Argo oceanographic NetCDF profiles** into CSV datasets.

The application processes Argo profile data, applies geographic and temporal filters, converts pressure to depth using **TEOS-10**, and exports measurements grouped by observation date.

## Features

- Argo NetCDF profile processing
- Geographic filtering by latitude and longitude
- Time-window filtering
- Pressure-to-depth conversion using `gsw.z_from_p`
- TEOS-10 based depth calculation
- Longitude normalization to `[0, 360)`
- CSV export grouped by observation date
- Processed-file tracking to avoid duplicate processing
- Command-line interface for automated workflows

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Xarray | NetCDF dataset processing |
| NumPy | Numerical operations |
| GSW-Python | TEOS-10 calculations |
| NetCDF4 | NetCDF backend |
| CSV | Output format |

## Processing Pipeline

```text
Argo NetCDF files
        │
        ▼
     Xarray
        │
        ├── Geographic filter
        ├── Time filter
        ├── Missing-value handling
        │
        ▼
TEOS-10 depth calculation
   gsw.z_from_p()
        │
        ▼
 Longitude normalization
        │
        ▼
 CSV files by observation date
```
## License

This project is licensed under the MIT License.
