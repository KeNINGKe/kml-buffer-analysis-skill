# -*- coding: utf-8 -*-
"""
Utility functions for coordinate transformations and geometry operations.
"""

from shapely.geometry import Polygon, MultiPolygon
from pyproj import Transformer


class CoordinateTransformer:
    """Manages coordinate transformations with cached transformers."""
    
    def __init__(self):
        self._transformers = {}
    
    def get_transformer(self, from_crs, to_crs):
        """Get or create a transformer for the given CRS pair."""
        key = (from_crs, to_crs)
        if key not in self._transformers:
            self._transformers[key] = Transformer.from_crs(from_crs, to_crs)
        return self._transformers[key]
    
    def transform_geometry(self, geom, from_crs, to_crs):
        """Transform a Shapely geometry from one CRS to another."""
        transformer = self.get_transformer(from_crs, to_crs)
        
        if geom.geom_type == 'Polygon':
            return self._transform_polygon(geom, transformer, from_crs, to_crs)
        elif geom.geom_type == 'MultiPolygon':
            polygons = [self._transform_polygon(p, transformer, from_crs, to_crs) 
                       for p in geom.geoms]
            return MultiPolygon(polygons)
        else:
            raise ValueError(f"Unsupported geometry type: {geom.geom_type}")
    
    def _transform_polygon(self, polygon, transformer, from_crs, to_crs):
        """Transform a single polygon."""
        # Determine coordinate order based on CRS
        if 'EPSG:4326' in from_crs:
            # WGS84: input is (lon, lat)
            exterior = [(x, y) for lon, lat in polygon.exterior.coords 
                       for x, y in [transformer.transform(lat, lon)]]
        else:
            # Projected: input is (x, y)
            exterior = [(x, y) for x, y in polygon.exterior.coords 
                       for x, y in [transformer.transform(x, y)]]
        
        # Handle output coordinate order
        if 'EPSG:4326' in to_crs:
            # Output should be (lon, lat)
            exterior = [(lon, lat) for lat, lon in exterior]
        
        # Transform interior rings
        interiors = []
        for interior in polygon.interiors:
            if 'EPSG:4326' in from_crs:
                interior_coords = [(x, y) for lon, lat in interior.coords 
                                  for x, y in [transformer.transform(lat, lon)]]
            else:
                interior_coords = [(x, y) for x, y in interior.coords 
                                  for x, y in [transformer.transform(x, y)]]
            
            if 'EPSG:4326' in to_crs:
                interior_coords = [(lon, lat) for lat, lon in interior_coords]
            
            interiors.append(interior_coords)
        
        return Polygon(exterior, interiors)


def calculate_utm_zone(lon, lat):
    """Calculate UTM zone number from longitude and latitude."""
    utm_zone = int((lon + 180) / 6) + 1
    hemisphere = 'north' if lat >= 0 else 'south'
    epsg_code = f'EPSG:326{utm_zone:02d}' if hemisphere == 'north' else f'EPSG:327{utm_zone:02d}'
    return epsg_code


def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def extract_height_from_properties(properties):
    """Extract height value from building properties."""
    height_keywords = ['height', '高度', '高']
    
    for key in properties:
        key_lower = key.lower()
        if any(keyword in key_lower or keyword in key for keyword in height_keywords):
            return safe_float(properties[key])
    
    return 0.0
