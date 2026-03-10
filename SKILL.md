---
name: "kml-buffer-analysis"
description: "Performs buffer analysis on KML/KMZ or SHP files, intersects with building data, and exports statistics to Excel. Modular library with CLI interface."
---

# KML Buffer Analysis Skill

A modular Python library for analyzing buffer zones around linear features in KML/KMZ/SHP files, intersecting with building data, and generating statistical reports.

## Features

- **Multi-format support**: KML, KMZ, and Shapefile inputs
- **Accurate buffering**: Uses UTM projection for precise distance calculations
- **Flexible intersection**: Choose between centroid or intersects methods
- **Comprehensive statistics**: Population, jobs, plot ratio, and density calculations
- **Modular design**: Use as a library or CLI tool
- **Configurable**: JSON-based configuration for easy customization

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Command Line Usage

```bash
# Process all files in a directory
python main.py --config config.json --input input_dir --output output_dir

# Process specific files
python main.py --input input_dir --output output_dir --files line1.kmz line2.kml

# Override building shapefile path
python main.py --input input_dir --output output_dir --building-shp path/to/buildings.shp
```

### Library Usage

```python
from kml_buffer import (
    parse_input_file,
    create_buffer,
    find_intersecting_buildings,
    calculate_statistics
)

# Parse input file
line_strings = parse_input_file('transit_line.kmz')

# Create 800m buffer
buffer_geom, buffer_area, utm_crs = create_buffer(line_strings, radius_meters=800)

# Find intersecting buildings
intersecting = find_intersecting_buildings(buffer_geom, buildings, method='centroid')

# Calculate statistics
stats = calculate_statistics(intersecting, buffer_area, config)
```

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "paths": {
    "building_shp": "path/to/building.shp"
  },
  "buffer": {
    "radius_meters": 800,
    "intersect_method": "centroid"
  },
  "statistics": {
    "per_capita_living_area": 34.71,
    "per_capita_office_area": 10,
    "residential_class": "住宅",
    "office_classes": ["办公", "医疗", "政府"]
  },
  "coordinate_systems": {
    "input_crs": "EPSG:4326",
    "area_calculation_crs": "EPSG:4527"
  }
}
```

### Configuration Options

**buffer.intersect_method**
- `centroid`: Building centroid must be within buffer (stricter)
- `intersects`: Any intersection counts (more inclusive)

**statistics**
- `per_capita_living_area`: Living area per person (㎡/person)
- `per_capita_office_area`: Office area per person (㎡/person)
- `residential_class`: Name of residential building class
- `office_classes`: List of office-related building classes

## Workflow

1. **Parse input files** - Extract line features from KML/KMZ/SHP
2. **Create buffers** - Generate buffers in UTM projection for accuracy
3. **Merge buffers** - Combine multiple buffers from same file
4. **Intersect with buildings** - Find buildings within buffer zones
5. **Calculate statistics** - Compute area, population, jobs, plot ratio, density
6. **Export results** - Save shapefiles and Excel report

## Output Structure

```
output_dir/
├── buffers/
│   ├── line1_buffer.shp
│   └── line2_buffer.shp
├── intersecting_buildings/
│   ├── line1_buildings.shp
│   └── line2_buildings.shp
└── 建筑统计.xlsx
```

## Module Reference

### parser.py
- `parse_input_file(file_path)` - Parse KML/KMZ/SHP and extract lines
- `load_building_data(shp_path, encoding)` - Load building shapefile

### buffer.py
- `create_buffer(lines, radius_meters)` - Create accurate buffers in UTM
- `merge_buffers(buffers)` - Merge multiple buffer polygons

### intersect.py
- `find_intersecting_buildings(buffer, buildings, method)` - Find intersections
- `save_buffer_shapefile(...)` - Save buffer to shapefile
- `save_intersecting_buildings(...)` - Save intersecting buildings

### stats.py
- `calculate_statistics(buildings, buffer_area, config)` - Calculate all statistics
- `format_statistics_for_export(name, stats)` - Format for Excel export

### export.py
- `export_to_excel(records, output_path)` - Export statistics to Excel

### utils.py
- `CoordinateTransformer` - Cached coordinate transformations
- `calculate_utm_zone(lon, lat)` - Determine UTM zone
- `extract_height_from_properties(props)` - Extract building height

## Technical Details

### Coordinate Systems
- **Input**: WGS84 (EPSG:4326)
- **Buffer calculation**: UTM (auto-detected zone)
- **Area calculation**: EPSG:4527 (CGCS2000 / 3-degree Gauss-Kruger zone 39)

### Calculations
- **Building area**: `(height / 4) × footprint_area`
- **Population**: `residential_building_area / per_capita_living_area`
- **Jobs**: `office_building_area / per_capita_office_area`
- **Plot ratio**: `total_building_area / total_footprint_area`
- **Density**: `(population + jobs) / buffer_area × 1,000,000` (people/km²)

### Encoding
- Shapefiles use GBK encoding
- Chinese field names are mapped to ASCII equivalents
- Field names limited to 10 characters (shapefile constraint)

## Common Issues

### Chinese Characters in Shapefiles
Ensure building shapefile uses GBK encoding and has a .cpg file with content `GBK`

### Field Name Limitations
Shapefile field names must be ASCII and ≤10 characters. The library automatically converts:
- `新分类` → `new_class`
- Other Chinese fields → ASCII equivalents

### Coordinate Transformation
The library automatically:
- Detects appropriate UTM zone based on input location
- Handles coordinate order differences between CRS
- Caches transformers for performance

## Best Practices

1. **Data preparation**: Ensure building shapefile has consistent attribute names
2. **Coordinate systems**: Verify input data is in WGS84
3. **Buffer radius**: Choose appropriate radius for analysis scale
4. **Intersection method**: Use `centroid` for stricter inclusion, `intersects` for broader coverage
5. **Configuration**: Store project-specific settings in separate config files

## Extending the Library

### Adding New File Formats

Edit `kml_buffer/parser.py`:

```python
def _parse_geojson(geojson_path):
    """Parse GeoJSON and extract line features."""
    # Implementation here
    pass
```

### Custom Statistics

Edit `kml_buffer/stats.py`:

```python
def calculate_custom_metric(buildings, config):
    """Calculate custom metric."""
    # Implementation here
    pass
```

### New Export Formats

Edit `kml_buffer/export.py`:

```python
def export_to_csv(records, output_path):
    """Export to CSV format."""
    # Implementation here
    pass
```

## Performance Tips

- **Large datasets**: Process files in batches
- **Coordinate transformations**: Transformers are cached automatically
- **Memory usage**: Buildings are loaded once and reused
- **Parallel processing**: Process multiple files in parallel (future enhancement)

## Troubleshooting

### No line features found
- Verify input file contains LineString or MultiLineString geometries
- Check KML namespace (should be `http://www.opengis.net/kml/2.2`)

### Incorrect buffer area
- Ensure input coordinates are in WGS84
- Verify UTM zone is correctly detected
- Check buffer radius units (meters)

### Missing statistics
- Verify building shapefile has required fields (`新分类`, height)
- Check building class names match configuration
- Ensure buildings intersect with buffer

## License

MIT
