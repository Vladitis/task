import sqlite3

# Yhdistä tietokantaan (tiedosto project_manager.db luodaan automaattisesti)
conn = sqlite3.connect('project_manager.db')
cursor = conn.cursor()

# Luo taulut
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    priority TEXT NOT NULL,
    deadline DATE,
    created_by INTEGER REFERENCES Users(user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    priority TEXT NOT NULL,
    deadline DATE,
    status TEXT NOT NULL,
    started TIMESTAMP,
    completed TIMESTAMP,
    project_id INTEGER REFERENCES Projects(project_id) ON DELETE CASCADE,
    assignee_id INTEGER REFERENCES Users(user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_id INTEGER REFERENCES Tasks(task_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES Users(user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS TeamMembers (
    team_member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES Projects(project_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES Users(user_id)
)
''')

# Lisää admin-käyttäjä (vain kerran)
cursor.execute('''
INSERT OR IGNORE INTO Users (username, password, role)
VALUES ('Admin', 'SaunakangasAdminKirkkoaho', 'admin')
''')

# Tallenna muutokset ja sulje yhteys
conn.commit()
conn.close()