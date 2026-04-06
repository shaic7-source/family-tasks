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
for k in ['msg_time', 'msg_task', 'msg_approve', 'msg_pele']:
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
.pele-card {
    background: #fff3cd; 
    padding: 20px; 
    border-radius: 20px; 
    border: 3px dashed #ff9f43; 
    margin: 20px 0;
    color: #856404;
    font-size: 1.1rem;
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
    "personal": {"ספורט": 10, "עבודה": 10, "קריאה": 10},
    "home": {"מדיח": 15, "ניקוי שיש": 15, "כביסה": 15, "טאטוא בית": 15, "פינוי זבל": 15, "בישול": 15, "סידור חדר": 15}
}
DATA_FILE = 'family_data.json'

def generate_pele_response(name, task_name):
    """מחולל תגובה יצירתית מפלא התוכי"""
    role_desc = "אבא" if name == "שי" else "אמא" if name == "ענבל" else "ילד" if name == "בארי" else "ילדה בת 9"
    prompt = f"""
    אתה 'פלא', תוכי חכם, מצחיק ומעודד שחי עם משפחת פלא.
    המשתמש {name} (שהוא {role_desc}) סיים הרגע את המשימה: {task_name}.
    כתוב תגובה קצרה (2-3 משפטים) הכוללת:
    1. מחמאה יצירתית ומקורית מאוד.
    2. פרט מצחיק על תחביב חדש שהמצאת לעצמך (למשל: איסוף כפיות, לימוד שחמט לנמלים).
    3. בדיחת קרש קצרה שמתאימה לילדים.
    דגשים חשובים:
    - אל תזכיר חזרה מהשכנים.
    - פנה ל{name} בצורה מתאימה (זכר/נקבה/גיל).
    - טון דיבור: חביב, ענייני ולא מתלהם.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"כל הכבוד {name}! אני בדיוק מנסה ללמד את הכרית שלי לעשות סלטה. בדיחה: מה עושה עץ שרוצה ללכת? שורש!"

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

    # הצגת תגובה מפלא אם קיימת
    if st.session_state.msg_pele:
        st.markdown(f"""<div class="pele-card"><b>🦜 פלא אומר:</b><br>{st.session_state.msg_pele}</div>""", unsafe_allow_html=True)
        if st.button("תודה פלא!"):
            st.session_state
