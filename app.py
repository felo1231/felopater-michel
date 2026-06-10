import streamlit as st
import google.generativeai as ai
import json
import smtplib
from email.mime.text import MIMEText
import random
from streamlit_cookies_controller import CookieController
from email_validator import validate_email, EmailNotValidError
import typing_extensions as typing

# --- APP CONFIG & SETUP ---
st.set_page_config(page_title="AI Study Assistant", layout="wide")
st.title('AI Studying Assistant✨')

# --- GEMINI SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    ai.configure(api_key=api_key)
    
    try:
        model = ai.GenerativeModel(model_name='gemini-3.5-flash')
    except Exception:
        model = ai.GenerativeModel(model_name='gemini-1.5-flash-latest')
        
except Exception as e:
    st.error("خطأ في إعدادات الاتصال: تأكد من إضافة GEMINI_API_KEY في إعدادات التطبيق.")
    st.stop()
    

# --- AUTHENTICATION & LOGIN CHECK ---
OFFICIAL_EMAIL = "ai.studying.assisstant@gmail.com"
controller = CookieController()

saved_user = controller.get("remembered_user")

if "logged_in" not in st.session_state:
    if saved_user:
        st.session_state.logged_in = True
        st.session_state.user_email = saved_user
    else:
        st.session_state.logged_in = False

if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0

# 🌟 1. هنا قمنا بتعريف سجل المحادثات لحفظ الشات من الاختفاء
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def send_otp_to_user(user_email, otp_code):
    try:
        sender_password = st.secrets["SMTP_PASSWORD"]
    except Exception:
        st.error("خطأ: يرجى إعداد SMTP_PASSWORD في الـ Secrets الخاصة بـ Streamlit أولاً.")
        return False

    email_content = f"مرحباً بك في AI Studying Assistant✨\n\nكود التحقق الخاص بك هو: {otp_code}\n\nتم إرسال هذا الكود بناءً على طلبك لتسجيل الدخول."
    msg = MIMEText(email_content, 'plain', 'utf-8')
    msg['Subject'] = f"Verification Code from {OFFICIAL_EMAIL}"
    msg['From'] = OFFICIAL_EMAIL
    msg['To'] = user_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(OFFICIAL_EMAIL, sender_password)
            server.sendmail(OFFICIAL_EMAIL, user_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"فشل في إرسال الإيميل: {e}")
        return False

if not st.session_state.logged_in:
    st.subheader("🔒 يرجى تسجيل الدخول أولاً للوصول إلى المساعد الدراسي")
    
    user_email_input = st.text_input("أدخل بريدك الإلكتروني (Gmail):", placeholder="example@gmail.com")
    remember_me = st.checkbox("البقاء قيد تسجيل الدخول (تذكرني) 🔐")

    if st.button("طلب كود التحقق ✉️"):
        if user_email_input:
            email_to_check = user_email_input.strip().lower()
            if "@gmail.com" in email_to_check:
                try:
                    with st.spinner("جاري التحقق من وجود الحساب وإرسال الكود..."):
                        email_info = validate_email(email_to_check, check_deliverability=True)
                        user_email_clean = email_info.email
                        
                        st.session_state.generated_otp = str(random.randint(100000, 999999))
                        if send_otp_to_user(user_email_clean, st.session_state.generated_otp):
                            st.session_state.otp_sent = True
                            st.success(f"تم إرسال الكود بنجاح! تفقد بريدك الوارد في الرسائل بعنوان {OFFICIAL_EMAIL}")
                except EmailNotValidError:
                    st.error("❌ عذراً، هذا البريد الإلكتروني غير موجود أو غير صالح لاستقبال الرسائل!")
            else:
                st.error("برجاء إدخال بريد جيميل صحيح ينتهي بـ @gmail.com")
        else:
            st.warning("برجاء كتابة بريدك الإلكتروني أولاً.")

    if st.session_state.otp_sent:
        st.divider()
        otp_input = st.text_input("أدخل كود التحقق المستلم (OTP):", type="password", placeholder="******")
        
        if st.button("تأكيد الدخول والتحقق ✅"):
            if otp_input == st.session_state.generated_otp:
                st.session_state.logged_in = True
                st.session_state.user_email = user_email_input
                if remember_me:
                    controller.set("remembered_user", user_email_input)
                st.success("تم التحقق وتسجيل الدخول بنجاح! 🎉")
                st.rerun()
            else:
                st.error("كود التحقق غير صحيح، يرجى مراجعة الإيميل والمحاولة مرة أخرى.")
                
    st.stop()


