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

CREATE TABLE CourseContent (
    content_id INT PRIMARY KEY,
    course_section_id INT NOT NULL,
    content_type ENUM('link', 'file', 'slide') NOT NULL,
    content_title VARCHAR(255),
    content_url TEXT,              -- For links and downloadable files/slides
    uploaded_file_path TEXT,       -- Optional: for server-stored files
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

-- Enrol Table (only for students)
CREATE TABLE Enrol (
    course_id INT,
    student_id INT,
    course_grade DECIMAL(5,2),
    PRIMARY KEY (course_id, student_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (student_id) REFERENCES User(user_id)
        -- ensure student_id refers only to users with user_type = 'Student'
);

-- Teach Table (only for lecturers)
CREATE TABLE Teach (
    course_id INT,
    lecturer_id INT,
    PRIMARY KEY (course_id, lecturer_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (lecturer_id) REFERENCES User(user_id)
        -- ensure lecturer_id refers only to users with user_type = 'Lecturer'
);

-- Assignment Table
CREATE TABLE Assignment (
    assignment_id INT PRIMARY KEY,
    course_id INT NOT NULL,
    assignment_title VARCHAR(255) NOT NULL,
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

-- Submit Table
CREATE TABLE Submit (
    submission_id INT PRIMARY KEY,
    assignment_id INT NOT NULL,
    student_id INT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES Assignment(assignment_id),
    FOREIGN KEY (student_id) REFERENCES User(user_id)
        -- should refer to users with user_type = 'Student'
);

-- GradeAssignment Table
CREATE TABLE GradeAssignment (
    submission_id INT,
    lecturer_id INT,
    assignment_grade DECIMAL(5,2),
    PRIMARY KEY (submission_id, lecturer_id),
    FOREIGN KEY (submission_id) REFERENCES Submit(submission_id),
    FOREIGN KEY (lecturer_id) REFERENCES User(user_id)
        -- should refer to users with user_type = 'Lecturer'
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

-- DELIMITER $$

-- CREATE TRIGGER check_student_enrol_before_insert
-- BEFORE INSERT ON Enrol
-- FOR EACH ROW
-- BEGIN
--   DECLARE userRole VARCHAR(20);
  
--   SELECT user_type INTO userRole FROM User WHERE user_id = NEW.student_id;
  
--   IF userRole != 'Student' THEN
--     SIGNAL SQLSTATE '45000' 
--     SET MESSAGE_TEXT = 'Only users with user_type = "Student" can be enrolled in courses.';
--   END IF;
-- END$$

-- DELIMITER ;