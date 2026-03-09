# -*- coding: utf-8 -*-
"""
KML文件缓冲区分析脚本
功能：
1. 读取KMZ文件中的线要素
2. 对每条线创建800米半径的缓冲区
3. 融合同一KMZ文件中的缓冲区为一个面
4. 与建筑shp数据相交，得到缓冲区区域内的建筑
"""

import os
import zipfile
from lxml import etree
from shapely.geometry import LineString, MultiPolygon, Polygon, mapping, shape
import fiona
from fiona.crs import from_epsg
from pyproj import Transformer

print("=" * 70)
print("KML文件缓冲区分析")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
building_shp = os.path.join(base_path, '北京市建筑_新分类_final2.shp')

# 创建输出目录
buffer_output_dir = os.path.join(base_path, 'buffer_results_new')
intersect_output_dir = os.path.join(base_path, 'intersect_results_new')
os.makedirs(buffer_output_dir, exist_ok=True)
os.makedirs(intersect_output_dir, exist_ok=True)

# 读取建筑shp文件
print("\n[1/3] 读取建筑数据...")
with fiona.open(building_shp, 'r', encoding='gbk') as src:
    building_schema = src.schema
    building_crs = src.crs
    buildings = []
    for feature in src:
        # 确保属性值是字符串类型
        properties = {}
        for key, value in feature['properties'].items():
            if value is not None:
                properties[key] = str(value)
            else:
                properties[key] = ''
        feature['properties'] = properties
        buildings.append(feature)
print(f"   建筑数据记录数: {len(buildings)}")
print(f"   建筑数据CRS: {building_crs}")

# 处理KMZ文件
# 只处理指定的两个KMZ文件
kmz_files = ['1号线北延.kmz', '4-9联络线.kmz']
print(f"\n[2/3] 处理 {len(kmz_files)} 个KMZ文件")

for kmz_file in kmz_files:
    kmz_path = os.path.join(base_path, kmz_file)
    kmz_name = os.path.splitext(kmz_file)[0]
    print(f"\n   处理: {kmz_name}")
    
    # 解压KMZ文件
    with zipfile.ZipFile(kmz_path, 'r') as zf:
        # 找到KML文件
        kml_files_in_kmz = [f for f in zf.namelist() if f.endswith('.kml')]
        if not kml_files_in_kmz:
            print(f"      警告: {kmz_file} 中没有找到KML文件")
            continue
        
        # 读取KML文件
        with zf.open(kml_files_in_kmz[0]) as kml_file_obj:
            kml_content = kml_file_obj.read()
    
    # 解析KML文件
    root = etree.fromstring(kml_content)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    # 提取线要素
    line_strings = []
    # 查找所有LineString元素
    for line_elem in root.findall('.//kml:LineString', ns):
        coords_elem = line_elem.find('kml:coordinates', ns)
        if coords_elem is not None:
            coords_str = coords_elem.text.strip()
            # 解析坐标
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
    if line_strings:
        # 获取第一条线的中心点
        first_line = line_strings[0]
        centroid = first_line.centroid
        lon, lat = centroid.x, centroid.y
        # 计算UTM带号
        utm_zone = int((lon + 180) / 6) + 1
        # 确定南半球还是北半球
        hemisphere = 'north' if lat >= 0 else 'south'
        # 创建WGS84到UTM的转换器
        transformer_to_utm = Transformer.from_crs('EPSG:4326', f'EPSG:326{utm_zone:02d}')
        transformer_to_wgs84 = Transformer.from_crs(f'EPSG:326{utm_zone:02d}', 'EPSG:4326')
    
    # 创建缓冲区并融合（在UTM坐标系中）
    buffers = []
    for line in line_strings:
        # 将线转换到UTM坐标系
        coords_wgs84 = list(line.coords)
        coords_utm = [transformer_to_utm.transform(point_lat, point_lon) for point_lon, point_lat in coords_wgs84]
        line_utm = LineString(coords_utm)
        
        # 创建800米缓冲区
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
        # 使用contains方法检查建筑是否完全包含在缓冲区中
        if merged_buffer.contains(building_geom.centroid):
            intersect_buildings.append(building)
    
    print(f"      相交建筑数: {len(intersect_buildings)}")
    
    # 保存相交结果
    if intersect_buildings:
        intersect_shp = os.path.join(intersect_output_dir, f'{kmz_name}_buildings.shp')
        
        # 创建ASCII兼容的字段名，特别处理"新分类"字段
        ascii_schema = {'geometry': building_schema['geometry'], 'properties': {}}
        field_mapping = {}
        for field_name, field_type in building_schema['properties'].items():
            # 特别处理"新分类"字段
            if field_name == '新分类':
                ascii_field_name = 'new_class'
            else:
                # 创建ASCII兼容的字段名
                ascii_field_name = ''.join([c if ord(c) < 128 else '_' for c in field_name])
                # 确保字段名不超过10个字符
                ascii_field_name = ascii_field_name[:10]
            ascii_schema['properties'][ascii_field_name] = field_type
            field_mapping[field_name] = ascii_field_name
        
        # 添加buffer名称、area和buffer_area字段
        ascii_schema['properties']['buffer_name'] = 'str:100'
        ascii_schema['properties']['area'] = 'float:10.2'
        ascii_schema['properties']['buffer_area'] = 'float:10.2'
        
        with fiona.open(intersect_shp, 'w', driver='ESRI Shapefile', schema=ascii_schema, crs=building_crs, encoding='gbk') as dst:
            for building in intersect_buildings:
                # 转换属性字段名
                ascii_properties = {}
                for field_name, value in building['properties'].items():
                    ascii_field_name = field_mapping.get(field_name, ''.join([c if ord(c) < 128 else '_' for c in field_name])[:10])
                    # 确保值是字符串类型
                    if value is not None:
                        ascii_properties[ascii_field_name] = str(value)
                    else:
                        ascii_properties[ascii_field_name] = ''
                
                # 添加buffer名称和buffer面积
                ascii_properties['buffer_name'] = kmz_name
                ascii_properties['buffer_area'] = buffer_area
                
                # 计算建筑面积（单位：平方米）
                building_geom = shape(building['geometry'])
                
                # 创建WGS84到EPSG:4527的转换器
                transformer_to_4527 = Transformer.from_crs('EPSG:4326', 'EPSG:4527')
                
                # 定义几何转换函数
                def transform_geom(geom, transformer):
                    if isinstance(geom, Polygon):
                        exterior = [transformer.transform(x, y) for x, y in geom.exterior.coords]
                        interiors = [[transformer.transform(x, y) for x, y in interior.coords] for interior in geom.interiors]
                        return Polygon(exterior, interiors)
                    elif isinstance(geom, MultiPolygon):
                        polygons = [transform_geom(polygon, transformer) for polygon in geom.geoms]
                        return MultiPolygon(polygons)
                    return geom
                
                # 转换到EPSG:4527坐标系
                building_geom_4527 = transform_geom(building_geom, transformer_to_4527)
                # 计算实际面积（单位：平方米）
                area = building_geom_4527.area
                ascii_properties['area'] = area
                
                # 写入记录
                dst.write({
                    'geometry': building['geometry'],
                    'properties': ascii_properties
                })
        print(f"      保存相交结果: {os.path.basename(intersect_shp)}")

print("\n[3/3] 处理完成!")
print(f"\n输出目录:")
print(f"   缓冲区文件: {buffer_output_dir}")
print(f"   相交结果: {intersect_output_dir}")