# --- APP TABS ---
# الصحيح: قائمة واحدة تضم كل الـ Tabs
questions_tab, quizzes_tab, planner_tab, account_tab, model_tab = st.tabs(
    ['Q&A ⁉️', 'Quizzes 📃', 'Study Planner✅', 'Account 👤', '3D Models 🎨']
)

# --- 4. QUESTIONS TAB ---
with questions_tab:
    col1, col2 = st.columns(2)
    with col1:
        subject = st.selectbox(label='Choose a subject:', options=['Math', 'Programming', 'Physics', 'AI','chemistry','دراسات اجتماعية','اللغةالعربية','science','biology'], key='q_sub')
        tone = st.selectbox(label='Choose a tone:', options=['Friendly', 'Professional'], key='q_tone')
    with col2:
        details = st.selectbox(label='Choose level of details:', options=['Brief', 'Medium', 'Detailed'], key='q_det')
        edu_level = st.selectbox(label='Choose educational level:', options=['School', 'University', 'Graduated'], key='q_edu')

    st.divider()
    
    # 🌟 2. هنا نقوم بعرض كل رسائل الشات القديمة المخزنة قبل خانة الكتابة
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar=msg["avatar"]):
            st.write(msg["text"])

    question = st.chat_input('Enter your question:')

    if question:
        # حفظ وعرض سؤال المستخدم في السجل
        st.session_state.chat_history.append({"role": "human", "avatar": "😉", "text": question})
        with st.chat_message('human', avatar='😉'):
            st.write(question)
            
        # توليد وحفظ وعرض رد الذكاء الاصطناعي في السجل
        with st.chat_message('ai', avatar='🤖'):
            prompt = f"Expert {subject} assistant. Level: {edu_level}. Tone: {tone}. Detail: {details}. Question: {question}"
            with st.spinner('Thinking...'):
                try:
                    answer = model.generate_content(prompt)
                    st.write(answer.text)
                    st.session_state.chat_history.append({"role": "ai", "avatar": "🤖", "text": answer.text})
                except Exception as e:
                    st.error("عذراً، حدث خطأ أثناء الاتصال بالخادم.")
        
        # إعادة تشغيل سريعة لتثبيت الشات في مكانه الصحيح فوق خانة الكتابة
        st.rerun()

# --- 5. QUIZZES CONFIG & TAB ---
class QuizQuestion(typing.TypedDict):
    question: str
    options: list[str]
    answer: str

