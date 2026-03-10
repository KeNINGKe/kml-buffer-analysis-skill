# -*- coding: utf-8 -*-
"""
File parser for KML/KMZ/SHP files.
Extracts line features from various geospatial file formats.
"""

import os
import zipfile
from lxml import etree
import fiona
from shapely.geometry import LineString, shape


def parse_input_file(file_path):
    """
    Parse input file and extract line features.
    
    Args:
        file_path: Path to KML/KMZ/SHP file
        
    Returns:
        list: List of Shapely LineString objects
        
    Raises:
        ValueError: If file format is not supported or no lines found
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.kmz':
        return _parse_kmz(file_path)
    elif ext == '.kml':
        return _parse_kml(file_path)
    elif ext == '.shp':
        return _parse_shp(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _parse_kmz(kmz_path):
    """Parse KMZ file and extract line features."""
    with zipfile.ZipFile(kmz_path, 'r') as zf:
        kml_files = [f for f in zf.namelist() if f.endswith('.kml')]
        if not kml_files:
            raise ValueError(f"No KML file found in {kmz_path}")
        
        with zf.open(kml_files[0]) as kml_file:
            kml_content = kml_file.read()
    
    return _parse_kml_content(kml_content)


def _parse_kml(kml_path):
    """Parse KML file and extract line features."""
    with open(kml_path, 'r', encoding='utf-8') as f:
        kml_content = f.read().encode('utf-8')
    
    return _parse_kml_content(kml_content)


def _parse_kml_content(kml_content):
    """Parse KML content and extract LineString geometries."""
    root = etree.fromstring(kml_content)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    line_strings = []
    
    for line_elem in root.findall('.//kml:LineString', ns):
        coords_elem = line_elem.find('kml:coordinates', ns)
        if coords_elem is not None:
            coords_str = coords_elem.text.strip()
            coords = []
            
            for coord in coords_str.split():
                parts = coord.split(',')
                if len(parts) >= 2:
                    lon, lat = float(parts[0]), float(parts[1])
                    coords.append((lon, lat))
            
            if len(coords) >= 2:
                line_strings.append(LineString(coords))
    
    if not line_strings:
        raise ValueError("No line features found in KML")
    
    return line_strings


def _parse_shp(shp_path):
    """Parse shapefile and extract line features."""
    line_strings = []
    
    with fiona.open(shp_path, 'r') as src:
        for feature in src:
            if not feature['geometry']:
                continue
            
            geom_type = feature['geometry']['type']
            if geom_type not in ['LineString', 'MultiLineString']:
                continue
            
            geom = shape(feature['geometry'])
            
            if geom.geom_type == 'LineString':
                line_strings.append(geom)
            elif geom.geom_type == 'MultiLineString':
                line_strings.extend(geom.geoms)
    
    if not line_strings:
        raise ValueError("No line features found in shapefile")
    
    return line_strings


def load_building_data(building_shp, encoding='gbk'):
    """
    Load building data from shapefile.
    
    Args:
        building_shp: Path to building shapefile
        encoding: File encoding (default: gbk)
        
    Returns:
        tuple: (buildings list, schema, crs)
    """
    with fiona.open(building_shp, 'r', encoding=encoding) as src:
        schema = src.schema
        crs = src.crs
        buildings = []
        
        for feature in src:
            # Ensure all property values are strings
            properties = {}
            for key, value in feature['properties'].items():
                properties[key] = str(value) if value is not None else ''
            
            feature['properties'] = properties
            buildings.append(feature)
    
    return buildings, schema, crs
