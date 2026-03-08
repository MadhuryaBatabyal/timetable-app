import pandas as pd
from collections import defaultdict

# --------- PARAMETERS YOU CAN TUNE --------- #

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
# 11 hourly slots from sir's 08:40–17:30 structure
SLOTS = [
    "08:40-09:30",
    "09:30-10:20",
    "10:20-11:10",
    "11:10-11:40",  # break
    "11:40-12:30",
    "12:30-01:20",
    "01:20-02:10",
    "02:10-03:00",
    "03:00-03:50",
    "03:50-04:40",
    "04:40-05:30",
]

BREAK_SLOT = "11:10-11:40"  # keep always free for all

# Section you want to generate timetable for
TARGET_SECTION = "BSDA-II"

# --------- LOAD COURSES --------- #

courses = pd.read_csv("courses.csv")

# Filter by section
courses = courses[courses["section"] == TARGET_SECTION].copy()

# Map each course to required classes/week based on credits & type
def classes_per_week(row):
    if row["type"].lower() == "theory":
        return row["credits"]
    else:  # lab
        # each lab class is 2 hours -> credits classes/week
        return row["credits"]

courses["classes_per_week"] = courses.apply(classes_per_week, axis=1)

# Expand into a list of "class units" to be scheduled
to_schedule = []
for _, row in courses.iterrows():
    for i in range(row["classes_per_week"]):
        to_schedule.append({
            "course_code": row["course_code"],
            "course_title": row["course_title"],
            "type": row["type"],
        })

# --------- BUILD EMPTY TIMETABLE GRID --------- #

timetable = {day: {slot: "" for slot in SLOTS} for day in DAYS}

# Always mark break slot
for day in DAYS:
    timetable[day][BREAK_SLOT] = "BREAK"

# To avoid same subject back-to-back in a day
def can_place(day, slot, course_code):
    if timetable[day][slot] not in ("", "BREAK"):
        return False
    # Check previous slot
    idx = SLOTS.index(slot)
    if idx > 0:
        prev_slot = SLOTS[idx - 1]
        if timetable[day][prev_slot].startswith(course_code):
            return False
    return True

# --------- SIMPLE GREEDY SCHEDULER --------- #

for cls in to_schedule:
    placed = False
    for day in DAYS:
        if placed:
            break
        # For labs, try to place in two consecutive slots (2-hour block)
        if cls["type"].lower() == "lab":
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
            # theory: single slot
            for slot in SLOTS:
                if slot == BREAK_SLOT:
                    continue
                if can_place(day, slot, cls["course_code"]):
                    timetable[day][slot] = cls["course_code"]
                    placed = True
                    break
    if not placed:
        print(f"WARNING: could not place {cls['course_code']} all required times.")

# --------- EXPORT AS DATAFRAME --------- #

rows = []
for day in DAYS:
    for slot in SLOTS:
        rows.append({
            "day": day,
            "time": slot,
            "course": timetable[day][slot],
        })

df_tt = pd.DataFrame(rows)
print(df_tt)

# Save to CSV for app/frontend
df_tt.to_csv(f"generated_timetable_{TARGET_SECTION}.csv", index=False)
print(f"\nSaved to generated_timetable_{TARGET_SECTION}.csv")
