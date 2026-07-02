import initializer as init
import course_scheduler as cs
import db_builder as db
import export as ex


def main():
    if init.DB_FILE.exists():
        init.DB_FILE.unlink()

    print("=== Setting up database and loading data ===")
    conn = init.sqlite3.connect(init.DB_FILE)

    try:
        db.create_tables(conn)
        db.load_rooms(conn)
        db.load_teachers_and_courses(conn)
        db.load_students_and_enrollments(conn)

        courses = db.get_course_data_from_db(conn)
        if not courses:
            return "hard_fail"

        cursor = conn.cursor()
        cursor.execute('SELECT "Room Number", Capacity FROM rooms')

        rooms = {}
        for row in cursor.fetchall():
            rooms[row[0]] = init.Room(row[0], int(row[1]), False)

        print("\n=== Attempt 1: Full constraints ===")
        scheduler = cs.CourseScheduler(
            courses, ignore_all_student_conflicts=False
        )
        schedule = scheduler.solve()

        if schedule is not None:
            print("✅ Schedule found with full constraints.")
            final_schedule = schedule
            result = "full_success"
        else:
            print("❌ No solution with full constraints.")
            print("🔁 Trying relaxed constraints...")

            scheduler2 = cs.CourseScheduler(
                courses, ignore_all_student_conflicts=True
            )
            schedule = scheduler2.solve()

            if schedule is not None:
                print(
                    "⚠️ Schedule found only after relaxing student conflicts."
                )
                final_schedule = schedule
                result = "relaxed_success"
            else:
                print("❌ No schedule found even after relaxing constraints.")
                return "hard_fail"

        print("\n=== Assigning rooms ===")
        try:
            room_schedule = cs.assign_rooms_backtracking(
                final_schedule, courses, rooms
            )
        except RuntimeError as e:
            print(f"\n❌ Room assignment failed: {e}")
            return "room_fail"

        db.write_schedule_to_db(conn, room_schedule)

        print("\n📤 Exporting CSV files...")
        init.OUTPUT_DIR.mkdir(exist_ok=True)

        if not room_schedule:
            return "room_fail"

        ex.write_course_room_schedule(room_schedule, init.COURSE_ROOM_CSV)
        ex.write_teacher_schedule(room_schedule, courses, init.TEACHER_CSV)
        ex.write_student_schedule(conn, room_schedule, init.STUDENT_CSV)

        return result

    finally:
        conn.close()


def run_multiple_times(n: int):
    full_success = 0
    relaxed_success = 0
    room_fail = 0
    hard_fail = 0

    for i in range(n):
        print(f"\n========== RUN {i + 1} / {n} ==========")
        result = main()

        if result == "full_success":
            full_success += 1
        elif result == "relaxed_success":
            relaxed_success += 1
        elif result == "room_fail":
            room_fail += 1
        else:
            hard_fail += 1

    print("\n========== RESULTS ==========")
    print(f"Full constraint successes:     {full_success}")
    print(f"Relaxed constraint successes:  {relaxed_success}")
    print(f"Room assignment failures:      {room_fail}")
    print(f"Hard failures:                 {hard_fail}")


if __name__ == "__main__":
    run_multiple_times(100)
