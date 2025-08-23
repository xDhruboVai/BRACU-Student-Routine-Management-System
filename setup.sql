create database if not exists Routine;
use Routine;

create table user (
    user_id int auto_increment primary key,
    email varchar(255) not null unique,
    password_hash varchar(255) not null,
    name varchar(100) not null,
    role boolean,
    department varchar(100)
);

create table student (
    student_id int auto_increment primary key,
    user_id int,
    foreign key (user_id) references user(user_id) on delete cascade
);

create table faculty (
    faculty_id int auto_increment primary key,
    user_id int,
    foreign key (user_id) references user(user_id) on delete cascade
);

create table course (
    course_id int auto_increment primary key,
    course_code varchar(50) not null unique,
    title varchar(255) not null,
    student_id int,
    foreign key (student_id) references student(student_id) on delete set null
);

create table classroom (
    class_id int auto_increment primary key,
    name varchar(100) not null,
    created_on datetime default current_timestamp
);

create table resource (
    resource_id int auto_increment primary key,
    title varchar(255) not null,
    file_link varchar(500)
);

create table user_otp (
    otp_id int auto_increment primary key,
    otp int not null,
    used boolean default false,
    expires_at datetime not null,
    user_id int,
    foreign key (user_id) references user(user_id) on delete cascade
);

create table event (
    event_id int auto_increment primary key,
    date_time datetime not null,
    title varchar(255) not null,
    resource_link varchar(500),
    created_at datetime default current_timestamp,
    user_id int,
    foreign key (user_id) references user(user_id) on delete cascade
);

create table notification (
    notification_id int auto_increment primary key,
    message_template varchar(500),
    event_id int,
    foreign key (event_id) references event(event_id) on delete cascade
);

create table enrolled_in (
    student_id int,
    classroom_id int,
    primary key (student_id, classroom_id),
    foreign key (student_id) references student(student_id) on delete cascade,
    foreign key (classroom_id) references classroom(class_id) on delete cascade
);

create table teaches (
    faculty_id int,
    course_id int,
    classroom_id int,
    primary key (faculty_id, course_id, classroom_id),
    foreign key (faculty_id) references faculty(faculty_id) on delete cascade,
    foreign key (course_id) references course(course_id) on delete cascade,
    foreign key (classroom_id) references classroom(class_id) on delete cascade
);

create table uploads (
    faculty_id int,
    classroom_id int,
    resource_id int,
    primary key (faculty_id, classroom_id, resource_id),
    foreign key (faculty_id) references faculty(faculty_id) on delete cascade,
    foreign key (classroom_id) references classroom(class_id) on delete cascade,
    foreign key (resource_id) references resource(resource_id) on delete cascade
);

create table creates (
    faculty_id int,
    classroom_id int,
    event_id int,
    primary key (faculty_id, classroom_id, event_id),
    foreign key (faculty_id) references faculty(faculty_id) on delete cascade,
    foreign key (classroom_id) references classroom(class_id) on delete cascade,
    foreign key (event_id) references event(event_id) on delete cascade
);

create table marks (
    course_id int,
    student_id int,
    assessment_name varchar(100),
    obtained_marks int,
    primary key (course_id, student_id, assessment_name),
    foreign key (course_id) references course(course_id) on delete cascade,
    foreign key (student_id) references student(student_id) on delete cascade
);

create table notification_recipients (
    event_id int,
    recipient int,
    primary key (event_id, recipient),
    foreign key (event_id) references event(event_id) on delete cascade
);