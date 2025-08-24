import os
from mysql import connector

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "Routine"
}

setup_file = os.path.join(os.path.dirname(__file__), "../Database/setup.sql")
host = db_config["host"]
user = db_config["user"]
password = db_config["password"]
database = db_config["database"]

def init_database():
    conn = connector.connect(
        host = host,
        user = user,
        password = password
    )
    cursor = conn.cursor()
    with open(setup_file, "r") as f:
        sql_commands = f.read().split(";")
    for command in sql_commands:
        if command.strip():
            try:
                cursor.execute(command)
            except:
                pass
    conn.commit()
    cursor.close()
    conn.close()

def get_connection():
    return connector.connect(
        host = host,
        user = user,
        password = password,
        database = database
    )

init_database()