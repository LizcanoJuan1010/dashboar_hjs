import pandas as pd
import sys

input_file = '/app/data/data/SEGUIMIENTO A LIDERES CAMPAÑA HJS 2023.xlsx'

try:
    xl = pd.ExcelFile(input_file)
    print(f"Sheets: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet, nrows=0)
        print(f"--- Sheet: {sheet} ---")
        print(f"Columns: {df.columns.tolist()}")
except Exception as e:
    print(f"Error: {e}")
