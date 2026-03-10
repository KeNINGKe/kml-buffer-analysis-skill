# -*- coding: utf-8 -*-
"""
Building intersection analysis.
"""

import fiona
from shapely.geometry import shape, mapping
from fiona.crs import from_epsg
from .utils import CoordinateTransformer


def find_intersecting_buildings(buffer_geom, buildings, method='centroid'):
    """
    Find buildings that intersect with buffer zone.
    
    Args:
        buffer_geom: Shapely geometry of buffer zone
        buildings: List of building features
        method: Intersection method ('centroid' or 'intersects')
        
    Returns:
        list: Buildings that intersect with buffer
    """
    intersecting = []
    
    for building in buildings:
        building_geom = shape(building['geometry'])
        
        if method == 'centroid':
            # Check if building centroid is within buffer
            if buffer_geom.contains(building_geom.centroid):
                intersecting.append(building)
        elif method == 'intersects':
            # Check if building intersects with buffer
            if buffer_geom.intersects(building_geom):
                intersecting.append(building)
        else:
            raise ValueError(f"Unknown intersection method: {method}")
    
    return intersecting


def save_buffer_shapefile(buffer_geom, buffer_area, buffer_name, output_path, encoding='gbk'):
    """
    Save buffer geometry to shapefile.
    
    Args:
        buffer_geom: Shapely geometry
        buffer_area: Buffer area in square meters
        buffer_name: Name of the buffer
        output_path: Output shapefile path
        encoding: File encoding
    """
    schema = {
        'geometry': 'Polygon',
        'properties': {
            'name': 'str:100',
            'area': 'float:19.2'
        }
    }
    
    with fiona.open(output_path, 'w', driver='ESRI Shapefile', 
                   schema=schema, crs=from_epsg(4326), encoding=encoding) as dst:
        
        if buffer_geom.geom_type == 'Polygon':
            dst.write({
                'geometry': mapping(buffer_geom),
                'properties': {
                    'name': buffer_name,
                    'area': buffer_area
                }
            })
        elif buffer_geom.geom_type == 'MultiPolygon':
            for polygon in buffer_geom.geoms:
                dst.write({
                    'geometry': mapping(polygon),
                    'properties': {
                        'name': buffer_name,
                        'area': buffer_area
                    }
                })


def save_intersecting_buildings(buildings, buffer_name, buffer_area, building_schema, 
                                building_crs, output_path, area_crs='EPSG:4527', 
                                encoding='gbk'):
    """
    Save intersecting buildings to shapefile with calculated areas.
    
    Args:
        buildings: List of building features
        buffer_name: Name of the buffer
        buffer_area: Buffer area in square meters
        building_schema: Original building schema
        building_crs: Original building CRS
        output_path: Output shapefile path
        area_crs: CRS for area calculation
        encoding: File encoding
    """
    if not buildings:
        return
    
    # Create ASCII-compatible schema
    ascii_schema = {'geometry': building_schema['geometry'], 'properties': {}}
    field_mapping = {}
    
    for field_name, field_type in building_schema['properties'].items():
        if field_name == '新分类':
            ascii_field_name = 'new_class'
        else:
            # Create ASCII-compatible field name
            ascii_field_name = ''.join([c if ord(c) < 128 else '_' for c in field_name])
            ascii_field_name = ascii_field_name[:10]
        
        ascii_schema['properties'][ascii_field_name] = field_type
        field_mapping[field_name] = ascii_field_name
    
    # Add buffer-related fields
    ascii_schema['properties']['buffer_nam'] = 'str:100'
    ascii_schema['properties']['area'] = 'float:19.2'
    ascii_schema['properties']['buffer_are'] = 'float:19.2'
    
    # Initialize transformer
    transformer = CoordinateTransformer()
    
    with fiona.open(output_path, 'w', driver='ESRI Shapefile', 
                   schema=ascii_schema, crs=building_crs, encoding=encoding) as dst:
        
        for building in buildings:
            # Map field names to ASCII
            ascii_properties = {}
            for field_name, value in building['properties'].items():
                ascii_field_name = field_mapping.get(
                    field_name, 
                    ''.join([c if ord(c) < 128 else '_' for c in field_name])[:10]
                )
                ascii_properties[ascii_field_name] = str(value) if value is not None else ''
            
            # Add buffer information
            ascii_properties['buffer_nam'] = buffer_name
            ascii_properties['buffer_are'] = buffer_area
            
            # Calculate building area in specified CRS
            building_geom = shape(building['geometry'])
            building_geom_projected = transformer.transform_geometry(
                building_geom, 'EPSG:4326', area_crs
            )
            ascii_properties['area'] = building_geom_projected.area
            
            # Write feature
            dst.write({
                'geometry': building['geometry'],
                'properties': ascii_properties
            })
