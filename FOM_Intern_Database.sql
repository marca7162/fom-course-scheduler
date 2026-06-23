create database FOM_Schedule;

use FOM_Schedule;

create table rooms(
	roomNo varchar(15) primary key,
	capacity int  not null,
	rState char(1) not null
);
drop table teachers;
create table teachers(
	tNo INT IDENTITY (1, 1) primary key,
	tName varchar (50) not null,
	availableDays varchar(15) not null,
	priods char(1) not null
	);
insert into teachers (tName,availableDays, priods) values ('ABC','M/W', '1')

create table courses(
	courseCode varchar(15) primary key,
	courseName varchar(50) not null, 
	credits int not null,
	totalRegisteredStudents int not null
);
 insert into courses values('101','CS', 3 , 40);
 insert into courses values('102','CS-II', 3 , 40);

drop table Teach_Course;
create table Teach_Course(
	T_ID INT ,
	C_ID varchar(15),

	foreign key (T_ID) references teachers  (tNo) ,
	foreign key (C_ID) references courses  (courseCode) 
);
insert into Teach_Course values('1','101')
insert into Teach_Course values('1','102')

create table students(
	stdId INT IDENTITY (1, 1) primary key,
	stdName varchar (50) not null
)

insert into students values('Nana')

create table student_courses(
	stdID int ,
	courseID varchar(15),
	foreign key (stdID) references students (stdId) ,
	foreign key (courseID) references courses (courseCode) 
)
insert into student_courses values (1,'101')

select * from students, teachers, courses where stdId=1 and courseCode='101'

select stdID, tNo, courseCode from students, teachers, courses where stdId=1 and courseCode='101'


-- ======================Query Data===================
Select * from teachers
select * from Courses
select * from Teach_Course
select * from students

