import tempfile
import sqlite3
from pathlib import Path
from typing import Optional
from collections import defaultdict

from .csv_loader import read_rooms, read_enrollment, read_availability, build_course_objects
from .domain_builder import build_domains
from .csp_solver import CourseScheduler
from .room_assigner import assign_rooms_backtracking
from .csv_exporter import write_course_room_schedule, write_teacher_schedule, write_student_schedule

def run_scheduler(
    rooms_path: str,
    enroll_path: str,
    avail_path: str,
    output_dir: Optional[str] = None
) -> dict:
    """
    Organize the entire scheduling pipeline.
    Args:
        rooms_path: path to rooms.csv
        enroll_path: path to tokenized_enrollment.csv
        avail_path: path to tokenized_availability-Copy.csv
        output_dir: optional directory to write CSV outputs
    Returns:
        dict with keys 'course_room', 'teacher', 'student'
    """
    # 1. Load raw data from CSVs
    rooms_data = read_rooms(rooms_path)
    enroll_data = read_enrollment(enroll_path)
    avail_data = read_availability(avail_path)

    # 2. Build domains for each course
    domains = build_domains(avail_data)

    # 3. Build teacher mapping (from availability)
    teacher_of = {}
    for code, rows in avail_data.items():
        teacher_of[code] = rows[0]['teacher_name']

    # 4. Create Course objects
    courses = build_course_objects(avail_data, enroll_data, teacher_of, domains)
    if not courses:
        raise RuntimeError("No schedulable courses found.")

    # 5. Solve CSP (strict first, relaxed if needed)
    scheduler = CourseScheduler(courses, ignore_all_student_conflicts=False)
    schedule = scheduler.solve()
    if schedule is None:
        scheduler = CourseScheduler(courses, ignore_all_student_conflicts=True)
        schedule = scheduler.solve()
        if schedule is None:
            raise RuntimeError("No feasible schedule even with relaxed student conflicts.")

    # 6. Assign rooms
    room_schedule = assign_rooms_backtracking(schedule, courses, rooms_data)

    # 7. Build result lists (JSON-ready)
    course_room_list = []
    teacher_list = []
    student_list = []

    course_teacher = {c.code: c.teacher for c in courses}

    for code, (pattern, room) in room_schedule.items():
        for day, period in sorted(pattern):
            course_room_list.append({
                'courseCode': code,
                'day': day,
                'period': period,
                'roomNumber': room
            })
            teacher_list.append({
                'teacherName': course_teacher.get(code, 'Unknown'),
                'day': day,
                'period': period,
                'courseCode': code,
                'roomNumber': room
            })

    # Student schedule: invert enroll_data
    student_courses = defaultdict(list)
    for course, students in enroll_data.items():
        for sid in students:
            student_courses[sid].append(course)

    for sid, courses_list in student_courses.items():
        for cid in courses_list:
            if cid in room_schedule:
                pattern, room = room_schedule[cid]
                for day, period in sorted(pattern):
                    student_list.append({
                        'studentId': sid,
                        'courseCode': cid,
                        'day': day,
                        'period': period,
                        'roomNumber': room
                    })

    # 8. Export CSV if output_dir is provided
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        write_course_room_schedule(room_schedule, output_path / "course_room_schedule.csv")
        write_teacher_schedule(room_schedule, courses, output_path / "teacher_schedule.csv")
        write_student_schedule(student_list, output_path / "student_schedule.csv")

    return {
        'course_room': course_room_list,
        'teacher': teacher_list,
        'student': student_list
    }