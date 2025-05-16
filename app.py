from flask import Flask, make_response, redirect, request, render_template, jsonify, url_for
import mysql.connector
from authhandler import AuthHandler
from config import Config

# Initialize app
app = Flask(__name__)
app.config.from_object(Config)

# Instantiate AuthHandler
auth_handler = AuthHandler(app.config['SECRET_KEY'])

# Database configuration
DB_CONFIG = {
    'user': 'boris',
    'password': 'password',
    'host': 'localhost',
    'database': 'VLE',
}

# Home Route
@app.route('/')
def home():
    current_user, error_response, status_code = auth_handler.verify_token(request)
    if error_response:
        return redirect(url_for('login'))
    
    if current_user['user_type'] == 'Student':
        return render_template('home_student.html', user=current_user)
    elif current_user['user_type'] == 'Lecturer':
        return render_template('home_lecturer.html', user=current_user)
    elif current_user['user_type'] == 'Admin':
        return render_template('home_admin.html', user=current_user)

# Register endpoint
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        user_email = data.get('user_email')
        user_password = data.get('user_password')
        user_type = data.get('user_type')
        
        if not all([user_id, user_name, user_email, user_password, user_type]):
            return jsonify({'message': 'Missing fields'}), 400
        
        return auth_handler.register_user(user_id, user_name, user_email, user_password, user_type)
    return render_template('register.html')

# Login endpoint
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user_id = data.get('user_id')
        user_password = data.get('user_password')

        if not all([user_id, user_password]):
            return jsonify({'message': 'Missing credentials'}), 400

        user_response = auth_handler.authenticate_user(user_id, user_password)
        
        if isinstance(user_response, tuple):
            return user_response
        
        token = user_response.get_json().get('token')

        response = make_response(jsonify({'message': 'Login successful','token': token}))
        response.set_cookie('auth_token', token, httponly=True, secure=True, max_age=3600)
        return response
    return render_template('login.html')

