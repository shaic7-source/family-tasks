import streamlit as st
import json
import os
from datetime import datetime
import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyDSd9qQCtjQTDpCPGnMyLy6RssIHJ3feEI"
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
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"screen_time": {u: 0 for u in USERS}, "tasks_today": [], "compliments": [], "last_date": str(datetime.now().date())}

def save_data(d):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

data = load_data()
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

    u_val = st.number_input("דקות שנוצלו:", min_value=0, step=1)
    if st.button("עדכן ניצול זמן"):
        data['screen_time'][user_select] -= u_val
        save_data(data)
        st.session_state.msg_time = "הזמן עודכן!"
        st.rerun()

    if st.session_state.msg_time:
        st.success(st.session_state.msg_time)
        st.session_state.msg_time = None

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
            data["tasks_today"].append({"user": user_select, "task": f_name, "reward": reward, "status": status})
            if role == "parent": data['screen_time'][user_select] += reward
            save_data(data)
            st.session_state.msg_task = "המשימה נרשמה!"
            st.rerun()

    if st.session_state.msg_task:
        st.success(st.session_state.msg_task)
        st.session_state.msg_task = None

    st.divider()

    if role == "parent":
        st.subheader("👀 אישור משימות ילדים")
        pending = [t for t in data["tasks_today"] if t["status"] == "pending"]
        if not pending: st.write("אין משימות לאישור.")
        for i, t in enumerate(pending):
            if st.button(f"אשר ל{t['user']}: {t['task']}", key=f"btn_{i}"):
                t["status"] = "approved"
                data['screen_time'][t['user']] += t['reward']
                save_data(data)
                st.session_state.msg_approve = "אושר!"
                st.rerun()

        if st.session_state.msg_approve:
            st.success(st.session_state.msg_approve)
            st.session_state.msg_approve = None

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
        st.success(st.session_state.msg_comp)
        st.session_state.msg_comp = None

st.divider()
st.subheader("🦜 סיכום יומי - פלא התוכי")
if st.button("הכן סיכום יומי עכשיו"):
    with st.spinner("פלא חושב..."):
        tasks_list = [f"{u} ({sum(1 for t in data['tasks_today'] if t['user'] == u and t['status'] == 'approved')} משימות)" for u in USERS]
        comps_list = [f"{c['from']} ל{c['to']}: {c['text']}" for c in data["compliments"]]

        t_str = " | ".join(tasks_list)
        c_str = " | ".join(comps_list) if comps_list else "אין פירגונים"

        prompt = f"אתה פלא, תוכי חצוף ומצחיק. סכם את היום של משפחת כהן.\nמשימות שבוצעו: {t_str}\nפירגונים: {c_str}"

        try:
            # משיכת רשימת המודלים ישירות מגוגל ובחירת הראשון שתומך בטקסט
            working_model_name = None
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    working_model_name = m.name
                    if 'flash' in working_model_name: 
                        break # אם מצאנו מודל Flash מהיר, נעצור כאן וניקח אותו
            
            if working_model_name:
                model = genai.GenerativeModel(working_model_name)
                res = model.generate_content(prompt)
                st.markdown(f'<div class="pele-summary"><h3>🦜 פלא אומר:</h3>{res.text}</div>', unsafe_allow_html=True)
            else:
                st.error("לא נמצא מודל פתוח במפתח ה-API שלך.")
        except Exception as e:
            st.error(f"שגיאה בתקשורת מול גוגל: {e}")
