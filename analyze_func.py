# -*- coding: utf-8 -*-
import shapefile

print("=== 查看功能分列的内容 ===")
sf = shapefile.Reader(r'c:\Users\ningke\Desktop\建筑shp功能分类\北京市建筑.shp', encoding='gbk')
fields = [f[0] for f in sf.fields[1:]]
print(f'字段: {fields}')

# 找到功能分列的索引
func_idx = fields.index('功能分')
print(f'\n功能分列索引: {func_idx}')

# 收集功能分的唯一值
func_values = set()
for rec in sf.records():
    func_value = rec[func_idx]
    if func_value:
        func_values.add(func_value)

print(f'\n功能分唯一值数量: {len(func_values)}')
print('\n功能分所有唯一值:')
for val in sorted(func_values):
    print(f'  "{val}"')
