import csv
from pathlib import Path
from typing import Dict, List

def write_course_room_schedule(room_schedule: Dict, output_path: Path) -> None:
    """Write each course meeting time and room to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['courseCode', 'day', 'period', 'roomNumber'])
        for code, (pattern, room) in room_schedule.items():
            for day, period in sorted(pattern):
                writer.writerow([code, day, period, room])

def write_teacher_schedule(room_schedule: Dict, courses: List, output_path: Path) -> None:
    """Write teacher schedule (one row per meeting)."""
    course_teacher = {c.code: c.teacher for c in courses}
    rows = []
    for code, (pattern, room) in room_schedule.items():
        teacher = course_teacher.get(code, 'Unknown')
        for day, period in sorted(pattern):
            rows.append((teacher, day, period, code, room))
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['teacherName', 'day', 'period', 'courseCode', 'roomNumber'])
        writer.writerows(rows)

def write_student_schedule(student_list: List[Dict], output_path: Path) -> None:
    """Write student schedule from the list of dicts."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['studentId', 'courseCode', 'day', 'period', 'roomNumber'])
        rows = [(row['studentId'], row['courseCode'], row['day'], row['period'], row['roomNumber'])
                for row in student_list]
        rows.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
        writer.writerows(rows)