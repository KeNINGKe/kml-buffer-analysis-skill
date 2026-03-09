# -*- coding: utf-8 -*-
import shapefile

print("=== 验证输出文件 ===")

# 尝试读取输出文件
try:
    sf = shapefile.Reader(r'c:\Users\ningke\Desktop\建筑shp功能分类\shp\北京市建筑_新分类_final.shp', encoding='gbk')
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
        
except Exception as e:
    print(f'错误: {e}')

print('\n=== 清理临时文件 ===')
import os
files_to_delete = [
    '北京市建筑_新分类_final.dbf',
    '北京市建筑_新分类_final.shp', 
    '北京市建筑_新分类_final.shx'
]

for f in files_to_delete:
    path = os.path.join(r'c:\Users\ningke\Desktop\建筑shp功能分类\shp', f)
    if os.path.exists(path):
        os.remove(path)
        print(f'已删除: {f}')
