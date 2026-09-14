import streamlit as st
import google.generativeai as ai
import json
import smtplib
from email.mime.text import MIMEText
import random
from streamlit_cookies_controller import CookieController
from email_validator import validate_email, EmailNotValidError
import typing_extensions as typing
import urllib.parse
from gtts import gTTS
import io


st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(-45deg, #19f775, #19f7b1, #19f7da, #19ecf7, #19cbf7, #19b1f7, #1993f7, #196ef7);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .main .block-container {
        background: rgba(255, 255, 255, 0.92);
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    .main-title {
        color: #0f172a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        font-size: 2.3rem;
        margin-bottom: 10px;
        text-align: center;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 700;
        font-size: 1rem;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.35);
        color: #38bdf8;
    }
    </style>
""", unsafe_allow_html=True)

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
questions_tab, quizzes_tab, planner_tab, flashcards_tab, cheatsheet_tab, pomodoro_tab, model_tab, account_tab, note_tab = st.tabs(
    ['Q&A ⁉️', 'Quizzes 📃', 'Study Planner✅', 'Flashcards🗂️','Cheat-Sheet 📄', 'Pomodoro ⏱️', 'Models 🎨', 'Account 👤', 'Important Notes 📌']
)

# --- 4. QUESTIONS TAB ---
with questions_tab:
    st.header("Write Your Questions Here ⁉️")
    col1, col2 = st.columns(2)
    with col1:
        subject = st.selectbox(label='Choose a subject:', options=['Math', 'Programming', 'Physics', 'AI','chemistry','دراسات اجتماعية','اللغةالعربية','science','biology','english'], key='q_sub')
        tone = st.selectbox(label='Choose a tone:', options=['Friendly', 'Professional'], key='q_tone')
    with col2:
        details = st.selectbox(label='Choose level of details:', options=['Brief', 'Medium', 'Detailed'], key='q_det')
        edu_level = st.selectbox(label='Choose educational level:', options=['grade 1', 'grade 2', 'grade 3',  'grade 4', 'grade 5', 'grade 6',
                                                                              'grade 7', 'grade 8', 'grade 9', 'University', 'Graduated'], key='q_edu')

    st.divider()
    
    # عرض سجل المحادثات
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar=msg["avatar"]):
            st.write(msg["text"])
            if "image_url" in msg and msg["image_url"]:
                st.image(msg["image_url"], use_container_width=True)

    question = st.chat_input('Enter your question:')

    if question:
        # حفظ وعرض سؤال المستخدم في السجل
        st.session_state.chat_history.append({"role": "human", "avatar": "😉", "text": question})
        with st.chat_message('human', avatar='😉'):
            st.write(question)
            
        with st.chat_message('ai', avatar='🤖'):
            prompt = f"Expert {subject} assistant. Level: {edu_level}. Tone: {tone}. Detail: {details}. Question: {question}"
            with st.spinner('Thinking and generating visual aid...'):
                try:
                    answer = model.generate_content(prompt)
                    ans_text = answer.text
                    st.write(ans_text)
                    
                    # 🌟 توليد/جلب صورة ذات صلة بالسؤال أو الإجابة عبر Pollinations AI (مجاني وبدون API Key)
                    # نأخذ كلمات مفتاحية من السؤال أو نصفيها
                    import urllib.parse
                    safe_query = urllib.parse.quote(f"{subject} {question[:50]}")
                    generated_image_url = f"https://pollinations.ai/p/{safe_query}?width=800&height=500&seed={random.randint(1,10000)}"
                    
                    st.image(generated_image_url, caption="صورة توضيحية تولدت بناءً على سؤالك 🖼️", use_container_width=True)
                    
                    st.session_state.chat_history.append({
                        "role": "ai", 
                        "avatar": "🤖", 
                        "text": ans_text,
                        "image_url": generated_image_url
                    })
                except Exception as e:
                    st.error(f"عذراً، حدث خطأ: {e}")
        
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

# --- 4. AI FLASHCARDS TAB 🗂️ ---
class FlashcardItem(typing.TypedDict):
    front: str
    back: str

with flashcards_tab:
    st.header("AI Flashcards 🗂️")
    st.write("اكتب اسم الدرس أو المفهوم، وسيقوم الذكاء الاصطناعي بتوليد فلاش كاردز تفاعلية للمراجعة السريعة!")
    
    fc_topic = st.text_input("أدخل موضوع الدرس أو المفاهيم:", placeholder="مثلاً: قوانين نيوتن أو أساسيات بايثون")
    fc_count = st.slider("عدد الكروت:", 3, 10, 5)

    if st.button("توليد الفلاش كاردز 🎴", key="gen_fc_btn"):
        if fc_topic:
            with st.spinner("جاري صياغة الفلاش كاردز..."):
                fc_prompt = f"""
                Generate {fc_count} study flashcards for the topic: {fc_topic}.
                Return JSON list of objects with keys "front" (question/concept) and "back" (concise answer/definition).
                """
                try:
                    res = model.generate_content(
                        fc_prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": list[FlashcardItem],
                        }
                    )
                    st.session_state.flashcards = json.loads(res.text)
                    st.success("تم توليد البطاقات بنجاح!")
                except Exception as e:
                    st.error(f"خطأ: {e}")

    if "flashcards" in st.session_state and st.session_state.flashcards:
        st.divider()
        for idx, card in enumerate(st.session_state.flashcards):
            with st.expander(f"بطاقة رقم {idx+1}: {card['front']}"):
                st.markdown(f"الإجابة / المفهوم:")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("فهمته جيداً ✅", key=f"know_{idx}"):
                        st.toast("ممتاز! استمر في التقدم 🌟")
                with c2:
                    if st.button("أحتاج مراجعة 🔁", key=f"rev_{idx}"):
                        st.toast("سجلنا أنك تحتاج مراجعتها لاحقاً 💪")

# --- 5. SMART CHEAT-SHEET GENERATOR 📄 ---
with cheatsheet_tab:
    st.header("Smart Cheat-Sheet Generator 📄")
    st.write("ألصق نص الدرس هنا، وسيقوم الـ AI باستخراج جدول لأهم المصطلحات، القوانين، وأهم الأسئلة المتوقعة في الامتحان!")
    
    lesson_text = st.text_area("ألصق محتوى أو نص الدرس هنا:", height=180, placeholder="ضع ملخص الدرس أو المقال هنا...")

    if st.button("إنشاء ملخص الغش وورقة المراجعة ⚡", key="gen_cheat_btn"):
        if lesson_text:
            with st.spinner("جاري تحليل النص واستخراج الخلاصة..."):
                cheat_prompt = f"""
                Analyze the following lesson text and produce:
                1. A table of key terms and definitions.
                2. Key rules/formulas or core points.
                3. Top 3 expected exam questions with brief answers.
                Lesson text: {lesson_text}
                """
                try:
                    cheat_res = model.generate_content(cheat_prompt)
                    st.markdown(cheat_res.text)
                except Exception as e:
                    if "ResourceExhausted" in str(e) or "429" in str(e):
                        st.warning("⚠️ لقد تجاوزت الحد المسموح من الطلبات في الدقيقة (Quota Exhausted). يرجى الانتظار لمدة دقيقة والمحاولة مرة أخرى.")
                    else:
                        st.error(f"حدث خطأ أثناء الاتصال بالخادم: {e}")
        else:
            st.warning("الرجاء لصق نص الدرس أولاً!")

# --- 6. SMART POMODORO WITH CHALLENGES ⏱️ ---
with pomodoro_tab:
    st.header("Smart Pomodoro Timer ⏱️")
    st.write("مؤقت تركيز بومودورو (25 دقيقة عمل / 5 دقائق راحة) مع تحديات ولغز علمي لتنشيط ذهنك في وقت الاستراحة!")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        work_mins = st.number_input("مدة وقت التركيز (دقائق):", min_value=1, max_value=60, value=25)
    with col_p2:
        break_mins = st.number_input("مدة الاستراحة (دقائق):", min_value=1, max_value=30, value=5)

    if st.button("توليد لغز أو تحدي استراحة علمي 🧩", key="pomo_puzzle_btn"):
        with st.spinner("جاري ابتكار تحدي استراحة..."):
            puzzle_res = model.generate_content("Give a fun, short science or logic puzzle with its hidden answer for a study break.")
            st.info("### 🧩 تحدي الاستراحة:")
            st.markdown(puzzle_res.text)

with model_tab:
    st.header("🎨 Generate Your Photo On 3D Model")
    st.write("اكتب وصفاً لأي شيء تريد تخيله كمجسم ثلاثي الأبعاد أو مشهد مجسم، وسيقوم التطبيق بتوليد الفكرة وعرضها لك!")
    
    user_image_prompt = st.text_input("اكتب وصف الصورة أو الموديل بالإنجليزية أو العربية:", placeholder="e.g. A cute 3D robot studying books, 3D render, blender style", key="img_prompt_input")
    
    if st.button("توليد الصورة 🚀", key="gen_img_btn"):
        if user_image_prompt:
            with st.spinner("جاري تصميم وتوليد الصورة ثلاثية الأبعاد... 🎨"):
                try:
                    # طريقة مضمونة أكثر لجلب صورة عبر pollinations أو استخدام Picsum/Loremflickr كبديل سريع وعالي الجودة
                    encoded_prompt = urllib.parse.quote(user_image_prompt)
                    # استخدام رابط pollinations الصحيح مع تحديد model=flux
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true"
                    
                    st.image(img_url, caption=f"النتيجة للوصف: {user_image_prompt}", use_container_width=True)
                except Exception as e:
                    st.error(f" حدث خطأ أثناء تحميل الصورة: {e}")
        else:
            st.warning("الرجاء كتابة وصف أولاً!")

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

with note_tab:
    st.header("📝 Treasure Notes")
    st.write("نقاط و معلومات يجب أن تعلمها!!")
    st.write("                                                                ")
    st.write("This is A Good Website to see All Informations and Books (Egyptian Knowledge Bank)")
    st.info("https://www.ekb.eg/ar/home")