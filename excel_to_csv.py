from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent

INPUT_FILE = ROOT / "Sample Enrollement Record.xlsx"

OUTPUT_ENROLLMENT = ROOT / "clean_enrollment.csv"
OUTPUT_PERIODS = ROOT / "clean_periods.csv"
OUTPUT_AVAILABILITY = ROOT / "clean_availability.csv"
OUTPUT_COUNTS = ROOT / "clean_counts.csv"


def clean_enrollment():
    df = pd.read_excel(INPUT_FILE, sheet_name="Final Enrollment", header=1)

    df = df[
        [
            "Last name, first name",
            "Course 1",
            "Course 2",
            "Course 3",
            "Course 4",
            "Course 5",
        ]
    ].copy()

    df.columns = [
        "student_name",
        "course_1",
        "course_2",
        "course_3",
        "course_4",
        "course_5",
    ]

    df = df.dropna(how="all")
    df.to_csv(OUTPUT_ENROLLMENT, index=False)


def clean_counts():
    df = pd.read_excel(
        INPUT_FILE,
        sheet_name="Final Enrollment",
        header=1,
    )

    df = df[["Full Course List", "Credits"]].copy()

    df.columns = [
        "full_course_list",
        "credits",
    ]

    df = df.dropna(subset=["full_course_list"])

    df["full_course_list"] = df["full_course_list"].astype(str).str.strip()

    df = df[~df["full_course_list"].str.startswith("Notes", na=False)]

    df = df.reset_index(drop=True)

    df.to_csv(OUTPUT_COUNTS, index=False)


def clean_periods():
    df = pd.read_excel(INPUT_FILE, sheet_name="Class Periods", header=None)

    clean_df = df.iloc[1:, 0:5].copy()

    clean_df.columns = [
        "time",
        "m",
        "t",
        "w",
        "th",
    ]

    clean_df = clean_df.dropna(subset=["time"], how="all")
    clean_df = clean_df.reset_index(drop=True)

    clean_df.to_csv(OUTPUT_PERIODS, index=False)


def clean_availability():
    df = pd.read_excel(
        INPUT_FILE,
        sheet_name="Teacher Availability",
        header=None,
    )

    clean_df = df.iloc[:, 0:5].copy()

    clean_df.columns = [
        "course_code",
        "course_name",
        "instructor",
        "availability_1",
        "availability_2",
    ]

    clean_df = clean_df.dropna(subset=["course_code"], how="all")

    clean_df["course_name"] = (
        clean_df["course_name"]
        .fillna("")
        .astype(str)
        .str.replace(":", "", regex=False)
        .str.strip()
    )

    clean_df = clean_df[
        ~clean_df.astype(str).apply(
            lambda row: row.str.contains("Notes", case=False).any(), axis=1
        )
    ]

    clean_df = clean_df.reset_index(drop=True)

    clean_df.to_csv(OUTPUT_AVAILABILITY, index=False)


def main():
    clean_enrollment()
    clean_counts()
    clean_periods()
    clean_availability()

    print("Created:")
    print(OUTPUT_ENROLLMENT)
    print(OUTPUT_PERIODS)
    print(OUTPUT_AVAILABILITY)
    print(OUTPUT_COUNTS)


if __name__ == "__main__":
    main()
