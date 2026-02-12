import pandas as pd
import glob
import os

def debug_excel():
    files = glob.glob("*.xls") + glob.glob("*.xlsx")
    if not files:
        print("No Excel files found.")
        return

    latest_file = max(files, key=os.path.getmtime)
    print(f"Reading: {latest_file}")
    
    try:
        # Read header first to find correct row
        df_raw = pd.read_excel(latest_file, header=None)
        header_idx = -1
        for i, row in df_raw.head(10).iterrows():
            row_str = row.astype(str).values
            if any('표준코드' in s for s in row_str):
                header_idx = i
                print(f"Header found at row {i}")
                break
        
        if header_idx == -1:
            print("Could not find header with '표준코드'. Dumping first 5 rows:")
            print(df_raw.head(5))
            return

        df = pd.read_excel(latest_file, header=header_idx)
        
        # Check Standard Code column
        std_col = next((c for c in df.columns if '표준코드' in c), None)
        if not std_col:
            print("Column '표준코드' not found in parsed header.")
            print(df.columns.tolist())
            return
            
        print(f"Found Standard Code Column: '{std_col}'")
        
        # Check for ANY KR codes
        kr_codes = df[df[std_col].astype(str).str.startswith('KR')]
        print(f"\nTotal rows: {len(df)}")
        
        kr5_codes = df[df[std_col].astype(str).str.startswith('KR5')]
        kr7_codes = df[df[std_col].astype(str).str.startswith('KR7')] # ETFs usually start with KR7
        
        print(f"Rows with 'KR' code: {len(kr_codes)}")
        print(f"Rows with 'KR5' (General Funds): {len(kr5_codes)}")
        print(f"Rows with 'KR7' (ETFs): {len(kr7_codes)}")
        
        if not kr5_codes.empty:
            print("\nSample KR5 codes:")
            print(kr5_codes[[std_col, '펀드명']].head(3))

        if not kr7_codes.empty:
            print("\nSample KR7 codes:")
            print(kr7_codes[[std_col, '펀드명']].head(3))
        
        # Search by Name to see what exists
        print("\nSearching for 'S&P500' in Excel:")
        name_matches = df[df['펀드명'].astype(str).str.contains('S&P500', na=False)]
        if not name_matches.empty:
            print(name_matches[['펀드명', std_col]].head(10))
        else:
            print("No 'S&P500' found.")

        print("\nSearching for '나스닥' in Excel:")
        nasdaq_matches = df[df['펀드명'].astype(str).str.contains('나스닥', na=False)]
        if not nasdaq_matches.empty:
            print(nasdaq_matches[['펀드명', std_col]].head(10))
        else:
            print("No '나스닥' found.")
                
        # Print a few sample codes to see format
        print("\nSample Standard Codes from Excel:")
        print(df[std_col].head(10).tolist())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_excel()
