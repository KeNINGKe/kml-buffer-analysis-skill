# -*- coding: utf-8 -*-
"""
检查buffer文件中的面积信息
"""

import os
import fiona

print("=" * 70)
print("检查buffer文件中的面积信息")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
buffer_dir = os.path.join(base_path, 'buffer_results_new')

# 处理每个buffer文件
kmz_files = [f for f in os.listdir(base_path) if f.endswith('.kmz')]

print(f"\n检查 {len(kmz_files)} 个buffer文件...")

for kmz_file in kmz_files:
    kmz_name = os.path.splitext(kmz_file)[0]
    buffer_shp = os.path.join(buffer_dir, f'{kmz_name}_buffer.shp')
    
    if os.path.exists(buffer_shp):
        print(f"   检查: {kmz_name}")
        
        # 读取buffer shapefile
        with fiona.open(buffer_shp, 'r') as src:
            print(f"      属性字段: {list(src.schema['properties'].keys())}")
            
            for feature in src:
                properties = feature['properties']
                print(f"      名称: {properties.get('name', 'N/A')}")
                if 'area' in properties:
                    print(f"      面积: {properties['area']:.2f} 平方米")
                else:
                    print(f"      面积: N/A")
    else:
        print(f"   警告: {buffer_shp} 不存在")
