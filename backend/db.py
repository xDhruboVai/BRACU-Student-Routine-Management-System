import random
import yagmail
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from . import init

# Email Utilities

def send_email(email_to: str, subject: str, body: str):
    try:
        yag = yagmail.SMTP("totestote4@gmail.com", "lusb npzk fnjj jnqp")
        yag.send(to=email_to, subject=subject, contents=body)
    except Exception as e:
        print(f"Error sending email to {email_to}: {e}")

def send_otp_email(email: str, otp: int):
    subject = "Your OTP for BRACU Routine"
    body = f"Your OTP is {otp}. It will expire in 10 minutes."
    send_email(email, subject, body)

# General Helper Functions

def make_otp() -> int:
    return random.randint(100000, 999999)

def list_all_classrooms() -> List[Tuple[int, str]]:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT class_id, name FROM classroom ORDER BY name")
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def get_student_id_by_user(user_id: int) -> Optional[str]:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT student_id FROM student WHERE user_id=%s", (user_id,))
    row = cur.fetchone(); cur.close(); conn.close(); return row[0] if row else None

def get_faculty_id_by_user(user_id: int) -> Optional[str]:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT faculty_id FROM faculty WHERE user_id=%s", (user_id,))
    row = cur.fetchone(); cur.close(); conn.close(); return row[0] if row else None

def get_student_id_by_email(email: str) -> Optional[str]:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT s.student_id FROM student s JOIN `user` u ON s.user_id = u.user_id WHERE u.email = %s", (email,))
    row = cur.fetchone(); cur.close(); conn.close(); return row[0] if row else None

def get_student_id(user_id: int) -> Optional[Tuple[str]]:
    conn = init.get_connection(); cur = conn.cursor()
    sql_query = "SELECT student_id from student where user_id = %s"
    cur.execute(sql_query, (user_id,))
    result = cur.fetchone(); cur.close(); conn.close()
    return result

# Authentication

def signup(email, password, name, role, university_id, department=None):
    conn = init.get_connection(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO `user` (email, password_hash, name, role, department) VALUES (%s, %s, %s, %s, %s)",
            (email, password, name, role, department)
        )
        user_id = cur.lastrowid

        if role == 0:
            cur.execute("INSERT INTO student (user_id, student_id) VALUES (%s, %s)", (user_id, university_id))
        else:
            cur.execute("INSERT INTO faculty (user_id, faculty_id) VALUES (%s, %s)", (user_id, university_id))

        otp = make_otp()
        expires = datetime.now() + timedelta(minutes=10)
        cur.execute(
            "INSERT INTO user_otp (otp, used, expires_at, user_id) VALUES (%s, %s, %s, %s)",
            (otp, False, expires, user_id)
        )
        conn.commit()
        send_otp_email(email, otp)
        return user_id
    except Exception as e:
        conn.rollback(); raise e
    finally:
        cur.close(); conn.close()

def login(email, password):
    conn = init.get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, password_hash, name, role, department, otp_verified FROM `user` WHERE email=%s", (email,))
    user = cur.fetchone()

    if not user or user['password_hash'] != password:
        print(f"DEBUG: Login failed for '{email}'. User not found or password incorrect.")
        cur.close(); conn.close(); return None

    if not user.get('otp_verified'):
         print(f"DEBUG: Login successful for '{email}', but OTP is required.")
         cur.close(); conn.close()
         return {"requires_otp": True, "user_id": user['user_id']}

    del user['password_hash']
    cur.close(); conn.close()
    print(f"DEBUG: Login successful for '{email}'.")
    return user

def verify_otp(user_id, otp):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT otp_id, used, expires_at FROM user_otp WHERE user_id=%s AND otp=%s ORDER BY otp_id DESC LIMIT 1", (user_id, otp))
    row = cur.fetchone()
    
    if not row:
        cur.close(); conn.close(); return False
        
    otp_id, used, expires_at = row
    if used or datetime.now() > expires_at:
        cur.close(); conn.close(); return False
    
    cur.execute("UPDATE user_otp SET used=true WHERE otp_id=%s", (otp_id,))
    cur.execute("UPDATE `user` SET otp_verified=true WHERE user_id=%s", (user_id,))
    conn.commit(); cur.close(); conn.close()
    return True

# Courses & Marks

def create_course(course_code: str, title: str, user_id: int) -> int:
    student_id = get_student_id_by_user(user_id)
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO course (course_code, title, user_id) VALUES (%s, %s, %s)", (student_id + '_' + course_code, title, user_id))
    course_id = cur.lastrowid; conn.commit(); cur.close(); conn.close(); return course_id

def delete_student_course(course_id: int, user_id: int) -> bool:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM course WHERE course_id = %s AND user_id = %s", (course_id, user_id))
    deleted_rows = cur.rowcount; conn.commit(); cur.close(); conn.close(); return deleted_rows > 0