with quizzes_tab:
    st.header("Interactive Quiz 🧠")

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        quiz_subject = st.text_input("Subject:", placeholder="e.g. Algebra or Python", key="quiz_subject_input")
        grade_level = st.selectbox(
            "Select your Grade/Level:",
            options=["Grade 1","Grade 2","Grade 3","Grade 4","Grade 5","Grade 6","Grade 7", "Grade 8", "Grade 9", "High School", "University"],
            index=7
        )

    with col_q2:
        num_q = st.slider("Number of Questions:", 1, 20, 5)
        difficulty = st.select_slider("Style:", options=["Basic", "mediam", "Challenge"])

    if st.button("Generate My Quiz 📝"):
        if quiz_subject:
            with st.spinner(f'Creating a {grade_level} quiz...'):
                quiz_prompt = f"""
                Create a {num_q} question multiple-choice quiz about {quiz_subject}.
                The difficulty must be strictly for {grade_level} students at a {difficulty} level.
                """
                try:
                    response = model.generate_content(
                        quiz_prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": list[QuizQuestion],
                        },
                    )
                    st.session_state.quiz_data = json.loads(response.text)
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_index += 1  
                    st.success("تم صياغة الاختبار بنجاح! حل الأسئلة بالأسفل 👇")
                    
                except Exception as e:
                    if "quota" in str(e).lower() or "429" in str(e):
                        st.warning("⚠️ لقد قمت بإرسال طلبات كثيرة في وقت قصير. يرجى الانتظار لمدة دقيقة ثم المحاولة مرة أخرى.")
                    else:
                        st.error("الخادم مشغول حالياً، يرجى إعادة الضغط على زر التوليد مرة أخرى.")
        else:
            st.warning("Please enter a subject first!")

    if "quiz_data" in st.session_state:
        st.divider()
        with st.form("quiz_form"):
            for i, q_item in enumerate(st.session_state.quiz_data):
                st.subheader(f"Question {i+1}")
                st.write(q_item["question"])
                st.session_state.user_answers[i] = st.radio(
                    "Select an option:",
                    options=q_item["options"],
                    key=f"quiz_q_{i}_{st.session_state.quiz_index}"
                )

            submit_quiz = st.form_submit_button("Submit Answers ✅")

        if submit_quiz:
            st.session_state.quiz_submitted = True
            score = 0
            st.divider()

            for i, q_item in enumerate(st.session_state.quiz_data):
                user_choice = st.session_state.user_answers[i]
                if user_choice == q_item["answer"]:
                    st.success(f"Question {i+1}: Correct! 🌟")
                    score += 1
                else:
                    st.error(f"Question {i+1}: Not quite.")
                    st.info(f"The right answer was: **{q_item['answer']}**")

            total_questions = len(st.session_state.quiz_data)
            percentage = (score / total_questions) * 100

            st.header("Your Performance Report 📊")
            col_res1, col_res2 = st.columns(2)
            col_res1.metric("Final Score", f"{score} / {total_questions}")
            col_res2.metric("Percentage", f"{percentage:g}%")

            if percentage == 100:
                st.success("### 🏆 Mastermind Status!")
            elif percentage >= 80:
                st.success("### 🚀 Outstanding Work!")
            elif percentage >= 60:
                st.warning("### 📈 Great Progress!")
            elif percentage >= 40:
                st.info("### 🧠 Brain Power Building!")
            else:
                st.error("### 🛡️ Don't Give Up!")

# --- 6. STUDY PLANNER TAB ---
with planner_tab:
    st.header("Plan Your Success 📅")

    with st.form("planner_form"):
        goal = st.text_area("What is your learning goal?", placeholder="e.g. Master React.js in two weeks")
        time_commit = st.number_input("How many hours can you study per day?", min_value=1, max_value=16, value=2)
        experience = st.selectbox("Current experience level:", ["Complete Beginner", "Intermediate", "Advanced"])

        submit_plan = st.form_submit_button("Create My Plan 🚀")

    if submit_plan:
        if goal:
            plan_prompt = f"""
            Create a detailed study schedule for the following goal: {goal}.
            The user can commit {time_commit} hours per day.
            User level: {experience}.
            Break the plan down into 'Milestones' and 'Daily Tasks'.
            Suggest specific resources or topics to cover.
            """
            with st.spinner('Mapping out your journey...'):
                plan_res = model.generate_content(plan_prompt)
            st.info("Here is your personalized study roadmap:")
            st.markdown(plan_res.text)
        else:
            st.warning("Tell me what you want to learn!")

# --- 7. ACCOUNT TAB ---
with account_tab:
    st.header("👤 Account Settings")
    st.success(f"مرحباً بك! أنت مسجل الدخول حالياً بحساب: **{st.session_state.user_email}**")
    st.info(f"البريد الرسمي للمساعد الدراسي: {OFFICIAL_EMAIL}")
    
    if st.button("تسجيل الخروج 🚪"):
        st.session_state.logged_in = False
        st.session_state.generated_otp = None
        st.session_state.otp_sent = False
        st.session_state.user_email = None
        
        try:
            if controller.get("remembered_user"):
                controller.remove("remembered_user")
        except Exception:
            pass
            
        st.rerun()