@app.route('/auth/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('auth_token', '', expires=0)
    return response

# Protected route
@app.route('/auth/protected', methods=['GET'])
def protected():
    current_user, error_response, status_code = auth_handler.verify_token(request)
    if error_response:
        return error_response, status_code
    return render_template('protected.html', user=current_user)

# c. /create_course [POST] (Admin Only)
@app.route('/create_course', methods=['POST'])
def create_course():
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        content = request.get_json()
        course_name = content['course_name']
        course_code = content['course_code']
        created_by = content['created_by']

        cursor.execute("SELECT user_type FROM User WHERE user_id = %s", (created_by,))
        user = cursor.fetchone()

        if user is None or user[0].lower() != 'admin':
            return make_response({"error": "Only admins can create courses"}, 403)

        query = "INSERT INTO Course (course_name, course_code) VALUES (%s, %s)"
        cursor.execute(query, (course_name, course_code))

        cnx.commit()
        cursor.close()
        cnx.close()

        return make_response({"success": "Course created successfully"}, 201)

    except Exception as e:
        return make_response({'error': str(e)}, 400)

# d. /retrieve_courses [GET]
@app.route('/retrieve_courses', methods=['GET'])
def retrieve_courses():
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        query = "SELECT * FROM courses"
        cursor.execute(query)
        courses = cursor.fetchall()

        cursor.close()
        cnx.close()

        return jsonify(courses), 200

    except Exception as e:
        return make_response({'error': str(e)}, 400)

# e. /retrieve_student_courses/<student_id> [GET]
@app.route('/retrieve_student_courses/<student_id>', methods=['GET'])
def retrieve_student_courses(student_id):
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        query = """
        SELECT c.*
        FROM courses c
        JOIN enrols e ON c.course_id = e.course_id
        WHERE e.student_id = %s
        """
        cursor.execute(query, (student_id,))
        courses = cursor.fetchall()

        cursor.close()
        cnx.close()

        return jsonify(courses), 200

    except Exception as e:
        return make_response({'error': str(e)}, 400)

# f. /retrieve_lecturer_courses/<lecturer_id> [GET]
@app.route('/retrieve_lecturer_courses/<lecturer_id>', methods=['GET'])
def retrieve_lecturer_courses(lecturer_id):
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        query = """
        SELECT c.*
        FROM courses c
        JOIN teaches t ON c.course_id = t.course_id
        WHERE t.lecturer_id = %s
        """
        cursor.execute(query, (lecturer_id,))
        courses = cursor.fetchall()

        cursor.close()
        cnx.close()

        return jsonify(courses), 200

    except Exception as e:
        return make_response({'error': str(e)}, 400)

# g. /register_for_course [POST]
@app.route('/register_for_course', methods=['POST'])
def register_for_course():
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        content = request.get_json()
        student_id = content['student_id']
        course_id = content['course_id']

        query = "INSERT INTO enrols (course_id, student_id) VALUES (%s, %s)"
        cursor.execute(query, (course_id, student_id))

        cnx.commit()
        cursor.close()
        cnx.close()

        return make_response({"success": "Student registered for course"}, 201)

    except Exception as e:
        return make_response({'error': str(e)}, 400)

# h. /assign_lecturer_to_course [POST]
@app.route('/assign_lecturer_to_course', methods=['POST'])
def assign_lecturer_to_course():
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        content = request.get_json()
        lecturer_id = content['lecturer_id']
        course_id = content['course_id']

        cursor.execute("SELECT * FROM teaches WHERE course_id = %s", (course_id,))
        existing = cursor.fetchone()

        if existing:
            return make_response({'error': 'Course already has a lecturer assigned'}, 400)

        query = "INSERT INTO teaches (course_id, lecturer_id) VALUES (%s, %s)"
        cursor.execute(query, (course_id, lecturer_id))

        cnx.commit()
        cursor.close()
        cnx.close()

        return make_response({"success": "Lecturer assigned to course"}, 201)

    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/course/<int:course_id>/members', methods=['GET'])
def get_course_members(course_id):
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        # Retrieve students
        cursor.execute("""
            SELECT u.user_id, u.user_name, 'Student' AS role
            FROM users u
            JOIN enrols e ON u.user_id = e.student_id
            WHERE e.course_id = %s
        """, (course_id,))
        students = cursor.fetchall()

        # Retrieve lecturers
        cursor.execute("""
            SELECT u.user_id, u.user_name, 'Lecturer' AS role
            FROM users u
            JOIN teaches t ON u.user_id = t.lecturer_id
            WHERE t.course_id = %s
        """, (course_id,))
        lecturers = cursor.fetchall()

        cursor.close()
        cnx.close()

        return jsonify({'students': students, 'lecturers': lecturers}), 200

    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/course/<int:course_id>/calendar_events', methods=['GET'])
def get_course_calendar_events(course_id):
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM calendar_events
            WHERE course_id = %s
            ORDER BY event_date
        """, (course_id,))
        events = cursor.fetchall()

        cursor.close()
        cnx.close()

        return jsonify(events), 200

    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/student/<int:student_id>/calendar_events/<date>', methods=['GET'])
def get_student_calendar_events(student_id, date):
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("""
            SELECT ce.*
            FROM calendar_events ce
            JOIN enrols e ON ce.course_id = e.course_id
            WHERE e.student_id = %s AND ce.event_date = %s
        """, (student_id, date))
        events = cursor.fetchall()

        cursor.close()
        cnx.close()

        return jsonify(events), 200

    except Exception as e:
        return make_response({'error': str(e)}, 400)


@app.route('/course/<int:course_id>/calendar_events', methods=['POST'])
def create_calendar_event(course_id):
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        event_date = data.get('event_date')  # Format: 'YYYY-MM-DD'

        if not all([title, description, event_date]):
            return make_response({'error': 'Missing fields'}, 400)

        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        cursor.execute("""
            INSERT INTO calendar_events (course_id, title, description, event_date)
            VALUES (%s, %s, %s, %s)
        """, (course_id, title, description, event_date))
        cnx.commit()

        cursor.close()
        cnx.close()

        return make_response({'message': 'Event created successfully'}, 201)

    except Exception as e:
        return make_response({'error': str(e)}, 400)

@app.route('/course/<int:course_id>/forums', methods=['GET'])
def get_course_forums(course_id):
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM forums
            WHERE course_id = %s
            ORDER BY created_at DESC
        """, (course_id,))
        forums = cursor.fetchall()

        cursor.close()
        cnx.close()

        return jsonify(forums), 200

    except Exception as e:
        return make_response({'error': str(e)}, 400)


