import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "csv_files"
DB_DIR = PROJECT_ROOT / "db"

DB_FILE = DB_DIR / "FOM_Intern_Database.db"
COUNTS_FILE = CSV_DIR / "clean_counts.csv"
STUDENTS_FILE = CSV_DIR / "clean_enrollment.csv"
STUDENT_COURSES_FILE = CSV_DIR / "tokenized_enrollment.csv"
TEACHERS_FILE = CSV_DIR / "tokenized_availability.csv"
ROOMS_FILE = CSV_DIR / "rooms.csv"


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

def import_tokenized_enrollment():
    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()

    cursor.execute("drop table student_courses")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS student_courses (
            stdID INTEGER,
            courseID VARCHAR(15),
            FOREIGN KEY (stdID) REFERENCES students(stdId),
            FOREIGN KEY (courseID) REFERENCES courses(courseCode)
        );
        """
    )

    with open(STUDENT_COURSES_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            command = "insert into student_courses values ("
            command += row['student_id'] + ', ' + "'" + row['course_id'] + "'" + ')'
            # print(command)
            cursor.execute(command)
            print("inserted " + row["student_id"] + " with " + row["course_id"])
        db.commit()
        db.close()

def import_teachers():
    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()

    cursor.execute("drop table if exists teachers")
    # cursor.execute("drop table sqlite_sequence")
    cursor.execute(
        """
        create table if not exists teachers(
        tID integer primary key autoincrement,
        tName varchar (50) not null,
        avM char(1) not null,
        avT char(1) not null,
        avW char(1) not null,
        avTh char(1) not null,
        periods varchar (15) not null
        );
        """
    )
    
    with open(TEACHERS_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        teachers = []

        for row in reader:
            if row["teacher_name"] not in teachers:
                cursor.execute(
                    "insert into teachers (tName, avM, avT, avW, avTh, periods) values (?, ?, ?, ?, ?, ?)",
                    (row["teacher_name"], 0, 0, 0, 0, row["period_options"]),
                )
                teachers.append(row["teacher_name"])
            tid = str(teachers.index(row['teacher_name']) + 1)
            if 'M' in row["day_group"]:
                cursor.execute(
                    "update teachers set avM = 1 where tID = ?",(tid,))
            if 'W' in row["day_group"]:
                cursor.execute(
                    "update teachers set avW = 1 where tID = ?",(tid,))
            if 'TTH' in row["day_group"]:
                cursor.execute(
                    "update teachers set avT = 1, avTh = 1 where tID = ?",(tid,))
            elif 'TH' in row["day_group"]:
                cursor.execute(
                    "update teachers set avTH = 1 where tID = ?",(tid,))
            elif 'T' in row["day_group"]:
                cursor.execute(
                    "update teachers set avT = 1 where tID = ?",(tid,))

        
        # for row in reader:
        #     print(row["day_group"])
        #     if 'M' in row["day_group"]:
        #         cursor.execute(
        #             """update teachers
        #                set avM = 1
        #                where tID = ?
        #             """,(teachers.index(row["teacher_name"]) + 1)
        #         )
                
    
    db.commit()
    db.close()

def import_rooms():
    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()

    cursor.execute("drop table if exists rooms")
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS rooms(
	    roomNo varchar(15) primary key,
	    capacity int  not null,
	    av1 char(1) not null,
        av2 char(1) not null,
        av3 char(1) not null,
        av4 char(1) not null,
        av5 char(1) not null,
        av6 char(1) not null,
        av7 char(1) not null
        );''')
    
    with open(ROOMS_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cursor.execute(
                '''
                insert into rooms (roomNo, capacity, av1, av2, av3, av4, av5, av6, av7)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (row["Room Number"], row['Capacity'], row['Av1'], row['Av2'], row['Av3'], row['Av4'],
                  row['Av5'], row['Av6'], row['Av7']),
            )
            print('inserted ' + row["Room Number"])
        
        db.commit()
        db.close()


if __name__ == "__main__":
    # import_courses()
    # import_students()
    # import_tokenized_enrollment()
    import_teachers()
    # import_rooms()