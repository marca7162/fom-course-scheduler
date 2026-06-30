import sqlite3
import csv
import itertools
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Set, Tuple, Dict, List, Optional, FrozenSet

# ---------- Paths ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "csv_files"
DB_DIR = PROJECT_ROOT / "db"

# OUTPUT_DIR = Path("output")

DB_DIR.mkdir(exist_ok=True)

DB_FILE = DB_DIR / "FOM_Intern_Database.db"

ROOMS_CSV = CSV_DIR / "rooms.csv"
ENROLL_CSV = CSV_DIR / "tokenized_enrollment.csv"
AVAIL_CSV = CSV_DIR / "tokenized_availability - Copy.csv"  # new filename

# Output file paths
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
COURSE_ROOM_CSV = OUTPUT_DIR / "course_room_schedule.csv"
TEACHER_CSV = OUTPUT_DIR / "teacher_schedule.csv"
STUDENT_CSV = OUTPUT_DIR / "student_schedule.csv"


# ---------- Data classes ----------
@dataclass
class Course:
    code: str
    teacher: str
    students: Set[int]
    domain: List[FrozenSet[Tuple[str, int]]]
    preference: str
    weekly_meeting: Optional[int]  # number of meetings per week (if specified)
    room_preference: Optional[str] = None


@dataclass
class Room:
    number: str
    capacity: int
    available: bool


# ---------- Domain builder (with weekly_meeting) ----------
DAY_GROUPS = {
    "M": ("M",),
    "T": ("T",),
    "W": ("W",),
    "TH": ("TH",),
    "MW": ("M", "W"),
    "TTH": ("T", "TH"),
    "ALL": ("M", "T", "W", "TH"),
}


def generate_options_for_row(row: Dict) -> List[FrozenSet[Tuple[str, int]]]:
    day_group = row["day_group"].strip()
    days = DAY_GROUPS.get(day_group, (day_group,))
    periods = [
        int(p.strip())
        for p in row["period_options"].split(",")
        if p.strip().isdigit()
    ]
    pref = row["preference"].strip()
    weekly = (
        int(row.get("weekly_meeting", 0))
        if row.get("weekly_meeting", "").strip()
        else None
    )

    options = []
    if pref == "once_per_week" or weekly == 1:
        for d in days:
            for p in periods:
                options.append(frozenset([(d, p)]))
    elif pref == "two_in_row" or (weekly == 2 and len(days) == 1):
        if len(days) == 1:
            d = days[0]
            for i in range(len(periods) - 1):
                p1, p2 = periods[i], periods[i + 1]
                if p2 == p1 + 1:
                    options.append(frozenset([(d, p1), (d, p2)]))
    else:
        # default: all days share the same period
        for p in periods:
            options.append(frozenset((d, p) for d in days))
    return options


def build_domains(
    avail_data: Dict[str, List[Dict]],
) -> Dict[str, List[FrozenSet[Tuple[str, int]]]]:
    domains = {}
    for course, rows in avail_data.items():
        has_room_pref = any(
            row["preference"] in ("classroom", "museum") for row in rows
        )

        if has_room_pref:
            row_options_list = []
            for row in rows:
                opts = generate_options_for_row(row)
                if not opts:
                    row_options_list = []
                    break
                row_options_list.append(opts)
            if not row_options_list:
                domains[course] = []
                continue
            domain_set = set()
            for combo in itertools.product(*row_options_list):
                merged = set()
                for pat in combo:
                    merged.update(pat)
                domain_set.add(frozenset(merged))
            domains[course] = list(domain_set)
        else:
            domain_set = set()
            for row in rows:
                opts = generate_options_for_row(row)
                domain_set.update(opts)
            domains[course] = list(domain_set)
    return domains


