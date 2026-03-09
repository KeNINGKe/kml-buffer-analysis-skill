# -*- coding: utf-8 -*-
"""
KML文件缓冲区分析脚本 - 修正版
功能：
1. 读取KMZ文件中的线要素
2. 对每条线创建800米半径的缓冲区
3. 融合同一KMZ文件中的缓冲区为一个面
4. 与建筑shp数据相交，得到缓冲区区域内的建筑
5. 计算人口数、岗位数、人岗密度、容积率
6. 导出到Excel文件
"""

import os
import zipfile
from lxml import etree
from shapely.geometry import LineString, MultiPolygon, Polygon, mapping, shape
import fiona
from fiona.crs import from_epsg
from pyproj import Transformer
import pandas as pd

print("=" * 70)
print("KML文件缓冲区分析 - 修正版")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
building_shp = os.path.join(base_path, '北京市建筑_新分类_final2.shp')
output_excel = os.path.join(base_path, '建筑统计_新kmz.xlsx')

# 创建输出目录
buffer_output_dir = os.path.join(base_path, 'buffer_results_new')
intersect_output_dir = os.path.join(base_path, 'intersect_results_new')
os.makedirs(buffer_output_dir, exist_ok=True)
os.makedirs(intersect_output_dir, exist_ok=True)

# 定义坐标系转换器
transformer_to_4527 = Transformer.from_crs('EPSG:4326', 'EPSG:4527')

# 定义几何转换函数（WGS84 -> EPSG:4527）
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

# 读取建筑shp文件
print("\n[1/4] 读取建筑数据...")
with fiona.open(building_shp, 'r', encoding='gbk') as src:
    building_schema = src.schema
    building_crs = src.crs
    buildings = []
    for feature in src:
        properties = {}
        for key, value in feature['properties'].items():
            if value is not None:
                properties[key] = str(value)
            else:
                properties[key] = ''
        feature['properties'] = properties
        buildings.append(feature)
print(f"   建筑数据记录数: {len(buildings)}")

# 只处理指定的两个KMZ文件
kmz_files = ['1号线北延.kmz', '4-9联络线.kmz']
print(f"\n[2/4] 处理 {len(kmz_files)} 个KMZ文件")

# 存储所有统计数据
all_stats = []

