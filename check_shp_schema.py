# -*- coding: utf-8 -*-
import fiona

shp_path = 'intersect_results_new/1-八通线出支线至6号线_buildings.shp'
with fiona.open(shp_path, 'r', encoding='gbk') as src:
    print('Schema:', src.schema)
    print('\nFirst feature properties:')
    for feature in src:
        print(feature['properties'])
        break
