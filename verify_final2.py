# -*- coding: utf-8 -*-
import shapefile

print("=== 验证输出文件 ===")

# 读取输出文件
sf = shapefile.Reader(r'c:\Users\ningke\Desktop\建筑shp功能分类\shp\北京市建筑_新分类_final2.shp', encoding='gbk')
fields = [f[0] for f in sf.fields[1:]]
print(f'字段: {fields}')
print(f'记录数: {len(sf)}')

# 统计新分类
print('\n新分类统计:')
new_class_idx = fields.index('新分类')
class_count = {}
for rec in sf.records():
    c = rec[new_class_idx]
    class_count[c] = class_count.get(c, 0) + 1

for c, count in sorted(class_count.items(), key=lambda x: x[1], reverse=True):
    print(f'  "{c}": {count} 条')

# 检查AOIType为空但新分类已填充的情况
print('\n=== 检查AOIType为空的处理情况 ===')
aioi_type_idx = fields.index('AOIType')
func_idx = fields.index('功能分')

empty_aoitype_with_class = 0
empty_aoitype_empty_class = 0

for rec in sf.records():
    aoi_type = str(rec[aioi_type_idx])
    new_class = rec[new_class_idx]
    if aoi_type == '' or aoi_type == 'nan':
        if new_class:
            empty_aoitype_with_class += 1
        else:
            empty_aoitype_empty_class += 1

print(f'AOIType为空但新分类已填充: {empty_aoitype_with_class} 条')
print(f'AOIType为空且新分类仍为空: {empty_aoitype_empty_class} 条')

# 检查功能分的处理情况
print('\n=== 检查功能分的处理情况 ===')
func_values = set()
for rec in sf.records():
    func_value = rec[func_idx]
    if func_value:
        func_values.add(func_value)

print(f'功能分唯一值数量: {len(func_values)}')
print('功能分所有唯一值:')
for val in sorted(func_values)[:20]:  # 只显示前20个
    print(f'  "{val}"')
if len(func_values) > 20:
    print(f'  ... 还有 {len(func_values) - 20} 个值')
