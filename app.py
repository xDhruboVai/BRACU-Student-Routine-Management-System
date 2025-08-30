import os
import secrets
from datetime import datetime, timedelta, date
from itertools import groupby
from typing import List, Tuple, Optional, Dict, Any
import json

from dotenv import load_dotenv
from nicegui import ui, app

from backend import db

load_dotenv()

# Theme & Global Styles

PRIMARY_COLOR = '#6366F1'
ui.colors(
    primary=PRIMARY_COLOR,
    secondary='#06B6D4', accent='#F59E0B', positive='#10B981',
    negative='#EF4444', warning='#F59E0B', info='#0EA5E9',
)
ui.add_head_html('''
<style>
  :root {
    --glass-bg: rgba(255, 255, 255, 0.08); --glass-border: rgba(255, 255, 255, 0.18);
    --glass-shadow: 0 10px 30px rgba(0,0,0,0.25);
  }
  body {
    min-height: 100vh; background: linear-gradient(180deg, #0b1220 0%, #0c1024 100%); color: #e5e7eb;
  }
  body::before, body::after {
    content: ''; position: fixed; inset: -20%; z-index: -2;
    background:
      radial-gradient(35rem 35rem at 20% 20%, rgba(99,102,241,.25), transparent 60%),
      radial-gradient(35rem 35rem at 80% 30%, rgba(6,182,212,.25), transparent 60%),
      radial-gradient(30rem 30rem at 40% 80%, rgba(245,158,11,.2), transparent 60%);
    filter: blur(60px); animation: bg-drift 26s ease-in-out infinite alternate;
  }
  body::after { animation-duration: 35s; opacity: .7; }
  @keyframes bg-drift { 0% { transform: translate3d(0, 0, 0) scale(1.1); } 100% { transform: translate3d(-2%, 3%, 0) scale(1); } }
  .glass {
    background: var(--glass-bg); backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border); border-radius: 16px; box-shadow: var(--glass-shadow);
  }
  .nav-item {
    display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px;
    color: #e5e7eb; text-decoration: none; transition: background 220ms ease, transform 160ms ease;
  }
  .nav-item:hover { background: rgba(99,102,241,.15); transform: translateX(2px); }
  .page-title { display: flex; align-items: center; gap: 12px; font-weight: 600; letter-spacing: .2px; }
  .q-header { background: transparent !important; box-shadow: none !important; }
  .q-drawer { background: rgba(8, 12, 24, .60) !important; backdrop-filter: blur(10px); }
  .maxw-lg { max-width: 1280px; margin: 0 auto; }
  .maxw-md { max-width: 768px; margin: 0 auto; }
  .divider { height: 1px; background: rgba(255,255,255,.08); margin: 18px 0; }
</style>
''')


# Utilities and Session State

def role_str(role: int) -> str: return 'Student' if role == 0 else 'Faculty'
def fmt_dt(dt: datetime) -> str: return dt.strftime('%Y-%m-%d %H:%M')
def current_user() -> Dict[str, Any]: return app.storage.user
def set_user(u: Dict[str, Any]) -> None: app.storage.user.update(u)
def clear_user() -> None: app.storage.user.clear()

def require_auth() -> bool:
    if not current_user().get('user_id'):
        ui.notify('Please log in first.', type='warning')
        ui.navigate.to('/auth')
        return False
    return True

# Database Wrappers

def my_student_id(user_id: int) -> Optional[str]: return db.get_student_id_by_user(user_id)
def my_faculty_id(user_id: int) -> Optional[str]: return db.get_faculty_id_by_user(user_id)
def list_my_classrooms(user_id: int) -> List[Tuple[int, str]]: return db.list_my_classrooms(user_id)
def list_faculty_classrooms(user_id: int) -> List[Tuple[int, str]]: return db.list_faculty_assignments(user_id)
def list_my_courses_user(user_id: int) -> List[Tuple[int, str, str]]: return db.list_my_personal_courses(user_id)
RESOURCES_PATH = '/Users/dihanislamdhrubo/Desktop/Summer 2025/CSE370 Project/resources'

def load_general_resources() -> List[Dict[str, Any]]:
    if not os.path.exists(RESOURCES_PATH):
        print(f"Warning: Resources directory not found at '{RESOURCES_PATH}'")
        return []

    all_courses_data = []
    for filename in sorted(os.listdir(RESOURCES_PATH)):
        if filename.lower().endswith('.json'):
            course_code = os.path.splitext(filename)[0]

            full_path = os.path.join(RESOURCES_PATH, filename)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['course_code'] = course_code
                    all_courses_data.append(data)
            except json.JSONDecodeError:
                print(f"Error: Could not parse {filename}. It may be malformed.")
            except Exception as e:
                print(f"An error occurred loading {filename}: {e}")

    all_courses_data.sort(key=lambda x: x.get('course_code', ''))
    return all_courses_data

# Reusable UI Components

def nav_link(icon: str, text: str, target: str):
    with ui.link(target=target).classes('nav-item'):
        ui.icon(icon).props('size=20px color=white')
        ui.label(text)

def build_app_header(drawer):
    with ui.header().classes('items-center justify-between q-px-md q-py-sm'):
        with ui.row().classes('items-center'):
            ui.button(icon='menu', on_click=drawer.toggle).props('flat round dense color=white')
            with ui.row().classes('items-center q-ml-sm'):
                ui.icon('school').props('color=primary size=26px')
                ui.label('BRACU Student Routine').classes('text-h6')
        user = current_user()
        if user.get('user_id'):
            with ui.row().classes('items-center'):
                ui.chip(f"{user['name']} ({role_str(user['role'])})").props('color=primary text-color=white')
                ui.button('Logout', on_click=lambda: (clear_user(), ui.navigate.to('/auth'))).props('outline color=negative dense q-ml-md')

