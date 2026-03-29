import streamlit as st
import json
import os
from datetime import datetime
import google.generativeai as genai

# --- הגדרות API ---
GEMINI_API_KEY = "AIzaSyDSd9qQCtjQTDpCPGnMyLy6RssIHJ3feEI"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- אתחול הודעות ---
for key in ['msg_time', 'msg_task', 'msg_approve', 'msg_comp']:
    if key not in st.session_state:
        st.session_state[key] = None

# --- עיצוב ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #d1e8e2, #fffd8d, #ffc8dd, #90e0ef); direction: rtl; }
    p, div, span, h1, h2, h3, h4, h5, h6, label, input, textarea { text-align: right !important; direction: rtl !important; }
    .stButton>button { background-color: #ff9f43; color: white; border-radius: 20px; width: 100%; font-weight: bold; }
    .pele-summary { background: white; padding: 20px; border-radius: 20px; border: 4px solid #ff6b6b; margin-top: 20px; color: black; }
</style>
""", unsafe_allow_html=True)

# --- נתונים ---
DATA_FILE = 'family_data.json'
USERS = {"שי": "parent", "ענבל": "parent", "בארי": "child", "טנא": "child"}
TASKS_DB = {
    "משימות אישיות": {"ספורט": 10, "עבודה": 10, "קריאה": 10},
    "משימות בית": {"מדיח": 15, "ניקוי שיש": 15, "כביסה": 15, "טאטוא בית": 15, "פינוי זבל": 15, "בישול": 15, "סידור חדר": 15}
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"screen_time": {u: 0 for u in USERS}, "tasks_today": [], "compliments": [], "last_date": str(datetime.now().date())}

def save_data(d):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

data = load_data()
if data["last_date"] != str(datetime.now().date()):
    data.update({"tasks_today": [], "compliments": [], "last_date": str(datetime.now().date())})
    save_data(data)

# --- ממשק ---
st.title("🏡 משימות משפחת פלא")
user = st.selectbox("מי אתה?", [""] + list(USERS.keys()))

if user:
    role = USERS[user]
    st.subheader(f"שלום {user}! 🦜 זמן מסך: {data['screen_time'][user]} דקות")
    
    # זמן מסך
    used = st.number_input("דקות שנוצלו:", min_value=0, step=1)
    if st.button("עדכן ניצול"):
        data['screen_time'][user] -= used
        save_data(data)
        st.session_state.msg_time = "עודכן בהצלחה!"
        st.rerun()
    if st.session_state.msg_time:
        st.success(st.session_state.msg_time)
        st.session_state.msg_time = None

    st.divider()
    
    # משימות
    cat = st.radio("סוג משימה:", ["משימות אישיות", "משימות בית"])
    opts = list(TASKS_DB[cat].keys()) + ["אחר"]
    t_name = st.selectbox("משימה:", opts)
    custom = st.text_input("שם המשימה:") if t_name == "אחר" else ""
    
    if st.button("סיימתי! ✨"):
        final_name = custom if t_name == "אחר" else t_name
        if final_name:
            val = 10 if cat == "משימות אישיות" else 15
            status = "approved" if role == "parent" else "pending"
            data["tasks_today"].append({"user": user, "task": final_name, "reward": val, "status": status})
            if role == "parent":
                data['screen_time'][user] += val
                st.session_state.msg_task = f"נוספו {val} דקות!"
            else:
                st.session_state.msg_task = "נשלח לאישור הורה."
            save_data(data)
            st.rerun()
    if st.session_state.msg_task:
        st.success(st.session_state.msg_task)
        st.session_state.msg_task = None

    st.divider()

    # אישור הורים
    if role == "parent":
        st.subheader("👀 אישור משימות")
        pending = [t for t in data["tasks_today"] if t["status"] == "pending"]
        for i, t in enumerate(pending):
            if st.button(f"אשר ל{t['user']}: {t['task']}", key=f"app_{i}"):
                t["status"] = "approved"
                data['screen_time'][t['user']] += t['reward']
                save_data(data)
                st.session_state.msg_approve = "אושר!"
                st.rerun()
        if st.session_state.msg_approve:
            st.success(st.session_state.msg_approve)
            st.session_state.msg_approve = None

    # פירגון
    target = st.selectbox("למי לפרגן?", [u for u in USERS if u != user])
    txt = st.text_area("מה לכתוב?")
    if st.button("שלח פירגון ❤️"):
        if txt:
            data["compliments"].append({"from": user, "to": target, "text": txt})
            save_data(data)
            st.session_state.msg_comp = "הפירגון נשמר!"
            st.rerun()
    if st.session_state.msg_comp:
        st.success(st.session_state.msg_comp)
        st.session_state.msg_comp = None

    st.divider()

    # סיכום פלא
    if st.button("הכן סיכום יומי 🦜"):
        with st.spinner("פלא חושב..."):
            tasks_txt = "\n".join([f"{u}: {len([t for t in data['tasks_today'] if t['user']==u and t['status']=='approved'])} משימות" for u in USERS])
            comps_txt = "\n".join([f"{c['from']} ל{c['to']}: {c['text']}" for c in data["compliments"]]) or "אין פירגונים."
            
            p = f"אתה פלא התוכי הגרינצ'יק. סכם את היום של משפחת כהן (שי, ענבל, בארי, טנא) בצורה מצחיקה וחצופה.\nנתונים:\n{tasks_txt}\nפירגונים:\n{comps_txt}"
            try:
                res = model.generate_content(p)
                st.markdown(f'<div class="pele-summary"><h3>🦜 פלא אומר:</h3>{res.text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error("פלא נרדם... נסה שוב.")