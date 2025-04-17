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
    course_id INT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) UNIQUE NOT NULL
);

-- CourseSection Table
CREATE TABLE CourseSection (
    course_section_id INT PRIMARY KEY,
    course_id INT NOT NULL,
    section_title VARCHAR(255),
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

-- CourseContent Table
CREATE TABLE CourseContent (
    content_id INT PRIMARY KEY,
    course_section_id INT NOT NULL,
    content_type ENUM('link', 'file', 'slide') NOT NULL,
    content_title VARCHAR(255),
    content_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_section_id) REFERENCES CourseSection(course_section_id)
);

-- CalendarEvent Table
CREATE TABLE CalendarEvent (
    event_id INT PRIMARY KEY,
    course_id INT NOT NULL,
    event_date DATE NOT NULL,
    event_title VARCHAR(255) NOT NULL,
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

-- Enrol Table (for students)
CREATE TABLE Enrol (
    course_id INT,
    student_id INT,
    course_grade DECIMAL(5,2),
    PRIMARY KEY (course_id, student_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (student_id) REFERENCES User(user_id)
        -- Ensure student_id refers to a student
);

-- Teach Table (for lecturers)
CREATE TABLE Teach (
    course_id INT,
    lecturer_id INT,
    PRIMARY KEY (course_id, lecturer_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (lecturer_id) REFERENCES User(user_id)
        -- Ensure lecturer_id refers to a lecturer
);

-- Assignment Table
CREATE TABLE Assignment (
    assignment_id INT PRIMARY KEY,
    course_id INT NOT NULL,
    assignment_title VARCHAR(255) NOT NULL,
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

-- Submit Table with embedded grade
CREATE TABLE Submit (
    submission_id INT PRIMARY KEY,
    assignment_id INT NOT NULL,
    student_id INT NOT NULL,
    assignment_grade DECIMAL(5,2),
    FOREIGN KEY (assignment_id) REFERENCES Assignment(assignment_id),
    FOREIGN KEY (student_id) REFERENCES User(user_id)
        -- Should refer to users with user_type = 'Student'
);

-- DiscussionForum Table
CREATE TABLE DiscussionForum (
    forum_id INT PRIMARY KEY,
    course_id INT NOT NULL,
    forum_title VARCHAR(255) NOT NULL,
    forum_content TEXT,
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

-- DiscussionThread Table
CREATE TABLE DiscussionThread (
    thread_id INT PRIMARY KEY,
    forum_id INT NOT NULL,
    parent_thread_id INT,
    thread_creator_id INT NOT NULL,
    thread_content TEXT NOT NULL,
    FOREIGN KEY (forum_id) REFERENCES DiscussionForum(forum_id),
    FOREIGN KEY (parent_thread_id) REFERENCES DiscussionThread(thread_id),
    FOREIGN KEY (thread_creator_id) REFERENCES User(user_id)
);


