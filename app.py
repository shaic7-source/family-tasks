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
for k in ['msg_time', 'msg_task', 'msg_approve', 'daily_summary_text']:
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
.pele-summary-box {
    background: white; 
    padding: 30px; 
    border-radius: 25px; 
    border: 6px solid #ff6b6b; 
    color: #222 !important; 
    margin-top: 20px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    font-size: 1.15rem;
    line-height: 1.8;
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

def generate_pele_feedback(name, task_name):
    """מחמאה מהירה על משימה בודדת"""
    role_desc = "אבא" if name == "שי" else "אמא" if name == "ענבל" else "ילד" if name == "בארי" else "ילדה בת 9"
    prompt = f"אתה פלא התוכי. {name} ({role_desc}) סיים/ה {task_name}. כתוב מחמאה קצרה, יצירתית ומצחיקה. פנה במין הנכון."
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"{name}, אתה פשוט פלא!"

def generate_full_daily_summary(tasks):
    """סיכום יום ארוך, מפורט, משמעותי ומצחיק במיוחד"""
    if not tasks:
        return "שקט בבית... שקט מדי. הנוצות שלי מתייבשות מרוב שיעמום! מישהו מוכן לעשות איזו משימה כדי שיהיה לי על מה לכתוב?"
    
    summary_data = {}
    for t in tasks:
        if t['status'] == 'approved':
            summary_data.setdefault(t['user'], []).append(t['task'])
    
    tasks_details = "\n".join([f"- {user}: {', '.join(tasks_list)}" for user, tasks_list in summary_data.items()])
    
    prompt = f"""
    אתה 'פלא', תוכי מזן 'קוקטייל פילוסופי' – אינטליגנטי, מצחיק בטירוף, ציורי וחד עין. 
    עבור על הרשימה של בני משפחת פלא שביצעו משימות היום:
    {tasks_details}

    כתוב סיכום יום ארוך (לפחות 3-4 פסקאות משמעותיות) בטון של "יומן מסע קסום":
    
    1. **פרק המעללים של פלא:** פתח בתיאור מפורט והזוי של מה שעבר עליך היום בבית בזמן שכולם עבדו. אולי ניסית לפרוץ לכספת הגרעינים? אולי ניהלת משא ומתן עם המראה בסלון? תהיה יצירתי ומצחיק מאוד.
    
    2. **היכל התהילה המשפחתי:** עבור אחד-אחד על כל מי שביצע משימה (שי האבא, ענבל האמא, בארי וטנא בת ה-9). 
       לכל אחד תן פסקה מפרגנת בטירוף. אל תגיד רק "כל הכבוד", אלא תאר איך המשימה שלהם שינתה את האנרגיה בבית. 
       שימוש במטאפורות (למשל: "שי לא רק התפלל, הוא הרעיד את אמות הסיפים של הכלוב שלי עם הכוונה שלו").
    
    3. **תובנת התוכי היומית:** תן מסר קצר ומשמעותי על עבודת צוות או על הבית כקן חמים.
    
    4. **הקינוח:** סיים בבדיחת קרש "של אבות" או "של תוכים" שתפיל אותנו מהרגליים.

    דגשים חשובים:
    - פנה לשי כאבא ולטנא כילדה בת 9.
    - בלי חזרה מהשכנים.
    - הטקסט צריך להיות עשיר, ססגוני ומפורט מאוד - לא סיכום יבש!
    """
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return "היה יום מופלא! כולם היו נהדרים, והבית פשוט נוצץ."

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
            st.session_state.msg_task = generate_pele_feedback(user_select, f_name)
            
            new_task = {"id": time.time(), "user": user_select, "task": f_name, "reward": reward, "status": status, "time": datetime.now().strftime("%H:%M")}
            data["tasks_today"].append(new_task)
            if status == "approved": data['screen_time'][user_select] += reward
            
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

    # --- כפתור סיכום יום משודרג ---
    st.divider()
    st.subheader("🦜 רגע השיא של היום")
    if st.button("🌟 פלא, פתח את יומן המסע היומי שלנו!"):
        with st.spinner("פלא מנקה את המקור ומכין את הדיו..."):
            approved = [t for t in data["tasks_today"] if t['status'] == 'approved']
            st.session_state.daily_summary_text = generate_full_daily_summary(approved)
    
    if st.session_state.daily_summary_text:
        st.markdown(f'<div class="pele-summary-box"><b>🦜 דברי הימים של משפחת פלא:</b><br><br>{st.session_state.daily_summary_text}</div>', unsafe_allow_html=True)
        if st.button("סגור סיכום"):
            st.session_state.daily_summary_text = None
            st.rerun()