def build_sidebar():
    with ui.column().classes('w-68 q-pa-md'):
        with ui.row().classes('items-center q-mb-sm'):
            ui.avatar('BR').props('color=primary text-color=white')
            ui.label('Navigation').classes('text-subtitle2 q-ml-sm')
        nav_link('dashboard', 'Dashboard', '/dashboard')
        nav_link('event', 'Events', '/events')
        nav_link('meeting_room', 'Classrooms', '/classrooms')
        nav_link('menu_book', 'Courses', '/courses')
        nav_link('bar_chart', 'Marks & Performance', '/marks')
        nav_link('attach_file', 'Classroom Resources', '/Classroom Resources')
        nav_link('source', 'General Resources', '/general_resources')
        nav_link('person', 'Profile', '/profile')

def page_scaffold(title: str, icon: str = 'circle'):
    global left_drawer
    drawer = ui.left_drawer(value=False, elevated=True).classes('glass')
    with drawer:
        build_sidebar()
    build_app_header(drawer)
    left_drawer = drawer
    with ui.row().classes('page-title maxw-lg w-full q-mt-md q-mb-sm px-4 md:px-8'):
        ui.icon(icon).props('color=primary size=28px')
        ui.label(title).classes('text-h5')

# Authentication Pages

@ui.page('/auth')
def auth_page():
    clear_user()
    with ui.row().classes('maxw-lg q-mt-xl q-gutter-xl items-stretch'):
        with ui.card().classes('glass col-6 q-pa-xl light-shadow').style('width: 100%'):
            ui.icon('school').props('color=primary size=40px')
            ui.label('BRACU Student Routine').classes('text-h5 q-mt-sm')
            ui.label('A clean, unified space for schedules, resources, and performance.').classes('text-subtitle2 q-mb-lg')
            with ui.column().classes('q-gutter-sm'):
                for icon, text in [('event', 'Interactive academic calendar'), ('bolt', 'Smart notifications and reminders'), ('folder', 'Centralized resources per classroom'), ('bar_chart', 'Personal performance tracking (drop-lowest)')]:
                    with ui.row().classes('items-center q-gutter-sm'):
                        ui.icon(icon).props('color=primary')
                        ui.label(text)
            ui.separator().classes('q-my-lg')
            ui.label('New here? Sign up and verify with OTP in minutes.').classes('text-body2')

        with ui.card().classes('glass col-6 q-pa-lg light-shadow').style('width: 100%'):
            with ui.tabs().classes('w-full') as tabs:
                ui.tab(name='Login', label='Login', icon='login')
                ui.tab(name='Sign up', label='Sign up', icon='person_add')

            with ui.tab_panels(tabs, value='Login').classes('w-full'):
                with ui.tab_panel('Login'):
                    email = ui.input('Email').classes('w-full')
                    password = ui.input('Password', password=True).classes('w-full')
                    with ui.row().classes('items-center q-gutter-sm'):
                        def do_login():
                            if not email.value or not password.value: return ui.notify('Please enter email and password', type='warning')
                            r = db.login(email.value.strip(), password.value)
                            if not r: return ui.notify('Invalid email or password', type='negative')
                            if r.get('requires_otp'):
                                app.storage.user['pending_user_id'] = r['user_id']
                                app.storage.user['pending_email'] = email.value.strip()
                                app.storage.user['pending_password'] = password.value
                                ui.notify('OTP required — please check your email.', type='info')
                                ui.navigate.to('/otp')
                                return
                            r['email'] = email.value.strip()
                            set_user(r)
                            ui.notify(f'Welcome back, {r["name"]}!', type='positive')
                            ui.navigate.to('/dashboard')
                        ui.button('Login', on_click=do_login).props('color=primary unelevated')
                        ui.link('Forgot password?', '#').classes('q-ml-md text-grey-5')

                with ui.tab_panel('Sign up'):
                    s_email = ui.input('Email').classes('w-full')
                    s_name = ui.input('Full name').classes('w-full')
                    s_password = ui.input('Password', password=True).classes('w-full')
                    s_role = ui.toggle(['Student', 'Faculty'], value='Student').classes('q-my-sm')
                    s_dept = ui.input('Department (optional)').classes('w-full')
                    s_student_id = ui.input('Student ID (e.g., 23301458)').classes('w-full').bind_visibility_from(s_role, 'value', value='Student')
                    s_faculty_id = ui.input('Faculty ID').classes('w-full').bind_visibility_from(s_role, 'value', value='Faculty')

                    def do_signup():
                        try:
                            if not all([s_email.value, s_name.value, s_password.value]):
                                return ui.notify('Please fill email, name, and password', type='warning')
                            role_val = 0 if s_role.value == 'Student' else 1
                            university_id = s_student_id.value if role_val == 0 else s_faculty_id.value
                            if not university_id or not university_id.strip():
                                return ui.notify(f"Please provide your {s_role.value} ID", type='warning')

                            user_id = db.signup(
                                s_email.value.strip(),
                                s_password.value,
                                s_name.value.strip(),
                                role_val,
                                university_id.strip(),
                                department=s_dept.value.strip() or None
                            )
                            app.storage.user['pending_user_id'] = user_id
                            app.storage.user['pending_email'] = s_email.value.strip()
                            app.storage.user['pending_password'] = s_password.value
                            ui.notify('Signup successful — OTP sent to your email.', type='positive')
                            ui.navigate.to('/otp')
                        except Exception as e:
                            if 'UNIQUE constraint' in str(e) or 'Duplicate entry' in str(e):
                                ui.notify('This email or ID is already registered.', type='negative')
                            else:
                                ui.notify(f'Error during signup: {e}', type='negative')
                    ui.button('Create account', on_click=do_signup).props('color=primary unelevated')

