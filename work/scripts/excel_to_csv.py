import argparse
from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "csv_files"




INPUT_FILE = PROJECT_ROOT.parent / "Sample Enrollement Record.xlsx"

OUTPUT_ENROLLMENT = CSV_DIR / "clean_enrollment.csv"
OUTPUT_PERIODS = CSV_DIR / "clean_periods.csv"
OUTPUT_AVAILABILITY = CSV_DIR / "clean_availability.csv"
OUTPUT_COUNTS = CSV_DIR / "clean_counts.csv"


def clean_enrollment(input_file=INPUT_FILE):
    df = pd.read_excel(input_file, sheet_name="Final Enrollment", header=1)

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


def clean_counts(input_file=INPUT_FILE):
    df = pd.read_excel(input_file, sheet_name="Final Enrollment", header=1)

    df = df[["Full Course List", "Credits"]].copy()

    df.columns = ["full_course_list", "credits"]

    df = df.dropna(subset=["full_course_list"])

    df["full_course_list"] = df["full_course_list"].astype(str).str.strip()

    df = df[~df["full_course_list"].str.startswith("Notes", na=False)]

    df = df.reset_index(drop=True)

    df["credits"] = pd.to_numeric(df["credits"], errors="coerce").astype(int)

    df.to_csv(OUTPUT_COUNTS, index=False)


def clean_periods(input_file=INPUT_FILE):
    df = pd.read_excel(input_file, sheet_name="Class Periods", header=None)

    clean_df = df.iloc[1:, 0:5].copy()

    clean_df.columns = ["time", "m", "t", "w", "th"]

    clean_df = clean_df.dropna(subset=["time"], how="all").reset_index(
        drop=True
    )

    clean_df.insert(0, "period", range(1, len(clean_df) + 1))

    clean_df.to_csv(OUTPUT_PERIODS, index=False)


def clean_availability(input_file=INPUT_FILE):
    df = pd.read_excel(
        input_file, sheet_name="Teacher Availability", header=None
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


def convert_excel(input_file=INPUT_FILE):
    CSV_DIR.mkdir(exist_ok=True)

    clean_enrollment(input_file)
    clean_counts(input_file)
    clean_periods(input_file)
    clean_availability(input_file)

    print("Created:")
    print(OUTPUT_ENROLLMENT)
    print(OUTPUT_PERIODS)
    print(OUTPUT_AVAILABILITY)
    print(OUTPUT_COUNTS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", nargs="?", default=str(INPUT_FILE))
    args = parser.parse_args()
    convert_excel(Path(args.input_file))
