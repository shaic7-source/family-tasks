import streamlit as st
import json
import os
import time
from datetime import datetime
import google.generativeai as genai

# הגדרות API
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

for k in ['msg_time', 'msg_task', 'msg_approve', 'msg_comp']:
    if k not in st.session_state:
        st.session_state[k] = None

# עדכון העיצוב לתיקון רקע וטקסט בתיבות בחירה
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #d1e8e2, #fffd8d, #ffc8dd, #90e0ef); 
    direction: rtl;
}
p, div, span, h1, h2, h3, h4, h5, h6, label {
    text-align: right !important; 
    direction: rtl !important; 
    color: black !important;
}
/* כפיית רקע לבן וטקסט שחור על תיבות קלט ורשימות בחירה נפתחות */
input, textarea, div[data-baseweb="select"] > div, ul[role="listbox"], li[role="option"] {
    background-color: white !important; 
    color: black !important;
    text-align: right !important; 
    direction: rtl !important;
}
.stButton>button {
    background-color: #ff9f43 !important; 
    color: white !important; 
    border-radius: 20px; 
    width: 100%; 
    font-weight: bold; 
    height: 3.5rem; 
    border: none;
}
.pele-summary {
    background: white; 
    padding: 20px; 
    border-radius: 20px; 
    border: 5px solid #ff6b6b; 
    color: #333 !important; 
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

USERS = {"שי": "parent", "ענבל": "parent", "בארי": "child", "טנא": "child"}
TASKS_DB = {
    "personal": {"ספורט": 10, "עבודה": 10, "קריאה": 10},
    "home": {"מדיח": 15, "ניקוי שיש": 15, "כביסה": 15, "טאטוא בית": 15, "פינוי זבל": 15, "בישול": 15, "סידור חדר": 15}
}
DATA_FILE = 'family_data.json'

def load_data():
    default_data = {
        "screen_time": {u: 0 for u in USERS}, 
        "tasks_today": [], 
        "compliments": [], 
        "last_date": str(datetime.now().date()), 
        "updates_applied": [],
        "active_stopwatches": {} 
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                for key in default_data:
                    if key in saved: default_data[key] = saved[key]
                return default_data
        except: pass
    return default_data

def save_data(d):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

data = load_data()

# עדכון יתרות חד-פעמי (12 שעות לטנא, 5 שעות לבארי)
if "time_update_april_2026" not in data.get("updates_applied", []):
    data["screen_time"]["טנא"] += 720
    data["screen_time"]["בארי"] += 300
    if "updates_applied" not in data: data["updates_applied"] = []
    data["updates_applied"].append("time_update_april_2026")
    save_data(data)

today_str = str(datetime.now().date())
if data.get("last_date") != today_str:
    data["tasks_today"] = []
    data["compliments"] = []
    data["last_date"] = today_str
    save_data(data)

st.title("🏡 משימות משפחת פלא")
user_select = st.selectbox("מי המשתמש?", [""] + list(USERS.keys()))

if user_select:
    role = USERS[user_select]
    st.subheader(f"שלום {user_select}! 🦜 יתרה: {data['screen_time'][user_select]} דקות")

    # --- סטופר מבוסס ענן למניעת איפוס ביציאה מהאפליקציה ---
    st.subheader("⏱️ סטופר זמן מסך")
    col1, col2 = st.columns(2)
    
    active_watches = data.get("active_stopwatches", {})
    
    if user_select not in active_watches:
        if col1.button("▶️ התחל זמן מסך"):
            if "active_stopwatches" not in data: data["active_stopwatches"] = {}
            data["active_stopwatches"][user_select] = time.time()
            save_data(data)
            st.rerun()
    else:
        start_time = active_watches[user_select]
        elapsed_now = int((time.time() - start_time) / 60)
        st.warning(f"זמן מסך פעיל: כ-{elapsed_now} דקות")
        
        if col2.button("⏹️ עצור ועדכן יתרה"):
            duration_mins = int((time.time() - start_time) / 60)
            if duration_mins < 1: duration_mins = 1 
            data['screen_time'][user_select] -= duration_mins
            del data["active_stopwatches"][user_select]
            save_data(data)
            st.success(f"נוצלו {duration_mins} דקות מהיתרה.")
            st.rerun()

    st.divider()
    
    u_val = st.number_input("ניצול ידני (דקות):", min_value=0, step=1)
    if st.button("עדכן ניצול ידני"):
        data['screen_time'][user_select] -= u_val
        save_data(data)
        st.session_state.msg_time = "הזמן עודכן!"
        st.rerun()

    if st.session_state.msg_time:
        st.success(st.session_state.msg_time); st.session_state.msg_time = None

    st.divider()
    st.subheader("🧹 דיווח על משימה")
    cat_display = st.radio("סוג משימה:", ["משימות אישיות", "משימות בית"], horizontal=True)
    cat_key = "personal" if cat_display == "משימות אישיות" else "home"
    t_list = list(TASKS_DB[cat_key].keys()) + ["אחר"]
    t_choice = st.selectbox("בחר משימה:", t_
