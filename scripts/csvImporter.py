import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "csv_files"
DB_DIR = PROJECT_ROOT / "db"

DB_FILE = DB_DIR / "FOM_Intern_Database.db"
COUNTS_FILE = CSV_DIR / "clean_counts.csv"
STUDENTS_FILE = CSV_DIR / "clean_enrollment.csv"


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

    cursor.execute("drop table courses")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            courseCode VARCHAR(15) PRIMARY KEY,
            courseName VARCHAR(50) NOT NULL,
            credits INTEGER NOT NULL,
            totalRegisteredStudents INTEGER NOT NULL
        );
        """
    )

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

def import_students():
    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()

    cursor.execute("drop table students")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            stdId INTEGER PRIMARY KEY AUTOINCREMENT,
            stdName VARCHAR(50) NOT NULL
        );
        """
    )
    
    with open(STUDENTS_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            command = "insert into students (stdName) values ('" + row['student_name'] + "')"
            cursor.execute(command)
            print('inserted ' + row["student_name"])
        db.commit()
        db.close()


if __name__ == "__main__":
    # import_courses()
    import_students()
