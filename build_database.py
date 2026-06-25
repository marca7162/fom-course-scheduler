import sqlite3
from pathlib import Path

import pandas as pd


# Project root = folder where this file lives
ROOT = Path(__file__).resolve().parent

# TO DO:
# Make a script that cleans our xcel file and makes into CSV


DB_PATH = ROOT / "fom_scheduler.db"

# Dicionary of file names and their corresponding table names in the database
FILES = {
    "enrollment": ROOT / "clean_enrollment.csv",
    "availability": ROOT / "clean_availability.csv",
    "periods": ROOT / "clean_periods.csv",
    "courses": ROOT / "clean_counts.csv",
    "sheets_rooms": ROOT / "rooms.csv"
}


def build_database():
    # Same as the colab
    # Connect to sql and loop through to add them to the DB
    conn = sqlite3.connect(DB_PATH)

    for table_name, file_path in FILES.items():
        df = pd.read_csv(file_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Loaded {file_path.name} into table '{table_name}'")

    # Commit to the DB and end the stuff
    conn.commit()
    conn.close()

    print(f"Database built successfully: {DB_PATH}")


if __name__ == "__main__":
    build_database()