# ---------- CSP Solver with conditional student conflicts ----------
class CourseScheduler:
    def __init__(
        self, courses: List[Course], ignore_all_student_conflicts: bool = False
    ):
        self.courses = courses
        self.course_dict = {c.code: c for c in courses}
        self.assignment = {}
        self.teacher_schedule = defaultdict(set)
        self.ignore_all_student_conflicts = ignore_all_student_conflicts

    def is_madr_course(self, code: str) -> bool:
        return code.startswith("MADR")

    def is_consistent(
        self, code: str, pattern: FrozenSet[Tuple[str, int]]
    ) -> bool:
        course = self.course_dict[code]
        teacher = course.teacher

        # 1) Teacher conflict (always enforced)
        for slot in pattern:
            if slot in self.teacher_schedule[teacher]:
                return False

        # 2) Student conflict (only if both courses are MADR and not globally ignored)
        if not self.ignore_all_student_conflicts:
            for other_code, other_pattern in self.assignment.items():
                other_course = self.course_dict[other_code]
                # Apply student conflict only if both course codes start with "MADR"
                if self.is_madr_course(code) and self.is_madr_course(
                    other_code
                ):
                    if course.students & other_course.students:
                        if pattern & other_pattern:
                            return False
        return True

    def assign(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> None:
        self.assignment[code] = pattern
        teacher = self.course_dict[code].teacher
        for slot in pattern:
            self.teacher_schedule[teacher].add(slot)

    def unassign(self, code: str) -> None:
        pattern = self.assignment.pop(code)
        teacher = self.course_dict[code].teacher
        for slot in pattern:
            self.teacher_schedule[teacher].remove(slot)

    def count_forward_conflicts(
        self, code: str, pattern: FrozenSet[Tuple[str, int]]
    ) -> int:
        conflicts = 0
        course = self.course_dict[code]
        for other in self.courses:
            if other.code == code or other.code in self.assignment:
                continue
            # Teacher overlap potential
            if other.teacher == course.teacher:
                for slot in pattern:
                    for dom in other.domain:
                        if slot in dom:
                            conflicts += 1
                            break
            # Student overlap potential only if both MADR
            if (
                not self.ignore_all_student_conflicts
                and self.is_madr_course(code)
                and self.is_madr_course(other.code)
            ):
                if course.students & other.students:
                    for slot in pattern:
                        for dom in other.domain:
                            if slot in dom:
                                conflicts += 1
                                break
        return conflicts

    def backtrack(self, idx: int) -> bool:
        if idx == len(self.courses):
            return True
        course = self.courses[idx]
        code = course.code
        domain_sorted = sorted(
            course.domain,
            key=lambda pat: self.count_forward_conflicts(code, pat),
        )
        for pattern in domain_sorted:
            if self.is_consistent(code, pattern):
                self.assign(code, pattern)
                if self.backtrack(idx + 1):
                    return True
                self.unassign(code)
        return False

    def solve(self) -> Optional[Dict[str, FrozenSet[Tuple[str, int]]]]:
        self.courses.sort(key=lambda c: len(c.domain))
        if self.backtrack(0):
            return self.assignment
        return None


# ---------- Room assignment with backtracking ----------
def assign_rooms_backtracking(
    schedule: Dict[str, FrozenSet[Tuple[str, int]]],
    courses: List[Course],
    rooms: Dict[str, Room],
) -> Dict[str, Tuple[FrozenSet[Tuple[str, int]], str]]:
    items = []
    for course in courses:
        code = course.code
        pattern = schedule[code]
        needed = len(course.students)
        items.append((code, pattern, needed))

    items.sort(key=lambda x: (-len(x[1]), -x[2]))
    room_list = list(rooms.values())
    occupancy = defaultdict(set)
    assignment = {}

    def backtrack(idx: int) -> bool:
        if idx == len(items):
            return True
        code, pattern, needed = items[idx]
        candidates = []
        for room in room_list:
            if room.capacity < needed:
                continue
            free = True
            for slot in pattern:
                if slot in occupancy and room.number in occupancy[slot]:
                    free = False
                    break
            if free:
                candidates.append(room.number)

        # Try candidates in order (could sort by capacity)
        for room_num in candidates:
            assignment[code] = room_num
            for slot in pattern:
                occupancy[slot].add(room_num)
            if backtrack(idx + 1):
                return True
            for slot in pattern:
                occupancy[slot].remove(room_num)
            del assignment[code]
        return False

    if backtrack(0):
        result = {}
        for course in courses:
            code = course.code
            pattern = schedule[code]
            room = assignment[code]
            result[code] = (pattern, room)
        return result
    else:
        raise RuntimeError(
            "No feasible room assignment found. Try adding more rooms or relaxing room capacity."
        )


# ---------- CSV export functions ----------
def write_course_room_schedule(room_schedule: Dict, output_path: Path) -> None:
    """Write each course meeting time and room to CSV."""
    print(f"  Writing course/room schedule to {output_path}")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["courseCode", "day", "period", "roomNumber"])
        count = 0
        for code, (pattern, room) in room_schedule.items():
            for day, period in sorted(pattern):
                writer.writerow([code, day, period, room])
                count += 1
        print(f"    Wrote {count} rows.")


