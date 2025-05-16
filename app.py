from binascii import Error
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='boris',
        password='password',
        database='VLE'
    )

# Register User
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO User (user_id, user_name, user_email, user_password, user_type) VALUES (%s, %s, %s, %s, %s)",
                       (data['user_id'], data['user_name'], data['user_email'], data['user_password'], data['user_type']))
        conn.commit()
        return jsonify({"message": "User registered successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Login User
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User WHERE user_id = %s AND user_password = %s",
                   (data['user_id'], data['user_password']))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return jsonify({"message": "Login successful", "user": user})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Create Course (only by admin)
@app.route('/create_course', methods=['POST'])
def create_course():
    data = request.get_json()
    if data.get('user_type') != 'Admin':
        return jsonify({"error": "Only admins can create courses"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Course (course_code, course_name) VALUES (%s, %s)",
                       (data['course_code'], data['course_name']))
        conn.commit()
        return jsonify({"message": "Course created successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Retrieve All Courses
@app.route('/courses', methods=['GET'])
def get_all_courses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Course")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(courses)

# Retrieve Courses for a Student
@app.route('/courses/student/<int:student_id>', methods=['GET'])
def get_courses_for_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.* FROM Course c
        JOIN Enrol e ON c.course_code = e.course_code
        WHERE e.student_id = %s
    """, (student_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(courses)

# Retrieve Courses Taught by Lecturer
@app.route('/courses/lecturer/<int:lecturer_id>', methods=['GET'])
def get_courses_for_lecturer(lecturer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.* FROM Course c
        JOIN Teach t ON c.course_code = t.course_code
        WHERE t.lecturer_id = %s
    """, (lecturer_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(courses)

# Register Lecturer to Course
@app.route('/register-course/lecturer', methods=['POST'])
def register_lecturer_to_course():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Teach (course_code, lecturer_id) VALUES (%s, %s)",
                       (data['course_code'], data['lecturer_id']))
        conn.commit()
        return jsonify({"message": "Lecturer registered to course"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Register Student to Course
@app.route('/register-student/student', methods=['POST'])
def register_student_to_course():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Enrol (course_code, student_id, course_grade) VALUES (%s, %s, %s)",
                       (data['course_code'], data['student_id'], 0.0))
        conn.commit()
        return jsonify({"message": "Student registered to course"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Retrieve Members of a Course
@app.route('/courses/<course_code>/members', methods=['GET'])
def get_course_members(course_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.user_name, u.user_type FROM User u
        JOIN Enrol e ON u.user_id = e.student_id
        WHERE e.course_code = %s
        UNION
        SELECT u.user_id, u.user_name, u.user_type FROM User u
        JOIN Teach t ON u.user_id = t.lecturer_id
        WHERE t.course_code = %s
    """, (course_code, course_code))
    members = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(members)


# Create Calendar Event
@app.route('/calendar/create', methods=['POST'])
def create_calendar_event():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert the calendar event
        cursor.execute("""
            INSERT INTO CalendarEvent (course_code, event_date, event_title)
            VALUES (%s, %s, %s)
        """, (data['course_code'], data['event_date'], data['event_title']))
        
        # Get the auto-generated event_id
        event_id = cursor.lastrowid

        # Retrieve all students enrolled in the course
        cursor.execute("""
            SELECT student_id FROM Enrol WHERE course_code = %s
        """, (data['course_code'],))
        students = cursor.fetchall()

        # Insert into StudentCalendarEvent for each student
        for (student_id,) in students:
            cursor.execute("""
                INSERT INTO StudentCalendarEvent (student_id, event_id)
                VALUES (%s, %s)
            """, (student_id, event_id))

        conn.commit()
        return jsonify({"message": "Calendar event created and assigned to enrolled students."}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Retrieve All Calendar Events for a Course
@app.route('/calendar/course/<course_code>', methods=['GET'])
def get_calendar_events_by_course(course_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM CalendarEvent
        WHERE course_code = %s
        ORDER BY event_date ASC
    """, (course_code,))
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(events)

# Retrieve Calendar Events for a Particular Date for a Student
@app.route('/calendar/student/<int:student_id>/date/<date>', methods=['GET'])
def get_calendar_events_by_student_and_date(student_id, date):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ce.* FROM CalendarEvent ce
        JOIN StudentCalendarEvent sce ON ce.event_id = sce.event_id
        WHERE sce.student_id = %s AND ce.event_date = %s
        ORDER BY ce.event_date ASC
    """, (student_id, date))
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(events)

# Route to create a new forum for a particular course
@app.route('/forums', methods=['POST'])
def create_forum():
    data = request.get_json()
    course_code = data.get('course_code')
    forum_title = data.get('forum_title')
    forum_content = data.get('forum_content')

    if not course_code or not forum_title:
        return jsonify({'error': 'course_code and forum_title are required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO DiscussionForum (course_code, forum_title, forum_content)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (course_code, forum_title, forum_content))
        conn.commit()
        return jsonify({'message': 'Forum created successfully'}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Route to retrieve all forums for a particular course
@app.route('/forums/<course_code>', methods=['GET'])
def get_forums(course_code):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM DiscussionForum WHERE course_code = %s"
        cursor.execute(query, (course_code,))
        forums = cursor.fetchall()
        return jsonify(forums), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Helper function: fetch threads recursively to build nested structure
def fetch_threads_recursive(cursor, forum_id, parent_thread_id=None):
    query = """
        SELECT thread_id, forum_id, parent_thread_id, thread_creator_id, thread_content
        FROM DiscussionThread
        WHERE forum_id = %s AND
              (parent_thread_id = %s OR (parent_thread_id IS NULL AND %s IS NULL))
        ORDER BY thread_id ASC
    """
    cursor.execute(query, (forum_id, parent_thread_id, parent_thread_id))
    threads = cursor.fetchall()
    result = []
    for thread in threads:
        # Recursively fetch replies for this thread
        children = fetch_threads_recursive(cursor, forum_id, thread['thread_id'])
        thread_dict = dict(thread)
        thread_dict['replies'] = children
        result.append(thread_dict)
    return result

# Route: Get all discussion threads for a forum (nested)
@app.route('/forums/<int:forum_id>/threads', methods=['GET'])
def get_discussion_threads(forum_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        threads = fetch_threads_recursive(cursor, forum_id)
        return jsonify(threads), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Route: Add a new top-level thread (with title + content)
@app.route('/forums/<int:forum_id>/threads', methods=['POST'])
def add_discussion_thread(forum_id):
    data = request.get_json()
    thread_creator_id = data.get('thread_creator_id')
    thread_title = data.get('thread_title')
    thread_content = data.get('thread_content')

    if not thread_creator_id or not thread_title or not thread_content:
        return jsonify({'error': 'thread_creator_id, thread_title, and thread_content are required'}), 400

    # We’ll store the thread title inside the thread_content as the first post content.
    # Alternatively, you could add a thread_title column if you want separate.
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert top-level thread: parent_thread_id = NULL
        insert_query = """
            INSERT INTO DiscussionThread (forum_id, parent_thread_id, thread_creator_id, thread_content)
            VALUES (%s, NULL, %s, %s)
        """
        # Combine title and content into thread_content or store separately (if table supports title)
        full_content = f"{thread_title}\n\n{thread_content}"
        cursor.execute(insert_query, (forum_id, thread_creator_id, full_content))
        conn.commit()
        return jsonify({'message': 'Thread created successfully'}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Route: Add a reply to a thread or reply (nested reply)
@app.route('/threads/<int:parent_thread_id>/reply', methods=['POST'])
def reply_to_thread(parent_thread_id):
    data = request.get_json()
    thread_creator_id = data.get('thread_creator_id')
    thread_content = data.get('thread_content')

    if not thread_creator_id or not thread_content:
        return jsonify({'error': 'thread_creator_id and thread_content are required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get forum_id of the parent thread to maintain FK integrity
        cursor.execute("SELECT forum_id FROM DiscussionThread WHERE thread_id = %s", (parent_thread_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Parent thread not found'}), 404
        forum_id = row[0]

        # Insert reply with parent_thread_id set
        insert_query = """
            INSERT INTO DiscussionThread (forum_id, parent_thread_id, thread_creator_id, thread_content)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (forum_id, parent_thread_id, thread_creator_id, thread_content))
        conn.commit()
        return jsonify({'message': 'Reply added successfully'}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Course Content

#Add Sectiont to  Course 
@app.route('/course/<string:course_code>/sections', methods=['POST'])
def add_course_section(course_code):
    data = request.get_json()
    section_title = data.get('section_title')

    if not section_title:
        return jsonify({'error': 'section_title is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO CourseSection (course_code, section_title)
            VALUES (%s, %s)
        """
        cursor.execute(insert_query, (course_code, section_title))
        conn.commit()

        return jsonify({'message': 'Section added successfully'}), 201

    except Error as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

#Add course content to a section
@app.route('/course_sections/<int:section_id>/content', methods=['POST'])
def add_course_content(section_id):
    data = request.get_json()
    content_type = data.get('content_type')  # 'link', 'file', 'slide'
    content_title = data.get('content_title')
    content_url = data.get('content_url')  # URL or file path

    if not content_type or not content_title or not content_url:
        return jsonify({'error': 'content_type, content_title and content_url are required'}), 400

    if content_type not in ['link', 'file', 'slide']:
        return jsonify({'error': 'Invalid content_type. Must be link, file, or slide.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO CourseContent (course_section_id, content_type, content_title, content_url)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (section_id, content_type, content_title, content_url))
        conn.commit()
        return jsonify({'message': 'Course content added successfully'}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Retrieve all course content for a given course (grouped by sections)
@app.route('/course/<course_code>/contents', methods=['GET'])
def get_course_content(course_code):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query joins CourseSection and CourseContent to get all contents for a course
        query = """
            SELECT cs.course_section_id, cs.section_title, cc.content_id, cc.content_type, cc.content_title, cc.content_url, cc.created_at
            FROM CourseSection cs
            LEFT JOIN CourseContent cc ON cs.course_section_id = cc.course_section_id
            WHERE cs.course_code = %s
            ORDER BY cs.course_section_id, cc.created_at
        """
        cursor.execute(query, (course_code,))
        rows = cursor.fetchall()

        # Group contents by sections
        sections = {}
        for row in rows:
            section_id = row['course_section_id']
            if section_id not in sections:
                sections[section_id] = {
                    'section_title': row['section_title'],
                    'contents': []
                }
            if row['content_id'] is not None:
                sections[section_id]['contents'].append({
                    'content_id': row['content_id'],
                    'content_type': row['content_type'],
                    'content_title': row['content_title'],
                    'content_url': row['content_url'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })

        return jsonify(list(sections.values())), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Assignments

# Create Assignment
@app.route('/assignments/create', methods=['POST'])
def create_assignment():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert new assignment
        cursor.execute("""
            INSERT INTO Assignment (course_code, title, due_date)
            VALUES (%s, %s, %s)
        """, (data['course_code'], data['title'], data['due_date']))
        
        conn.commit()
        return jsonify({"message": "Assignment created successfully."})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Submit Assignment
@app.route('/assignments/submit', methods=['POST'])
def submit_assignment():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Only store student_id and assignment_id
        cursor.execute("""
            INSERT INTO Submit (assignment_id, student_id)
            VALUES (%s, %s)
        """, (data['assignment_id'], data['student_id']))
        conn.commit()
        return jsonify({"message": "Assignment submission recorded."})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Grade Assignment and Update Course Average
@app.route('/assignments/grade', methods=['POST'])
def grade_assignment():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Update the grade
        cursor.execute("""
            UPDATE Submit SET grade = %s
            WHERE assignment_id = %s AND student_id = %s
        """, (data['grade'], data['assignment_id'], data['student_id']))

        # Get course code from assignment
        cursor.execute("""
            SELECT course_code FROM Assignment WHERE assignment_id = %s
        """, (data['assignment_id'],))
        course = cursor.fetchone()
        course_code = course[0]

        # Recalculate student's average for the course
        cursor.execute("""
            SELECT AVG(grade) FROM Submit
            JOIN Assignment ON Submit.assignment_id = Assignment.assignment_id
            WHERE Submit.student_id = %s AND Assignment.course_code = %s AND grade IS NOT NULL
        """, (data['student_id'], course_code))
        average = cursor.fetchone()[0]

        # Update student's grade in Enrol
        cursor.execute("""
            UPDATE Enrol SET course_grade = %s
            WHERE student_id = %s AND course_code = %s
        """, (average, data['student_id'], course_code))

        conn.commit()
        return jsonify({"message": "Grade submitted and student average updated.", "average": average})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()


# Reports
# All Courses with 50 or More Students
@app.route('/report/courses-50-or-more', methods=['GET'])
def report_courses_50_or_more():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.course_code, c.course_name, COUNT(e.student_id) AS student_count
        FROM Course c
        JOIN Enrol e ON c.course_code = e.course_code
        GROUP BY c.course_code, c.course_name
        HAVING COUNT(e.student_id) >= 50
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

#  All Students in 5 or More Courses
@app.route('/report/students-5-or-more', methods=['GET'])
def report_students_5_or_more():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.user_name, COUNT(e.course_code) AS course_count
        FROM User u
        JOIN Enrol e ON u.user_id = e.student_id
        WHERE u.user_type = 'Student'
        GROUP BY u.user_id, u.user_name
        HAVING COUNT(e.course_code) >= 5
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

# All Lecturers Teaching 3 or More Courses
@app.route('/report/lecturers-3-or-more', methods=['GET'])
def report_lecturers_3_or_more():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.user_name, COUNT(t.course_code) AS courses_taught
        FROM User u
        JOIN Teach t ON u.user_id = t.lecturer_id
        WHERE u.user_type = 'Lecturer'
        GROUP BY u.user_id, u.user_name
        HAVING COUNT(t.course_code) >= 3
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

# The 10 Most Enrolled Courses
@app.route('/report/top-10-courses', methods=['GET'])
def report_top_10_courses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.course_code, c.course_name, COUNT(e.student_id) AS student_count
        FROM Course c
        JOIN Enrol e ON c.course_code = e.course_code
        GROUP BY c.course_code, c.course_name
        ORDER BY student_count DESC
        LIMIT 10
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

# Top 10 Students with the Highest Overall Averages
@app.route('/report/top-10-students', methods=['GET'])
def report_top_10_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.user_name, ROUND(AVG(e.course_grade), 2) AS average_grade
        FROM User u
        JOIN Enrol e ON u.user_id = e.student_id
        WHERE u.user_type = 'Student'
        GROUP BY u.user_id, u.user_name
        ORDER BY average_grade DESC
        LIMIT 10
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)