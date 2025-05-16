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
@app.route('/register/lecturer', methods=['POST'])
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
@app.route('/register/student', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True)