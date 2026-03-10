"""
KML Buffer Analysis Library

A modular library for buffer analysis on KML/KMZ/SHP files with building data intersection.
"""

__version__ = "1.0.0"

from .parser import parse_input_file
from .buffer import create_buffer, merge_buffers
from .intersect import find_intersecting_buildings
from .stats import calculate_statistics
from .export import export_to_excel

__all__ = [
    'parse_input_file',
    'create_buffer',
    'merge_buffers',
    'find_intersecting_buildings',
    'calculate_statistics',
    'export_to_excel'
]
