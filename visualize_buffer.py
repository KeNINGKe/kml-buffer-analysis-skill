import os
import fiona
from shapely.geometry import shape, LineString, MultiPolygon, Polygon
from pyproj import Transformer
import zipfile
from lxml import etree

# 路径设置
base_path = r'c:\Users\ningke\Desktop\建筑shp功能分类\shp'
building_shp = os.path.join(base_path, '北京市建筑_新分类_final2.shp')

# 读取建筑数据
def read_buildings():
    print("读取建筑数据...")
    buildings = []
    with fiona.open(building_shp, 'r', encoding='gbk') as src:
        for i, feature in enumerate(src):
            if i < 1000:  # 只读取前1000个建筑
                building_geom = shape(feature['geometry'])
                buildings.append(building_geom)
            else:
                break
    print(f"读取了 {len(buildings)} 个建筑")
    return buildings

# 从KMZ文件读取线