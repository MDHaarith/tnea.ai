
import pandas as pd
import os
import json
import numpy as np

DATA_DIR = "/home/mdhaarith/Desktop/PROJECT/TNEA_AI/Launched/tnea.ai/data/json"
RAW_DIR = "/home/mdhaarith/Desktop/Data_for_training/ALLOTMENT_LIST/2025"

def load_reference_data():
    print("Loading reference data...")
    colleges = {}
    try:
        with open(os.path.join(DATA_DIR, "colleges.json"), "r") as f:
            for c in json.load(f):
                colleges[str(c.get('code'))] = {
                    "name": c.get('name'),
                    "district": c.get('district')
                }
    except Exception as e:
        print(f"Error loading colleges.json: {e}")
            
    branches = {}
    try:
        with open(os.path.join(DATA_DIR, "branches.json"), "r") as f:
            for b in json.load(f):
                branches[str(b.get('code'))] = b.get('name')
    except:
        print("branches.json not found, utilizing codes as names")
        
    return colleges, branches

def normalize_column_names(df):
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
    return df

def find_header_row(df_sample):
    """Finds the row index where 'S NO' or 'APPLN NO' appears in the first few rows of a dataframe."""
    for i, row in df_sample.head(10).iterrows():
        row_str = row.astype(str).str.upper().tolist()
        if any("S NO" in str(x) or "APPLN NO" in str(x) for x in row_str):
            return i + 1 # +1 because header=None reads from 0, so if row 2 is header (index 2), we want header=2? 
                         # Wait. if header is at index 2 (row 3), read_excel needs header=2.
                         # df.head(10) indices are 0..9. If found at 2, return 2.
            return i
            
    return 0

def process_file(file_path):
    print(f"Processing {os.path.basename(file_path)}...")
    
    # Read all sheets at once. This is much faster.
    # However, we don't know the header row yet.
    # Read with header=None first? No, default header=0 is common.
    # If header is row 2, columns will be messy.
    # But reading all sheets with header=None is efficient, then we can process each DF.
    
    try:
        # Use openpyxl engine explicitly
        dict_dfs = pd.read_excel(file_path, sheet_name=None, header=None)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return pd.DataFrame()
        
    all_data = []
    
    print(f"  Loaded {len(dict_dfs)} sheets. Processing...")
    
    # Heuristic: Detect header row from the first sheet and apply to all?
    # Or detect for each? Since they are in memory, detection is fast.
    
    # Let's detect for the first sheet and reuse, but verify.
    first_sheet = list(dict_dfs.keys())[0]
    header_idx = -1
    
    # Detect header on first sheet
    df_first = dict_dfs[first_sheet]
    for i, row in df_first.head(10).iterrows():
        row_str = row.astype(str).str.upper().tolist()
        if any("S NO" in str(x) or "APPLN NO" in str(x) for x in row_str):
            header_idx = i
            break
            
    if header_idx == -1:
        header_idx = 0 # Default
        
    print(f"  Assuming header at row index {header_idx}")
    
    for sheet_name, df_raw in dict_dfs.items():
        # df_raw has header=None (columns are Ints 0, 1, 2...)
        
        # If header_idx is valid for this sheet (rows >= header_idx + 1)
        if len(df_raw) <= header_idx:
            continue
            
        # Set new header
        # Get the row at header_idx
        header_row = df_raw.iloc[header_idx]
        
        # Slice data after header
        df_content = df_raw.iloc[header_idx+1:].copy()
        
        # Assign columns
        df_content.columns = header_row
        
        df = normalize_column_names(df_content)
        
        # Column Mapping
        column_map = {
            'COLLEGE CODE': 'college_code',
            'COLLEGE': 'college_code',
            'BRANCH CODE': 'branch_code',
            'BRANCH': 'branch_code',
            'AGGREGATE MARK': 'mark',
            'ALLOTTED COMMUNITY': 'community'
        }
        
        renamed = {}
        for col in df.columns:
            col_upper = str(col).upper()
            for key, val in column_map.items():
                if key in col_upper:
                    renamed[col] = val
                    break
        
        df = df.rename(columns=renamed)
        
        required = ['college_code', 'branch_code', 'mark', 'community']
        
        # Check for missing columns
        if not all(col in df.columns for col in required):
            # Try re-detecting header if first assumption failed for this specific sheet? 
            # For now skip.
            # print(f"    Skipping sheet {sheet_name} - Missing columns")
            continue
            
        valid_data = df[required].dropna(subset=['college_code', 'branch_code', 'mark', 'community'])
        all_data.append(valid_data)
        
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

