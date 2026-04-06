import streamlit as st
import json
import os
import time
from datetime import datetime

# אתחול Session State
for k in ['msg_time', 'msg_task', 'msg_approve']:
    if k not in st.session_state:
        st.session_state[k] = None

# עיצוב ה-UI
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
.stButton>button {
    background-color: #ff9f43 !important; 
    color: white !important; 
    border-radius: 20px; 
    width: 100%; 
    font-weight: bold; 
    height: 3.5rem;
}
.task-card {
    background: white; 
    padding: 15px; 
    border-radius: 15px; 
    border-right: 10px solid #ff6b6b; 
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

USERS = {"שי": "parent", "ענבל": "parent", "בארי": "child", "טנא": "child"}
TASKS_DB = {
    "personal": {"תפילה": 10, "ספורט": 10, "עבודה": 10, "קריאה": 10},
    "home": {"מדיח": 15, "ניקוי שיש": 15, "כביסה": 15, "טאטוא בית": 15, "פינוי זבל": 15, "בישול": 15, "סידור חדר": 15}
}
DATA_FILE = 'family_data.json'

def load_data():
    default_data = {
        "screen_time": {u: 0 for u in USERS}, 
        "tasks_today": [], 
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
        except: return default_data
    return default_data

def save_data(d):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

data = load_data()

# איפוס יומי
today_str = str(datetime.now().date())
if data.get("last_date") != today_str:
    data["tasks_today"] = []
    data["last_date"] = today_str
    save_data(data)

st.title("🏡 משימות משפחת פלא")
user_select = st.selectbox("מי המשתמש?", [""] + list(USERS.keys()))

if user_select:
    role = USERS[user_select]
    st.subheader(f"שלום {user_select}! 🦜 יתרה: {data['screen_time'].get(user_select, 0)} דקות")

    # --- סטופר ---
    st.subheader("⏱️ סטופר זמן מסך")
    col1, col2 = st.columns(2)
    active_watches = data.setdefault("active_stopwatches", {})
    
    if user_select not in active_watches:
        if col1.button("▶️ התחל זמן מסך"):
            data["active_stopwatches"][user_select] = time.time()
            save_data(data)
            st.rerun()
    else:
        elapsed = int((time.time() - active_watches[user_select]) / 60)
        st.warning(f"זמן מסך פעיל: {elapsed} דקות")
        if col2.button("⏹️ עצור ועדכן"):
            data['screen_time'][user_select] -= max(1, elapsed)
            data["active_stopwatches"].pop(user_select, None)
            save_data(data)
            st.rerun()

    st.divider()
    
    # --- דיווח משימות ---
    st.subheader("🧹 דיווח על משימה")
    cat_display = st.radio("סוג משימה:", ["משימות אישיות", "משימות בית"], horizontal=True)
    cat_key = "personal" if cat_display == "משימות אישיות" else "home"
    t_list = list(TASKS_DB[cat_key].keys()) + ["אחר"]
    t_choice = st.selectbox("בחר משימה:", t_list)
    c_name = st.text_input("שם המשימה:") if t_choice == "אחר" else ""

    if st.button("סיימתי! ✨"):
        f_name = c_name if t_choice == "אחר" else t_choice
        if f_name:
            reward = TASKS_DB[cat_key].get(t_choice, 15)
            status = "approved" if role == "parent" else "pending"
            
            new_task = {
                "id": time.time(), "user": user_select, "task": f_name,
                "reward": reward, "status": status, "time": datetime.now().strftime("%H:%M")
            }
            data["tasks_today"].append(new_task)
            
            if status == "approved":
                data['screen_time'][user_select] += reward
            
            save_data(data)
            st.rerun()

    st.divider()

    # --- אישור משימות (הורים) ---
    if role == "parent":
        st.subheader("📋 אישור משימות ילדים")
        pending = [t for t in data["tasks_today"] if t.get("status") == "pending"]
        
        if not pending:
            st.info("אין משימות הממתינות לאישור.")
            
        for task in pending:
            with st.container():
                st.markdown(f'<div class="task-card"><b>{task["user"]}</b>: {task["task"]} ({task["reward"]} דק\')</div>', unsafe_allow_html=True)
                c_aprv, c_rej = st.columns(2)
                
                if c_aprv.button(f"✅ אשר ל{task['user']}", key=f"aprv_{task['id']}"):
                    for t in data["tasks_today"]:
                        if t.get("id") == task["id"]: t["status"] = "approved"
                    data["screen_time"][task["user"]] += task["reward"]
                    save_data(data)
                    st.rerun()
                
                if c_rej.button(f"❌ אל תאשר", key=f"rej_{task['id']}"):
                    data["tasks_today"] = [t for t in data["tasks_today"] if t.get("id") != task["id"]]
                    save_data(data)
                    st.rerun()

    # --- היסטוריה יומית ---
    st.subheader("✅ מה עשינו היום")
    if not data["tasks_today"]:
        st.write("עוד לא בוצעו משימות היום.")
    for t in data["tasks_today"]:
        st.write(f"{'✔️' if t['status']=='approved' else '⏳'} {t['user']}: {t['task']}")
