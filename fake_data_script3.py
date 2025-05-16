import random
from faker import Faker
from tqdm import tqdm

fake = Faker()

# Output file
sql_file = open("seed_data2.sql", "w", encoding="utf-8")

# Constants
NUM_STUDENTS = 100_000
NUM_COURSES = 200
MAX_COURSES_PER_STUDENT = 6
MIN_COURSES_PER_STUDENT = 3
MIN_STUDENTS_PER_COURSE = 10
MAX_COURSES_PER_LECTURER = 5

# ID counters
user_id_counter = 1
assignment_id_counter = 1
course_codes = []

student_ids = []
lecturer_ids = []

# --- Create Students ---
for _ in tqdm(range(NUM_STUDENTS), desc="Generating Students"):
    name = fake.name().replace("'", "''")
    email = fake.unique.email()
    password = fake.password()
    sql_file.write(f"INSERT INTO User (user_id, user_name, user_email, user_password, user_type) "
                   f"VALUES ({user_id_counter}, '{name}', '{email}', '{password}', 'Student');\n")
    student_ids.append(user_id_counter)
    user_id_counter += 1

# --- Create Lecturers ---
num_lecturers = (NUM_COURSES // MAX_COURSES_PER_LECTURER) + 10
for _ in tqdm(range(num_lecturers), desc="Generating Lecturers"):
    name = fake.name().replace("'", "''")
    email = fake.unique.email()
    password = fake.password()
    sql_file.write(f"INSERT INTO User (user_id, user_name, user_email, user_password, user_type) "
                   f"VALUES ({user_id_counter}, '{name}', '{email}', '{password}', 'Lecturer');\n")
    lecturer_ids.append(user_id_counter)
    user_id_counter += 1

# --- Create Courses ---
for i in tqdm(range(NUM_COURSES), desc="Generating Courses"):
    name = f"{fake.word().capitalize()} {fake.word().capitalize()}"
    code = f"CSE{i+1000}"
    course_codes.append(code)
    sql_file.write(f"INSERT INTO Course (course_code, course_name) VALUES ('{code}', '{name}');\n")

# --- Assign Lecturers to Courses ---
lecturer_course_map = {lecturer: [] for lecturer in lecturer_ids}
for course_code in tqdm(course_codes, desc="Assigning Lecturers"):
    eligible = [l for l, c in lecturer_course_map.items() if len(c) < MAX_COURSES_PER_LECTURER]
    lecturer = random.choice(eligible)
    lecturer_course_map[lecturer].append(course_code)
    sql_file.write(f"INSERT INTO Teach (course_code, lecturer_id) VALUES ('{course_code}', {lecturer});\n")

# --- Enroll Students ---
course_student_map = {code: set() for code in course_codes}
for student_id in tqdm(student_ids, desc="Enrolling Students"):
    num_courses = random.randint(MIN_COURSES_PER_STUDENT, MAX_COURSES_PER_STUDENT)
    selected = random.sample(course_codes, num_courses)
    for course_code in selected:
        grade = round(random.uniform(50, 100), 2)
        sql_file.write(f"INSERT INTO Enrol (course_code, student_id, course_grade) "
                       f"VALUES ('{course_code}', {student_id}, {grade});\n")
        course_student_map[course_code].add(student_id)

# --- Ensure minimum students per course ---
for course_code, students in tqdm(course_student_map.items(), desc="Ensuring Min Students"):
    needed = MIN_STUDENTS_PER_COURSE - len(students)
    if needed > 0:
        available = list(set(student_ids) - students)
        extras = random.sample(available, needed)
        for student_id in extras:
            grade = round(random.uniform(50, 100), 2)
            sql_file.write(f"INSERT INTO Enrol (course_code, student_id, course_grade) "
                           f"VALUES ('{course_code}', {student_id}, {grade});\n")

# --- Create Assignments and Submissions ---
# for course_code in tqdm(course_codes, desc="Creating Assignments"):
#     num_assignments = random.randint(1, 3)
#     for _ in range(num_assignments):
#         title = fake.sentence(nb_words=4).replace("'", "''")
#         sql_file.write(f"INSERT INTO Assignment (assignment_id, course_code, assignment_title) "
#                        f"VALUES ({assignment_id_counter}, '{course_code}', '{title}');\n")

#         # Randomly select 50–100 students to submit
#         enrolled_students = list(course_student_map[course_code])
#         submissions = random.sample(enrolled_students, min(100, len(enrolled_students)))
#         for student_id in submissions:
#             grade = round(random.uniform(50, 100), 2)
#             sql_file.write(f"INSERT INTO Submit (assignment_id, student_id, assignment_grade) "
#                            f"VALUES ({assignment_id_counter}, {student_id}, {grade});\n")
#         assignment_id_counter += 1

sql_file.close()
print("✅ Updated SQL seed data generated.")
