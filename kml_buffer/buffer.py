# -*- coding: utf-8 -*-
"""
Buffer creation and merging operations.
"""

from shapely.geometry import MultiPolygon
from .utils import CoordinateTransformer, calculate_utm_zone


def create_buffer(line_strings, radius_meters=800):
    """
    Create buffers around line features with accurate distance calculation.
    
    Args:
        line_strings: List of Shapely LineString objects in WGS84
        radius_meters: Buffer radius in meters
        
    Returns:
        tuple: (merged_buffer_wgs84, buffer_area_sqm, utm_crs)
    """
    if not line_strings:
        raise ValueError("No line strings provided")
    
    # Determine UTM zone from first line's centroid
    first_line = line_strings[0]
    centroid = first_line.centroid
    utm_crs = calculate_utm_zone(centroid.x, centroid.y)
    
    # Initialize transformer
    transformer = CoordinateTransformer()
    
    # Create buffers in UTM projection for accurate distance
    buffers_utm = []
    for line in line_strings:
        # Transform line to UTM
        line_utm = transformer.transform_geometry(line, 'EPSG:4326', utm_crs)
        
        # Create buffer
        buffer_utm = line_utm.buffer(radius_meters)
        buffers_utm.append(buffer_utm)
    
    # Merge buffers
    merged_buffer_utm = merge_buffers(buffers_utm)
    
    # Calculate area in square meters
    buffer_area = merged_buffer_utm.area
    
    # Transform back to WGS84
    merged_buffer_wgs84 = transformer.transform_geometry(
        merged_buffer_utm, utm_crs, 'EPSG:4326'
    )
    
    return merged_buffer_wgs84, buffer_area, utm_crs


def merge_buffers(buffers):
    """
    Merge multiple buffer polygons into one.
    
    Args:
        buffers: List of Shapely Polygon objects
        
    Returns:
        Polygon or MultiPolygon: Merged buffer
    """
    if len(buffers) == 1:
        return buffers[0]
    
    # Use buffer(0) to dissolve overlapping polygons
    multi = MultiPolygon(buffers)
    return multi.buffer(0)