@ui.page('/otp')
def otp_page():
    pending_uid = app.storage.user.get('pending_user_id')
    if not pending_uid:
        ui.notify('No pending OTP session. Please login or sign up.', type='warning')
        ui.navigate.to('/auth')
        return

    with ui.card().classes('glass maxw-md q-pa-xl q-mt-xl'):
        ui.icon('verified_user').props('color=primary size=36px')
        ui.label('OTP Verification').classes('text-h6')
        ui.label('Check your email for a 6-digit code.').classes('text-caption q-mb-sm')
        otp_input = ui.input('Enter OTP').props('mask=######').classes('w-full')
        with ui.row().classes('q-mt-sm q-gutter-sm'):
            def verify():
                if not otp_input.value: return ui.notify('Please enter the OTP', type='warning')
                try:
                    ok = db.verify_otp(pending_uid, int(otp_input.value))
                    if not ok: return ui.notify('Invalid or expired OTP. Try again.', type='negative')
                    email = app.storage.user.get('pending_email')
                    pwd = app.storage.user.get('pending_password')
                    r = db.login(email, pwd)
                    if isinstance(r, dict) and not r.get('requires_otp'):
                        r['email'] = email
                        set_user(r)
                        app.storage.user.pop('pending_user_id', None)
                        app.storage.user.pop('pending_email', None)
                        app.storage.user.pop('pending_password', None)
                        ui.notify('OTP verified. Welcome!', type='positive')
                        ui.navigate.to('/dashboard')
                    else:
                        ui.notify('OTP verified, but login failed. Please login again.', type='warning')
                        ui.navigate.to('/auth')
                except Exception as e:
                    ui.notify(f'Error verifying OTP: {e}', type='negative')
            ui.button('Verify OTP', on_click=verify).props('color=primary')
            ui.button('Back to Auth', on_click=lambda: ui.navigate.to('/auth')).props('flat color=grey')


# Main Application Pages

@ui.page('/dashboard')
def dashboard_page():
    if not require_auth(): return
    user = current_user()
    page_scaffold('Dashboard', icon='dashboard')

    with ui.grid(columns=3).classes('w-full px-4 md:px-8 gap-4'):
        with ui.column().classes('col-span-3 lg:col-span-2'):
            with ui.card().classes('glass q-pa-md w-full'):
                ui.label('Quick add: personal event').classes('text-subtitle1')
                form_data = {
                    'title': '',
                    'date': date.today().strftime('%Y-%m-%d'),
                    'time': '12:00',
                    'link': '',
                }
                with ui.row().classes('q-gutter-sm items-center'):
                    ui.input('Title').classes('flex-grow').props('placeholder="e.g., Study session, Lab meeting"').bind_value(form_data, 'title')
                    ui.date().props('label="Date"').bind_value(form_data, 'date')
                    ui.time().props('label="Time"').bind_value(form_data, 'time')
                ui.input('Resource link (optional)').classes('w-full').props('placeholder="https://..."').bind_value(form_data, 'link')

                def add_personal():
                    d_val, t_val, title_val, link_val = form_data['date'], form_data['time'], form_data['title'], form_data['link']
                    if not d_val or not t_val: return ui.notify('Please select a valid date and time.', type='negative')
                    if not title_val or not title_val.strip(): return ui.notify('Please enter a title for the event.', type='warning')
                    try:
                        dt = datetime.strptime(f"{d_val} {t_val}", '%Y-%m-%d %H:%M')
                    except (ValueError, TypeError):
                        return ui.notify('The selected date or time is invalid.', type='negative')
                    db.add_personal_event(user['user_id'], dt, title_val.strip(), link_val.strip() or None)
                    ui.notify('Personal event added successfully!', type='positive')
                    ui.navigate.reload()
                ui.button('Add Event', on_click=add_personal).props('color=primary')

        with ui.column().classes('col-span-3 lg:col-span-1'):
            with ui.card().classes('glass q-pa-md w-full'):
                ui.label('Upcoming (next 14 days)').classes('text-subtitle1 q-mb-sm')
                timeline = ui.timeline().classes('w-full')
                events = sorted(db.list_my_calendar(user['user_id']), key=lambda x: x[1])
                now = datetime.now()
                cutoff = now + timedelta(days=14)
                upcoming_events = [e for e in events if now <= e[1] <= cutoff]
                with timeline:
                    if not upcoming_events:
                        ui.label("No events in the next 14 days.").classes('text-gray-400 p-4')
                    for (_eid, dtv, title, link, class_id, kind, _) in upcoming_events:
                        with ui.timeline_entry(title=title, subtitle=fmt_dt(dtv), icon='event'):
                            ui.chip(kind.replace('_', ' ')).props('dense size=sm')

