# -*- coding: utf-8 -*-
"""
建筑shp文件新分类属性添加脚本
功能：根据映射表将AOIType映射到新分类，并添加到shp文件中
"""

import pandas as pd
import shapefile
from collections import defaultdict
import os

print("=" * 60)
print("建筑shp文件新分类属性添加")
print("=" * 60)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类'
excel_path = os.path.join(base_path, 'output2-新分类_规模.xlsx')
shp_path = os.path.join(base_path, '北京市建筑.shp')
output_path = os.path.join(base_path, 'shp', '北京市建筑_新分类.shp')

# 1. 读取Excel映射表
print("\n[1/5] 读取Excel映射表...")
df_excel = pd.read_excel(excel_path)
print(f"   Excel记录数: {len(df_excel)}")

# 创建AOIName+AOIType组合键
df_excel['key'] = df_excel['AOIName'].astype(str) + '|' + df_excel['AOIType'].astype(str)

# 2. 构建映射字典
print("\n[2/5] 构建映射字典...")

# 方法1: 基于AOIName+AOIType组合的精确映射
# 对于多分类情况，选择出现频率最高的新分类
key_to_class = df_excel.groupby('key')['新分类'].agg(lambda x: x.value_counts().index[0]).to_dict()
print(f"   精确映射组合数: {len(key_to_class)}")

# 方法2: 基于AOIType的默认映射（用于没有AOIName匹配的情况）
# 选择每个AOIType中出现频率最高的新分类
aoitype_to_class = df_excel.groupby('AOIType')['新分类'].agg(lambda x: x.value_counts().index[0]).to_dict()
print(f"   AOIType默认映射数: {len(aoitype_to_class)}")

# 3. 读取shp文件
print("\n[3/5] 读取shp文件...")
sf = shapefile.Reader(shp_path, encoding='gbk')
fields = [f[0] for f in sf.fields[1:]]
aoi_name_idx = fields.index('AOIName')
aoi_type_idx = fields.index('AOIType')
print(f"   shp记录数: {len(sf)}")
print(f"   字段: {fields}")

# 4. 创建新的shp文件
print("\n[4/5] 创建新的shp文件...")

# 使用pyshp创建新文件
with shapefile.Reader(shp_path, encoding='gbk') as r:
    with shapefile.Writer(output_path, encoding='gbk', shapeType=r.shapeType) as w:
        # 复制字段定义
        w.fields = list(r.fields)
        # 添加新分类字段
        w.field('新分类', 'C', size=20)
        
        # 统计
        exact_match = 0
        type_match = 0
        no_match = 0
        empty_aoitype = 0
        
        # 处理每条记录
        for i, (rec, shape) in enumerate(zip(r.records(), r.shapes())):
            aoi_name = str(rec[aoi_name_idx])
            aoi_type = str(rec[aoi_type_idx])
            key = aoi_name + '|' + aoi_type
            
            # 确定新分类
            if key in key_to_class:
                new_class = key_to_class[key]
                exact_match += 1
            elif aoi_type in aoitype_to_class:
                new_class = aoitype_to_class[aoi_type]
                type_match += 1
            elif aoi_type == '' or aoi_type == 'nan':
                new_class = ''
                empty_aoitype += 1
            else:
                new_class = ''
                no_match += 1
            
            # 写入记录
            w.record(*rec, new_class)
            w.shape(shape)
            
            # 进度显示
            if (i + 1) % 100000 == 0:
                print(f"   已处理 {i + 1} 条记录...")

# 5. 输出统计结果
print("\n[5/5] 处理完成!")
print(f"\n统计结果:")
print(f"   - 精确匹配(AOIName+AOIType): {exact_match} 条")
print(f"   - AOIType默认匹配: {type_match} 条")
print(f"   - AOIType为空: {empty_aoitype} 条")
print(f"   - 无匹配: {no_match} 条")
print(f"\n输出文件: {output_path}")

# 复制prj文件
import shutil
prj_src = os.path.join(base_path, '北京市建筑.prj')
prj_dst = os.path.join(base_path, 'shp', '北京市建筑_新分类.prj')
if os.path.exists(prj_src):
    shutil.copy(prj_src, prj_dst)
    print(f"已复制prj文件")
