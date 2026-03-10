# KML Buffer Analysis

对 KML/KMZ 或 SHP 文件进行缓冲区分析，与建筑数据相交，并导出统计报告到 Excel。

## 特性

- 支持多种输入格式：KML、KMZ、SHP
- 精确的缓冲区计算（使用 UTM 投影）
- 灵活的相交策略（质心或相交）
- 完整的统计分析（人口、岗位、容积率、密度）
- 模块化设计，易于扩展

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 配置

编辑 `config.json`：

```json
{
  "paths": {
    "building_shp": "path/to/building.shp"
  },
  "buffer": {
    "radius_meters": 800,
    "intersect_method": "centroid"
  },
  "statistics": {
    "per_capita_living_area": 34.71,
    "per_capita_office_area": 10
  }
}
```

### 2. 运行

```bash
# 处理目录中的所有文件
python main.py --config config.json --input input_dir --output output_dir

# 处理指定文件
python main.py --config config.json --input input_dir --output output_dir --files file1.kmz file2.kml

# 覆盖配置中的建筑数据路径
python main.py --config config.json --input input_dir --output output_dir --building-shp path/to/building.shp
```

## 配置说明

### buffer.intersect_method

- `centroid`: 建筑中心点在缓冲区内即算相交（更严格）
- `intersects`: 建筑与缓冲区有任何交集即算相交（更宽松）

### statistics

- `per_capita_living_area`: 人均居住面积（㎡/人）
- `per_capita_office_area`: 人均办公面积（㎡/人）
- `residential_class`: 住宅类别名称
- `office_classes`: 办公类别名称列表

## 输出

```
output_dir/
├── buffers/                      # 缓冲区 shapefile
│   ├── file1_buffer.shp
│   └── file2_buffer.shp
├── intersecting_buildings/       # 相交建筑 shapefile
│   ├── file1_buildings.shp
│   └── file2_buildings.shp
└── 建筑统计.xlsx                 # 统计报告
```

## 作为库使用

```python
from kml_buffer import (
    parse_input_file,
    create_buffer,
    find_intersecting_buildings,
    calculate_statistics,
    export_to_excel
)

# 解析输入文件
lines = parse_input_file('input.kmz')

# 创建缓冲区
buffer_geom, buffer_area, utm_crs = create_buffer(lines, radius_meters=800)

# 查找相交建筑
intersecting = find_intersecting_buildings(buffer_geom, buildings, method='centroid')

# 计算统计
stats = calculate_statistics(intersecting, buffer_area, config)
```

## 项目结构

```
kml-buffer-analysis/
├── config.json              # 配置文件
├── main.py                  # CLI 入口
├── requirements.txt         # 依赖
├── README.md               # 本文件
├── SKILL.md                # 详细文档
└── kml_buffer/             # 核心库
    ├── __init__.py
    ├── parser.py           # 文件解析
    ├── buffer.py           # 缓冲区创建
    ├── intersect.py        # 相交分析
    ├── stats.py            # 统计计算
    ├── export.py           # Excel 导出
    └── utils.py            # 工具函数
```

## 技术细节

- **坐标系统**：输入 WGS84 (EPSG:4326)，缓冲区计算使用 UTM，面积计算使用 EPSG:4527
- **编码**：Shapefile 使用 GBK 编码
- **人岗密度单位**：人/平方公里
- **容积率**：总建筑面积 / 总占地面积

## 常见问题

### 中文乱码

确保建筑 shapefile 使用 GBK 编码，并创建 .cpg 文件内容为 `GBK`

### 字段名限制

Shapefile 字段名必须是 ASCII 且不超过 10 个字符，程序会自动转换

### 缓冲区精度

使用 UTM 投影确保缓冲区距离精确，不同地区会自动选择合适的 UTM 带号

## License

MIT