@ui.page('/events')
def events_page():
    if not require_auth(): return
    user = current_user()
    page_scaffold('All Events', icon='event_note')

    @ui.refreshable
    def event_timeline():
        all_events = db.list_my_calendar(user['user_id'])
        sorted_events = sorted([e for e in all_events if e[1].date() >= date.today()], key=lambda x: x[1])
        with ui.card().classes('glass w-full q-pa-md'):
            if not sorted_events:
                ui.label("You have no upcoming events.").classes('text-gray-400 p-4 text-center')
                return
            for event_date, events_on_day in groupby(sorted_events, key=lambda x: x[1].date()):
                ui.label(event_date.strftime('%A, %B %d, %Y')).classes('text-lg font-bold mt-4 opacity-90')
                with ui.timeline(side='right').classes('w-full'):
                    for event in events_on_day:
                        (_eid, dt, title, link, class_id, kind, _) = event
                        color = 'primary' if kind == 'personal' else 'secondary'
                        icon = 'person' if kind == 'personal' else 'groups'
                        with ui.timeline_entry(title=title, subtitle=dt.strftime('%I:%M %p'), icon=icon).props(f'color={color}'):
                            with ui.row().classes('items-center gap-2'):
                                ui.chip(kind.replace('_', ' ').title()).props(f'color={color} text-color=white dense size=sm')
                                if class_id:
                                    class_name = next((c[1] for c in db.list_my_classrooms(user['user_id']) if c[0] == class_id), f"ID: {class_id}")
                                    ui.chip(class_name).props('dense size=sm')
                                if link:
                                    ui.link('Resource', link, new_tab=True).classes('text-indigo-400')
                                if kind == 'personal':
                                    ui.button(icon='delete', on_click=lambda eid=_eid: confirm_delete_event(eid)).props('flat dense color=negative').classes('ml-auto')

    async def confirm_delete_event(event_id: int):
        with ui.dialog() as dialog, ui.card().classes('glass'):
            ui.label('Are you sure you want to delete this personal event?')
            with ui.row():
                ui.button('Yes, delete', on_click=lambda: (db.delete_personal_event(event_id, user['user_id']), event_timeline.refresh(), dialog.close())).props('color=negative')
                ui.button('Cancel', on_click=dialog.close).props('flat')
        await dialog

    with ui.column().classes('maxw-lg w-full px-4 md:px-8'):
        event_timeline()

@ui.page('/courses')
def courses_page():
    if not require_auth(): return
    user = current_user()
    page_scaffold('Courses', icon='menu_book')

    with ui.column().classes('maxw-lg w-full px-4 md:px-8'):
        if user['role'] == 0:
            with ui.card().classes('glass q-pa-md w-full'):
                ui.label('My courses (personal mark books)').classes('text-subtitle1')
                my_table = ui.table(columns=[{'name': 'course_code', 'label': 'Code', 'field': 'course_code'}, {'name': 'title', 'label': 'Title', 'field': 'title'}], rows=[], row_key='course_id').classes('w-full')
                def load_my():
                    rows = list_my_courses_user(user['user_id'])
                    my_table.rows = [{'course_id': r[0], 'course_code': r[1], 'title': r[2]} for r in rows]
                    my_table.update()
                load_my()
                ui.separator().classes('q-my-sm')
                with ui.row().classes('w-full gap-8'):
                    with ui.column().classes('col'):
                        ui.label('Create a new course').classes('text-subtitle2')
                        code = ui.input('Course code (e.g., CSE220)')
                        title = ui.input('Title')
                        def do_create():
                            if not code.value or not title.value: return ui.notify('Enter code and title', type='warning')
                            db.create_course(code.value.strip(), title.value.strip(), user['user_id'])
                            ui.notify('Course created', type='positive')
                            code.value = ''; title.value = ''
                            load_my(); refresh_delete_options()
                        ui.button('Create course', on_click=do_create).props('color=primary q-mt-sm')

                    with ui.column().classes('col'):
                        ui.label('Delete a course').classes('text-subtitle2')
                        pdel = ui.select([], label='Which course?').classes('w-full')
                        def refresh_delete_options():
                            rows = list_my_courses_user(user['user_id'])
                            pdel.options = {r[0]: f'{r[1]} - {r[2]}' for r in rows}
                            pdel.update()
                        refresh_delete_options()
                        async def do_delete():
                            if not pdel.value: return ui.notify('Pick a course to delete', type='warning')
                            with ui.dialog() as dialog, ui.card():
                                ui.label(f'Are you sure you want to delete this course and all its data?')
                                ui.button('Yes, delete', on_click=lambda: (db.delete_student_course(int(pdel.value), user['user_id']), ui.notify('Deleted', type='positive'), load_my(), refresh_delete_options(), dialog.close()))
                                ui.button('Cancel', on_click=dialog.close)
                            await dialog
                        ui.button('Delete selected', on_click=do_delete).props('color=negative outline q-mt-sm')
        if user['role'] == 1:
            with ui.card().classes('glass q-pa-md col'):
                ui.label('Courses are personal to each user').classes('text-subtitle1')
                ui.label('Students create their own courses here to track marks.').classes('text-body2')

