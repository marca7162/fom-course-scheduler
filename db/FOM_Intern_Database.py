import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "csv_files"
DB_DIR = PROJECT_ROOT / "db"

DB_DIR.mkdir(exist_ok=True)

DB_FILE = DB_DIR / "FOM_Intern_Database.db"
ROOMS_FILE = CSV_DIR / "rooms.csv"


if __name__ == "__main__":
    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()

    # cursor.execute("DROP TABLE IF EXISTS rooms")

    # df = pd.read_csv(ROOMS_FILE)
    # df.to_sql("rooms", db, if_exists="replace", index=False)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS teachers (
            tNo INTEGER PRIMARY KEY AUTOINCREMENT,
            tName VARCHAR(50) NOT NULL,
            availableDays VARCHAR(15) NOT NULL,
            periods CHAR(1) NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            courseCode VARCHAR(15) PRIMARY KEY,
            courseName VARCHAR(50) NOT NULL,
            credits INTEGER NOT NULL,
            totalRegisteredStudents INTEGER NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Teach_Course (
            T_ID INTEGER,
            C_ID VARCHAR(15),
            FOREIGN KEY (T_ID) REFERENCES teachers(tNo),
            FOREIGN KEY (C_ID) REFERENCES courses(courseCode)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            stdId INTEGER PRIMARY KEY AUTOINCREMENT,
            stdName VARCHAR(50) NOT NULL
        );
        """
    )

    cursor.execute(
        """
        create table if not exists teachers(
        tNo INT IDENTITY (1, 1) primary key,
        tName varchar (50) not null,
        availableDays varchar(15) not null,
        priods char(1) not null
        );
        """
    )

    db.commit()
    db.close()

    # print(f"Committed database to {DB_FILE}")
