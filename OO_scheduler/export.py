import initializer as init
# import course_scheduler as cs
# import db_builder as db


#  ---------- CSV export functions ----------
def write_course_room_schedule(
    room_schedule: init.Dict, output_path: init.Path
) -> None:
    """Write each course meeting time and room to CSV."""
    print(f"  Writing course/room schedule to {output_path}")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = init.csv.writer(f)
        writer.writerow(["courseCode", "day", "period", "roomNumber"])
        count = 0
        for code, (pattern, room) in room_schedule.items():
            for day, period in sorted(pattern):
                writer.writerow([code, day, period, room])
                count += 1
        print(f"    Wrote {count} rows.")


def write_teacher_schedule(
    room_schedule: init.Dict,
    courses: init.List[init.Course],
    output_path: init.Path,
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
        writer = init.csv.writer(f)
        writer.writerow(
            ["teacherName", "day", "period", "courseCode", "roomNumber"]
        )
        writer.writerows(rows)
    print(f"    Wrote {len(rows)} rows.")


def write_student_schedule(
    conn: init.sqlite3.Connection,
    room_schedule: init.Dict,
    output_path: init.Path,
) -> None:
    """Write each student's enrolled courses with times and rooms."""
    print(f"  Writing student schedule to {output_path}")
    cursor = conn.cursor()
    cursor.execute("SELECT stdId, courseID FROM student_courses")
    student_courses = init.defaultdict(list)
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
        writer = init.csv.writer(f)
        writer.writerow(
            ["studentId", "courseCode", "day", "period", "roomNumber"]
        )
        writer.writerows(rows)
    print(f"    Wrote {len(rows)} rows.")