def create_assessment_group(course_id, name, drop_lowest=1):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO assessment_group (course_id, name, drop_lowest) VALUES (%s,%s,%s)", (course_id, name, drop_lowest))
    group_id = cur.lastrowid; conn.commit(); cur.close(); conn.close(); return group_id

def delete_assessment_group(group_id: int, user_id: int) -> bool:
    conn = init.get_connection(); cur = conn.cursor()
    try:

        cur.execute("SELECT 1 FROM assessment_group ag JOIN course c ON ag.course_id = c.course_id WHERE ag.group_id = %s AND c.user_id = %s", (group_id, user_id))
        if not cur.fetchone():
            cur.close(); conn.close(); return False

        cur.execute("DELETE m FROM marks m JOIN got g ON m.mark_id = g.mark_id WHERE g.group_id = %s", (group_id,))
        
        cur.execute("DELETE FROM assessment_group WHERE group_id = %s", (group_id,))
        deleted_rows = cur.rowcount
        conn.commit()
        return deleted_rows > 0
    except Exception as e:
        conn.rollback(); return False
    finally:
        cur.close(); conn.close()

def add_mark(course_id, student_id, group_id, assessment_name, obtained_marks, total_marks):
    conn = init.get_connection(); cur = conn.cursor()
    try:
        find_mark_query = """
            SELECT m.mark_id 
            FROM marks m 
            JOIN got g ON m.mark_id = g.mark_id 
            WHERE g.course_id=%s AND g.student_id=%s AND g.group_id=%s AND m.assessment_name=%s
        """
        cur.execute(find_mark_query, (course_id, student_id, group_id, assessment_name))
        result = cur.fetchone()

        if result:
            mark_id = result[0]
            cur.execute("UPDATE marks SET obtained_marks = %s, total_marks = %s WHERE mark_id = %s", (obtained_marks, total_marks, mark_id))
        else:
            cur.execute("INSERT INTO marks (assessment_name, obtained_marks, total_marks) VALUES (%s, %s, %s)", (assessment_name, obtained_marks, total_marks))
            mark_id = cur.lastrowid
            cur.execute("INSERT INTO got (mark_id, course_id, student_id, group_id) VALUES (%s, %s, %s, %s)", (mark_id, course_id, student_id, group_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        cur.close(); conn.close()

def delete_mark(mark_id: int, user_id: int) -> bool:
    conn = init.get_connection(); cur = conn.cursor()
    try:
        delete_query = """
            DELETE m FROM marks m 
            JOIN got g ON m.mark_id = g.mark_id
            JOIN course c ON g.course_id = c.course_id 
            WHERE m.mark_id = %s AND c.user_id = %s
        """
        cur.execute(delete_query, (mark_id, user_id))
        deleted_rows = cur.rowcount
        conn.commit()
        return deleted_rows > 0
    except Exception as e:
        conn.rollback(); return False
    finally:
        cur.close(); conn.close()

def group_average_percent(course_id, student_id, group_id):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT drop_lowest FROM assessment_group WHERE group_id=%s AND course_id=%s", (group_id, course_id))
    row = cur.fetchone()
    if not row: cur.close(); conn.close(); return 0.0
    drop_lowest = row[0]

    marks_query = """
        SELECT m.obtained_marks, m.total_marks 
        FROM marks m 
        JOIN got g ON m.mark_id = g.mark_id 
        WHERE g.course_id=%s AND g.student_id=%s AND g.group_id=%s
    """
    cur.execute(marks_query, (course_id, student_id, group_id))
    marks = cur.fetchall(); cur.close(); conn.close()
    
    if not marks: return 0.0
    percents = [(float(ob) / float(tot)) * 100.0 for ob, tot in marks if tot and float(tot) > 0]
    if not percents: return 0.0
    percents.sort()
    to_drop = min(drop_lowest, max(0, len(percents) - 1))
    kept = percents[to_drop:]
    if not kept: return 0.0
    return float(round(sum(kept) / len(kept), 2))

# Classrooms & Teaching

def create_classroom(name: str, faculty_id: str) -> int:
    conn = init.get_connection(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO classroom (name) VALUES (%s)", (name,)); class_id = cur.lastrowid
        cur.execute("INSERT INTO teaches (faculty_id, classroom_id) VALUES (%s, %s)", (faculty_id, class_id))
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Error creating classroom: {e}"); return 0
    finally:
        cur.close(); conn.close()
    return class_id

def delete_faculty_classroom(classroom_id: int, faculty_id: str) -> bool:
    conn = init.get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM teaches WHERE classroom_id = %s AND faculty_id = %s", (classroom_id, faculty_id))
        if not cur.fetchone():
            print(f"DEBUG: Permission denied. Faculty {faculty_id} tried to delete classroom {classroom_id}.")
            cur.close(); conn.close(); return False
        cur.execute("DELETE FROM classroom WHERE class_id = %s", (classroom_id,))
        deleted_rows = cur.rowcount
        conn.commit()
        return deleted_rows > 0
    except Exception as e:
        conn.rollback(); print(f"Error deleting classroom: {e}"); return False
    finally:
        cur.close(); conn.close()

def enroll_student_in_class(student_id: str, class_id: int):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO enrolled_in (student_id, classroom_id) VALUES (%s,%s) ON DUPLICATE KEY UPDATE student_id=student_id", (student_id, class_id))
    conn.commit(); cur.close(); conn.close()

def assign_teaches(faculty_id: str, class_id: int):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO teaches (faculty_id, classroom_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE faculty_id=faculty_id", (faculty_id, class_id))
    conn.commit(); cur.close(); conn.close()

# Events

def add_personal_event(user_id, date_time, title, resource_link=None):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO event (date_time, title, resource_link, user_id) VALUES (%s,%s,%s,%s)", (date_time, title, resource_link, user_id))
    event_id = cur.lastrowid; conn.commit(); cur.close(); conn.close(); return event_id

def add_class_event(faculty_id, class_id, date_time, title, resource_link=None):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM teaches WHERE faculty_id=%s AND classroom_id=%s LIMIT 1", (faculty_id, class_id))
    if not cur.fetchone(): cur.close(); conn.close(); return None
    cur.execute("SELECT user_id FROM faculty WHERE faculty_id=%s", (faculty_id,)); fac_user_id = cur.fetchone()[0]
    cur.execute("INSERT INTO event (date_time, title, resource_link, user_id) VALUES (%s,%s,%s,%s)", (date_time, title, resource_link, fac_user_id))
    event_id = cur.lastrowid
    cur.execute("INSERT INTO creates (faculty_id, classroom_id, event_id) VALUES (%s,%s,%s)", (faculty_id, class_id, event_id))
    conn.commit(); cur.close(); conn.close(); return event_id

def delete_personal_event(event_id: int, user_id: int) -> bool:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM event WHERE event_id = %s AND user_id = %s AND event_id NOT IN (SELECT event_id FROM creates)", (event_id, user_id))
    deleted_rows = cur.rowcount; conn.commit(); cur.close(); conn.close(); return deleted_rows > 0

def delete_class_event(event_id: int, faculty_id: str) -> bool:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM creates WHERE event_id = %s AND faculty_id = %s", (event_id, faculty_id))
    if not cur.fetchone():
        cur.close(); conn.close(); return False
    cur.execute("DELETE FROM event WHERE event_id = %s", (event_id,))
    deleted_rows = cur.rowcount; conn.commit(); cur.close(); conn.close(); return deleted_rows > 0

# Resources

def add_resource(faculty_id, class_id, title, file_link):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO resource (title, file_link) VALUES (%s,%s)", (title, file_link)); resource_id = cur.lastrowid
    cur.execute("INSERT INTO uploads (faculty_id, classroom_id, resource_id) VALUES (%s,%s,%s)", (faculty_id, class_id, resource_id))
    conn.commit(); cur.close(); conn.close(); return resource_id

def list_classroom_resources(class_id):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT r.resource_id, r.title, r.file_link FROM resource r JOIN uploads u ON u.resource_id = r.resource_id WHERE u.classroom_id = %s ORDER BY r.resource_id DESC", (class_id,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

# Listings & Calendar

def list_my_personal_courses(user_id: int) -> List[Tuple[int, str, str]]:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT course_id, course_code, title FROM course WHERE user_id = %s ORDER BY course_code", (user_id,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def list_my_classrooms(user_id: int) -> List[Tuple[int, str]]:
    sid = get_student_id_by_user(user_id)
    if not sid: return []
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT c.class_id, c.name FROM enrolled_in en JOIN classroom c ON c.class_id = en.classroom_id WHERE en.student_id = %s ORDER BY c.name", (sid,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def list_faculty_assignments(user_id: int) -> List[Tuple[int, str]]:
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT cr.class_id, cr.name FROM teaches t JOIN faculty f ON f.faculty_id = t.faculty_id JOIN classroom cr ON cr.class_id = t.classroom_id WHERE f.user_id = %s ORDER BY cr.name", (user_id,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def list_assessment_groups(course_id):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT group_id, name, drop_lowest FROM assessment_group WHERE course_id=%s ORDER BY name", (course_id,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def list_marks(course_id, student_id):
    conn = init.get_connection(); cur = conn.cursor()
    query = """
        SELECT 
            m.mark_id, ag.name AS group_name, m.assessment_name, 
            m.obtained_marks, m.total_marks, m.created_at, g.group_id 
        FROM marks m
        JOIN got g ON m.mark_id = g.mark_id
        JOIN assessment_group ag ON g.group_id = ag.group_id
        WHERE g.course_id=%s AND g.student_id=%s 
        ORDER BY ag.name, m.created_at
    """
    cur.execute(query, (course_id, student_id))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def list_classroom_events(class_id):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT e.event_id, e.date_time, e.title, e.resource_link FROM event e JOIN creates c ON c.event_id = e.event_id WHERE c.classroom_id = %s ORDER BY e.date_time ASC", (class_id,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def list_my_calendar(user_id):
    conn = init.get_connection(); cur = conn.cursor()
    cur.execute("SELECT e.event_id, e.date_time, e.title, e.resource_link, c.classroom_id, 'classroom', c.faculty_id FROM event e JOIN creates c ON c.event_id = e.event_id JOIN enrolled_in en ON en.classroom_id = c.classroom_id JOIN student s ON s.student_id = en.student_id WHERE s.user_id = %s", (user_id,))
    rows_student = cur.fetchall()
    cur.execute("SELECT e.event_id, e.date_time, e.title, e.resource_link, c.classroom_id, 'classroom', c.faculty_id FROM event e JOIN creates c ON c.event_id = e.event_id JOIN faculty f ON f.faculty_id = c.faculty_id WHERE f.user_id = %s", (user_id,))
    rows_faculty = cur.fetchall()
    cur.execute("SELECT e.event_id, e.date_time, e.title, e.resource_link, NULL, 'personal', NULL FROM event e WHERE e.user_id = %s AND e.event_id NOT IN (SELECT event_id FROM creates)", (user_id,))
    rows_personal = cur.fetchall()
    cur.close(); conn.close()
    all_rows = rows_student + rows_faculty + rows_personal
    all_rows.sort(key=lambda r: r[1])
    return all_rows

# Background Tasks

def get_users_for_events_on_date(target_date: datetime.date) -> list:
    conn = init.get_connection(); cur = conn.cursor()
    all_notifications = []
    
    personal_events_query = """
        SELECT e.title, e.date_time, u.name, u.email
        FROM event e JOIN `user` u ON e.user_id = u.user_id
        WHERE DATE(e.date_time) = %s AND e.event_id NOT IN (SELECT event_id FROM creates)
    """
    cur.execute(personal_events_query, (target_date,)); all_notifications.extend(cur.fetchall())

    student_classroom_events_query = """
        SELECT e.title, e.date_time, u.name, u.email
        FROM event e JOIN creates c ON e.event_id = c.event_id
        JOIN enrolled_in ei ON c.classroom_id = ei.classroom_id
        JOIN student s ON ei.student_id = s.student_id
        JOIN `user` u ON s.user_id = u.user_id
        WHERE DATE(e.date_time) = %s
    """
    cur.execute(student_classroom_events_query, (target_date,)); all_notifications.extend(cur.fetchall())
    
    faculty_classroom_events_query = """
        SELECT e.title, e.date_time, u.name, u.email
        FROM event e JOIN creates c ON e.event_id = c.event_id
        JOIN teaches t ON c.classroom_id = t.classroom_id
        JOIN faculty f ON t.faculty_id = f.faculty_id
        JOIN `user` u ON f.user_id = u.user_id
        WHERE DATE(e.date_time) = %s
    """
    cur.execute(faculty_classroom_events_query, (target_date,)); all_notifications.extend(cur.fetchall())

    cur.close(); conn.close()
    return all_notifications

# User Analytics

def days_since_last_activity(user_id):
    conn = init.get_connection(); cur = conn.cursor()
    query = """
        SELECT TIMESTAMPDIFF(DAY, MAX(last_time), NOW()) AS days_since_last FROM (
            SELECT MAX(e.date_time) AS last_time FROM event e WHERE e.user_id = %s
            UNION ALL
            SELECT MAX(e2.date_time) AS last_time FROM event e2
                JOIN creates c ON c.event_id = e2.event_id
                JOIN enrolled_in en ON en.classroom_id = c.classroom_id
                JOIN student s ON s.student_id = en.student_id
                WHERE s.user_id = %s
            UNION ALL
            SELECT MAX(e3.date_time) AS last_time FROM event e3
                JOIN creates c2 ON c2.event_id = e3.event_id
                JOIN faculty f ON f.faculty_id = c2.faculty_id
                WHERE f.user_id = %s
        ) t
    """
    cur.execute(query, (user_id, user_id, user_id))
    row = cur.fetchone(); cur.close(); conn.close()
    return row[0] if row and row[0] is not None else None