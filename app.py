import streamlit as st
import google.generativeai as ai
import json
import smtplib
from email.mime.text import MIMEText
import random
from streamlit_cookies_controller import CookieController
from email_validator import validate_email, EmailNotValidError

# --- APP CONFIG & SETUP ---
st.set_page_config(page_title="AI Study Assistant", layout="wide")
st.title('AI Studying Assistant✨')

# --- GEMINI SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    ai.configure(api_key=api_key)
    model = ai.GenerativeModel(model_name='gemini-3-flash-preview')
except Exception as e:
    st.error("خطأ في إعدادات الاتصال: تأكد من إضافة GEMINI_API_KEY في إعدادات التطبيق.")
    st.stop()

# --- AUTHENTICATION & LOGIN CHECK (حماية التطبيق بالكامل) ---
OFFICIAL_EMAIL = "ai.studying.assisstant@gmail.com"
controller = CookieController()

# جلب الإيميل المحفوظ من الكوكيز إن وجد
saved_user = controller.get("remembered_user")

# تهيئة متغيرات الجلسة
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

# دالة إرسال الإيميل
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

# حظر التطبيق إذا لم يكن مسجلاً للدخول
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


# --- بقية التطبيق تظهر فقط إذا تخطى شرط تسجيل الدخول بالأعلى ---
# إنشاء الـ Tabs مرة واحدة بشكل سليم
questions_tab, quizzes_tab, planner_tab, account_tab = st.tabs(
    ['Q&A ⁉️', 'Quizzes 📃', 'Study Planner✅', 'Account 👤'])

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
    question = st.chat_input('Enter your question:')

    if question:
        with st.chat_message('human', avatar='😉'):
            st.write(question)
        with st.chat_message('ai', avatar='🤖'):
            prompt = f"Expert {subject} assistant. Level: {edu_level}. Tone: {tone}. Detail: {details}. Question: {question}"
            with st.spinner('Thinking...'):
                answer = model.generate_content(prompt)
            st.write(answer.text)

# --- 5. QUIZZES TAB WITH GRADE LEVELS ---
with quizzes_tab:
    st.header("Interactive Quiz 🧠")

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        quiz_subject = st.text_input("Subject:", placeholder="e.g. Algebra or Python")
        grade_level = st.selectbox(
            "Select your Grade/Level:",
            options=["Grade 1","Grade 2","Grade 3","Grade 4","Grade 5","Grade 6","Grade 7", "Grade 8", "Grade 9", "High School", "University"],
            index=7 # تم ضبط المؤشر الافتراضي ليكون على الصف الثامن مباشرة
        )

    with col_q2:
        num_q = st.slider("Number of Questions:", 1, 10, 3)
        difficulty = st.select_slider("Style:", options=["Basic", "mediam", "Challenge"])

    # زر توليد الكويز الرئيسي
    # زر توليد الكويز الرئيسي
    if st.button("Generate My Quiz 📝"):
        if quiz_subject:
            with st.spinner(f'Creating a {grade_level} quiz...'):
                # تطوير الـ Prompt ليكون صارماً جداً مع الهيكل
                quiz_prompt = f"""
                You are a strict quiz generator. Create a {num_q} question multiple-choice quiz about {quiz_subject}.
                The difficulty must be strictly for {grade_level} students at a {difficulty} level.

                You MUST return the response ONLY as a raw valid JSON list of objects, without any markdown formatting, without wrapping it in ```json, and without any conversational text.
                
                Expected JSON Structure:
                [
                  {{
                    "question": "Write the question text here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "Write the exact text of the correct option here"
                  }}
                ]
                """
                try:
                    # نستخدم هنا إعدادات إجبار الموديل على إخراج JSON فقط لضمان عدم الانهيار
                    response = model.generate_content(
                        quiz_prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    # تنظيف النص الاحتياطي من أي علامات اقتباس برمجية
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    
                    # تحويل النص إلى كائن بايثون (List)
                    st.session_state.quiz_data = json.loads(raw_json)
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                    
                    st.success("تم توليد الاختبار بنجاح! جاهز للحل بالأسفل 👇")
                except Exception as e:
                    # في حال حدث خطأ، يطبع لك تفاصيل الخطأ الحقيقية في الـ terminal لتسهيل معرفة السبب
                    print(f"Quiz Error Details: {e}")
                    st.error("حدث خطأ أثناء صياغة الاختبار من الذكاء الاصطناعي. يرجى الضغط على الزر مرة أخرى للتبديل!")
        else:
            st.warning("Please enter a subject first!")
    # عرض الكويز وتصحيحه
    if "quiz_data" in st.session_state:
        st.divider()
        with st.form("quiz_form"):
            for i, q_item in enumerate(st.session_state.quiz_data):
                st.subheader(f"Question {i+1}")
                st.write(q_item["question"])
                st.session_state.user_answers[i] = st.radio(
                    "Select an option:",
                    options=q_item["options"],
                    key=f"quiz_q_{i}"
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
                st.write("Perfect score! You've completely mastered this topic.")
            elif percentage >= 80:
                st.success("### 🚀 Outstanding Work!")
                st.write("You're a natural at this. Just a tiny bit more focus and you'll be at 100%.")
            elif percentage >= 60:
                st.warning("### 📈 Great Progress!")
                st.write("You've got the core concepts down! Review the questions you missed.")
            elif percentage >= 40:
                st.info("### 🧠 Brain Power Building!")
                st.write("Every mistake is just a learning point. Keep practicing!")
            else:
                st.error("### 🛡️ Don't Give Up!")
                st.write("Let's try a 'Basic' level quiz to build your confidence!")

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