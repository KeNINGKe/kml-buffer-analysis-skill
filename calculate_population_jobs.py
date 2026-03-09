# -*- coding: utf-8 -*-
"""
计算人口和岗位数脚本
功能：
1. 读取建筑统计Excel文件
2. 根据住宅建筑面积计算人口数（人均居住面积34.71㎡/人）
3. 根据办公相关建筑面积计算岗位数（人均办公面积10㎡/人）
4. 导出到新的Excel文件
"""

import pandas as pd
import os

print("=" * 70)
print("计算人口和岗位数")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
input_excel = os.path.join(base_path, '建筑统计_v2.xlsx')
output_excel = os.path.join(base_path, '建筑统计_人口岗位_v2.xlsx')

# 读取Excel文件
print("\n[1/4] 读取Excel文件...")
df = pd.read_excel(input_excel)
print(f"   读取成功，共 {len(df)} 条记录")

# 计算人口数（根据住宅建筑面积）
print("\n[2/4] 计算人口数...")
per_capita_living_area = 34.71  # 人均居住面积（㎡/人）

for index, row in df.iterrows():
    # 查找住宅建筑面积列
    residential_area_col = None
    for col in df.columns:
        if '住宅_建筑面积' in col:
            residential_area_col = col
            break
    
    if residential_area_col:
        residential_area = row[residential_area_col] if pd.notna(row[residential_area_col]) else 0
        population = residential_area / per_capita_living_area
        df.at[index, '人口数'] = population
    else:
        df.at[index, '人口数'] = 0

# 计算岗位数（根据办公、医疗、政府建筑面积）
print("\n[3/4] 计算岗位数...")
per_capita_office_area = 10  # 人均办公面积（㎡/人）

for index, row in df.iterrows():
    total_office_area = 0
    
    # 查找办公相关建筑面积列
    office_cols = ['办公_建筑面积', '医疗_建筑面积', '政府_建筑面积']
    for col in df.columns:
        for office_col in office_cols:
            if office_col in col:
                office_area = row[col] if pd.notna(row[col]) else 0
                total_office_area += office_area
                break
    
    jobs = total_office_area / per_capita_office_area
    df.at[index, '岗位数'] = jobs

# 计算容积率
print("\n[4/4] 计算容积率...")

for index, row in df.iterrows():
    total_building_area = 0
    total_area = 0
    
    # 计算所有建筑面积之和
    for col in df.columns:
        if '_建筑面积' in col:
            area = row[col] if pd.notna(row[col]) else 0
            total_building_area += area
    
    # 计算所有面积之和
    for col in df.columns:
        if '_面积' in col and '_建筑面积' not in col:
            area = row[col] if pd.notna(row[col]) else 0
            total_area += area
    
    # 计算容积率
    if total_area > 0:
        plot_ratio = total_building_area / total_area
    else:
        plot_ratio = 0
    
    df.at[index, '容积率'] = plot_ratio

# 导出到新的Excel文件
print("\n[5/5] 导出到Excel...")
df.to_excel(output_excel, index=False)

print(f"\n处理完成!")
print(f"Excel文件保存路径: {output_excel}")
print(f"\n统计结果预览:")
print(df[['buffer_name', '人口数', '岗位数']].head())
