import streamlit as st
from datetime import datetime
import sqlite3
import pandas as pd
import plotly.express as px

# Yhdistä tietokantaan
conn = sqlite3.connect('project_manager.db')
cursor = conn.cursor()

# Alusta session state
if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

if 'show_add_project_page' not in st.session_state:
    st.session_state.show_add_project_page = False

if 'show_add_task_page' not in st.session_state:
    st.session_state.show_add_task_page = False

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'show_add_user_page' not in st.session_state:
    st.session_state.show_add_user_page = False

# Käyttäjäroolit ja oikeudet
USER_ROLES = {
    "admin": ["lisää_projekti", "poista_projekti", "lisää_tehtävä", "muokkaa_tehtävä", "lisää_kommentti", "lisää_käyttäjä"],
    "projektipäällikkö": ["lisää_tehtävä", "muokkaa_tehtävä", "lisää_kommentti"],
    "tiimin_jäsen": ["lisää_kommentti"]
}

# Funktio käyttäjän lisäämiseksi
def add_user(name, email, password, role):
    if name and email and password and role:
        cursor.execute('''
            INSERT INTO Users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', (name, email, password, role))
        conn.commit()
        st.success(f"Käyttäjä {name} lisätty onnistuneesti!")
        st.session_state.show_add_user_page = False

# Funktio käyttäjän kirjautumiseen
def login(email, password):
    cursor.execute('SELECT user_id, name, role FROM Users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    if user:
        st.session_state.current_user = user[0]  # Tallenna käyttäjän ID
        st.session_state.logged_in = True
        st.success(f"Kirjauduttu sisään käyttäjällä {user[1]} ({user[2]})")
    else:
        st.error("Väärä sähköposti tai salasana")

# Funktio projektin lisäämiseksi
def add_project(project_name, priority, deadline, created_by):
    if project_name:
        cursor.execute('''
            INSERT INTO Projects (project_name, priority, deadline, created_by)
            VALUES (?, ?, ?, ?)
        ''', (project_name, priority, deadline, created_by))
        conn.commit()
        st.session_state.show_add_project_page = False

# Funktio tehtävän lisäämiseksi
def add_task(project_id, task_name, priority, deadline, assignee_id, assignee_type="user"):
    if task_name:
        cursor.execute('''
            INSERT INTO Tasks (task_name, priority, deadline, status, project_id, assignee_id, assignee_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task_name, priority, deadline, "Aloittamatta", project_id, assignee_id, assignee_type))
        conn.commit()
        st.session_state.show_add_task_page = False

# Funktio tehtävän tilan päivittämiseksi
def update_task_status(task_id, new_status):
    if new_status == "Työn alla":
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('UPDATE Tasks SET status = ?, started = ? WHERE task_id = ?', (new_status, started, task_id))
    elif new_status == "Tehtävä suoritettu":
        completed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('UPDATE Tasks SET status = ?, completed = ? WHERE task_id = ?', (new_status, completed, task_id))
    else:
        cursor.execute('UPDATE Tasks SET status = ? WHERE task_id = ?', (new_status, task_id))
    conn.commit()

# Funktio kommentin lisäämiseksi
def add_comment(task_id, comment):
    if comment:
        cursor.execute('''
            INSERT INTO Comments (comment_text, task_id, user_id)
            VALUES (?, ?, ?)
        ''', (comment, task_id, st.session_state.current_user))
        conn.commit()

# Funktio projektin tilastojen näyttämiseksi
def show_project_stats(project_id):
    st.write("### Projektin tilastot")

    # Tehtävien tilastot
    cursor.execute('SELECT status, COUNT(*) FROM Tasks WHERE project_id = ? GROUP BY status', (project_id,))
    status_data = cursor.fetchall()
    if status_data:
        df_status = pd.DataFrame(status_data, columns=["Status", "Määrä"])
        fig_status = px.pie(df_status, values="Määrä", names="Status", title="Tehtävien tilat", 
                            color="Status", color_discrete_map={"Aloittamatta": "red", "Työn alla": "yellow", "Tehtävä suoritettu": "green"})
        st.plotly_chart(fig_status)
    else:
        st.write("Ei tehtäviä tilastoitavaksi.")

    # Tehtävien määräaikojen jakauma
    cursor.execute('SELECT deadline FROM Tasks WHERE project_id = ?', (project_id,))
    deadline_data = cursor.fetchall()
    if deadline_data:
        df_deadlines = pd.DataFrame(deadline_data, columns=["Määräaika"])
        df_deadlines["Määräaika"] = pd.to_datetime(df_deadlines["Määräaika"])
        fig_deadlines = px.histogram(df_deadlines, x="Määräaika", title="Tehtävien määräaikojen jakauma")
        st.plotly_chart(fig_deadlines)
    else:
        st.write("Ei määräaikoja tilastoitavaksi.")

