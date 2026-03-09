import zipfile
from lxml import etree
from shapely.geometry import LineString

# 检查KMZ文件
kmz_files = ['1号线北延.kmz', '4-9联络线.kmz']

for kmz_file in kmz_files:
    print(f'\n检查 {kmz_file}:')
    
    # 解压KMZ文件
    with zipfile.ZipFile(kmz_file, 'r') as zf:
        # 找到KML文件
        kml_files_in_kmz = [f for f in zf.namelist() if f.endswith('.kml')]
        if not kml_files_in_kmz:
            print(f'  警告: {kmz_file} 中没有找到KML文件')
            continue
        
        # 读取KML文件
        with zf.open(kml_files_in_kmz[0]) as kml_file_obj:
            kml_content = kml_file_obj.read()
    
    # 解析KML文件
    root = etree.fromstring(kml_content)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    # 提取线要素
    line_strings = []
    # 查找所有LineString元素
    for line_elem in root.findall('.//kml:LineString', ns):
        coords_elem = line_elem.find('kml:coordinates', ns)
        if coords_elem is not None:
            coords_str = coords_elem.text.strip()
            # 解析坐标
            coords = []
            for coord in coords_str.split():  
                lon, lat, _ = map(float, coord.split(','))
                coords.append((lon, lat))
                print(f'  坐标: {lon}, {lat}')
            if len(coords) >= 2:
                line = LineString(coords)
                line_strings.append(line)
                print(f'  线长度: {line.length}')
                print(f'  线中心点: {line.centroid}')
    
    print(f'  提取到 {len(line_strings)} 条线')
