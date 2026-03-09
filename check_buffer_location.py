# -*- coding: utf-8 -*-
"""
检查缓冲区和建筑数据的位置关系
"""

import os
import zipfile
from lxml import etree
from shapely.geometry import LineString, Polygon, shape
import fiona
from pyproj import Transformer

print("=" * 70)
print("检查缓冲区和建筑数据的位置关系")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
building_shp = os.path.join(base_path, '北京市建筑_新分类_final2.shp')

# 读取建筑数据
print("\n[1/3] 读取建筑数据...")
with fiona.open(building_shp, 'r', encoding='gbk') as src:
    buildings = list(src)
    building_bbox = src.bounds
print(f"   建筑数据记录数: {len(buildings)}")
print(f"   建筑数据范围: {building_bbox}")

# 处理KMZ文件
kmz_files = ['1号线北延.kmz', '4-9联络线.kmz']

for kmz_file in kmz_files:
    kmz_path = os.path.join(base_path, kmz_file)
    kmz_name = os.path.splitext(kmz_file)[0]
    print(f"\n[2/3] 检查: {kmz_name}")
    
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
        continue
    
    # 确定UTM投影带
    first_line = line_strings[0]
    centroid = first_line.centroid
    lon, lat = centroid.x, centroid.y
    utm_zone = int((lon + 180) / 6) + 1
    
    print(f"      线中心点: ({lon}, {lat})")
    print(f"      UTM带号: {utm_zone}")
    
    # 创建WGS84到UTM的转换器
    transformer_to_utm = Transformer.from_crs('EPSG:4326', f'EPSG:326{utm_zone:02d}')
    transformer_to_wgs84 = Transformer.from_crs(f'EPSG:326{utm_zone:02d}', 'EPSG:4326')
    
    # 创建缓冲区
    buffers = []
    for line in line_strings:
        coords_wgs84 = list(line.coords)
        print(f"      原始线坐标示例: {coords_wgs84[:3]}")
        
        # 转换到UTM
        coords_utm = [transformer_to_utm.transform(lat, lon) for lon, lat in coords_wgs84]
        print(f"      UTM坐标示例: {coords_utm[:3]}")
        
        line_utm = LineString(coords_utm)
        buffer_utm = line_utm.buffer(800)
        buffers.append(buffer_utm)
    
    # 融合缓冲区
    from shapely.geometry import MultiPolygon
    if len(buffers) == 1:
        merged_buffer_utm = buffers[0]
    else:
        merged_buffer_utm = MultiPolygon(buffers).buffer(0)
    
    # 转换回WGS84
    def transform_geom(geom, transformer):
        if isinstance(geom, Polygon):
            exterior = [transformer.transform(x, y) for x, y in geom.exterior.coords]
            interiors = [[transformer.transform(x, y) for x, y in interior.coords] for interior in geom.interiors]
            return Polygon(exterior, interiors)
        elif isinstance(geom, MultiPolygon):
            polygons = [transform_geom(polygon, transformer) for polygon in geom.geoms]
            return MultiPolygon(polygons)
        return geom
    
    merged_buffer = transform_geom(merged_buffer_utm, transformer_to_wgs84)
    
    # 检查缓冲区范围
    buffer_bbox = merged_buffer.bounds
    print(f"      缓冲区范围: {buffer_bbox}")
    
    # 检查是否与建筑数据范围重叠
    if (buffer_bbox[0] > building_bbox[2] or buffer_bbox[2] < building_bbox[0] or
        buffer_bbox[1] > building_bbox[3] or buffer_bbox[3] < building_bbox[1]):
        print(f"      警告: 缓冲区与建筑数据范围不重叠!")
    else:
        print(f"      缓冲区与建筑数据范围重叠")
    
    # 检查缓冲区内是否有建筑
    print(f"      检查缓冲区内的建筑...")
    count = 0
    for i, building in enumerate(buildings[:1000]):  # 只检查前1000个建筑
        building_geom = shape(building['geometry'])
        if merged_buffer.intersects(building_geom):
            count += 1
            if count <= 5:
                print(f"         找到建筑: {building_geom.centroid}")
    
    print(f"      前1000个建筑中，有 {count} 个与缓冲区相交")

print("\n[3/3] 检查完成!")