def write_teacher_schedule(
    room_schedule: Dict, courses: List[Course], output_path: Path
) -> None:
    """Write teacher schedule (one row per meeting)."""
    print(f"  Writing teacher schedule to {output_path}")
    course_teacher = {c.code: c.teacher for c in courses}
    rows = []
    for code, (pattern, room) in room_schedule.items():
        teacher = course_teacher.get(code, "Unknown")
        for day, period in sorted(pattern):
            rows.append((teacher, day, period, code, room))
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["teacherName", "day", "period", "courseCode", "roomNumber"]
        )
        writer.writerows(rows)
    print(f"    Wrote {len(rows)} rows.")


def write_student_schedule(
    conn: sqlite3.Connection, room_schedule: Dict, output_path: Path
) -> None:
    """Write each student's enrolled courses with times and rooms."""
    print(f"  Writing student schedule to {output_path}")
    cursor = conn.cursor()
    cursor.execute("SELECT stdId, courseID FROM student_courses")
    student_courses = defaultdict(list)
    for sid, cid in cursor.fetchall():
        student_courses[sid].append(cid)

    rows = []
    for sid, courses in student_courses.items():
        for cid in courses:
            if cid in room_schedule:
                pattern, room = room_schedule[cid]
                for day, period in sorted(pattern):
                    rows.append((sid, cid, day, period, room))
            else:
                print(f"    Warning: course {cid} not in room_schedule")
    rows.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["studentId", "courseCode", "day", "period", "roomNumber"]
        )
        writer.writerows(rows)
    print(f"    Wrote {len(rows)} rows.")


