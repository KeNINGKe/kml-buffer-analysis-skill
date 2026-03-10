#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KML Buffer Analysis - Main CLI Entry Point

Usage:
    python main.py --config config.json --input input_dir --output output_dir
    python main.py --help
"""

import os
import sys
import json
import argparse
from pathlib import Path

from kml_buffer import (
    parse_input_file,
    create_buffer,
    find_intersecting_buildings,
    calculate_statistics,
    export_to_excel
)
from kml_buffer.parser import load_building_data
from kml_buffer.intersect import save_buffer_shapefile, save_intersecting_buildings
from kml_buffer.stats import format_statistics_for_export


def load_config(config_path):
    """Load configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def process_file(input_file, building_data, config, output_dirs):
    """Process a single input file."""
    file_name = Path(input_file).stem
    print(f"\n处理: {file_name}")
    
    try:
        # Parse input file
        print("  [1/6] 解析输入文件...")
        line_strings = parse_input_file(input_file)
        print(f"    提取到 {len(line_strings)} 条线")
        
        # Create buffer
        print("  [2/6] 创建缓冲区...")
        buffer_radius = config['buffer']['radius_meters']
        buffer_geom, buffer_area, utm_crs = create_buffer(line_strings, buffer_radius)
        print(f"    缓冲区面积: {buffer_area:.2f} 平方米")
        
        # Save buffer shapefile
        print("  [3/6] 保存缓冲区文件...")
        buffer_output = os.path.join(output_dirs['buffer'], f'{file_name}_buffer.shp')
        save_buffer_shapefile(
            buffer_geom, buffer_area, file_name, buffer_output,
            encoding=config['encoding']['shapefile']
        )
        
        # Find intersecting buildings
        print("  [4/6] 查找相交建筑...")
        buildings, schema, crs = building_data
        intersect_method = config['buffer']['intersect_method']
        intersecting = find_intersecting_buildings(buffer_geom, buildings, intersect_method)
        print(f"    相交建筑数: {len(intersecting)}")
        
        # Save intersecting buildings
        if intersecting:
            print("  [5/6] 保存相交建筑...")
            intersect_output = os.path.join(output_dirs['intersect'], f'{file_name}_buildings.shp')
            save_intersecting_buildings(
                intersecting, file_name, buffer_area, schema, crs, intersect_output,
                area_crs=config['coordinate_systems']['area_calculation_crs'],
                encoding=config['encoding']['shapefile']
            )
        
        # Calculate statistics
        print("  [6/6] 计算统计数据...")
        stats = calculate_statistics(intersecting, buffer_area, config['statistics'])
        stats_record = format_statistics_for_export(file_name, stats)
        
        print(f"    人口数: {stats['population']:.2f}")
        print(f"    岗位数: {stats['jobs']:.2f}")
        print(f"    容积率: {stats['plot_ratio']:.4f}")
        print(f"    人岗密度: {stats['density']:.2f} 人/平方公里")
        
        return stats_record
        
    except Exception as e:
        print(f"  错误: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='KML/KMZ/SHP Buffer Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--config', default='config.json',
                       help='Configuration file path (default: config.json)')
    parser.add_argument('--input', required=True,
                       help='Input directory containing KML/KMZ/SHP files')
    parser.add_argument('--output', required=True,
                       help='Output directory for results')
    parser.add_argument('--building-shp', 
                       help='Building shapefile path (overrides config)')
    parser.add_argument('--files', nargs='+',
                       help='Specific files to process (default: all files in input dir)')
    
    args = parser.parse_args()
    
    # Load configuration
    print("=" * 70)
    print("KML Buffer Analysis")
    print("=" * 70)
    print(f"\n加载配置: {args.config}")
    config = load_config(args.config)
    
    # Override building shapefile if provided
    if args.building_shp:
        config['paths']['building_shp'] = args.building_shp
    
    # Create output directories
    output_dirs = {
        'buffer': os.path.join(args.output, 'buffers'),
        'intersect': os.path.join(args.output, 'intersecting_buildings')
    }
    
    for dir_path in output_dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    # Load building data
    print(f"\n加载建筑数据: {config['paths']['building_shp']}")
    building_data = load_building_data(
        config['paths']['building_shp'],
        encoding=config['encoding']['shapefile']
    )
    print(f"  建筑数据记录数: {len(building_data[0])}")
    
    # Get input files
    if args.files:
        input_files = [os.path.join(args.input, f) for f in args.files]
    else:
        input_files = []
        for ext in ['.kml', '.kmz', '.shp']:
            input_files.extend(Path(args.input).glob(f'*{ext}'))
        input_files = [str(f) for f in input_files]
    
    if not input_files:
        print("\n错误: 未找到输入文件")
        return 1
    
    print(f"\n找到 {len(input_files)} 个输入文件")
    
    # Process files
    all_stats = []
    for input_file in input_files:
        stats = process_file(input_file, building_data, config, output_dirs)
        if stats:
            all_stats.append(stats)
    
    # Export to Excel
    if all_stats:
        excel_output = os.path.join(args.output, '建筑统计.xlsx')
        print(f"\n导出统计数据到 Excel: {excel_output}")
        df = export_to_excel(all_stats, excel_output)
        print("\n统计结果预览:")
        print(df[['buffer_name', 'buffer面积', '人口数', '岗位数', '容积率', '人岗密度']])
    
    print("\n处理完成!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
