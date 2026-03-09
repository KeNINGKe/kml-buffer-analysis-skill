---
name: "kml-buffer-analysis"
description: "Performs buffer analysis on KML/KMZ or SHP files, intersects with building data, and exports statistics to Excel. Invoke when user needs to analyze buffer zones around linear features and calculate related statistics."
---

# KML Buffer Analysis Skill

This skill provides a complete workflow for analyzing buffer zones around linear features in KML files, intersecting with building data, and generating statistical reports.

## Workflow Overview

1. **Read input files** - Extract line features from KML/KMZ or SHP files
2. **Create buffers** - Generate 800m radius buffers around lines
3. **Merge buffers** - Combine multiple buffers in the same file
4. **Intersect with buildings** - Identify buildings within buffer zones
5. **Calculate statistics** - Compute area, building area, population, jobs, and plot ratio
6. **Export to Excel** - Generate comprehensive Excel reports

## Required Libraries

- `fiona` - For reading and writing shapefiles
- `shapely` - For geometric operations
- `pandas` - For data manipulation and Excel export
- `lxml` - For parsing KML files
- `zipfile` - For extracting KMZ files

## Step-by-Step Implementation

### 1. Extract Line Features from Input Files

#### Automatic File Type Detection

```python
import os
import zipfile
from lxml import etree
import fiona
from shapely.geometry import LineString, shape

def extract_line_features(file_path):
    """Extract line features from KML/KMZ or SHP files"""
    line_strings = []
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.kml', '.kmz']:
        # Handle KML/KMZ files
        if ext == '.kmz':
            # Extract KML from KMZ
            with zipfile.ZipFile(file_path, 'r') as zf:
                kml_files = [f for f in zf.namelist() if f.endswith('.kml')]
                if not kml_files:
                    return []
                with zf.open(kml_files[0]) as kml_file_obj:
                    kml_content = kml_file_obj.read()
        else:
            # Read KML file directly
            with open(file_path, 'r', encoding='utf-8') as f:
                kml_content = f.read().encode('utf-8')
        
        # Parse KML
        root = etree.fromstring(kml_content)
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        for line_elem in root.findall('.//kml:LineString', ns):
            coords_elem = line_elem.find('kml:coordinates', ns)
            if coords_elem is not None:
                coords_str = coords_elem.text.strip()
                coords = []
                for coord in coords_str.split():
                    lon, lat, _ = map(float, coord.split(','))
                    coords.append((lon, lat))
                if len(coords) >= 2:
                    line = LineString(coords)
                    line_strings.append(line)
    
    elif ext == '.shp':
        # Handle SHP files
        with fiona.open(file_path, 'r') as src:
            for feature in src:
                if feature['geometry'] and feature['geometry']['type'] in ['LineString', 'MultiLineString']:
                    geom = shape(feature['geometry'])
                    if geom.geom_type == 'LineString':
                        line_strings.append(geom)
                    elif geom.geom_type == 'MultiLineString':
                        for line in geom.geoms:
                            line_strings.append(line)
    
    return line_strings

# Usage
line_strings = extract_line_features('path/to/input/file.(kml|kmz|shp)')
```

### 2. Create and Merge Buffers with Accurate Projection

