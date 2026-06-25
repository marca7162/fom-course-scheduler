import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "csv_files"
DB_DIR = PROJECT_ROOT / "db"

DB_FILE = DB_DIR / "FOM_Intern_Database.db"
COUNTS_FILE = CSV_DIR / "clean_counts.csv"


def get_course_id(full_course):
    parts = str(full_course).strip().split()

    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"

    return str(full_course).strip()


def get_course_name(full_course):
    parts = str(full_course).strip().split()

    if len(parts) >= 3:
        return " ".join(parts[2:])

    return ""


def import_courses():
    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()

    with open(COUNTS_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            full_course = row["full_course_list"]
            credits = int(row["credits"])

            course_id = get_course_id(full_course)
            course_name = get_course_name(full_course)

            cursor.execute(
                """
                INSERT OR REPLACE INTO courses (
                    courseCode,
                    courseName,
                    credits,
                    totalRegisteredStudents
                )
                VALUES (?, ?, ?, ?)
                """,
                (course_id, course_name, credits, 0),
            )

            print(f"Inserted {course_id} - {course_name}")

    db.commit()
    db.close()


if __name__ == "__main__":
    import_courses()
