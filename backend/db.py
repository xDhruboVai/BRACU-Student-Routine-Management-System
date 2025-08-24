from backend.init import get_connection
from passlib.hash import bcrypt
from random import randint
from datetime import datetime, timedelta

def singup(email, password, name, role, department):
    hashed = bcrypt.hash(password)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "insert into user (email, password_hash, name, role, department) values (%s, %s, %s, %s, %s)"
        cursor.execute(query, (email, hashed, name, role, department))
        user_id = cursor.lastrowid

        otp_value = randint(100000, 999999)
        expires = datetime.now() + timedelta(minutes=10)
        otp_query = "insert into user_otp (otp, used, expires_at, user_id) values (%s, %s, %s, %s)"
        cursor.execute(otp_query, (otp_value, False, expires, user_id))

        conn.commit()
        return {"success": True, "user_id": user_id, "otp": otp_value}
    except Exception as e:
        print("Signup error:", e)
        return {"success": False}
    finally:
        cursor.close()
        conn.close()

def login(email, password):
    query = "select password_hash, user_id, role from user where email = %s"
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        if result:
            hashed, user_id, role = result
            if bcrypt.verify(password, hashed):
                return {"user_id": user_id, "role": role}
        return None
    except Exception as e:
        print("Login error:", e)
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_events(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "select event_id, date_time, title, resource_link, created_at from event where user_id = %s"
        cursor.execute(query, (user_id,))
        events = cursor.fetchall()
        return events
    except Exception as e:
        print("Error fetching events:", e)
        return []
    finally:
        cursor.close()
        conn.close()

def create_course_and_classroom(faculty_user_id, course_code, course_title, classroom_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("select faculty_id from faculty where user_id = %s", (faculty_user_id,))
        result = cursor.fetchone()
        if not result:
            return {"success": False, "error": "Faculty not found"}
        faculty_id = result[0]

        course_query = "insert into course (course_code, title) values (%s, %s)"
        cursor.execute(course_query, (course_code, course_title))
        course_id = cursor.lastrowid

        classroom_query = "insert into classroom (name, created_on) valeus (%s, %s)"
        created_on = datetime.now()
        cursor.execute(classroom_query, (classroom_name, created_on))
        class_id = cursor.lastrowid

        teaches_query = "insert into teaches (faculty_id, course_id, classroom_id) values (%s, %s, %s)"
        cursor.execute(teaches_query, (faculty_id, course_id, class_id))

        conn.commit()
        return {"success": True, "course_id": course_id, "classroom_id": class_id}
    
    except Exception as e:
        print("Error creating course and classroom:", e)
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()

def upload_resource(faculty_user_id, classroom_id, resource_title, file_link):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("select faculty_id from faculty where user_id=%s", (faculty_user_id,))
        result = cursor.fetchone()
        if not result:
            return {"success": False, "error": "Faculty not found"}
        faculty_id = result[0]

        resource_query = "insert into resource (title, file_link) values (%s, %s)"
        cursor.execute(resource_query, (resource_title, file_link))
        resource_id = cursor.lastrowid

        uploads_query = "insert into uploads (faculty_id, classroom_id, resource_id) values (%s, %s, %s)"
        cursor.execute(uploads_query, (faculty_id, classroom_id, resource_id))

        conn.commit()
        return {"success": True, "resource_id": resource_id}
    except Exception as e:
        print("Error uploading resource:", e)
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()

def enroll_student(student_user_id, classroom_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("select student_id from student where user_id = %s", (student_user_id,))
        result = cursor.fetchone()
        if not result:
            return {"success": False, "error": "Student not found"}
        student_id = result[0]

        enroll_query = "insert into enrolled_in (student_id, classroom_id) values (%s, %s)"
        cursor.execute(enroll_query, (student_id, classroom_id))

        conn.commit()
        return {"success": True, "student_id": student_id, "classroom_id": classroom_id}
    except Exception as e:
        print("Error enrolling student:", e)
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()

def save_marks(student_user_id, course_id, assessment_name, obtained_marks):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("select student_id from student where user_id = %s", (student_user_id,))
        result = cursor.fetchone()
        if not result:
            return {"success": False, "error": "Student not found"}
        student_id = result[0]

        marks_query = """
        insert into marks (course_id, student_id, assessment_name, obtained_marks)
        values (%s, %s, %s, %s)
        on duplicate key update obtained_marks = %s
        """
        cursor.execute(marks_query, (course_id, student_id, assessment_name, obtained_marks, obtained_marks))

        conn.commit()
        return {"success": True, "student_id": student_id, "course_id": course_id, "assessment_name": assessment_name}
    except Exception as e:
        print("Error saving marks:", e)
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()