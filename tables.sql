-- Select Database
USE VLE;

-- User Table
CREATE TABLE User (
    user_id INT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    user_email VARCHAR(100) UNIQUE NOT NULL,
    user_password VARCHAR(255) NOT NULL,
    user_type ENUM('Admin', 'Student', 'Lecturer') NOT NULL
);

-- Course Table
CREATE TABLE Course (
    course_code VARCHAR(20) PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL
);

-- CourseSection Table
CREATE TABLE CourseSection (
    course_section_id INT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL,
    section_title VARCHAR(255),
    FOREIGN KEY (course_code) REFERENCES Course(course_code) ON DELETE CASCADE
);

-- CourseContent Table
CREATE TABLE CourseContent (
    content_id INT PRIMARY KEY,
    course_section_id INT NOT NULL,
    content_type ENUM('link', 'file', 'slide') NOT NULL,
    content_title VARCHAR(255),
    content_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_section_id) REFERENCES CourseSection(course_section_id) ON DELETE CASCADE
);

-- CalendarEvent Table
CREATE TABLE CalendarEvent (
    event_id INT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL,
    event_date DATE NOT NULL,
    event_title VARCHAR(255) NOT NULL,
    FOREIGN KEY (course_code) REFERENCES Course(course_code) ON DELETE CASCADE
);

-- Enrol Table (for students)
CREATE TABLE Enrol (
    course_code VARCHAR(20),
    student_id INT,
    course_grade DECIMAL(5,2),
    PRIMARY KEY (course_code, student_id),
    FOREIGN KEY (course_code) REFERENCES Course(course_code),
    FOREIGN KEY (student_id) REFERENCES User(user_id)
);

-- Teach Table (for lecturers)
CREATE TABLE Teach (
    course_code VARCHAR(20),
    lecturer_id INT,
    PRIMARY KEY (course_code, lecturer_id),
    FOREIGN KEY (course_code) REFERENCES Course(course_code),
    FOREIGN KEY (lecturer_id) REFERENCES User(user_id)
);

-- Assignment Table
CREATE TABLE Assignment (
    assignment_id INT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL,
    assignment_title VARCHAR(255) NOT NULL,
    FOREIGN KEY (course_code) REFERENCES Course(course_code)
);

-- Submit Table (without submission_id)
CREATE TABLE Submit (
    assignment_id INT NOT NULL,
    student_id INT NOT NULL,
    assignment_grade DECIMAL(5,2),
    PRIMARY KEY (assignment_id, student_id),
    FOREIGN KEY (assignment_id) REFERENCES Assignment(assignment_id),
    FOREIGN KEY (student_id) REFERENCES User(user_id)
);

-- DiscussionForum Table
CREATE TABLE DiscussionForum (
    forum_id INT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL,
    forum_title VARCHAR(255) NOT NULL,
    forum_content TEXT,
    FOREIGN KEY (course_code) REFERENCES Course(course_code) ON DELETE CASCADE
);

-- DiscussionThread Table
CREATE TABLE DiscussionThread (
    thread_id INT PRIMARY KEY,
    forum_id INT NOT NULL,
    parent_thread_id INT,
    thread_creator_id INT NOT NULL,
    thread_content TEXT NOT NULL,
    FOREIGN KEY (forum_id) REFERENCES DiscussionForum(forum_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_thread_id) REFERENCES DiscussionThread(thread_id),
    FOREIGN KEY (thread_creator_id) REFERENCES User(user_id)
);
