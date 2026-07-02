import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "csv_files"

INPUT_FILE = CSV_DIR / "clean_enrollment.csv"
OUTPUT_FILE = CSV_DIR / "tokenized_enrollment.csv"


def get_student_id(student_name):
    match = re.search(r"(\d+)", str(student_name))
    return int(match.group(1)) if match else None


def get_course_id(course_text):
    if pd.isna(course_text):
        return None

    parts = str(course_text).strip().split()

    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"

    return str(course_text).strip()


def tokenize_enrollment():
    df = pd.read_csv(INPUT_FILE)

    df = df.rename(
        columns={
            "Last name, first name": "student_name",
            "Course 1": "course_1",
            "Course 2": "course_2",
            "Course 3": "course_3",
            "Course 4": "course_4",
            "Course 5": "course_5",
        }
    )

    course_columns = [
        "course_1",
        "course_2",
        "course_3",
        "course_4",
        "course_5",
    ]

    rows = []

    for _, row in df.iterrows():
        student_id = get_student_id(row["student_name"])

        for course_col in course_columns:
            course = row.get(course_col)

            if pd.isna(course) or str(course).strip() == "":
                continue

            rows.append(
                {
                    "student_id": student_id,
                    "course_id": get_course_id(course),
                }
            )

    tokenized = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)

    tokenized.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved tokenized enrollment to {OUTPUT_FILE}")
    print(tokenized.head(20))

    return tokenized


if __name__ == "__main__":
    tokenize_enrollment()
