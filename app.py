from flask import Flask, request, jsonify, make_response
import mysql.connector
from mysql.connector import Error
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import os

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # Change this in production
jwt = JWTManager(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_mysql_user',
    'password': 'your_mysql_password',
    'database': 'VLE'
}

# ------------------- User Routes ----------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if data['type'] not in ['Admin', 'Lecturer', 'Student']:
        return make_response({'msg': 'Invalid user type'}, 400)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO User (user_name, user_email, user_password, user_type) VALUES (%s, %s, %s, %s)",
                       (data['name'], data['email'], data['password'], data['type']))
        conn.commit()
        return make_response({'msg': 'User registered successfully'}, 200)
    except mysql.connector.IntegrityError:
        return make_response({'msg': 'Email already exists'}, 400)
    except Error as e:
        return make_response({'msg': str(e)}, 500)
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, user_password, user_type FROM User WHERE user_email = %s", (data['email'],))
        row = cursor.fetchone()
        if row and row[1] == data['password']:
            token = create_access_token(identity={'id': row[0], 'type': row[2]})
            return make_response({'token': token}, 200)
        return make_response({'msg': 'Invalid credentials'}, 401)
    finally:
        cursor.close()
        conn.close()

# --------------- Course Management ------------
@app.route('/course', methods=['POST'])
@jwt_required()
def create_course():
    user = get_jwt_identity()
    if user['type'] != 'Admin':
        return make_response({'msg': 'Only admins can create courses'}, 403)
    
    data = request.json
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Course WHERE course_code = %s", (data['code'],))
        if cursor.fetchone()[0] > 0:
            return make_response({'msg': 'Course code already exists'}, 400)
        cursor.execute("INSERT INTO Course (course_name, course_code) VALUES (%s, %s)", (data['name'], data['code']))
        conn.commit()
        return make_response({'msg': 'Course created'}, 201)
    finally:
        cursor.close()
        conn.close()

@app.route('/courses', methods=['GET'])
def get_all_courses():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT course_id, course_name, course_code FROM Course")
        courses = [{'id': row[0], 'name': row[1], 'code': row[2]} for row in cursor.fetchall()]
        return make_response(jsonify(courses), 200)
    finally:
        cursor.close()
        conn.close()

@app.route('/courses/student/<int:student_id>', methods=['GET'])
def get_student_courses(student_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.course_id, c.course_name, c.course_code
            FROM Enrol e
            JOIN Course c ON e.course_id = c.course_id
            WHERE e.student_id = %s
        """, (student_id,))
        courses = [{'id': row[0], 'name': row[1], 'code': row[2]} for row in cursor.fetchall()]
        return make_response(jsonify(courses), 200)
    finally:
        cursor.close()
        conn.close()

@app.route('/courses/lecturer/<int:lecturer_id>', methods=['GET'])
def get_lecturer_courses(lecturer_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT course_id, course_name FROM Course WHERE lecturer_id = %s", (lecturer_id,))
        courses = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        return make_response(jsonify(courses), 200)
    finally:
        cursor.close()
        conn.close()

# --------------- Enrolment and Assignments ------------
@app.route('/enrol', methods=['POST'])
@jwt_required()
def enrol_in_course():
    user = get_jwt_identity()
    if user['type'] != 'Student':
        return make_response({'msg': 'Only students can enrol in courses'}, 403)
    
    data = request.json
    student_id = user['id']
    course_id = data['course_id']
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Enrol WHERE student_id = %s AND course_id = %s", (student_id, course_id))
        if cursor.fetchone()[0] > 0:
            return make_response({'msg': 'You are already enrolled in this course'}, 400)
        
        cursor.execute("INSERT INTO Enrol (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
        conn.commit()
        return make_response({'msg': 'Successfully enrolled in the course'}, 201)
    finally:
        cursor.close()
        conn.close()

@app.route('/assign_lecturer', methods=['POST'])
@jwt_required()
def assign_lecturer_to_course():
    user = get_jwt_identity()
    if user['type'] != 'Admin':
        return make_response({'msg': 'Only admins can assign lecturers'}, 403)
    
    data = request.json
    lecturer_id = data['lecturer_id']
    course_id = data['course_id']
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT user_type FROM User WHERE user_id = %s", (lecturer_id,))
        row = cursor.fetchone()
        if row[0] != 'Lecturer':
            return make_response({'msg': 'Only lecturers can be assigned to courses'}, 400)
        
        cursor.execute("INSERT INTO Teach (course_id, lecturer_id) VALUES (%s, %s)", (course_id, lecturer_id))
        conn.commit()
        return make_response({'msg': 'Lecturer assigned to course'}, 201)
    finally:
        cursor.close()
        conn.close()

@app.route('/calendar_event', methods=['POST'])
@jwt_required()
def create_calendar_event():
    user = get_jwt_identity()
    if user['type'] not in ['Admin', 'Lecturer']:
        return make_response({'msg': 'Only admins and lecturers can create calendar events'}, 403)
    
    data = request.json
    course_id = data['course_id']
    event_date = data['event_date']
    event_title = data['event_title']
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO CalendarEvent (course_id, event_date, event_title) VALUES (%s, %s, %s)",
                       (course_id, event_date, event_title))
        conn.commit()
        return make_response({'msg': 'Calendar event created'}, 201)
    finally:
        cursor.close()
        conn.close()

# --------------- Course Content and Discussion ------------
@app.route('/course_content/<int:course_section_id>', methods=['GET'])
def get_course_content(course_section_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content_type, content_title, content_url, uploaded_file_path
            FROM CourseContent
            WHERE course_section_id = %s
        """, (course_section_id,))
        content = [{'type': row[0], 'title': row[1], 'url': row[2], 'file_path': row[3]} for row in cursor.fetchall()]
        return make_response(jsonify(content), 200)
    finally:
        cursor.close()
        conn.close()

@app.route('/discussion_forum', methods=['POST'])
@jwt_required()
def create_forum():
    user = get_jwt_identity()
    if user['type'] not in ['Admin', 'Lecturer']:
        return make_response({'msg': 'Only admins and lecturers can create forums'}, 403)
    
    data = request.json
    course_id = data['course_id']
    forum_title = data['forum_title']
    forum_content = data.get('forum_content', '')
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO DiscussionForum (course_id, forum_title, forum_content) VALUES (%s, %s, %s)",
                       (course_id, forum_title, forum_content))
        conn.commit()
        return make_response({'msg': 'Discussion forum created'}, 201)
    finally:
        cursor.close()
        conn.close()

@app.route('/discussion_thread', methods=['POST'])
@jwt_required()
def create_thread():
    user = get_jwt_identity()
    data = request.json
    forum_id = data['forum_id']
    thread_creator_id = user['id']
    thread_content = data['thread_content']
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO DiscussionThread (forum_id, thread_creator_id, thread_content) VALUES (%s, %s, %s)",
                       (forum_id, thread_creator_id, thread_content))
        conn.commit()
        return make_response({'msg': 'Thread created'}, 201)
    finally:
        cursor.close()
        conn.close()

# ------------------- Main -------------------
if __name__ == '__main__':
    app.run(debug=True)
