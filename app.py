import streamlit as st
import pandas as pd
import hashlib

st.set_page_config(page_title="College Workload System", layout="wide")

# ---------- DEMO USERS (no timetable roles now) ---------- #

def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

DEMO_USERS = {
    "admin": {"password": hash_pwd("admin"), "role": "Admin"},
}

# ---------- LOAD SIR'S EXCEL ONLY ---------- #

@st.cache_data
def load_work_distribution():
    return pd.read_excel("EVEN-SEM-WORK-DISTRIBUTION-AY-2024-AND-2026.xlsx")

# ---------- SESSION ---------- #

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

st.title("🎓 Even Semester Workload – 2025‑26")

# ---------- LOGIN ---------- #

if st.session_state.user is None:
    st.header("🔐 Admin Login")

    with st.form("login_form"):
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        submitted = st.form_submit_button("🚀 Login")

        if submitted:
            if username in DEMO_USERS and hash_pwd(password) == DEMO_USERS[username]["password"]:
                st.session_state.user = username
                st.session_state.role = DEMO_USERS[username]["role"]
                st.success("Welcome admin!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# ---------- AFTER LOGIN ---------- #

with st.sidebar:
    st.success(f"👋 {st.session_state.user} ({st.session_state.role})")
    page = st.radio("Go to", ["Courses & Modules", "Faculty Workload"])
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

df = load_work_distribution()

if page == "Courses & Modules":
    st.header("📘 Courses, Coordinators & Modules")
    # Assuming first big table is rows 1–43 (you can adjust)
    course_table = df.iloc[:43].copy()
    st.dataframe(course_table, use_container_width=True)

elif page == "Faculty Workload":
    st.header("👩‍🏫 Faculty Workload Summary")
    # Assuming last part of sheet is workload summary
    workload_table = df.iloc[43:].copy()
    st.dataframe(workload_table, use_container_width=True)