with model_tab:
    st.header("🎨 Generate Your Photo On 3D Model")
    
    user_prompt = st.text_input("أدخل وصف الشيء الذي تريده:", placeholder="مثال: plant")

    if st.button("generate 3d photo"):
        if user_prompt:
            with st.spinner("جاري الإبداع..."):
                # تحسين الوصف لضمان ظهور النتيجة
                enhanced_prompt = f"a high quality 3d model render of {user_prompt}, cinematic lighting, 8k, detailed texture"
                
                # استخدام رابط التوليد مع الوصف المحسن
                encoded_prompt = enhanced_prompt.replace(" ", "%20")
                image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=800&height=600&nologo=true"
                
                st.image(image_url, caption=f"نتائج البحث عن: {user_prompt}", use_container_width=True)
        else:
            st.warning("من فضلك اكتب اسم الشيء أولاً!")
# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
    <style>
    /* 1. الخلفية العامة للتطبيق (تدرج لوني غامق ومريح للعين) */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%) !important;
        color: #f8fafc !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 2. تحسين مظهر العناوين والنصوص */
    h1, h2, h3, .stSubheader {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* 3. تعديل شكل الـ Tabs بالكامل لتصبح كأزرار مودرن */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(255, 255, 255, 0.04) !important;
        padding: 8px 12px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        background-color: transparent !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease-in-out;
    }
    /* الـ Tab النشط حالياً */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        box-shadow: 0px 4px 12px rgba(124, 58, 237, 0.4) !important;
    }
    
    /* 4. تجميل الأزرار (Buttons) وإضافة تأثير حركي عند الإشارة (Hover) */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 12px 28px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.3) !important;
        width: auto;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(124, 58, 237, 0.6) !important;
        background: linear-gradient(90deg, #5a52ff 0%, #8b4aff 100%) !important;
    }
    .stButton>button:active {
        transform: translateY(1px) !important;
    }
    
    /* 5. تحسين حقول الإدخال والقوائم (Inputs & Selectboxes) */
    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stNumberInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 10px !important;
        transition: border 0.3s ease;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 1px #7c3aed !important;
    }
    
    /* 6. تجميل الصناديق التنبيهية (Alerts & Success Messages) */
    .stAlert {
        border-radius: 14px !important;
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* 7. تجميل الرسائل داخل الـ Chat */
    [data-testid="stChatMessage"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        border-radius: 16px !important;
        margin-bottom: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%) !important;
        color: #f8fafc !important;
        font-size: 18px !important; /* زيادة حجم الخط الأساسي */
    }
    
    /* تكبير خط الأزرار */
    .stButton>button {
        font-size: 18px !important; 
        font-weight: 600 !important;
        padding: 15px 30px !important;
    }
    
    /* تحسين النصوص داخل التطبيق */
    p, label, div {
        font-size: 18px !important;
    }
    
    /* تحسين حجم الخط في الـ Tabs */
    .stTabs [data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 700 !important;0
    .stApp, .stApp div, .stApp p, .stApp span, .stApp li {
        color: #FFFFFF !important;
    }
    
    /* تغيير لون نص رسائل الشات (سواء المستخدم أو البوت) */
    [data-testid="stChatMessage"] div, [data-testid="stChatMessage"] p {
        color: #FFFFFF !important;
    }
    
    /* تحسين لون حقول الإدخال */
    .stTextInput input, .stTextArea textarea {
        color: #FFFFFF !important;
        background-color: #262730 !important;
    }
    
    /* تحسين لون العناوين */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    
    /* تحسين لون التنبيهات */
    .stAlert div {
        color: #FFFFFF !important;
    .stApp, div, p, label, .stRadio label, .stTextInput input, .stTextArea textarea {
        color: #FFFFFF !important;
    }

    /* ضمان ظهور نصوص الأسئلة والاختيارات بشكل واضح */
    [data-testid="stMarkdownContainer"] {
        color: #FFFFFF !important;
    }
    
    /* تغيير لون الخط داخل الـ Quiz تحديداً */
    .stForm label {
        color: #FFFFFF !important;
    }
    
    /* تنسيق خاص للـ Selectbox والـ Radio ليظهر الخط أبيض */
    div[role="radiogroup"] label {
        color: #FFFFFF !important;
    }
    }
    </style>
""", unsafe_allow_html=True)