# -*- coding: utf-8 -*-
"""
Statistical calculations for building data.
"""

from shapely.geometry import shape
from .utils import CoordinateTransformer, extract_height_from_properties


def calculate_statistics(buildings, buffer_area, config):
    """
    Calculate population, jobs, plot ratio, and density statistics.
    
    Args:
        buildings: List of building features
        buffer_area: Buffer area in square meters
        config: Configuration dictionary with statistics parameters
        
    Returns:
        dict: Statistics including population, jobs, plot_ratio, density, and class breakdown
    """
    # Extract config parameters
    per_capita_living = config.get('per_capita_living_area', 34.71)
    per_capita_office = config.get('per_capita_office_area', 10)
    residential_class = config.get('residential_class', '住宅')
    office_classes = config.get('office_classes', ['办公', '医疗', '政府'])
    area_crs = config.get('area_calculation_crs', 'EPSG:4527')
    
    # Initialize transformer
    transformer = CoordinateTransformer()
    
    # Group statistics by building class
    class_stats = {}
    
    for building in buildings:
        properties = building['properties']
        building_class = properties.get('新分类', properties.get('new_class', ''))
        
        # Calculate building footprint area
        building_geom = shape(building['geometry'])
        building_geom_projected = transformer.transform_geometry(
            building_geom, 'EPSG:4326', area_crs
        )
        footprint_area = building_geom_projected.area
        
        # Extract height and calculate building area
        height = extract_height_from_properties(properties)
        building_area = (height / 4) * footprint_area if height > 0 else 0
        
        # Accumulate by class
        if building_class not in class_stats:
            class_stats[building_class] = {
                'footprint_area': 0,
                'building_area': 0
            }
        
        class_stats[building_class]['footprint_area'] += footprint_area
        class_stats[building_class]['building_area'] += building_area
    
    # Calculate population and jobs
    population = 0
    jobs = 0
    total_building_area = 0
    total_footprint_area = 0
    
    for building_class, stats in class_stats.items():
        total_building_area += stats['building_area']
        total_footprint_area += stats['footprint_area']
        
        if building_class == residential_class:
            population = stats['building_area'] / per_capita_living
        elif building_class in office_classes:
            jobs += stats['building_area'] / per_capita_office
    
    # Calculate plot ratio (容积率)
    plot_ratio = total_building_area / total_footprint_area if total_footprint_area > 0 else 0
    
    # Calculate population-job density (人岗密度)
    # Unit: people per square kilometer
    density = (population + jobs) / buffer_area * 1_000_000 if buffer_area > 0 else 0
    
    return {
        'population': population,
        'jobs': jobs,
        'plot_ratio': plot_ratio,
        'density': density,
        'buffer_area': buffer_area,
        'total_building_area': total_building_area,
        'total_footprint_area': total_footprint_area,
        'class_stats': class_stats
    }


def format_statistics_for_export(buffer_name, stats):
    """
    Format statistics dictionary for Excel export.
    
    Args:
        buffer_name: Name of the buffer
        stats: Statistics dictionary from calculate_statistics
        
    Returns:
        dict: Flattened statistics ready for DataFrame
    """
    record = {
        'buffer_name': buffer_name,
        'buffer面积': stats['buffer_area'],
        '人口数': stats['population'],
        '岗位数': stats['jobs'],
        '容积率': stats['plot_ratio'],
        '人岗密度': stats['density']
    }
    
    # Add class-specific areas
    for building_class, class_data in stats['class_stats'].items():
        record[f'{building_class}_面积'] = class_data['footprint_area']
        record[f'{building_class}_建筑面积'] = class_data['building_area']
    
    return record