@ui.page('/classrooms')
def classrooms_page():
    if not require_auth(): return
    user = current_user()
    page_scaffold('Classrooms', icon='meeting_room')

    with ui.column().classes('maxw-lg w-full px-4 md:px-8 gap-4'):
        if user['role'] == 0:
            with ui.card().classes('glass q-pa-md w-full'):
                with ui.row(wrap=False).classes('w-full justify-between items-center'):
                    ui.label('My classrooms').classes('text-subtitle1')
                    ui.button('Enroll', icon='add', on_click=lambda: enroll_dlg.open()).props('color=primary')
                ctable = ui.table(columns=[{'name': 'name', 'label': 'Classroom Name', 'field': 'name'}], rows=[], row_key='class_id').classes('w-full mt-2')
                def load_my_classes():
                    rows = list_my_classrooms(user['user_id'])
                    ctable.rows = [{'class_id': cid, 'name': n} for (cid, n) in rows]
                    ctable.update()
                load_my_classes()
                with ui.dialog() as enroll_dlg, ui.card().classes('glass q-pa-md'):
                    ui.label('Enroll in classroom').classes('text-subtitle2')
                    class_options = {cid: name for cid, name in db.list_all_classrooms()}
                    class_id_input = ui.select(class_options, label='Search and select a classroom', with_input=True).classes('w-full')
                    with ui.row().classes('q-mt-sm'):
                        def do_enroll():
                            if not class_id_input.value: return ui.notify('Select a classroom', type='warning')
                            sid = db.get_student_id_by_user(user['user_id'])
                            if not sid: return ui.notify('Not a student', type='negative')
                            db.enroll_student_in_class(sid, int(class_id_input.value))
                            ui.notify('Enrolled', type='positive')
                            enroll_dlg.close()
                            load_my_classes()
                        ui.button('Enroll', on_click=do_enroll).props('color=primary')
                        ui.button('Cancel', on_click=enroll_dlg.close).props('flat')

        if user['role'] == 1:
            with ui.card().classes('glass q-pa-md w-full'):
                with ui.row(wrap=False).classes('w-full justify-between items-center'):
                    ui.label('Manage Classrooms').classes('text-subtitle1')
                    with ui.row():
                        ui.button('Create', icon='add', on_click=lambda: create_class_dlg.open()).props('color=primary')
                        ui.button('Assign Myself', icon='person_add', on_click=lambda: assign_dlg.open()).props('color=secondary').classes('q-ml-sm')
                all_rows = db.list_all_classrooms()
                ui.table(columns=[{'name': 'name', 'label': 'All Classroom Names', 'field': 'name'}], rows=[{'class_id': r[0], 'name': r[1]} for r in all_rows], row_key='class_id').classes('w-full mt-2')
                with ui.dialog() as create_class_dlg, ui.card().classes('glass q-pa-md'):
                    ui.label('Create classroom').classes('text-subtitle2')
                    cname = ui.input('Classroom name (e.g., CSE370 Section A)').classes('w-full')
                    ui.label("Your name will be automatically appended.").classes("text-caption text-gray-400")
                    with ui.row().classes('q-mt-sm'):
                        def create_class():
                            if not cname.value: return ui.notify('Enter a classroom name', type='warning')
                            fid = db.get_faculty_id_by_user(user['user_id'])
                            if not fid: return ui.notify('Not a faculty', type='negative')
                            faculty_name = user['name']
                            full_classroom_name = f"{cname.value.strip()} ({faculty_name}_{user['user_id']})"
                            db.create_classroom(full_classroom_name, fid)
                            ui.notify('Classroom created', type='positive')
                            create_class_dlg.close()
                            ui.navigate.reload()
                        ui.button('Create', on_click=create_class).props('color=primary')
                        ui.button('Cancel', on_click=create_class_dlg.close).props('flat')
                with ui.dialog() as assign_dlg, ui.card().classes('glass q-pa-md'):
                    ui.label('Assign myself to an existing classroom').classes('text-subtitle2')
                    classes_opts = {c[0]: c[1] for c in db.list_all_classrooms()}
                    csel = ui.select(classes_opts, label='Search and select a classroom', with_input=True).classes('w-full')
                    with ui.row().classes('q-mt-sm'):
                        def do_assign():
                            fid = db.get_faculty_id_by_user(user['user_id'])
                            if not fid or not csel.value: return ui.notify('Select a classroom', type='warning')
                            db.assign_teaches(fid, csel.value)
                            ui.notify('Assigned', type='positive')
                            assign_dlg.close()
                            ui.navigate.reload()
                        ui.button('Assign', on_click=do_assign).props('color=primary')
                        ui.button('Cancel', on_click=assign_dlg.close).props('flat')

            with ui.card().classes('glass q-pa-md w-full'):
                ui.label('Delete a Classroom').classes('text-subtitle1')
                delete_options = {cid: name for cid, name in db.list_faculty_assignments(user['user_id'])}
                class_to_delete = ui.select(delete_options, label='Select one of your classrooms to delete').classes('w-full')
                async def confirm_and_delete_classroom():
                    if not class_to_delete.value:
                        return ui.notify('Please select a classroom to delete.', type='warning')
                    selected_name = delete_options.get(class_to_delete.value, "this classroom")
                    with ui.dialog() as dialog, ui.card().classes('glass'):
                        ui.label(f"Permanently delete '{selected_name}'?").classes('mb-2 text-lg')
                        ui.label('All associated enrollments, events, and resources will be removed. This cannot be undone.')
                        with ui.row().classes('mt-4 w-full justify-end'):
                            def perform_delete():
                                fid = db.get_faculty_id_by_user(user['user_id'])
                                if not fid:
                                    ui.notify('Faculty ID not found.', type='negative'); dialog.close(); return
                                success = db.delete_faculty_classroom(int(class_to_delete.value), fid)
                                ui.notify('Classroom deleted.' if success else 'Failed to delete classroom.', type='positive' if success else 'negative')
                                dialog.close()
                                ui.navigate.reload()
                            ui.button('Cancel', on_click=dialog.close).props('flat')
                            ui.button('Yes, permanently delete', on_click=perform_delete).props('color=negative')
                    await dialog
                ui.button('Delete Selected Classroom', on_click=confirm_and_delete_classroom).props('color=negative outline q-mt-sm')

            with ui.card().classes('glass w-full q-pa-md'):
                ui.label('Classroom Events').classes('text-subtitle1')
                class_opts = {cid: name for (cid, name) in db.list_faculty_assignments(user['user_id'])}
                cls_sel = ui.select(class_opts, label='Select a classroom to manage its events').classes('w-full')
                @ui.refreshable
                def events_table_for_faculty():
                    if not cls_sel.value:
                        with ui.column().classes('w-full items-center p-4'):
                             ui.icon('arrow_upward', size='lg', color='primary').classes('opacity-50')
                             ui.label("Select a classroom to see its events").classes('text-xl text-gray-400')
                        return
                    rows = db.list_classroom_events(cls_sel.value)
                    table_rows = [{'event_id': r[0], 'date_time': fmt_dt(r[1]), 'title': r[2], 'link': r[3] or ''} for r in rows]
                    with ui.table(columns=[
                        {'name': 'date_time', 'label': 'Date/Time', 'field': 'date_time', 'sortable': True},
                        {'name': 'title', 'label': 'Title', 'field': 'title'},
                        {'name': 'link', 'label': 'Resource', 'field': 'link'},
                        {'name': 'actions', 'label': '', 'field': 'actions'}
                    ], rows=table_rows, row_key='event_id').classes('w-full q-mt-sm') as table:
                        table.add_slot('body-cell-actions', '''
                            <q-td :props="props">
                                <q-btn flat dense round color="negative" icon="delete" @click="() => $parent.$emit('delete', props.row)" />
                            </q-td>
                        ''')
                    table.on('delete', lambda e: confirm_delete_class_event(e.args))
                cls_sel.on('update:model-value', events_table_for_faculty.refresh)
                events_table_for_faculty()

                async def confirm_delete_class_event(row_data):
                    event_id = row_data['event_id']
                    faculty_id = db.get_faculty_id_by_user(user['user_id'])
                    with ui.dialog() as dialog, ui.card():
                        ui.label(f"Delete event '{row_data['title']}'?")
                        ui.button('Yes, delete', on_click=lambda: (db.delete_class_event(event_id, faculty_id), events_table_for_faculty.refresh(), dialog.close()))
                        ui.button('Cancel', on_click=dialog.close)
                    await dialog

                with ui.expansion('Add Event to Selected Classroom', icon='add').classes('w-full'):
                    with ui.card_section():
                        ed = ui.date(value=date.today().strftime('%Y-%m-%d')).props('label="Date"')
                        et = ui.time(value='10:00').props('label="Time"')
                        etitle = ui.input('Title').classes('w-full')
                        elink = ui.input('Resource link (optional)').classes('w-full')
                        def add_e():
                            if not cls_sel.value: return ui.notify('Choose a classroom above', type='warning')
                            dt = datetime.strptime(f'{ed.value} {et.value}', '%Y-%m-%d %H:%M')
                            if not dt or not etitle.value: return ui.notify('Enter title and date/time', type='warning')
                            fid = db.get_faculty_id_by_user(user['user_id'])
                            if not fid: return ui.notify('Not a faculty', type='negative')
                            eid = db.add_class_event(fid, cls_sel.value, dt, etitle.value.strip(), elink.value.strip() or None)
                            if not eid: return ui.notify('Not allowed: make sure you are assigned to teach this classroom', type='negative')
                            ui.notify('Event added', type='positive')
                            events_table_for_faculty.refresh()
                        ui.button('Add Event', on_click=add_e).props('color=primary')

