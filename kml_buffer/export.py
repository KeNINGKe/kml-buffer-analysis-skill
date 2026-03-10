# -*- coding: utf-8 -*-
"""
Excel export functionality.
"""

import pandas as pd


def export_to_excel(statistics_records, output_path):
    """
    Export statistics to Excel file.
    
    Args:
        statistics_records: List of statistics dictionaries
        output_path: Output Excel file path
    """
    if not statistics_records:
        raise ValueError("No statistics to export")
    
    df = pd.DataFrame(statistics_records)
    
    # Reorder columns: put main stats first
    main_cols = ['buffer_name', 'buffer面积', '人口数', '岗位数', '容积率', '人岗密度']
    other_cols = [col for col in df.columns if col not in main_cols]
    
    df = df[main_cols + other_cols]
    
    # Export to Excel
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    return df
