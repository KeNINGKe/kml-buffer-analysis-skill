# -*- coding: utf-8 -*-
import pandas as pd

# 读取Excel文件
df = pd.read_excel('建筑统计_人口岗位_v2.xlsx')

# 显示前5行
print("前5行数据:")
print(df.head())

# 显示列名
print("\n列名:")
print(df.columns.tolist())

# 显示buffer_name列
print("\nbuffer_name列:")
print(df['buffer_name'].tolist())