```python
from shapely.geometry import MultiPolygon, LineString, Polygon
from pyproj import Transformer

# Determine UTM zone based on the first line's centroid
first_line = line_strings[0]
centroid = first_line.centroid
lon, lat = centroid.x, centroid.y
utm_zone = int((lon + 180) / 6) + 1

# Create transformers for accurate buffer creation
transformer_to_utm = Transformer.from_crs('EPSG:4326', f'EPSG:326{utm_zone:02d}')
transformer_to_wgs84 = Transformer.from_crs(f'EPSG:326{utm_zone:02d}', 'EPSG:4326')

# Create buffers in UTM projection for accurate distance
buffers = []
for line in line_strings:
    # Convert line to UTM coordinates
    # IMPORTANT: transformer parameter order is (lat, lon), returns (x, y)
    coords_wgs84 = list(line.coords)
    coords_utm = [transformer_to_utm.transform(lat, lon) for lon, lat in coords_wgs84]
    line_utm = LineString(coords_utm)
    
    # Create 800m buffer
    buffer_utm = line_utm.buffer(800)
    buffers.append(buffer_utm)

# Merge buffers
if len(buffers) == 1:
    merged_buffer_utm = buffers[0]
else:
    merged_buffer_utm = MultiPolygon(buffers).buffer(0)

# Calculate buffer area in square meters
buffer_area = merged_buffer_utm.area

# Convert buffer back to WGS84 for intersection
# IMPORTANT: transformer parameter order is (x, y), returns (lat, lon)
def transform_geom_to_wgs84(geom):
    if geom.geom_type == 'Polygon':
        exterior = []
        for x, y in geom.exterior.coords:
            lat, lon = transformer_to_wgs84.transform(x, y)
            exterior.append((lon, lat))  # Convert to (lon, lat) format
        interiors = []
        for interior in geom.interiors:
            interior_coords = []
            for x, y in interior.coords:
                lat, lon = transformer_to_wgs84.transform(x, y)
                interior_coords.append((lon, lat))
            interiors.append(interior_coords)
        return Polygon(exterior, interiors)
    elif geom.geom_type == 'MultiPolygon':
        polygons = [transform_geom_to_wgs84(polygon) for polygon in geom.geoms]
        return MultiPolygon(polygons)
    return geom

merged_buffer = transform_geom_to_wgs84(merged_buffer_utm)
```

### 3. Project Buffer to EPSG:4527 for Area Calculation

```python
# Create transformer to EPSG:4527 (CGCS2000 / 3-degree Gauss-Kruger zone 39)
transformer_to_4527 = Transformer.from_crs('EPSG:4326', 'EPSG:4527')

# Convert geometry to EPSG:4527
# IMPORTANT: transformer parameter order is (lat, lon), returns (x, y)
def transform_geom_to_4527(geom):
    if geom.geom_type == 'Polygon':
        exterior = []
        for lon, lat in geom.exterior.coords:
            x, y = transformer_to_4527.transform(lat, lon)
            exterior.append((x, y))
        interiors = []
        for interior in geom.interiors:
            interior_coords = []
            for lon, lat in interior.coords:
                x, y = transformer_to_4527.transform(lat, lon)
                interior_coords.append((x, y))
            interiors.append(interior_coords)
        return Polygon(exterior, interiors)
    elif geom.geom_type == 'MultiPolygon':
        polygons = [transform_geom_to_4527(polygon) for polygon in geom.geoms]
        return MultiPolygon(polygons)
    return geom

# Convert building geometry to EPSG:4527 for accurate area calculation
building_geom_4527 = transform_geom_to_4527(building_geom)

# Calculate area in EPSG:4527 (square meters)
area = building_geom_4527.area
```

### 4. Intersect with Building Data

```python
import fiona
from shapely.geometry import shape

# Read building data
with fiona.open(building_shp, 'r', encoding='gbk') as src:
    buildings = list(src)

# Find intersecting buildings
intersect_buildings = []
for building in buildings:
    building_geom = shape(building['geometry'])
    if building_geom.intersects(merged_buffer):
        intersect_buildings.append(building)
```

### 5. Calculate Statistics and Export

