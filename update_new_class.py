# -*- coding: utf-8 -*-
"""
建筑shp文件新分类属性更新脚本
功能：使用"功能分"列填充AOIType为空的记录的"新分类"
使用shapefile库，分块处理
"""

import shapefile
import os

print("=" * 60)
print("建筑shp文件新分类属性更新")
print("=" * 60)

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类'
input_path = os.path.join(base_path, 'shp', '北京市建筑_新分类.shp')
output_path = os.path.join(base_path, 'shp', '北京市建筑_新分类_final.shp')

# 建立功能分到新分类的映射
func_to_class = {
    # 英文部分
    'cemetery': '特殊',           # 墓地
    'commercial': '商业',         # 商业
    'farmland': '绿地',           # 农田
    'farmyard': '绿地',           # 农家院
    'forest': '绿地',             # 森林
    'grass': '绿地',              # 草地
    'industrial': '工业',         # 工业
    'meadow': '绿地',             # 草地
    'military': '特殊',           # 军事
    'nature_reserve': '绿地',     # 自然保护区
    'orchard': '绿地',            # 果园
    'others': '特殊',             # 其他
    'park': '公园',               # 公园
    'quarry': '工业',             # 采石场
    'recreation_ground': '商业',  # 娱乐场
    'residential': '住宅',        # 住宅
    'retail': '商业',             # 零售
    'scrub': '绿地',              # 灌木丛
    'vineyard': '绿地',           # 葡萄园
    
    # 中文部分
    '丽人': '商业',
    '交通设施': '交通',
    '休闲娱乐': '商业',
    '公司企业': '办公',
    '医疗': '医疗',
    '房地产': '住宅',
    '政府机构': '政府',
    '教育培训': '学校',
    '文化传媒': '文化',
    '旅游景点': '景区',
    '汽车服务': '商业',
    '生活服务': '商业',
    '绿地': '绿地',
    '美食': '商业',
    '自然地物': '绿地',
    '行政地标': '政府',
    '购物': '商业',
    '运动健身': '文化',
    '酒店': '商业',
    '金融': '办公',
    '门址': '商业'
}

print(f"\n[1/3] 读取输入文件...")
with shapefile.Reader(input_path, encoding='gbk') as r:
    fields = [f[0] for f in r.fields[1:]]
    print(f"   字段: {fields}")
    
    # 找到相关字段的索引
    aoi_type_idx = fields.index('AOIType')
    func_idx = fields.index('功能分')
    new_class_idx = fields.index('新分类')
    
    print(f"\n[2/3] 创建更新后的文件...")
    with shapefile.Writer(output_path, encoding='gbk', shapeType=r.shapeType) as w:
        # 复制字段定义
        w.fields = list(r.fields)
        
        # 统计
        updated_count = 0
        total_count = 0
        
        # 处理每条记录
        for i, (rec, shape) in enumerate(zip(r.records(), r.shapes())):
            total_count += 1
            
            # 检查AOIType是否为空
            aoi_type = str(rec[aoi_type_idx])
            if aoi_type == '' or aoi_type == 'nan':
                # 获取功能分
                func_value = rec[func_idx]
                if func_value in func_to_class:
                    # 更新新分类
                    new_rec = list(rec)
                    new_rec[new_class_idx] = func_to_class[func_value]
                    w.record(*new_rec)
                    updated_count += 1
                else:
                    # 保持原样
                    w.record(*rec)
            else:
                # 保持原样
                w.record(*rec)
            
            w.shape(shape)
            
            # 进度显示
            if (i + 1) % 50000 == 0:
                print(f"   已处理 {i + 1} 条记录...")

# 复制prj文件
import shutil
prj_src = os.path.join(base_path, 'shp', '北京市建筑_新分类.prj')
prj_dst = os.path.join(base_path, 'shp', '北京市建筑_新分类_final.prj')
if os.path.exists(prj_src):
    shutil.copy(prj_src, prj_dst)

print(f"\n[3/3] 处理完成!")
print(f"\n统计结果:")
print(f"   - 总记录数: {total_count}")
print(f"   - 更新记录数: {updated_count}")
print(f"\n输出文件: {output_path}")
