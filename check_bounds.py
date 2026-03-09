import fiona
from shapely.geometry import shape

# 读取建筑数据
with fiona.open('北京市建筑_新分类_final2.shp', 'r', encoding='gbk') as src:
    bbox = src.bounds
    print('建筑数据范围:', bbox)
    
    # 读取前10个建筑的位置
    print('\n前10个建筑的位置:')
    count = 0
    for feature in src:
        if count < 10:
            geom = shape(feature['geometry'])
            print(f'建筑 {count+1}: {geom.centroid}')
            count += 1
        else:
            break
