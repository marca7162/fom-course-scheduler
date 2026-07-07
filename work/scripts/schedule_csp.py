import csv
import itertools
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Set, Tuple, Dict, List, Optional, FrozenSet

# ---------- Paths ----------
PROJECT_ROOT = Path(__file__).resolve().parent
CSV_DIR = PROJECT_ROOT / "csv_files"
DB_FILE = PROJECT_ROOT / "db" / "FOM_Intern_Database.db"

ROOMS_CSV = CSV_DIR / "rooms.csv"
ENROLL_CSV = CSV_DIR / "tokenized_enrollment.csv"
AVAIL_CSV = CSV_DIR / "tokenized_availability.csv"



# ---------- Data Classes ----------
@dataclass
class Course:
    code: str
    teacher: str
    students: Set[int]
    domain: List[FrozenSet[Tuple[str, int]]]
    preference: str
    room_preference: Optional[str] = None   # 'classroom' or 'museum'

@dataclass
class Room:
    number: str
    capacity: int
    available: bool

# ---------- CSV Readers ----------
def read_rooms(csv_path: Path) -> Dict[str, Room]:
    rooms = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rooms[row['Room Number']] = Room(
                number=row['Room Number'],
                capacity=int(row['Capacity']),
                available=bool(int(row['Availability status (is full)']))
            )
    return rooms

def read_enrollment(csv_path: Path) -> Dict[str, Set[int]]:
    enroll = defaultdict(set)
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            enroll[row['course_id']].add(int(row['student_id']))
    return enroll

def read_availability(csv_path: Path) -> Dict[str, List[Dict]]:
    avail = defaultdict(list)
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            avail[row['course_id']].append(row)
    return avail

# ---------- Domain Builder ----------
DAY_GROUPS = {
    'M': ('M',), 'T': ('T',), 'W': ('W',), 'TH': ('TH',), 'F': ('F',),
    'MW': ('M','W'), 'TTH': ('T','TH'), 'TH': ('TH',), 'ALL': ('M','T','W','TH','F'),
}

def build_domains(avail_data: Dict[str, List[Dict]]) -> Dict[str, List[FrozenSet[Tuple[str, int]]]]:
    domains = {}
    for course, rows in avail_data.items():
        # Determine expected number of meetings (max across rows)
        expected = 0
        row_options_list = []

        for row in rows:
            day_group = row['day_group'].strip()
            days = DAY_GROUPS.get(day_group, (day_group,))
            periods = [int(p.strip()) for p in row['period_options'].split(',') if p.strip().isdigit()]
            pref = row['preference'].strip()

            if pref in ('classroom', 'museum'):
                expected = max(expected, len(days))
            elif pref == 'two_in_row':
                expected = max(expected, 2)
            elif pref == 'once_per_week':
                expected = max(expected, 1)
            else:
                expected = max(expected, len(days))

            # Build options for this row
            options = []
            if pref == 'once_per_week':
                for d in days:
                    for p in periods:
                        options.append(frozenset([(d, p)]))
            elif pref == 'two_in_row':
                if len(days) == 1:
                    d = days[0]
                    for i in range(len(periods) - 1):
                        p1, p2 = periods[i], periods[i+1]
                        if p2 == p1 + 1:
                            options.append(frozenset([(d, p1), (d, p2)]))
            else:
                for p in periods:
                    options.append(frozenset((d, p) for d in days))
            row_options_list.append(options)

        # Combine rows via Cartesian product
        domain_set = set()
        for combo in itertools.product(*row_options_list):
            merged = set()
            for pat in combo:
                merged.update(pat)
            if len(merged) == expected:
                domain_set.add(frozenset(merged))
        domains[course] = list(domain_set)
    return domains

