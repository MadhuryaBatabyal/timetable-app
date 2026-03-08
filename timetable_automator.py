import streamlit as st
import pandas as pd

# ---------- CONFIG ---------- #

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
SLOTS = [
    "08:40-09:30",
    "09:30-10:20",
    "10:20-11:10",
    "11:10-11:40",   # break
    "11:40-12:30",
    "12:30-01:20",
    "01:20-02:10",
    "02:10-03:00",
    "03:00-03:50",
    "03:50-04:40",
    "04:40-05:30",
]
BREAK_SLOT = "11:10-11:40"

st.set_page_config(page_title="Simple Timetable Automator", layout="wide")
st.title("📅 Simple Timetable Automator")

st.write("Uses credit rules: theory credits = classes/week, lab credits = 2‑hour blocks per week.")

@st.cache_data
def load_courses():
    return pd.read_csv("courses.csv")

def classes_per_week(row):
    t = row["type"].lower()
    credits = int(row["credits"])
    if t == "theory":
        return credits          # 1 hr each
    else:
        return credits          # each class is 2 hr block

def generate_timetable(section):
    courses = load_courses()
    courses = courses[courses["section"] == section].copy()
    if courses.empty:
        return None, "No courses found for this section in courses.csv"

    courses["classes_per_week"] = courses.apply(classes_per_week, axis=1)

    # expand into class units
    to_schedule = []
    for _, row in courses.iterrows():
        for _ in range(row["classes_per_week"]):
            to_schedule.append({
                "course_code": row["course_code"],
                "course_title": row["course_title"],
                "type": row["type"].lower(),
            })

    # empty grid
    timetable = {day: {slot: "" for slot in SLOTS} for day in DAYS}
    for day in DAYS:
        timetable[day][BREAK_SLOT] = "BREAK"

    def can_place(day, slot, code):
        if timetable[day][slot] not in ("", "BREAK"):
            return False
        idx = SLOTS.index(slot)
        if idx > 0:
            prev = SLOTS[idx - 1]
            if timetable[day][prev].startswith(code):
                return False
        return True

    # greedy scheduler
    warnings = []
    for cls in to_schedule:
        placed = False
        for day in DAYS:
            if placed:
                break
            if cls["type"] == "lab":
                for i in range(len(SLOTS) - 1):
                    s1, s2 = SLOTS[i], SLOTS[i + 1]
                    if BREAK_SLOT in (s1, s2):
                        continue
                    if can_place(day, s1, cls["course_code"]) and can_place(day, s2, cls["course_code"]):
                        timetable[day][s1] = f"{cls['course_code']} (LAB)"
                        timetable[day][s2] = f"{cls['course_code']} (LAB)"
                        placed = True
                        break
            else:
                for slot in SLOTS:
                    if slot == BREAK_SLOT:
                        continue
                    if can_place(day, slot, cls["course_code"]):
                        timetable[day][slot] = cls["course_code"]
                        placed = True
                        break
        if not placed:
            warnings.append(f"Could not place all classes for {cls['course_code']}")

    # convert to DataFrame
    rows = []
    for day in DAYS:
        for slot in SLOTS:
            rows.append({"Day": day, "Time": slot, "Course": timetable[day][slot]})
    df = pd.DataFrame(rows)
    return df, "\n".join(warnings) if warnings else None

# ---------- UI ---------- #

courses = load_courses()
sections = sorted(courses["section"].unique())
section = st.selectbox("Select Section / Program", sections)

if st.button("Generate Timetable"):
    df_tt, warn = generate_timetable(section)
    if df_tt is None:
        st.error(warn)
    else:
        if warn:
            st.warning(warn)
        st.subheader(f"Generated Timetable – {section}")
        st.dataframe(df_tt, use_container_width=True)

        csv = df_tt.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download as CSV",
            data=csv,
            file_name=f"generated_timetable_{section}.csv",
            mime="text/csv",
        )

st.markdown("----")
st.subheader("📘 Courses loaded from courses.csv")
st.dataframe(courses, use_container_width=True)
