# -*- coding: utf-8 -*-
"""
导出建筑数据到Excel脚本
功能：
1. 读取生成的shp文件
2. 提取buffer_name, new_class, area, height字段
3. 计算建筑面积 = height/4 * area
4. 按buffer_name和new_class分组统计
5. 导出到Excel表格
"""

import os
import fiona
import pandas as pd
from shapely.geometry import shape

print("=" * 70)
print("导出建筑数据到Excel")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
input_dir = os.path.join(base_path, 'intersect_results_new')
excel_output = os.path.join(base_path, '建筑统计_v3.xlsx')

# 只处理指定的两个KMZ文件的结果
target_buffers = ['1号线北延', '4-9联络线']

# 读取所有shp文件
shp_files = [f for f in os.listdir(input_dir) if f.endswith('.shp')]
print(f"\n[1/4] 发现 {len(shp_files)} 个shp文件")

# 存储所有数据
alldata = []

# 处理相交结果文件
for shp_file in shp_files:
    buffer_name = os.path.splitext(shp_file)[0].replace('_buildings', '')
    # 只处理目标缓冲区
    if buffer_name in target_buffers:
        shp_path = os.path.join(input_dir, shp_file)
        print(f"\n[2/4] 处理: {buffer_name}")
        
        with fiona.open(shp_path, 'r', encoding='gbk') as src:
            for feature in src:
                properties = feature['properties']
                
                # 提取所需字段
                new_class = properties.get('new_class', '')
                area = properties.get('area', 0)
                buffer_area = properties.get('buffer_are', 0)
                
                # 提取height字段（可能有不同的字段名）
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
                
                # 添加到数据列表
                alldata.append({
                    'buffer_name': buffer_name,
                    'new_class': new_class,
                    'area': area,
                    'buffer_area': buffer_area,
                    'height': height,
                    '建筑面积': building_area
                })

# 检查buffer_results_new目录中的目标缓冲区文件
buffer_dir = os.path.join(base_path, 'buffer_results_new')

# 检查是否有buffer没有对应的intersect文件
for buffer_name in target_buffers:
    buffer_path = os.path.join(buffer_dir, f'{buffer_name}_buffer.shp')
    if os.path.exists(buffer_path):
        # 检查是否已经处理过
        processed = any(item['buffer_name'] == buffer_name for item in alldata)
        if not processed:
            print(f"\n[2/4] 处理: {buffer_name} (无相交建筑)")
            # 读取buffer文件获取面积
            with fiona.open(buffer_path, 'r', encoding='gbk') as src:
                for feature in src:
                    buffer_area = feature['properties'].get('area', 0)
                    # 添加空记录
                    alldata.append({
                        'buffer_name': buffer_name,
                        'new_class': '',
                        'area': 0,
                        'buffer_area': buffer_area,
                        'height': 0,
                        '建筑面积': 0
                    })
                    break

print(f"\n[3/4] 处理完成，共 {len(alldata)} 条记录")

# 转换为DataFrame
df = pd.DataFrame(alldata)

# 按buffer_name和new_class分组统计
grouped = df.groupby(['buffer_name', 'new_class']).agg({
    'area': 'sum',
    '建筑面积': 'sum'
}).reset_index()

# 重命名列
grouped.rename(columns={'area': '面积总计', '建筑面积': '建筑面积总计'}, inplace=True)

# 计算每个buffer的总面积（使用第一个记录的buffer_area，因为所有记录的buffer_area应该相同）
buffer_areas = df.groupby('buffer_name')['buffer_area'].first().reset_index()
buffer_areas.rename(columns={'buffer_area': 'buffer面积'}, inplace=True)

# 使用透视表将相同的buffer_name合并成一行
pivot_area = grouped.pivot(index='buffer_name', columns='new_class', values='面积总计')
pivot_building_area = grouped.pivot(index='buffer_name', columns='new_class', values='建筑面积总计')

# 重命名列
pivot_area.columns = [f'{col}_面积' for col in pivot_area.columns]
pivot_building_area.columns = [f'{col}_建筑面积' for col in pivot_building_area.columns]

# 合并两个透视表
final_df = pd.concat([pivot_area, pivot_building_area], axis=1)
final_df.reset_index(inplace=True)

# 合并buffer面积
final_df = final_df.merge(buffer_areas, on='buffer_name', how='left')

# 导出到Excel
print("\n[4/4] 导出到Excel...")
final_df.to_excel(excel_output, index=False)

print(f"\n统计结果预览:")
print(final_df[['buffer_name', 'buffer面积']].head())

print(f"\n处理完成!")
print(f"Excel文件保存路径: {excel_output}")
