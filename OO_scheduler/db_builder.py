import initializer as init
# import course_scheduler as cs


# ---------- Database functions ----------
def create_tables(conn: init.sqlite3.Connection):
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS course_schedule;
        DROP TABLE IF EXISTS student_courses;
        DROP TABLE IF EXISTS students;
        DROP TABLE IF EXISTS teach_course;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS teachers;
        DROP TABLE IF EXISTS rooms;

        CREATE TABLE rooms (
            "Room Number" VARCHAR(10) PRIMARY KEY,
            Capacity INTEGER,
            Av1 INTEGER,
            Av2 INTEGER,
            Av3 INTEGER,
            Av4 INTEGER,
            Av5 INTEGER,
            Av6 INTEGER,
            Av7 INTEGER
        );

        CREATE TABLE teachers (
            tNo INTEGER PRIMARY KEY AUTOINCREMENT,
            tName VARCHAR(50) NOT NULL,
            availableDays VARCHAR(15) NOT NULL,
            periods varchar(15) NOT NULL,
            preference varchar(20) not null,
            weekly_meeting integer       
        );

        CREATE TABLE courses (
            courseCode VARCHAR(15) PRIMARY KEY,
            courseName VARCHAR(50) NOT NULL,
            credits INTEGER NOT NULL,
            totalRegisteredStudents INTEGER NOT NULL
        );

        CREATE TABLE teach_course (
            T_ID INTEGER,
            C_ID VARCHAR(15),
            FOREIGN KEY (T_ID) REFERENCES teachers(tNo),
            FOREIGN KEY (C_ID) REFERENCES courses(courseCode)
        );

        CREATE TABLE students (
            stdId INTEGER PRIMARY KEY AUTOINCREMENT,
            stdName VARCHAR(50) NOT NULL
        );

        CREATE TABLE student_courses (
            stdID INTEGER,
            courseID VARCHAR(15),
            FOREIGN KEY (stdID) REFERENCES students(stdId),
            FOREIGN KEY (courseID) REFERENCES courses(courseCode)
        );

        CREATE TABLE course_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            courseCode VARCHAR(15) NOT NULL,
            day VARCHAR(2) NOT NULL,
            period INTEGER NOT NULL,
            teacherName VARCHAR(50) NOT NULL,
            roomNumber VARCHAR(10),
            FOREIGN KEY (courseCode) REFERENCES courses(courseCode)
        );
    """)
    conn.commit()


def load_rooms(conn: init.sqlite3.Connection):
    import pandas as pd

    df = pd.read_csv(init.ROOMS_CSV)
    df.to_sql("rooms", conn, if_exists="append", index=False)


def load_teachers_and_courses(conn: init.sqlite3.Connection):
    cursor = conn.cursor()
    avail = {}
    with open(init.AVAIL_CSV, "r", encoding="utf-8") as f:
        reader = init.csv.DictReader(f)
        for row in reader:
            course = row["course_id"]
            if course not in avail:
                avail[course] = []
            avail[course].append(row)

    teachers = {}
    for rows in avail.values():
        for row in rows:
            name = row["teacher_name"]
            day_group = row["day_group"]
            period_options = row["period_options"]
            preference = row["preference"]
            weekly_meeting = row.get("weekly_meeting", None)
            if name not in teachers:
                cursor.execute(
                    "INSERT INTO teachers (tName, availableDays, periods, preference, weekly_meeting) VALUES (?, ?, ?, ?, ?)",
                    (
                        name,
                        day_group,
                        period_options,
                        preference,
                        weekly_meeting,
                    ),
                )
                teachers[name] = cursor.lastrowid

    conn.commit()

    enroll_counts = init.defaultdict(int)
    with open(init.ENROLL_CSV, "r", encoding="utf-8") as f:
        reader = init.csv.DictReader(f)
        for row in reader:
            enroll_counts[row["course_id"]] += 1

    for course, rows in avail.items():
        course_name = course
        credits = 3
        total = enroll_counts.get(course, 0)
        cursor.execute(
            "INSERT INTO courses (courseCode, courseName, credits, totalRegisteredStudents) VALUES (?, ?, ?, ?)",
            (course, course_name, credits, total),
        )
        teacher_name = rows[0]["teacher_name"]
        t_id = teachers[teacher_name]
        cursor.execute(
            "INSERT INTO teach_course (T_ID, C_ID) VALUES (?, ?)",
            (t_id, course),
        )
    conn.commit()


def load_students_and_enrollments(conn: init.sqlite3.Connection):
    cursor = conn.cursor()
    student_courses = init.defaultdict(list)
    with open(init.ENROLL_CSV, "r", encoding="utf-8") as f:
        reader = init.csv.DictReader(f)
        for row in reader:
            student_id = int(row["student_id"])
            course = row["course_id"]
            student_courses[student_id].append(course)

    for std_id, courses in student_courses.items():
        cursor.execute(
            "INSERT INTO students (stdName) VALUES (?)", (f"Student_{std_id}",)
        )
        new_id = cursor.lastrowid
        for course in courses:
            cursor.execute(
                "INSERT INTO student_courses (stdID, courseID) VALUES (?, ?)",
                (new_id, course),
            )
    conn.commit()


def get_course_data_from_db(
    conn: init.sqlite3.Connection,
) -> init.List[init.Course]:
    cursor = conn.cursor()
    cursor.execute("SELECT courseID, stdID FROM student_courses")
    enroll = init.defaultdict(set)
    for course, sid in cursor.fetchall():
        enroll[course].add(sid)

    cursor.execute("""
        SELECT C_ID, tName
        FROM teach_course tc
        JOIN teachers t ON tc.T_ID = t.tNo
    """)
    teacher_of = dict(cursor.fetchall())

    # Read availability from CSV (could read from a table if stored)
    avail = {}
    with open(init.AVAIL_CSV, "r", encoding="utf-8") as f:
        reader = init.csv.DictReader(f)
        for row in reader:
            course = row["course_id"]
            if course not in avail:
                avail[course] = []
            avail[course].append(row)

    domains = init.build_domains(avail)

    courses = []
    for code, domain in domains.items():
        if not domain:
            print(f"WARNING: {code} has empty domain → skipped")
            continue
        teacher = teacher_of.get(code, "Unknown")
        # Get preference and weekly_meeting from first row (assuming consistent)
        first_row = avail[code][0]
        pref = first_row["preference"].strip()
        weekly_str = first_row.get("weekly_meeting", "").strip()
        weekly = int(weekly_str) if weekly_str else None
        room_pref = None
        for row in avail[code]:
            if row["preference"] in ("classroom", "museum"):
                room_pref = row["preference"]
        students = enroll.get(code, set())
        courses.append(
            init.Course(
                code=code,
                teacher=teacher,
                students=students,
                domain=domain,
                preference=pref,
                weekly_meeting=weekly,
                room_preference=room_pref,
            )
        )
    return courses


def write_schedule_to_db(
    conn: init.sqlite3.Connection, room_schedule: init.Dict
):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM course_schedule")
    for course_code, (pattern, room) in room_schedule.items():
        cursor.execute(
            """
            SELECT tName FROM teachers t
            JOIN teach_course tc ON t.tNo = tc.T_ID
            WHERE tc.C_ID = ?
        """,
            (course_code,),
        )
        teacher_row = cursor.fetchone()
        teacher = teacher_row[0] if teacher_row else "Unknown"
        for day, period in pattern:
            cursor.execute(
                """
                INSERT INTO course_schedule (courseCode, day, period, teacherName, roomNumber)
                VALUES (?, ?, ?, ?, ?)
            """,
                (course_code, day, period, teacher, room),
            )
    conn.commit()


# ---------- Print student schedules ----------
def print_student_schedules(
    conn: init.sqlite3.Connection,
    room_schedule: init.Dict,
    courses: init.List[init.Course],
):
    # Build mapping from course to time pattern + room
    course_time_room = {
        code: (pattern, room)
        for code, (pattern, room) in room_schedule.items()
    }

    # Get all students and their courses
    cursor = conn.cursor()
    cursor.execute("""
        SELECT stdId, courseID FROM student_courses
    """)
    student_courses = init.defaultdict(list)
    for std_id, course in cursor.fetchall():
        student_courses[std_id].append(course)

    # Print per student
    print("\n👨‍🎓 Student schedules:")
    for std_id, courses_enrolled in student_courses.items():
        print(f"\nStudent {std_id}:")
        for course in sorted(courses_enrolled):
            if course in course_time_room:
                pattern, room = course_time_room[course]
                times = sorted(pattern)
                # Convert to readable format
                time_str = ", ".join(f"{d} P{p}" for d, p in times)
                print(f"  {course}: {time_str} → Room {room}")
            else:
                print(f"  {course}: NOT SCHEDULED")