@ui.page('/Classroom Resources')
def resources_page():
    if not require_auth(): return
    user = current_user()
    page_scaffold('Classroom Resources', icon='attach_file')

    with ui.column().classes('maxw-lg w-full px-4 md:px-8'):
        if user['role'] == 1: class_opts = {cid: n for (cid, n) in db.list_faculty_assignments(user['user_id'])}
        else: class_opts = {cid: n for (cid, n) in list_my_classrooms(user['user_id'])}
        with ui.card().classes('glass w-full q-pa-md'):
            csel = ui.select(class_opts, label='Select classroom').classes('w-full')
            resources_container = ui.column().classes('w-full pt-4')
            def load_resources():
                resources_container.clear()
                if not csel.value: return
                with resources_container:
                    rows = db.list_classroom_resources(csel.value)
                    if not rows: ui.label('No resources found for this classroom.').classes('text-gray-400')
                    else:
                        with ui.list().props('bordered separator'):
                            for r in rows:
                                with ui.item():
                                    with ui.item_section(): ui.link(r[1], r[2], new_tab=True)
            csel.on('update:model-value', load_resources)
            if user['role'] == 1:
                with ui.expansion('Add Resource to Selected Classroom', icon='add').classes('w-full'):
                    with ui.card_section():
                        rtitle = ui.input('Title').classes('w-full')
                        rlink = ui.input('File link (URL)').classes('w-full')
                        def add_resource():
                            if not csel.value or not rtitle.value or not rlink.value: return ui.notify('Choose a class and enter title/link', type='warning')
                            fid = my_faculty_id(user['user_id'])
                            db.add_resource(fid, csel.value, rtitle.value.strip(), rlink.value.strip())
                            ui.notify('Resource added', type='positive')
                            load_resources(); rtitle.value = ''; rlink.value = ''
                        ui.button('Add Resource', on_click=add_resource).props('color=primary')

