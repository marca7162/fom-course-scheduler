import initializer as init
import course_scheduler as cs
import db_builder as db
import export as ex


# ---------- Main ----------
def main():
    print("=== Setting up database and loading data ===")
    conn = init.sqlite3.connect(init.DB_FILE)
    try:
        db.create_tables(conn)
        db.load_rooms(conn)
        db.load_teachers_and_courses(conn)
        db.load_students_and_enrollments(conn)
        print("Database created and data loaded successfully.")

        print("\n=== Building CSP model ===")
        courses = db.get_course_data_from_db(conn)
        if not courses:
            print("No schedulable courses found. Exiting.")
            return

        cursor = conn.cursor()
        cursor.execute('SELECT "Room Number", Capacity FROM rooms')
        rooms = {}
        for row in cursor.fetchall():
            rooms[row[0]] = init.Room(row[0], int(row[1]), False)

        print(f"Number of courses to schedule: {len(courses)}")
        print(f"Number of rooms available: {len(rooms)}")

        # ----- First attempt: full constraints (teacher + MADR student conflicts) -----
        print(
            "\n=== Attempt 1: Full constraints (teacher + MADR student conflicts) ==="
        )
        scheduler = cs.CourseScheduler(
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
            scheduler2 = cs.CourseScheduler(
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
            room_schedule = cs.assign_rooms_backtracking(
                final_schedule, courses, rooms
            )
            print("\n🏫 Room assignment:")
            for code, (pattern, room) in room_schedule.items():
                print(f"  {code}: {sorted(pattern)} → Room {room}")
        except RuntimeError as e:
            print(f"\n Room assignment failed: {e}")
            return

        # ----- Write to DB -----
        db.write_schedule_to_db(conn, room_schedule)
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
        db.print_student_schedules(conn, room_schedule, courses)

        print("\n🎉 Scheduling complete!")

        # ----- Export CSVs -----
        print("\n📤 Exporting CSV files...")
        init.OUTPUT_DIR.mkdir(exist_ok=True)  # ensure folder exists

        if room_schedule:
            ex.write_course_room_schedule(room_schedule, init.COURSE_ROOM_CSV)
            ex.write_teacher_schedule(room_schedule, courses, init.TEACHER_CSV)
            ex.write_student_schedule(conn, room_schedule, init.STUDENT_CSV)
            print(f"  - Course/Room schedule: {init.COURSE_ROOM_CSV}")
            print(f"  - Teacher schedule:      {init.TEACHER_CSV}")
            print(f"  - Student schedule:      {init.STUDENT_CSV}")
            return True
        else:
            print("⚠️  room_schedule is empty – nothing to export.")
            return False
    finally:
        conn.close()


def run_multiple_times(n: int):
    global success, fail
    for _ in range(n):
        if main():
            success += 1
        else:
            fail += 1
        print(f"\n✅ Successful runs: {success}")
        print(f"❌ Failed runs: {fail}")
if __name__ == "__main__":
    success = 0
    fail = 0
    run_multiple_times(100)