def main():
    colleges_ref, branches_ref = load_reference_data()
    
    all_allotments = []
    
    # Walk through directories
    for root, dirs, files in os.walk(RAW_DIR):
        for file in files:
            if file.endswith(('.xlsx', '.xls')) and not file.startswith('~'):
                path = os.path.join(root, file)
                try:
                    df = process_file(path)
                    if not df.empty:
                        all_allotments.append(df)
                except Exception as e:
                    print(f"Error processing file {file}: {e}")
                    
    if not all_allotments:
        print("No valid data found from any file!")
        return
        
    full_df = pd.concat(all_allotments, ignore_index=True)
    print(f"Total allotments records parsed: {len(full_df)}")
    
    # Clean data
    # Convert marks to numeric, handle errors
    full_df['mark'] = pd.to_numeric(full_df['mark'], errors='coerce')
    full_df = full_df.dropna(subset=['mark'])
    
    # Clean college codes
    full_df['college_code'] = pd.to_numeric(full_df['college_code'], errors='coerce').fillna(0).astype(int)
    full_df = full_df[full_df['college_code'] > 0]
    
    # Group by College, Branch, Community -> Min Mark
    grouped = full_df.groupby(['college_code', 'branch_code', 'community'])['mark'].min().reset_index()
    
    processed_json = []
    
    # Unique college-branch pairs
    pairs = grouped[['college_code', 'branch_code']].drop_duplicates()
    
    for _, row in pairs.iterrows():
        c_code_int = row['college_code']
        c_code_str = str(c_code_int)
        b_code = str(row['branch_code']).strip()
        
        subset = grouped[(grouped['college_code'] == c_code_int) & (grouped['branch_code'] == row['branch_code'])]
        
        cutoffs_map = {}
        for _, cut_row in subset.iterrows():
            comm = str(cut_row['community']).strip().upper()
            val = float(cut_row['mark'])
            cutoffs_map[comm] = val
            
        # Ensure standard keys exist as null
        for std_comm in ['OC', 'BC', 'BCM', 'MBC', 'SC', 'SCA', 'ST']:
            if std_comm not in cutoffs_map:
                cutoffs_map[std_comm] = None
        
        col_meta = colleges_ref.get(c_code_str, {})
        c_name = col_meta.get('name', f"College {c_code_str}")
        district = col_meta.get('district', "Unknown")
        b_name = branches_ref.get(b_code, b_code)
        
        record = {
            "college_code": int(c_code_int),
            "college_name": c_name,
            "branch_code": b_code,
            "branch_name": b_name,
            "year": 2025,
            "district": district,
            "cutoffs": cutoffs_map
        }
        processed_json.append(record)
        
    print(f"Generated {len(processed_json)} cutoff records for 2025")
    
    # Merge with existing data
    # Load existing cutoffs
    existing_cutoffs_path = os.path.join(DATA_DIR, "cutoffs.json")
    existing_cutoffs = []
    if os.path.exists(existing_cutoffs_path):
        with open(existing_cutoffs_path, "r") as f:
            existing_cutoffs = json.load(f)
            
    print(f"Existing cutoff records: {len(existing_cutoffs)}")
    
    # Filter out any existing 2025 data to avoid dupes?
    existing_cutoffs = [c for c in existing_cutoffs if c.get('year') != 2025]
    
    # Append new data
    combined = existing_cutoffs + processed_json
    
    # Save back to cutoffs.json
    with open(existing_cutoffs_path, "w") as f:
        json.dump(combined, f, indent=2)
        
    print(f"Updated {existing_cutoffs_path} with total {len(combined)} records.")

if __name__ == "__main__":
    main()