@ui.page('/marks')
def marks_page():
    if not require_auth(): return
    user = current_user()
    page_scaffold('Marks & Performance', icon='bar_chart')

    with ui.column().classes('maxw-lg w-full px-4 md:px-8'):
        if user['role'] == 0:
            my_courses = list_my_courses_user(user['user_id'])
            if not my_courses:
                with ui.card().classes('glass w-full items-center p-8'):
                    ui.label("You don't have any courses to track yet.").classes('text-xl')
                    ui.button('Add Your First Course', on_click=lambda: ui.navigate.to('/courses'), icon='add').props('color=primary')
                return
            course_opts = {cid: f'{code} - {title}' for (cid, code, title) in my_courses}
            with ui.card().classes('glass w-full q-pa-md'):
                csel = ui.select(course_opts, label='Select a course to see its performance', clearable=True).classes('w-full')
                with ui.column().classes('w-full items-center p-4').bind_visibility_from(csel, 'value', backward=lambda val: not val):
                    ui.icon('arrow_upward', size='lg', color='primary').classes('opacity-50')
                    ui.label("Select a course above to begin").classes('text-xl text-gray-400')
                with ui.column().classes('w-full gap-4').bind_visibility_from(csel, 'value'):
                    with ui.row().classes('w-full justify-end'): overall_avg_chip = ui.chip(icon='military_tech').props('color=amber text-color=black size=lg')
                    group_table = ui.table(columns=[{'name': 'name', 'label': 'Group', 'field': 'name', 'align': 'left'},{'name': 'drop_lowest', 'label': 'Drop lowest', 'field': 'drop_lowest'},{'name': 'avg', 'label': 'Average %', 'field': 'avg'}], rows=[], row_key='group_id').classes('w-full')
                    group_table.props('selection="single"')
                    with ui.row().classes('w-full justify-end q-gutter-sm'):
                        def delete_selected_group():
                            selected = group_table.selected or []
                            if not selected: return ui.notify('Select a group to delete', type='warning')
                            gid = int(selected[0]['group_id'])
                            with ui.dialog() as dialog, ui.card():
                                ui.label('Delete this group? All its marks will be removed.').classes('q-mb-sm')
                                with ui.row().classes('q-gutter-sm'):
                                    def do_yes():
                                        ok = db.delete_assessment_group(gid, user['user_id'])
                                        ui.notify('Group deleted' if ok else 'Unable to delete group', type='positive' if ok else 'negative')
                                        dialog.close(); refresh_data()
                                    ui.button('Yes, delete', on_click=do_yes).props('color=negative')
                                    ui.button('Cancel', on_click=dialog.close).props('flat')
                            dialog.open()
                        ui.button('Delete selected group', on_click=delete_selected_group).props('outline color=negative')
                    marks_table = ui.table(columns=[{'name': 'group', 'label': 'Group', 'field': 'group', 'align': 'left'},{'name': 'assessment', 'label': 'Assessment', 'field': 'assessment'},{'name': 'score', 'label': 'Score', 'field': 'score'}], rows=[], row_key='id').classes('w-full')
                    marks_table.props('selection="single"')
                    with ui.row().classes('w-full justify-end q-gutter-sm'):
                        def delete_selected_mark():
                            selected = marks_table.selected or []
                            if not selected: return ui.notify('Select a mark to delete', type='warning')
                            mid = int(selected[0]['id'])
                            with ui.dialog() as dialog, ui.card():
                                ui.label('Delete this mark?').classes('q-mb-sm')
                                with ui.row().classes('q-gutter-sm'):
                                    def do_yes():
                                        ok = db.delete_mark(mid, user['user_id'])
                                        ui.notify('Mark deleted' if ok else 'Unable to delete mark', type='positive' if ok else 'negative')
                                        dialog.close(); refresh_data()
                                    ui.button('Yes, delete', on_click=do_yes).props('color=negative')
                                    ui.button('Cancel', on_click=dialog.close).props('flat')
                            dialog.open()
                        ui.button('Delete selected mark', on_click=delete_selected_mark).props('outline color=negative')
                    chart = ui.echart({'xAxis': {'type': 'category', 'data': []},'yAxis': {'type': 'value', 'max': 100},'series': [{'type': 'bar', 'data': [], 'itemStyle': {'color': '#6366F1'}}],'tooltip': {}, 'grid': {'left': 40, 'right': 24, 'top': 20, 'bottom': 28}}).classes('w-full')
                    ui.separator().classes('q-my-md')
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('col'):
                            ui.label('Manage assessment groups').classes('text-subtitle2')
                            gname = ui.input('Group name')
                            gdrop = ui.select([0, 1, 2], value=1, label='Drop lowest N')
                            def add_group():
                                if not csel.value or not gname.value: return ui.notify('Select a course and enter group name', type='warning')
                                db.create_assessment_group(csel.value, gname.value.strip(), int(gdrop.value))
                                ui.notify('Group created', type='positive')
                                gname.value = ''; refresh_data()
                            ui.button('Create group', on_click=add_group).props('color=primary')
                        with ui.column().classes('col'):
                            ui.label('Add mark').classes('text-subtitle2')
                            gsel = ui.select([], label='Group').classes('w-full')
                            aname = ui.input('Assessment name').classes('w-full')
                            with ui.row():
                                obtained = ui.number('Obtained'); total = ui.number('Total')
                            def add_mark():
                                if not all([csel.value, gsel.value, aname.value, obtained.value is not None, total.value is not None]):
                                    return ui.notify('Fill all fields', type='warning')
                                sid = my_student_id(user['user_id'])
                                db.add_mark(csel.value, sid, int(gsel.value), aname.value.strip(), float(obtained.value), float(total.value))
                                ui.notify('Mark added', type='positive')
                                aname.value = ''; obtained.value = None; total.value = None
                                refresh_data()
                            ui.button('Add mark', on_click=add_mark).props('color=secondary')
                def refresh_data():
                    if not csel.value: return
                    sid = my_student_id(user['user_id'])
                    groups = db.list_assessment_groups(csel.value)
                    grows, gx, gy, all_averages = [], [], [], []
                    for gid, name, drop in groups:
                        avg = db.group_average_percent(csel.value, sid, gid)
                        grows.append({'group_id': gid, 'name': name, 'drop_lowest': drop, 'avg': f'{avg:.2f}%'})
                        gx.append(name); gy.append(avg); all_averages.append(avg)
                    group_table.rows = grows
                    group_table.update()
                    chart.options['xAxis']['data'] = gx
                    chart.options['series'][0]['data'] = gy
                    chart.update()
                    total_avg = sum(all_averages) / len(all_averages) if all_averages else 0
                    overall_avg_chip.text = f'Overall Performance: {total_avg:.2f}%'
                    mrows = db.list_marks(csel.value, sid)
                    marks_table.rows = [{'id': r[0], 'group': r[1], 'assessment': r[2], 'score': f'{r[3]} / {r[4]}'} for r in mrows]
                    marks_table.update()
                    gsel.options = {g['group_id']: g['name'] for g in grows}
                    gsel.update()
                csel.on('update:model-value', lambda _: refresh_data())
        else:
            with ui.card().classes('glass w-full q-pa-md'):
                ui.label('Faculty note').classes('text-subtitle1'); ui.label('Students manage their personal marks here.').classes('text-body2')