for kmz_file in kmz_files:
    kmz_path = os.path.join(base_path, kmz_file)
    kmz_name = os.path.splitext(kmz_file)[0]
    print(f"\n   处理: {kmz_name}")
    
    # 解压KMZ文件
    with zipfile.ZipFile(kmz_path, 'r') as zf:
        kml_files_in_kmz = [f for f in zf.namelist() if f.endswith('.kml')]
        if not kml_files_in_kmz:
            print(f"      警告: {kmz_file} 中没有找到KML文件")
            continue
        
        with zf.open(kml_files_in_kmz[0]) as kml_file_obj:
            kml_content = kml_file_obj.read()
    
    # 解析KML文件
    root = etree.fromstring(kml_content)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    # 提取线要素
    line_strings = []
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
    
    print(f"      提取到 {len(line_strings)} 条线")
    
    if not line_strings:
        print(f"      警告: {kmz_name} 中没有找到线要素")
        continue
    
    # 确定UTM投影带（基于第一条线的中心点）
    first_line = line_strings[0]
    centroid = first_line.centroid
    lon, lat = centroid.x, centroid.y
    utm_zone = int((lon + 180) / 6) + 1
    
    # 创建WGS84到UTM的转换器
    transformer_to_utm = Transformer.from_crs('EPSG:4326', f'EPSG:326{utm_zone:02d}')
    transformer_to_wgs84 = Transformer.from_crs(f'EPSG:326{utm_zone:02d}', 'EPSG:4326')
    
    # 创建缓冲区并融合（在UTM坐标系中）
    buffers = []
    for line in line_strings:
        coords_wgs84 = list(line.coords)
        # 注意：transformer的参数顺序是(lat, lon)，返回(x, y)
        coords_utm = [transformer_to_utm.transform(lat, lon) for lon, lat in coords_wgs84]
        line_utm = LineString(coords_utm)
        buffer_utm = line_utm.buffer(800)
        buffers.append(buffer_utm)
    
    # 融合缓冲区
    if len(buffers) == 1:
        merged_buffer_utm = buffers[0]
    else:
        merged_buffer_utm = MultiPolygon(buffers).buffer(0)
    
    # 计算buffer的实际面积（单位：平方米）
    buffer_area = merged_buffer_utm.area
    print(f"      Buffer面积: {buffer_area:.2f} 平方米")
    
    # 将缓冲区转换回WGS84坐标系
    def transform_geom_to_wgs84(geom):
        if isinstance(geom, Polygon):
            # 注意：transformer的参数顺序是(x, y)，返回(lat, lon)
            exterior = []
            for x, y in geom.exterior.coords:
                lat, lon = transformer_to_wgs84.transform(x, y)
                exterior.append((lon, lat))  # 转换为(lon, lat)格式
            
            interiors = []
            for interior in geom.interiors:
                interior_coords = []
                for x, y in interior.coords:
                    lat, lon = transformer_to_wgs84.transform(x, y)
                    interior_coords.append((lon, lat))
                interiors.append(interior_coords)
            
            return Polygon(exterior, interiors)
        elif isinstance(geom, MultiPolygon):
            polygons = [transform_geom_to_wgs84(polygon) for polygon in geom.geoms]
            return MultiPolygon(polygons)
        return geom
    
    merged_buffer = transform_geom_to_wgs84(merged_buffer_utm)
    
    # 检查缓冲区范围
    buffer_bbox = merged_buffer.bounds
    print(f"      缓冲区范围: {buffer_bbox}")
    
    # 保存缓冲区为shp文件
    buffer_shp = os.path.join(buffer_output_dir, f'{kmz_name}_buffer.shp')
    schema = {
        'geometry': 'Polygon',
        'properties': {'name': 'str:100', 'area': 'float:10.2'}
    }
    
    with fiona.open(buffer_shp, 'w', driver='ESRI Shapefile', schema=schema, crs=from_epsg(4326), encoding='gbk') as dst:
        if isinstance(merged_buffer, Polygon):
            dst.write({
                'geometry': mapping(merged_buffer),
                'properties': {'name': kmz_name, 'area': buffer_area}
            })
        elif isinstance(merged_buffer, MultiPolygon):
            for polygon in merged_buffer.geoms:
                dst.write({
                    'geometry': mapping(polygon),
                    'properties': {'name': kmz_name, 'area': buffer_area}
                })
    print(f"      保存缓冲区文件: {os.path.basename(buffer_shp)}")
    
    # 与建筑数据相交
    print("      与建筑数据相交...")
    intersect_buildings = []
    
    for building in buildings:
        building_geom = shape(building['geometry'])
        if merged_buffer.intersects(building_geom):
            intersect_buildings.append(building)
    
    print(f"      相交建筑数: {len(intersect_buildings)}")
    
    # 保存相交结果
    if intersect_buildings:
        intersect_shp = os.path.join(intersect_output_dir, f'{kmz_name}_buildings.shp')
        
        ascii_schema = {'geometry': building_schema['geometry'], 'properties': {}}
        field_mapping = {}
        for field_name, field_type in building_schema['properties'].items():
            if field_name == '新分类':
                ascii_field_name = 'new_class'
            else:
                ascii_field_name = ''.join([c if ord(c) < 128 else '_' for c in field_name])
                ascii_field_name = ascii_field_name[:10]
            ascii_schema['properties'][ascii_field_name] = field_type
            field_mapping[field_name] = ascii_field_name
        
        ascii_schema['properties']['buffer_name'] = 'str:100'
        ascii_schema['properties']['area'] = 'float:10.2'
        ascii_schema['properties']['buffer_area'] = 'float:10.2'
        
        with fiona.open(intersect_shp, 'w', driver='ESRI Shapefile', schema=ascii_schema, crs=building_crs, encoding='gbk') as dst:
            for building in intersect_buildings:
                ascii_properties = {}
                for field_name, value in building['properties'].items():
                    ascii_field_name = field_mapping.get(field_name, ''.join([c if ord(c) < 128 else '_' for c in field_name])[:10])
                    if value is not None:
                        ascii_properties[ascii_field_name] = str(value)
                    else:
                        ascii_properties[ascii_field_name] = ''
                
                ascii_properties['buffer_name'] = kmz_name
                ascii_properties['buffer_area'] = buffer_area
                
                building_geom = shape(building['geometry'])
                building_geom_4527 = transform_geom_to_4527(building_geom)
                area = building_geom_4527.area
                ascii_properties['area'] = area
                
                dst.write({
                    'geometry': building['geometry'],
                    'properties': ascii_properties
                })
        print(f"      保存相交结果: {os.path.basename(intersect_shp)}")
        
        # 计算统计数据
        print("      计算统计数据...")
        
        # 按new_class分组统计
        class_stats = {}
        for building in intersect_buildings:
            properties = building['properties']
            new_class = properties.get('新分类', '')
            
            building_geom = shape(building['geometry'])
            building_geom_4527 = transform_geom_to_4527(building_geom)
            area = building_geom_4527.area
            
            # 提取height字段
            height = 0
            for key in properties:
                if 'height' in key.lower() or '高度' in key or '高' in key:
                    try:
                        height = float(properties[key])
                    except:
                        height = 0
                    break
            
            # 计算建筑面积
            building_area = (height / 4) * area if height > 0 else 0
            
            if new_class not in class_stats:
                class_stats[new_class] = {'area': 0, 'building_area': 0}
            
            class_stats[new_class]['area'] += area
            class_stats[new_class]['building_area'] += building_area
        
        # 计算人口数、岗位数
        per_capita_living_area = 34.71
        per_capita_office_area = 10
        
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
        
        # 计算容积率
        plot_ratio = total_building_area / total_area if total_area > 0 else 0
        
        # 计算人岗密度（单位：人/平方公里）
        # buffer_area单位是平方米，需要转换为平方公里（1平方公里 = 1,000,000平方米）
        density = (population + jobs) / buffer_area * 1000000 if buffer_area > 0 else 0
        
        # 保存统计数据
        stats_record = {
            'buffer_name': kmz_name,
            'buffer面积': buffer_area,
            '人口数': population,
            '岗位数': jobs,
            '容积率': plot_ratio,
            '人岗密度': density
        }
        
        # 添加各类建筑面积
        for new_class, stats in class_stats.items():
            stats_record[f'{new_class}_面积'] = stats['area']
            stats_record[f'{new_class}_建筑面积'] = stats['building_area']
        
        all_stats.append(stats_record)
        
        print(f"      人口数: {population:.2f}")
        print(f"      岗位数: {jobs:.2f}")
        print(f"      容积率: {plot_ratio:.4f}")
        print(f"      人岗密度: {density:.2f} 人/平方公里")
    else:
        # 如果没有相交建筑，保存空记录
        stats_record = {
            'buffer_name': kmz_name,
            'buffer面积': buffer_area,
            '人口数': 0,
            '岗位数': 0,
            '容积率': 0,
            '人岗密度': 0
        }
        all_stats.append(stats_record)

# 导出到Excel
print("\n[3/4] 导出到Excel...")
df = pd.DataFrame(all_stats)
df.to_excel(output_excel, index=False)

print(f"\n[4/4] 处理完成!")
print(f"Excel文件保存路径: {output_excel}")
if len(df) > 0:
    print(f"\n统计结果预览:")
    print(df[['buffer_name', 'buffer面积', '人口数', '岗位数', '容积率', '人岗密度']])
