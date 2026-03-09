# -*- coding: utf-8 -*-
"""
更新人岗密度单位为人/平方公里
"""

import pandas as pd
import os

print("=" * 70)
print("更新人岗密度单位")
print("=" * 70)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
input_excel = os.path.join(base_path, '建筑统计_新kmz.xlsx')
output_excel = os.path.join(base_path, '建筑统计_新kmz_updated.xlsx')

# 读取Excel文件
print("\n[1/2] 读取Excel文件...")
df = pd.read_excel(input_excel)
print(f"   读取成功，共 {len(df)} 条记录")

# 更新人岗密度（从人/平方米转换为人/平方公里）
print("\n[2/2] 更新人岗密度...")
df['人岗密度'] = df['人岗密度'] * 1000000

# 保存回Excel文件
df.to_excel(output_excel, index=False)

print(f"\n处理完成!")
print(f"Excel文件已更新: {output_excel}")
print(f"\n统计结果预览:")
print(df[['buffer_name', 'buffer面积', '人口数', '岗位数', '容积率', '人岗密度']])
