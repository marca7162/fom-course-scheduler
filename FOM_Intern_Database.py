import sqlite3

if __name__ == "__main__":
	# with open('FOM_Intern_Database.sql', 'r') as sql_file:
	# 	sql_script = sql_file.read()

	db = sqlite3.connect('FOM_Intern_Database.db')
	cursor = db.cursor()
	cursor.execute('''CREATE TABLE IF NOT EXISTS rooms(
	roomNo varchar(15) primary key,
	capacity int  not null,
	rState char(1) not null
	);''')
	cursor.execute('''create table if not exists teachers(
	tNo INT IDENTITY (1, 1) primary key,
	tName varchar (50) not null,
	availableDays varchar(15) not null,
	priods char(1) not null
	);''')
	cursor.execute('''insert into teachers (tName,availableDays, priods) values ('ABC','M/W', '1')
	''')
	cursor.execute('''create table if not EXISTS courses(
	courseCode varchar(15) primary key,
	courseName varchar(50) not null, 
	credits int not null,
	totalRegisteredStudents int not null
	);''')
	# cursor.execute(''' insert into courses values('101','CS', 3 , 40);''')
	# cursor.execute(''' insert into courses values('102','CS-II', 3 , 40);''')
	cursor.execute('''create table if not exists Teach_Course(
	T_ID INT ,
	C_ID varchar(15),

	foreign key (T_ID) references teachers  (tNo) ,
	foreign key (C_ID) references courses  (courseCode) 
	);''')
	cursor.execute('''insert into Teach_Course values('1','101')
	''')
	cursor.execute('''insert into Teach_Course values('1','102')
	''')
	cursor.execute('''create table if not exists students(
	stdId INT IDENTITY (1, 1) primary key,
	stdName varchar (50) not null)
	''')
	cursor.execute('''insert into students (stdName) values('Nana')
	''')
	cursor.execute('''create table if not exists student_courses(
	stdID int ,
	courseID varchar(15),
	foreign key (stdID) references students (stdId) ,
	foreign key (courseID) references courses (courseCode) 
	)''')
	cursor.execute('''insert into student_courses values (1,'101')
	''')

	db.commit()
	db.close()
	print("committed")

