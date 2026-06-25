import csv
import sqlite3

db = sqlite3.connect('FOM_Intern_Database.db')
cursor = db.cursor()

# import courses
def import_courses():
    firstLine = True
    with open("clean_counts.csv", newline='') as file:
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            if (firstLine):
                firstLine = False
                continue
            command = "insert into courses values ("
            command += "'" + row[0][:9].rstrip() + "'"
            command += ", '" + row[0][10:].lstrip() + "', "
            command += row[1] + ', 0)'
            cursor.execute(command)

            print("inserted " + row[0])
        db.commit()
        db.close()

if (__name__ == "__main__"):
    import_courses()