import datetime
from . import db

def send_event_reminder(event_title, event_datetime, user_name, user_email, notice_period_str):

    subject = f"Upcoming Event Reminder: {event_title}"
    
    body = f"""
    Hi {user_name},

    This is a reminder that you have an upcoming event:

    Event: {event_title}
    Date: {event_datetime.strftime('%A, %B %d, %Y')}
    Time: {event_datetime.strftime('%I:%M %p')}

    This event is scheduled for {notice_period_str}.

    Regards,
    BRACU Routine App
    """

    db.send_email(user_email, subject, body)
    
    print(f"Sent '{notice_period_str}' reminder for '{event_title}' to {user_email}")


def find_and_send_reminders_for_target_date(target_date, notice_period_str):
    events_and_users = db.get_users_for_events_on_date(target_date)
    
    for event in events_and_users:
        event_title, event_datetime, user_name, user_email = event
        send_event_reminder(event_title, event_datetime, user_name, user_email, notice_period_str)
        
    print(f"Finished sending reminders for {target_date.strftime('%Y-%m-%d')}. Found {len(events_and_users)} notifications.")


def main():
    print(f"--- Starting daily reminder check at {datetime.datetime.now()} ---")
    today = datetime.date.today()
    
    target_date_2_weeks = today + datetime.timedelta(days=14)
    print(f"\n[1] Checking for events 2 weeks away (on {target_date_2_weeks})...")
    find_and_send_reminders_for_target_date(target_date_2_weeks, "in 2 weeks")
    
    target_date_1_week = today + datetime.timedelta(days=7)
    print(f"\n[2] Checking for events 1 week away (on {target_date_1_week})...")
    find_and_send_reminders_for_target_date(target_date_1_week, "in 1 week")
    
    target_date_tomorrow = today + datetime.timedelta(days=1)
    print(f"\n[3] Checking for events for tomorrow (on {target_date_tomorrow})...")
    find_and_send_reminders_for_target_date(target_date_tomorrow, "tomorrow")

    print(f"\n--- Reminder check finished at {datetime.datetime.now()} ---")


if __name__ == "__main__":
    main()