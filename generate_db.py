import pandas as pd
import sqlite3
import datetime

# Load your Excel file
excel_file = "technical_asset_inventory.xlsx"  # Ensure this file is in the same folder as this script
df = pd.read_excel(excel_file)

# Add required columns if not present
if 'Functional' not in df.columns:
    df['Functional'] = 0
if 'last_updated' not in df.columns:
    df['last_updated'] = None

# Save to SQLite database
db_filename = "assets.db"
conn = sqlite3.connect(db_filename)
df.to_sql("assets", conn, if_exists="replace", index=False)
conn.close()

print(f"✅ Database '{db_filename}' created with {len(df)} rows and {len(df.columns)} columns.")
