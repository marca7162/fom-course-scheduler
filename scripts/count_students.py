import sqlite3
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "csv_files"
DB_DIR = PROJECT_ROOT / "db"

DB_FILE = DB_DIR / "FOM_Intern_Database.db"

if __name__ == "__main__":
    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()
    cursor.execute("select courseID from student_courses")
    rows = cursor.fetchall()
    counts = dict()
    for row in rows:
        counts[row[0]] = 0
    for row in rows:
        counts[row[0]] += 1
    for row in rows:
        command = "update courses "
        command += "set totalRegisteredStudents = '" + str(counts[row[0]]) + "'"
        command += " where courseCode = '" + str(row[0]) + "'"
        cursor.execute(command)

    db.commit()
    db.close()