CREATE DATABASE IF NOT EXISTS Routine;

USE Routine;

CREATE TABLE `user` (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `role` BOOLEAN,
    department VARCHAR(100),
    otp_verified BOOLEAN DEFAULT FALSE 
);

CREATE TABLE course (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES `user`(user_id) ON DELETE CASCADE
);

CREATE TABLE resource (
    resource_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    file_link VARCHAR(500)
);

CREATE TABLE classroom (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student (
    student_id VARCHAR(50) PRIMARY KEY,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES `user`(user_id) ON DELETE CASCADE
);

CREATE TABLE faculty (
    faculty_id VARCHAR(50) PRIMARY KEY,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES `user`(user_id) ON DELETE CASCADE
);

CREATE TABLE user_otp (
    otp_id INT AUTO_INCREMENT PRIMARY KEY,
    otp INT NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES `user`(user_id) ON DELETE CASCADE
);

CREATE TABLE event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    date_time DATETIME NOT NULL,
    title VARCHAR(255) NOT NULL,
    resource_link VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES `user`(user_id) ON DELETE CASCADE
);

CREATE TABLE assessment_group (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    drop_lowest INT NOT NULL DEFAULT 1,
    CONSTRAINT chk_drop_lowest CHECK (drop_lowest IN (0,1,2)),
    UNIQUE KEY uk_course_group (course_id, `name`),
    FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);


CREATE TABLE enrolled_in (
    student_id VARCHAR(50),
    classroom_id INT,
    PRIMARY KEY (student_id, classroom_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classroom(class_id) ON DELETE CASCADE
);

CREATE TABLE teaches (
    faculty_id VARCHAR(50),
    classroom_id INT,
    PRIMARY KEY (faculty_id, classroom_id),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classroom(class_id) ON DELETE CASCADE
);

CREATE TABLE creates (
    faculty_id VARCHAR(50),
    classroom_id INT,
    event_id INT,
    PRIMARY KEY (faculty_id, classroom_id, event_id),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classroom(class_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES event(event_id) ON DELETE CASCADE
);

CREATE TABLE marks (
    mark_id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_name VARCHAR(100) NOT NULL,
    obtained_marks DECIMAL(10, 2),
    total_marks DECIMAL(10, 2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE got (
    mark_id INT,
    course_id INT,
    group_id INT,
    student_id VARCHAR(50),
    PRIMARY KEY (mark_id, course_id, group_id, student_id),
    FOREIGN KEY (mark_id) REFERENCES marks(mark_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES assessment_group(group_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
);


CREATE TABLE uploads (
    faculty_id VARCHAR(50),
    classroom_id INT,
    resource_id INT,
    PRIMARY KEY (faculty_id, classroom_id, resource_id),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classroom(class_id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resource(resource_id) ON DELETE CASCADE
);