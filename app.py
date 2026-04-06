import streamlit as st
import json
import os
import time
from datetime import datetime
import google.generativeai as genai

# הגדרות API
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

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
.pele-summary {
    background: white; 
    padding: 25px; 
    border-radius: 25px; 
    border: 5px solid #ff6b6b; 
    color: #333 !important; 
    margin-top: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.pele-speech {
    background: #fff3cd;
    border: 2px solid #ff9f43;
    padding: 20px;
    border-radius: 15px;
    margin: 10px 0;
    color: #856404;
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

def generate_pele_feedback(name, task_name, is_summary=False, tasks_list=None):
    """מחולל את כל סוגי התגובות של פלא - עם בדיחות, סיפורים ומעוף"""
    role_desc = "אבא" if name == "שי" else "אמא" if name == "ענבל" else "ילד" if name == "בארי" else "ילדה בת 9"
    
    if is_summary:
        tasks_str = ", ".join([f"{t['user']} שסיים {t['task']}" for t in tasks_list])
        prompt = f"""
        אתה 'פלא', תוכי חכם, צבעוני וקצת משוגע. כתוב סיכום יומי עסיסי למשפחת פלא על המשימות: {tasks_str}.
        דגשים:
        1. כתוב פסקה אחת ארוכה, ציורית ומלאה ב'מעוף'.
        2. המצא סיפור מצחיק על מה עשית היום בזמן שהם עבדו (תחביבים הזויים).
        3. שלב בדיחת קרש אחת מעולה שמתאימה לילדים.
        4. שי הוא האבא, טנא בת 9. פנה אליהם בהתאם.
        5. בלי חזרה מהשכנים.
        """
    else:
        prompt = f"""
        אתה 'פלא', תוכי מפרגן עם חוש הומור מוזר. {name} ({role_desc}) סיים/ה הרגע {task_name}.
        כתוב תגובה קצרה שכוללת:
        1. מחמאה סופר יצירתית ומטאפורית.
        2. בדיחת קרש קצרה ומצחיקה.
        3. עדכון קצר על תחביב חדש שהמצאת לעצמך הרגע.
        בלי שכנים. פנה במין הנכון.
        """
    
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"{name}, אתה פשוט פלא! (והייתי מספר בדיחה אבל נתקע לי גרעין בגרון)."

def load_data():
    default_data = {"screen_time": {u: 0 for u in USERS}, "tasks_today": [], "last_date": str(datetime.now().date()), "active_stopwatches": {}}
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
    if user_select in active_watches:
        elapsed = int((time.time() - active_watches[user_select]) / 60)
        st.warning(f"זמן מסך פעיל: {elapsed} דקות")
        if col2.button("⏹️ עצור ועדכן"):
            data['screen_time'][user_select] -= max(1, elapsed)
            data["active_stopwatches"].pop(user_select, None)
            save_data(data)
            st.rerun()
    elif col1.button("▶️ התחל זמן מסך"):
        data["active_stopwatches"][user_select] = time.time()
        save_data(data)
        st.rerun()

    st.divider()
    
    # --- דיווח משימות ---
    st.subheader("🧹 דיווח על משימה")
    cat_display = st.radio("סוג משימה:", ["משימות אישיות", "משימות בית"], horizontal=True)
    cat_key = "personal" if cat_display == "משימות אישיות" else "home"
    t_choice = st.selectbox("בחר משימה:", list(TASKS_DB[cat_key].keys()) + ["אחר"])
    c_name = st.text_input("שם המשימה:") if t_choice == "אחר" else ""

    if st.button("סיימתי! ✨"):
        f_name = c_name if t_choice == "אחר" else t_choice
        if f_name:
            reward = TASKS_DB[cat_key].get(t_choice, 15)
            status = "approved" if role == "parent" else "pending"
            
            # תגובה מיידית מפלא
            feedback = generate_pele_feedback(user_select, f_name)
            
            new_task = {"id": time.time(), "user": user_select, "task": f_name, "reward": reward, "status": status, "time": datetime.now().strftime("%H:%M")}
            data["tasks_today"].append(new_task)
            if status == "approved": data['screen_time'][user_select] += reward
            
            st.session_state.msg_task = feedback
            save_data(data)
            st.rerun()

    if st.session_state.msg_task:
        st.markdown(f'<div class="pele-speech"><b>🦜 פלא אומר:</b><br>{st.session_state.msg_task}</div>', unsafe_allow_html=True)
        if st.button("תודה פלא!"):
            st.session_state.msg_task = None
            st.rerun()

    st.divider()

    # --- אישור משימות (הורים) ---
    if role == "parent":
        st.subheader("📋 אישור משימות ילדים")
        pending = [t for t in data["tasks_today"] if t.get("status") == "pending"]
        for task in pending:
            with st.container():
                st.markdown(f'<div class="task-card"><b>{task["user"]}</b>: {task["task"]}</div>', unsafe_allow_html=True)
                c_aprv, c_rej = st.columns(2)
                if c_aprv.button(f"✅ אשר ל{task['user']}", key=f"aprv_{task['id']}"):
                    for t in data["tasks_today"]:
                        if t.get("id") == task["id"]: t["status"] = "approved"
                    data["screen_time"][task["user"]] += task["reward"]
                    save_data(data)
                    st.rerun()
                if c_rej.button(f"❌ דחה", key=f"rej_{task['id']}"):
                    data["tasks_today"] = [t for t in data["tasks_today"] if t.get("id") != task["id"]]
                    save_data(data)
                    st.rerun()

    # --- סיכום יומי של פלא (המלא והמצחיק) ---
    approved_tasks = [t for t in data["tasks_today"] if t['status'] == 'approved']
    if approved_tasks:
        st.subheader("🦜 סיכום היום של פלא")
        if st.button("🔄 רענן סיכום יצירתי"):
            st.session_state.daily_summary = generate_pele_feedback("משפחה", "", is_summary=True, tasks_list=approved_tasks)
            st.rerun()
        
        if "daily_summary" not in st.session_state:
            st.session_state.daily_summary = generate_pele_feedback("משפחה", "", is_summary=True, tasks_list=approved_tasks)
        
        st.markdown(f'<div class="pele-summary">{st.session_state.daily_summary}</div>', unsafe_allow_html=True)