# ---------- Database functions ----------
def create_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS course_schedule;
        DROP TABLE IF EXISTS student_courses;
        DROP TABLE IF EXISTS students;
        DROP TABLE IF EXISTS Teach_Course;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS teachers;
        DROP TABLE IF EXISTS rooms;

        CREATE TABLE rooms (
            "Room Number" VARCHAR(10) PRIMARY KEY,
            Capacity INTEGER,
            "Availability status (is full)" INTEGER
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

        CREATE TABLE Teach_Course (
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


def load_rooms(conn: sqlite3.Connection):
    import pandas as pd

    df = pd.read_csv(ROOMS_CSV)
    df.to_sql("rooms", conn, if_exists="append", index=False)


def load_teachers_and_courses(conn: sqlite3.Connection):
    cursor = conn.cursor()
    avail = {}
    with open(AVAIL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
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

    enroll_counts = defaultdict(int)
    with open(ENROLL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
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
            "INSERT INTO Teach_Course (T_ID, C_ID) VALUES (?, ?)",
            (t_id, course),
        )
    conn.commit()


def load_students_and_enrollments(conn: sqlite3.Connection):
    cursor = conn.cursor()
    student_courses = defaultdict(list)
    with open(ENROLL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
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


def get_course_data_from_db(conn: sqlite3.Connection) -> List[Course]:
    cursor = conn.cursor()
    cursor.execute("SELECT courseID, stdID FROM student_courses")
    enroll = defaultdict(set)
    for course, sid in cursor.fetchall():
        enroll[course].add(sid)

    cursor.execute("""
        SELECT C_ID, tName
        FROM Teach_Course tc
        JOIN teachers t ON tc.T_ID = t.tNo
    """)
    teacher_of = dict(cursor.fetchall())

    # Read availability from CSV (could read from a table if stored)
    avail = {}
    with open(AVAIL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            course = row["course_id"]
            if course not in avail:
                avail[course] = []
            avail[course].append(row)

    domains = build_domains(avail)

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
            Course(
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


def write_schedule_to_db(conn: sqlite3.Connection, room_schedule: Dict):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM course_schedule")
    for course_code, (pattern, room) in room_schedule.items():
        cursor.execute(
            """
            SELECT tName FROM teachers t
            JOIN Teach_Course tc ON t.tNo = tc.T_ID
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
    conn: sqlite3.Connection, room_schedule: Dict, courses: List[Course]
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
    student_courses = defaultdict(list)
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


# ---------- Main ----------
def main():
    print("=== Setting up database and loading data ===")
    conn = sqlite3.connect(DB_FILE)
    try:
        create_tables(conn)
        load_rooms(conn)
        load_teachers_and_courses(conn)
        load_students_and_enrollments(conn)
        print("Database created and data loaded successfully.")

        print("\n=== Building CSP model ===")
        courses = get_course_data_from_db(conn)
        if not courses:
            print("No schedulable courses found. Exiting.")
            return

        cursor = conn.cursor()
        cursor.execute(
            'SELECT "Room Number", Capacity, "Availability status (is full)" FROM rooms'
        )
        rooms = {}
        for row in cursor.fetchall():
            rooms[row[0]] = Room(row[0], int(row[1]), bool(int(row[2])))

        print(f"Number of courses to schedule: {len(courses)}")
        print(f"Number of rooms available: {len(rooms)}")

        # ----- First attempt: full constraints (teacher + MADR student conflicts) -----
        print(
            "\n=== Attempt 1: Full constraints (teacher + MADR student conflicts) ==="
        )
        scheduler = CourseScheduler(
            courses, ignore_all_student_conflicts=False
        )
        schedule = scheduler.solve()

        if schedule is not None:
            print("✅ Schedule found with full constraints.")
            final_schedule = schedule
            relaxed = False
        else:
            print("❌ No solution with full constraints.")
            print(
                "🔁 Relaxing student‑conflict constraint for ALL courses (including MADR)..."
            )
            scheduler2 = CourseScheduler(
                courses, ignore_all_student_conflicts=True
            )
            schedule = scheduler2.solve()
            if schedule is not None:
                print("✅ Schedule found with all student conflicts relaxed.")
                final_schedule = schedule
                relaxed = True
            else:
                print(
                    "❌ Even with all student conflicts relaxed, no feasible schedule found."
                )
                print(
                    "   This indicates teacher conflicts are too tight. Consider adding more periods."
                )
                return

        # ----- Display teacher-room schedule -----
        print("\n📅 Teacher-Room Schedule:")
        for code, pattern in final_schedule.items():
            print(f"  {code}: {sorted(pattern)}")

        if relaxed:
            print(
                "\n⚠️  WARNING: Student conflicts were relaxed for ALL courses."
            )
            print("   Overlaps between MADR courses may exist.")
            add_trigger = False
        else:
            add_trigger = True

        # ----- Assign rooms (using backtracking) -----
        print("\n=== Assigning rooms (backtracking) ===")
        try:
            room_schedule = assign_rooms_backtracking(
                final_schedule, courses, rooms
            )
            print("\n🏫 Room assignment:")
            for code, (pattern, room) in room_schedule.items():
                print(f"  {code}: {sorted(pattern)} → Room {room}")
        except RuntimeError as e:
            print(f"\n❌ Room assignment failed: {e}")
            return

        # ----- Write to DB -----
        write_schedule_to_db(conn, room_schedule)
        print("\n✅ Schedule written to database table 'course_schedule'.")

        # ----- Add trigger (only if student conflicts were NOT relaxed) -----
        if add_trigger:
            print(
                "\n=== Adding trigger to prevent student overlaps (only for MADR courses) ==="
            )
            # We can add a trigger that checks if both courses are MADR
            # But a simple trigger on student_courses cannot easily check the course code of the existing course.
            # So we'll skip the trigger or implement a more complex one. For simplicity, we warn.
            print(
                "   (Skipping trigger; use application logic to enforce MADR-only overlap rule.)"
            )
        else:
            print(
                "\n⚠️  Trigger NOT added because student conflicts were relaxed."
            )

        # ----- Print student schedules -----
        print_student_schedules(conn, room_schedule, courses)

        print("\n🎉 Scheduling complete!")

        # ----- Export CSVs -----
        print("\n📤 Exporting CSV files...")
        OUTPUT_DIR.mkdir(exist_ok=True)  # ensure folder exists

        if room_schedule:
            write_course_room_schedule(room_schedule, COURSE_ROOM_CSV)
            write_teacher_schedule(room_schedule, courses, TEACHER_CSV)
            write_student_schedule(conn, room_schedule, STUDENT_CSV)
            print(f"  - Course/Room schedule: {COURSE_ROOM_CSV}")
            print(f"  - Teacher schedule:      {TEACHER_CSV}")
            print(f"  - Student schedule:      {STUDENT_CSV}")
        else:
            print("⚠️  room_schedule is empty – nothing to export.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