# ---------- CSP Solver ----------
class CourseScheduler:
    def __init__(self, courses: List[Course]):
        self.courses = courses
        self.course_dict = {c.code: c for c in courses}
        self.assignment = {}
        self.teacher_schedule = defaultdict(set)

    def is_consistent(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> bool:
        course = self.course_dict[code]
        teacher = course.teacher

        # Teacher conflict
        for slot in pattern:
            if slot in self.teacher_schedule[teacher]:
                return False

        # Student conflict
        for other_code, other_pattern in self.assignment.items():
            other_course = self.course_dict[other_code]
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

    def count_forward_conflicts(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> int:
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
            # Student overlap potential
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

        # Sort domain by forward‑checking heuristic
        domain_sorted = sorted(
            course.domain,
            key=lambda pat: self.count_forward_conflicts(code, pat)
        )

        for pattern in domain_sorted:
            if self.is_consistent(code, pattern):
                self.assign(code, pattern)
                if self.backtrack(idx + 1):
                    return True
                self.unassign(code)
        return False

    def solve(self) -> Optional[Dict[str, FrozenSet[Tuple[str, int]]]]:
        # MRV ordering
        self.courses.sort(key=lambda c: len(c.domain))
        if self.backtrack(0):
            return self.assignment
        return None

# ---------- Room Assignment ----------
def assign_rooms(
    schedule: Dict[str, FrozenSet[Tuple[str, int]]],
    courses: List[Course],
    rooms: Dict[str, Room]
) -> Dict[str, Tuple[FrozenSet[Tuple[str, int]], str]]:
    time_rooms = defaultdict(set)
    room_schedule = {}
    sorted_courses = sorted(courses, key=lambda c: len(c.students), reverse=True)

    for course in sorted_courses:
        code = course.code
        pattern = schedule[code]
        needed = len(course.students)

        chosen = None
        for room in rooms.values():
            if room.capacity < needed:
                continue
            free = True
            for slot in pattern:
                if slot in time_rooms and room.number in time_rooms[slot]:
                    free = False
                    break
            if free:
                chosen = room.number
                break

        if chosen is None:
            raise RuntimeError(f"No room available for {code} (needs {needed} students)")

        for slot in pattern:
            time_rooms[slot].add(chosen)
        room_schedule[code] = (pattern, chosen)
    return room_schedule

# ---------- Main ----------
def main():
    print("Loading CSV data...")
    rooms = read_rooms(ROOMS_CSV)
    enrollment = read_enrollment(ENROLL_CSV)
    avail = read_availability(AVAIL_CSV)

    # Warn about missing availability
    available_courses = set(avail.keys())
    enrolled_courses = set(enrollment.keys())
    missing = enrolled_courses - available_courses
    if missing:
        print(f"WARNING: These courses have no availability data and will be skipped: {missing}")

    # Build domains
    all_domains = build_domains(avail)

    # Create Course objects
    courses = []
    for code, domain in all_domains.items():
        if not domain:
            print(f"WARNING: {code} has empty domain → skipped")
            continue
        first_row = avail[code][0]
        teacher = first_row['teacher_name']
        pref = first_row['preference']
        # Detect room preference if any row says 'classroom' or 'museum'
        room_pref = None
        for row in avail[code]:
            if row['preference'] in ('classroom', 'museum'):
                room_pref = row['preference']
        courses.append(Course(
            code=code,
            teacher=teacher,
            students=enrollment.get(code, set()),
            domain=domain,
            preference=pref,
            room_preference=room_pref
        ))

    if not courses:
        print("No schedulable courses found.")
        return

    print(f"Scheduling {len(courses)} courses...")
    scheduler = CourseScheduler(courses)
    schedule = scheduler.solve()

    if schedule is None:
        print("❌ No feasible time‑slot schedule found.")
        return

    print("\n✅ Time schedule found:")
    for code, pattern in schedule.items():
        print(f"  {code}: {sorted(pattern)}")

    # Assign rooms
    try:
        room_schedule = assign_rooms(schedule, courses, rooms)
        print("\n🏫 Room assignment:")
        for code, (pattern, room) in room_schedule.items():
            print(f"  {code}: {sorted(pattern)} → Room {room}")
    except RuntimeError as e:
        print(f"\n❌ Room assignment failed: {e}")
        return

    # ------------------ Write to database ------------------
    # Uncomment this block to insert the schedule into your SQLite DB
    
    print("\nWriting schedule to database...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Clear old schedule
    cursor.execute("DELETE FROM course_schedule")

    # Insert each meeting
    for code, (pattern, room) in room_schedule.items():
        teacher = next(c.teacher for c in courses if c.code == code)
        for (day, period) in pattern:
            cursor.execute(
                "INSERT INTO course_schedule (courseCode, day, period, teacherName, roomNumber) "
                "VALUES (?, ?, ?, ?, ?)",
                (code, day, period, teacher, room)
            )
    conn.commit()
    conn.close()
    print("Schedule written to database.")
    #-------------------------- 

if __name__ == "__main__":
    main()