@ui.page('/general_resources')
def general_resources_page():
    if not require_auth(): return
    page_scaffold('General Resources', icon='source')

    with ui.column().classes('maxw-lg w-full px-4 md:px-8'):
        courses_data = load_general_resources()

        if not courses_data:
            with ui.card().classes('glass w-full items-center p-8'):
                ui.icon('error_outline', size='lg', color='warning')
                ui.label("No general resources found.").classes('text-xl mt-4')
                ui.label(f"Make sure you have a '{RESOURCES_PATH}' folder with .json files in it.").classes('text-gray-400')
            return

        with ui.column().classes('w-full gap-2') as courses_container:
            for course in courses_data:
                with ui.expansion().classes('w-full glass group') as expansion:
                    with expansion.add_slot('header'):
                        with ui.item_section():
                            ui.label(course.get('title', 'Untitled Course')).classes('text-lg font-semibold')
                            ui.label(course.get('description', 'No description')).classes('text-sm text-gray-400')


                    resources = course.get('resources', [])
                    if resources:
                        with ui.list().props('bordered separator'):
                            for resource in resources:
                                with ui.item():
                                    with ui.item_section():
                                        ui.link(
                                            resource.get('name', 'Unnamed Resource'),
                                            resource.get('link', '#'),
                                            new_tab=True
                                        ).classes('text-indigo-300 hover:text-indigo-400')
                    else:
                        ui.label('No resources available for this course.').classes('p-4 text-gray-500')

@ui.page('/profile')
def profile_page():
    if not require_auth(): return
    user = current_user()
    page_scaffold('Profile', icon='person')

    with ui.column().classes('maxw-md w-full px-4 md:px-8'):
        with ui.card().classes('glass w-full q-pa-md'):
            ui.label('User Info').classes('text-subtitle1')
            with ui.row().classes('q-gutter-sm'):
                ui.input('Name', value=user['name']).props('readonly').classes('col')
                ui.input('Email', value=user.get('email', '(not cached)')).props('readonly').classes('col')
            with ui.row().classes('q-gutter-sm'):
                ui.input('Role', value=role_str(user['role'])).props('readonly').classes('col')
                ui.input('Department', value=user['department'] or '').props('readonly').classes('col')
            ui.separator().classes('q-my-sm')
            ui.button('Logout', on_click=lambda: (clear_user(), ui.navigate.to('/auth'))).props('color=negative outline')


# --- Index Page & Application Startup

@ui.page('/')
def index():
    if current_user().get('user_id'):
        ui.navigate.to('/dashboard')
    else:
        ui.navigate.to('/auth')

if __name__ in {'__main__', '__mp_main__'}:
    left_drawer = None
    if os.path.exists('backend/init.py'):
        from backend import init
        init.init_database()

    STORAGE_SECRET = os.getenv('STORAGE_SECRET')
    if not STORAGE_SECRET:
        raise ValueError("STORAGE_SECRET environment variable is not set! Please create a .env file.")

    ui.run(
        title='BRACU Routine',
        host='0.0.0.0',
        port=int(os.getenv('PORT', '8080')),
        reload=False,
        storage_secret=STORAGE_SECRET
    )