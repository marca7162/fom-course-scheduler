import sqlite3
from pathlib import Path

import pandas as pd


# Project root = folder where this file lives
ROOT = Path(__file__).resolve().parent

DB_PATH = ROOT / "fom_scheduler.db"

FILES = {
    "enrollment": ROOT / "clean_enrollment.csv",
    "availability": ROOT / "clean_availability.csv",
    "periods": ROOT / "clean_periods.csv",
    "courses": ROOT / "clean_counts.csv",
}


def build_database():
    conn = sqlite3.connect(DB_PATH)

    for table_name, file_path in FILES.items():
        df = pd.read_csv(file_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Loaded {file_path.name} into table '{table_name}'")

    conn.commit()
    conn.close()

    print(f"Database built successfully: {DB_PATH}")


if __name__ == "__main__":
    build_database()