@app.route('/course/<int:course_id>/forums', methods=['POST'])
def create_forum(course_id):
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')

        if not all([title, description]):
            return make_response({'error': 'Missing fields'}, 400)

        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        cursor.execute("""
            INSERT INTO forums (course_id, title, description, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (course_id, title, description))
        cnx.commit()

        cursor.close()
        cnx.close()

        return make_response({'message': 'Forum created successfully'}, 201)

    except Exception as e:
        return make_response({'error': str(e)}, 400)


# Discussion Threads

# Add a New Thread to a Forum
@app.route('/forum/<int:forum_id>/threads', methods=['POST'])
def create_thread(forum_id):
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        user_id = data.get('user_id')

        if not all([title, content, user_id]):
            return make_response({'error': 'Missing fields'}, 400)

        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        cursor.execute("""
            INSERT INTO threads (forum_id, title, content, user_id, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (forum_id, title, content, user_id))
        cnx.commit()

        cursor.close()
        cnx.close()

        return make_response({'message': 'Thread created successfully'}, 201)

    except Exception as e:
        return make_response({'error': str(e)}, 400)


# Retrieve Threads for a Forum
@app.route('/forum/<int:forum_id>/threads', methods=['GET'])
def get_forum_threads(forum_id):
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM threads
            WHERE forum_id = %s
            ORDER BY created_at DESC
        """, (forum_id,))
        threads = cursor.fetchall()

        cursor.close()
        cnx.close()

        return jsonify(threads), 200

    except Exception as e:
        return make_response({'error': str(e)}, 400)
    
# Reply to a Thread (Nested Replies)
@app.route('/thread/<int:thread_id>/replies', methods=['POST'])
def add_reply(thread_id):
    try:
        data = request.get_json()
        content = data.get('content')
        user_id = data.get('user_id')
        parent_reply_id = data.get('parent_reply_id')  # Optional for nested replies

        if not all([content, user_id]):
            return make_response({'error': 'Missing fields'}, 400)

        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        cursor.execute("""
            INSERT INTO replies (thread_id, parent_reply_id, content, user_id, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (thread_id, parent_reply_id, content, user_id))
        cnx.commit()

        cursor.close()
        cnx.close()

        return make_response({'message': 'Reply added successfully'}, 201)

    except Exception as e:
        return make_response({'error': str(e)}, 400)

# Course Content

# Create Course Section
@app.route('/course/<int:course_id>/section', methods=['POST'])
def create_course_section(course_id):
    try:
        data = request.get_json()
        section_title = data.get('section_title')

        if not section_title:
            return make_response({'error': 'Missing section_title'}, 400)

        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        cursor.execute("""
            INSERT INTO CourseSection (course_id, section_title)
            VALUES (%s, %s)
        """, (course_id, section_title))

        cnx.commit()
        section_id = cursor.lastrowid

        cursor.close()
        cnx.close()

        return jsonify({'message': 'Section created', 'course_section_id': section_id}), 201

    except Exception as e:
        return make_response({'error': str(e)}, 400)


#  Add Course Content to a Section
@app.route('/section/<int:course_section_id>/content', methods=['POST'])
def add_course_content(course_section_id):
    try:
        data = request.get_json()
        content_type = data.get('content_type')  # 'link', 'file', or 'slide'
        content_title = data.get('content_title')
        content_url = data.get('content_url')

        if not all([content_type, content_title, content_url]):
            return make_response({'error': 'Missing fields'}, 400)

        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        cursor.execute("""
            INSERT INTO CourseContent (course_section_id, content_type, content_title, content_url)
            VALUES (%s, %s, %s, %s)
        """, (course_section_id, content_type, content_title, content_url))

        cnx.commit()
        cursor.close()
        cnx.close()

        return make_response({'message': 'Content added to section'}, 201)

    except Exception as e:
        return make_response({'error': str(e)}, 400)




if __name__ == '__main__':
    app.run(debug=True)
