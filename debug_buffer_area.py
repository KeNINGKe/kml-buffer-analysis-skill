# -*- coding: utf-8 -*-
"""
调试buffer面积计算
"""

import os
import fiona
from shapely.geometry import shape
from pyproj import Transformer

print("=" * 70)
print("调试buffer面积计算")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
buffer_dir = os.path.join(base_path, 'buffer_results_new')

# 定义坐标系转换
transformer_to_4527 = Transformer.from_crs('EPSG:4326', 'EPSG:4527')

# 选择一个测试文件
test_file = '1-八通线出支线至6号线.kmz'
test_name = os.path.splitext(test_file)[0]
buffer_shp = os.path.join(buffer_dir, f'{test_name}_buffer.shp')

if os.path.exists(buffer_shp):
    print(f"测试文件: {test_name}")
    
    # 读取buffer shapefile
    with fiona.open(buffer_shp, 'r') as src:
        for feature in src:
            geom = shape(feature['geometry'])
            print(f"原始几何类型: {geom.geom_type}")
            print(f"原始几何有效性: {geom.is_valid}")
            print(f"原始坐标示例: {list(geom.exterior.coords)[:3]}")
            
            # 转换到EPSG:4527坐标系
            def transform_geom(geom):
                if geom.geom_type == 'Polygon':
                    # 注意：transformer的参数是(lat, lon)
                    exterior = []
                    for lon, lat in geom.exterior.coords:
                        try:
                            x, y = transformer_to_4527.transform(lat, lon)
                            exterior.append((x, y))
                        except Exception as e:
                            print(f"转换错误: {e}")
                    
                    interiors = []
                    for interior in geom.interiors:
                        interior_coords = []
                        for lon, lat in interior.coords:
                            try:
                                x, y = transformer_to_4527.transform(lat, lon)
                                interior_coords.append((x, y))
                            except Exception as e:
                                print(f"转换错误: {e}")
                        interiors.append(interior_coords)
                    
                    from shapely.geometry import Polygon
                    return Polygon(exterior, interiors)
                return geom
            
            # 转换几何对象
            geom_4527 = transform_geom(geom)
            print(f"转换后几何类型: {geom_4527.geom_type}")
            print(f"转换后几何有效性: {geom_4527.is_valid}")
            print(f"转换后坐标示例: {list(geom_4527.exterior.coords)[:3]}")
            
            # 计算面积
            try:
                area = geom_4527.area
                print(f"面积: {area:.2f} 平方米")
            except Exception as e:
                print(f"面积计算错误: {e}")
else:
    print(f"测试文件 {buffer_shp} 不存在")
