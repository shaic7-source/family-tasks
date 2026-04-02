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

st.markdown("<style>.stApp{background: linear-gradient(135deg, #d1e8e2, #fffd8d, #ffc8dd, #90e0ef); direction: rtl;} p,div,span,h1,h2,h3,h4,h5,h6,label,input,textarea{text-align: right !important; direction: rtl !important;} .stButton>button{background-color: #ff9f43; color: white; border-radius: 20px; width: 100%; font-weight: bold; height: 3.5rem; border: none;} .pele-summary{background: white; padding: 20px; border-radius: 20px; border: 5px solid #ff6b6b; color: #333; margin-top: 20px;}</style>", unsafe_allow_html=True)

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
        "active_stopwatches": {} # שומר את שעת ההתחלה במסד הנתונים
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
    t_choice = st.selectbox("בחר משימה:", t_list)
    c_name = st.text_input("שם המשימה:") if t_choice == "אחר" else ""

    if st.button("סיימתי! ✨"):
        f_name = c_name if t_choice == "אחר" else t_choice
        if f_name:
            reward = TASKS_DB[cat_key].get(t_choice, 15)
            status = "approved" if role == "parent" else "pending"
            data["tasks_today"].append({"user": user_select, "category": cat_key, "task": f_name, "reward": reward, "status": status})
            if role == "parent": data['screen_time'][user_select] += reward
            save_data(data)
            st.session_state.msg_task = "המשימה נרשמה!"
            st.rerun()

    if st.session_state.msg_task:
        st.success(st.session_state.msg_task); st.session_state.msg_task = None

    if role == "parent":
        st.divider()
        st.subheader("👀 אישור משימות ילדים")
        pending = [t for t in data["tasks_today"] if t["status"] == "pending"]
        for i, t in enumerate(pending):
            if st.button(f"אשר ל{t['user']}: {t['task']}", key=f"btn_{i}"):
                t["status"] = "approved"
                data['screen_time'][t['user']] += t['reward']
                save_data(data)
                st.session_state.msg_approve = "אושר!"
                st.rerun()
        if st.session_state.msg_approve:
            st.success(st.session_state.msg_approve); st.session_state.msg_approve = None

    st.divider()
    target = st.selectbox("למי לפרגן?", [u for u in USERS if u != user_select])
    txt = st.text_area("מה לכתוב?")
    if st.button("שלח פירגון ❤️"):
        if txt:
            data["compliments"].append({"from": user_select, "to": target, "text": txt})
            save_data(data)
            st.session_state.msg_comp = "הפירגון נשמר!"
            st.rerun()
    if st.session_state.msg_comp:
        st.success(st.session_state.msg_comp); st.session_state.msg_comp = None

st.divider()

st.subheader("🏆 אלופי משק הבית (היום)")
home_counts = {u: 0 for u in USERS}
for t in data.get("tasks_today", []):
    if t.get("status") == "approved" and t.get("category") == "home":
        home_counts[t["user"]] += 1

max_val = max(home_counts.values()) if any(home_counts.values()) else 0
chart_html = "<div style='display: flex; justify-content: space-around; align-items: flex-end; height: 180px; background: white; border-radius: 15px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>"
for u, count in home_counts.items():
    is_winner = (count == max_val and max_val > 0)
    crown = "👑" if is_winner else "&nbsp;"
    h = int((count / max_val) * 100) if max_val > 0 else 5
    chart_html += f"<div style='text-align: center;'><div style='font-size:20px;'>{crown}</div><div style='height: {h}px; width: 40px; background-color: #38b000; margin: 0 auto; border-radius: 5px 5px 0 0; display:flex; align-items:flex-end; justify-content:center; color:white; font-size:12px;'>{count if count>0 else ''}</div><div style='margin-top:5px; font-size:14px;'>{u}</div></div>"
chart_html += "</div>"
st.markdown(chart_html, unsafe_allow_html=True)

st.subheader("🦜 סיכום יומי - פלא התוכי")
if st.button("הכן סיכום יומי עכשיו"):
    with st.spinner("פלא חושב..."):
        t_list = [f"{u} ({sum(1 for t in data['tasks_today'] if t['user'] == u and t['status'] == 'approved')} משימות)" for u in USERS]
        c_list = [f"{c['from']} ל{c['to']}: {c['text']}" for c in data["compliments"]]
        prompt = f"אתה פלא, תוכי חצוף ומצחיק. סכם את היום של משפחת כהן:\nמשימות: {' | '.join(t_list)}\nפירגונים: {' | '.join(c_list) if c_list else 'אין'}"
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    res = genai.GenerativeModel(m.name).generate_content(prompt)
                    st.markdown(f'<div class="pele-summary"><h3>🦜 פלא אומר:</h3>{res.text}</div>', unsafe_allow_html=True)
                    break
        except Exception as e: st.error(f"שגיאה: {e}")
