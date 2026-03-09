# -*- coding: utf-8 -*-
"""
更新buffer面积到Excel文件
功能：
1. 读取buffer shapefile文件
2. 将缓冲区投影到EPSG:4527坐标系
3. 计算缓冲区面积
4. 更新到建筑统计_人口岗位_v2.xlsx文件
5. 计算人岗密度
"""

import os
import fiona
from shapely.geometry import shape
from pyproj import Transformer
import pandas as pd

print("=" * 70)
print("更新buffer面积到Excel文件")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
buffer_dir = os.path.join(base_path, 'buffer_results_new')
input_excel = os.path.join(base_path, '建筑统计_人口岗位_v2.xlsx')
output_excel = os.path.join(base_path, '建筑统计_人口岗位_v2_updated.xlsx')

# 读取Excel文件
print("\n[1/4] 读取Excel文件...")
df = pd.read_excel(input_excel)
print(f"   读取成功，共 {len(df)} 条记录")

# 定义坐标系转换
transformer_to_4527 = Transformer.from_crs('EPSG:4326', 'EPSG:4527')

# 处理每个buffer文件
buffer_areas = {}
kmz_files = [f for f in os.listdir(base_path) if f.endswith('.kmz')]

print(f"\n[2/4] 处理 {len(kmz_files)} 个buffer文件...")

for kmz_file in kmz_files:
    kmz_name = os.path.splitext(kmz_file)[0]
    buffer_shp = os.path.join(buffer_dir, f'{kmz_name}_buffer.shp')
    
    if os.path.exists(buffer_shp):
        print(f"   处理: {kmz_name}")
        
        # 读取buffer shapefile
        with fiona.open(buffer_shp, 'r') as src:
            for feature in src:
                # 直接从属性中读取面积
                if 'area' in feature['properties']:
                    area = feature['properties']['area']
                    buffer_areas[kmz_name] = area
                    print(f"      面积: {area:.2f} 平方米")
                else:
                    print(f"      警告: 没有找到area属性")
    else:
        print(f"   警告: {buffer_shp} 不存在")

# 更新Excel文件
print("\n[3/4] 更新Excel文件...")

# 添加buffer面积列
if 'buffer面积' not in df.columns:
    df['buffer面积'] = 0

# 更新buffer面积
for index, row in df.iterrows():
    buffer_name = row['buffer_name']
    if buffer_name in buffer_areas:
        df.at[index, 'buffer面积'] = buffer_areas[buffer_name]
        print(f"   更新: {buffer_name} - 面积: {buffer_areas[buffer_name]:.2f} 平方米")

# 计算人岗密度
print("\n[4/4] 计算人岗密度...")

if '人岗密度' not in df.columns:
    df['人岗密度'] = 0

for index, row in df.iterrows():
    population = row['人口数'] if pd.notna(row['人口数']) else 0
    jobs = row['岗位数'] if pd.notna(row['岗位数']) else 0
    buffer_area = row['buffer面积'] if pd.notna(row['buffer面积']) else 0
    
    if buffer_area > 0:
        density = (population + jobs) / buffer_area
    else:
        density = 0
    
    df.at[index, '人岗密度'] = density
    print(f"   计算: {row['buffer_name']} - 人岗密度: {density:.6f} 人/平方米")

# 导出到Excel文件
df.to_excel(output_excel, index=False)

print("\n处理完成!")
print(f"Excel文件保存路径: {output_excel}")

# 显示结果预览
print("\n结果预览:")
print(df[['buffer_name', 'buffer面积', '人口数', '岗位数', '人岗密度']])
