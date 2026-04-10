import streamlit as st
import json
import os
import time
from datetime import datetime
import google.generativeai as genai

# --- אתחול והגדרות API חסינות לשגיאות ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_resource
def get_working_model():
    """
    פונקציה שסורקת אילו מודלים זמינים בסביבת השרת הנוכחית
    ובוחרת את הטוב ביותר כדי למנוע שגיאות 404 (Not Found).
    """
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if 'models/gemini-1.5-flash' in available_models:
            return genai.GenerativeModel('gemini-1.5-flash')
        elif 'models/gemini-1.5-flash-latest' in available_models:
            return genai.GenerativeModel('gemini-1.5-flash-latest')
        elif 'models/gemini-pro' in available_models:
            return genai.GenerativeModel('gemini-pro')
        elif available_models:
            return genai.GenerativeModel(available_models[0])
        else:
            return genai.GenerativeModel('gemini-pro')
    except:
        return genai.GenerativeModel('gemini-pro')

model = get_working_model()
# ----------------------------------------

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
    padding: 35px; 
    border-radius: 30px; 
    border: 8px solid #ff6b6b; 
    color: #1a1a1a !important; 
    margin-top: 20px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.2);
    font-size: 1.25rem;
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
    """מחמאה מהירה על ביצוע משימה בודדת"""
    role_desc = "אבא" if name == "שי" else "אמא" if name == "ענבל" else "ילד" if name == "בארי" else "ילדה בת 9"
    prompt = f"אתה פלא התוכי. {name} ({role_desc}) סיים/ה {task_name}. כתוב מחמאה יצירתית ומצחיקה על סיום המשימה. פנה במין הנכון."
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"קווה קווה! {name}, איזה פלא! שיחקת אותה עם ה{task_name}."

def generate_full_daily_summary(tasks):
    """סיכום יום מפורט המשלב את משימות המשפחה יחד עם הרפתקאותיו של פלא התוכי"""
    if not tasks:
        return "הקן ריק ממשימות היום! אני יושב על הנדנדה שלי ומחכה שמישהו יזיז משהו. קדימה משפחת פלא, תנו לי חומר לכתיבה!"
    
    summary_data = {}
    for t in tasks:
        if t.get('status') == 'approved':
            summary_data.setdefault(t['user'], []).append(t['task'])
            
    if not summary_data:
        return "קווה קווה! יש משימות שדווחו, אבל הן עדיין מחכות לאישור של ההורים. בינתיים אני מנקר גרעינים!"
    
    tasks_details = "\n".join([f"- {user}: {', '.join(tasks_list)}" for user, tasks_list in summary_data.items()])
    
    prompt = f"""
    אתה פלא, התוכי המשפחתי האהוב של משפחת פלא - שנון, משעשע, ומרגיש שהוא המנהל האמיתי של הבית.
    עליך לכתוב את "סיכום היום של משפחת פלא" (לפחות 300 מילים) על סמך המשימות שבוצעו היום.

    המשימות שבוצעו ואושרו היום (חובה להזכיר אותן!):
    {tasks_details}

    על הסיכום להכיל את החלקים הבאים:
    1. **הרפתקאות פלא בבית:** תאר סיפור קצר, יצירתי ומצחיק על מה שעשית בבית בזמן שכולם עבדו/למדו (למשל: תכנון מזימה להפיל כוס, שיחה פילוסופית עם המטאטא, או מלחמה בדמותך המשתקפת במראה). 
    2. **חלוקת כבוד למשפחה:** הקדש פסקה לכל בן משפחה מהרשימה שביצע משימה היום. עליך לציין במפורש את המשימות הספציפיות שהוא ביצע (מהרשימה למעלה), ולהעניק לו פרגון אישי ומשעשע על כך. 
       - הקפד לפנות במין הנכון: שי (אבא - זכר), ענבל (אמא - נקבה), בארי (ילד - זכר), טנא (ילדה בת