# Kirjautumissivu
if not st.session_state.logged_in:
    st.title("Kirjaudu sisään")
    email = st.text_input("Sähköposti")
    password = st.text_input("Salasana", type="password")
    if st.button("Kirjaudu sisään"):
        login(email, password)
    st.stop()

# Sivuvalikko
st.sidebar.title("Toiminnot")
if st.sidebar.button("Kirjaudu ulos"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

if st.session_state.current_user:
    # Hae käyttäjän rooli
    cursor.execute('SELECT role FROM Users WHERE user_id = ?', (st.session_state.current_user,))
    user_role = cursor.fetchone()[0]

    if "lisää_projekti" in USER_ROLES[user_role]:
        if st.sidebar.button("Lisää projekti"):
            st.session_state.show_add_project_page = True

    if "poista_projekti" in USER_ROLES[user_role]:
        if st.sidebar.button("Poista projekti"):
            if st.session_state.selected_project:
                cursor.execute('DELETE FROM Projects WHERE project_id = ?', (st.session_state.selected_project,))
                conn.commit()
                st.session_state.selected_project = None
                st.rerun()

    if "lisää_käyttäjä" in USER_ROLES[user_role]:
        if st.sidebar.button("Lisää käyttäjä"):
            st.session_state.show_add_user_page = True

# Väliaikainen sivu käyttäjän lisäämiseksi
if st.session_state.show_add_user_page:
    st.title("Lisää uusi käyttäjä")
    name = st.text_input("Nimi")
    email = st.text_input("Sähköposti")
    password = st.text_input("Salasana", type="password")
    role = st.selectbox("Rooli", list(USER_ROLES.keys()))
    if st.button("Tallenna käyttäjä"):
        if name and email and password and role:  # Tarkista, että kaikki kentät on täytetty
            add_user(name, email, password, role)
        else:
            st.error("Täytä kaikki kentät!")
    if st.button("Peruuta"):
        st.session_state.show_add_user_page = False
    st.stop()

# Väliaikainen sivu projektin lisäämiseksi
if st.session_state.show_add_project_page:
    st.title("Lisää uusi projekti")
    project_name = st.text_input("Anna projektin nimi:")
    priority = st.selectbox("Prioriteetti", ["Korkea", "Keski", "Matala"])
    deadline = st.date_input("Määräaika")
    created_by = st.session_state.current_user

    # Lisää tiimin jäsenet
    cursor.execute('SELECT user_id, name FROM Users')
    users = cursor.fetchall()
    team_members = st.multiselect("Valitse tiimin jäsenet", [f"{user[1]} (ID: {user[0]})" for user in users])

    if st.button("Tallenna projekti"):
        add_project(project_name, priority, deadline, created_by)
        # Lisää tiimin jäsenet TeamMembers-tauluun
        project_id = cursor.lastrowid  # Viimeisin lisätty project_id
        for member in team_members:
            user_id = int(member.split("(ID: ")[1].replace(")", ""))  # Poimi user_id
            cursor.execute('INSERT INTO TeamMembers (project_id, user_id) VALUES (?, ?)', (project_id, user_id))
        conn.commit()
        st.session_state.show_add_project_page = False
    if st.button("Peruuta"):
        st.session_state.show_add_project_page = False
    st.stop()

# Pääsivu
st.title("Projektien Seuranta")

# Näytä projektilista
cursor.execute('SELECT project_id, project_name FROM Projects')
projects = cursor.fetchall()
if not projects:
    st.write("Ei käynnissä olevia projekteja.")
else:
    st.write("### Käynnissä olevat projektit:")
    # Järjestä projektinapit vierekkäin (5 per rivi)
    cols = st.columns(5)  # Luo 5 saraketta
    for i, (project_id, project_name) in enumerate(projects):
        with cols[i % 5]:  # Käytä saraketta modulo 5:llä
            if st.button(project_name, key=f"project_{project_id}"):
                st.session_state.selected_project = project_id

# Näytä valitun projektin tiedot
if st.session_state.selected_project:
    cursor.execute('SELECT * FROM Projects WHERE project_id = ?', (st.session_state.selected_project,))
    project = cursor.fetchone()
    st.write(f"### Valittu projekti: {project[1]}")

    # Näytä tiimin jäsenet
    st.write("#### Tiimin jäsenet:")
    cursor.execute('''
        SELECT Users.name FROM TeamMembers
        JOIN Users ON TeamMembers.user_id = Users.user_id
        WHERE TeamMembers.project_id = ?
    ''', (st.session_state.selected_project,))
    team_members = cursor.fetchall()
    for member in team_members:
        st.write(f"- {member[0]}")

    # Lisää tehtävä -nappi tiimijäsenten alle
    if "lisää_tehtävä" in USER_ROLES[user_role]:
        if st.button("Lisää tehtävä", key="add_task_button"):
            st.session_state.show_add_task_page = True

    # Väliaikainen sivu tehtävän lisäämiseksi
    if st.session_state.show_add_task_page:
        st.title("Lisää uusi tehtävä")
        
        # Lomake tehtävän tiedoille
        with st.form("add_task_form"):
            task_name = st.text_input("Tehtävän nimi")
            priority = st.selectbox("Prioriteetti", ["Korkea", "Keski", "Matala"])
            deadline = st.date_input("Määräaika")
            
            # Hae käyttäjät, joille tehtävä voidaan määrittää
            cursor.execute('SELECT user_id, name FROM Users')
            users = cursor.fetchall()
            assignee_id = st.selectbox("Tekijä", [f"{user[1]} (ID: {user[0]})" for user in users])
            
            # Lisää tehtävä -painike
            if st.form_submit_button("Lisää tehtävä"):
                if task_name:
                    # Poimi assignee_id käyttäjän valinnasta
                    assignee_id = int(assignee_id.split("(ID: ")[1].replace(")", ""))
                    
                    # Lisää tehtävä tietokantaan
                    add_task(st.session_state.selected_project, task_name, priority, deadline, assignee_id)
                    st.success("Tehtävä lisätty onnistuneesti!")
                    st.session_state.show_add_task_page = False  # Sulje lomake
                else:
                    st.error("Anna tehtävän nimi!")
            
            # Sulje ikkuna -nappi
            if st.form_submit_button("Sulje"):
                st.session_state.show_add_task_page = False

    # Välilehtivalikko
    tab1, tab2 = st.tabs(["Tehtävät", "Projektin tilastot"])

    with tab1:  # Tehtävät-välilehti
        # Tehtävien suodatus ja lajittelu
        st.write("### Tehtävät")
        filter_status = st.selectbox("Suodata tilan mukaan", ["Kaikki", "Aloittamatta", "Työn alla", "Tehtävä suoritettu"])
        sort_option = st.selectbox("Lajittele", ["Määräaika", "Prioriteetti"])

        query = 'SELECT * FROM Tasks WHERE project_id = ?'
        if filter_status != "Kaikki":
            query += f" AND status = '{filter_status}'"
        if sort_option == "Määräaika":
            query += ' ORDER BY deadline'
        elif sort_option == "Prioriteetti":
            query += ' ORDER BY priority'

        cursor.execute(query, (st.session_state.selected_project,))
        tasks = cursor.fetchall()

        # Näytä tehtävät
        for task in tasks:
            task_id, task_name, priority, deadline, status, started, completed, project_id, assignee_id, assignee_type = task
            status_color = {
                "Aloittamatta": "red",
                "Työn alla": "yellow",
                "Tehtävä suoritettu": "green"
            }.get(status, "gray")

            # Näytä tehtävän nimi ja tila (ilman tekijää ja tyyppiä)
            st.markdown(
                f"""
                <div style="display: flex; align-items: center;">
                    <div style="width: 10px; height: 10px; border-radius: 50%; background-color: {status_color}; margin-right: 10px;"></div>
                    <div>{task_name} - {status}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.expander("Näytä tiedot"):
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    # Hae tekijän nimi
                    cursor.execute('SELECT name FROM Users WHERE user_id = ?', (assignee_id,))
                    assignee_name = cursor.fetchone()[0]
                    st.write(f"**Tekijä:** {assignee_name}")  # Tekijä-tiedot expanderin sisällä
                    st.write(f"**Prioriteetti:** {priority}")
                    st.write(f"**Määräaika:** {deadline}")
                with col2:
                    if "muokkaa_tehtävä" in USER_ROLES[user_role]:
                        new_status = st.selectbox(
                            "Tila",
                            ["Aloittamatta", "Työn alla", "Tehtävä suoritettu"],
                            index=["Aloittamatta", "Työn alla", "Tehtävä suoritettu"].index(status),
                            key=f"status_{task_id}"
                        )
                        if new_status != status:
                            update_task_status(task_id, new_status)
                            st.rerun()
                with col3:
                    if started:
                        st.write(f"**Aloitettu:** {started}")
                    if completed:
                        st.write(f"**Suoritettu:** {completed}")

                # Kommentit
                st.write("#### Kommentit")
                cursor.execute('SELECT user_id, comment_text, timestamp FROM Comments WHERE task_id = ?', (task_id,))
                comments = cursor.fetchall()
                for comment in comments:
                    cursor.execute('SELECT name FROM Users WHERE user_id = ?', (comment[0],))
                    commenter_name = cursor.fetchone()[0]
                    st.write(f"**{commenter_name}** ({comment[2]}): {comment[1]}")

                # Lisää kommentti
                if "lisää_kommentti" in USER_ROLES[user_role]:
                    new_comment = st.text_input("Lisää kommentti", key=f"comment_{task_id}")
                    if st.button("Tallenna kommentti", key=f"save_comment_{task_id}"):
                        add_comment(task_id, new_comment)
                        st.rerun()

    with tab2:  # Projektin tilastot-välilehti
        show_project_stats(st.session_state.selected_project)