```python
import pandas as pd

# Group statistics by building class
class_stats = {}
for building in intersect_buildings:
    properties = building['properties']
    new_class = properties.get('新分类', '')  # Chinese field name for building class
    
    # Convert building geometry to EPSG:4527 for accurate area calculation
    building_geom = shape(building['geometry'])
    building_geom_4527 = transform_geom_to_4527(building_geom)
    area = building_geom_4527.area
    
    # Extract height
    height = 0
    for key in properties:
        if 'height' in key.lower() or '高度' in key or '高' in key:
            try:
                height = float(properties[key])
            except:
                height = 0
            break
    
    # Calculate building area (height / 4 * footprint area)
    building_area = (height / 4) * area if height > 0 else 0
    
    if new_class not in class_stats:
        class_stats[new_class] = {'area': 0, 'building_area': 0}
    
    class_stats[new_class]['area'] += area
    class_stats[new_class]['building_area'] += building_area

# Calculate population and jobs
per_capita_living_area = 34.71  # 人均居住面积（㎡/人）
per_capita_office_area = 10      # 人均办公面积（㎡/人）

population = 0
jobs = 0
total_building_area = 0
total_area = 0

for new_class, stats in class_stats.items():
    total_building_area += stats['building_area']
    total_area += stats['area']
    
    if new_class == '住宅':
        population = stats['building_area'] / per_capita_living_area
    elif new_class in ['办公', '医疗', '政府']:
        jobs += stats['building_area'] / per_capita_office_area

# Calculate plot ratio (容积率)
plot_ratio = total_building_area / total_area if total_area > 0 else 0

# Calculate population-job density (人岗密度)
# Unit: people per square kilometer
# buffer_area is in square meters, convert to square kilometers (1 km² = 1,000,000 m²)
density = (population + jobs) / buffer_area * 1000000 if buffer_area > 0 else 0

# Create statistics record
stats_record = {
    'buffer_name': buffer_name,
    'buffer面积': buffer_area,
    '人口数': population,
    '岗位数': jobs,
    '容积率': plot_ratio,
    '人岗密度': density
}

# Add area and building area by class
for new_class, stats in class_stats.items():
    stats_record[f'{new_class}_面积'] = stats['area']
    stats_record[f'{new_class}_建筑面积'] = stats['building_area']

# Export to Excel
df = pd.DataFrame([stats_record])
df.to_excel('建筑统计.xlsx', index=False)
```

## Common Errors and Solutions

### 1. Encoding Issues

**Error**: Chinese characters appear as garbled text in shapefile attributes

**Solution**: 
- Set `encoding='gbk'` when opening shapefiles with fiona
- Create .cpg files with 'GBK' content for all shapefiles
- Ensure consistent encoding throughout the workflow

### 2. File Permission Errors

**Error**: "Permission denied" when writing output files

**Solution**:
- Close any open files in GIS software
- Use different output file names
- Check file system permissions
- Create new output directories if needed

### 3. Field Name Limitations

**Error**: "Failed to create field name" errors

**Solution**:
- Shapefile field names must be ASCII and <= 10 characters
- Map Chinese field names to ASCII equivalents
- Example: '新分类' → 'new_class'

### 4. Geometric Operations

**Error**: Inaccurate buffer creation in geographic coordinates

**Solution**:
- For precise calculations, project geometries to a projected coordinate system
- Use approximate buffer sizes for initial analysis
- Consider using UTM zones for better accuracy

### 5. Large Data Processing

**Error**: Memory issues with large building datasets

**Solution**:
- Process data in chunks if necessary
- Use efficient data structures
- Consider spatial indexing for faster intersections

## Input/Output Examples

### Input
- KML/KMZ files containing linear features
- SHP files containing linear features (LineString or MultiLineString geometries)
- Building shapefile with attributes including '新分类' and height information

### Output
- Buffer shapefiles for each input file (KML/KMZ or SHP)
- Intersected building shapefiles for each buffer zone
- Excel file with statistics including:
  - Area by building type
  - Building area by building type
  - Population estimates
  - Job estimates
  - Plot ratios

## Best Practices

1. **Data Preparation**:
   - Ensure building shapefile has consistent attribute names
   - Verify KML files contain valid line geometries
   - Check coordinate systems are consistent

2. **Performance Optimization**:
   - Use spatial indexing for large datasets
   - Process files in parallel if possible
   - Use appropriate buffer distances for the analysis scale

3. **Quality Control**:
   - Validate buffer creation visually
   - Check intersection results for accuracy
   - Verify statistical calculations with sample data

4. **Documentation**:
   - Document all processing steps
   - Include metadata about data sources
   - Record any assumptions made during analysis

## Troubleshooting

- **KMZ files not found**: Check file paths and ensure KMZ files are in the correct directory
- **No buildings found in buffers**: Verify buffer distance and coordinate systems
- **Excel export errors**: Check file permissions and available disk space
- **Attribute errors**: Ensure building shapefile has required fields

This skill provides a comprehensive workflow for KML buffer analysis and building data intersection, addressing common issues encountered during the process.