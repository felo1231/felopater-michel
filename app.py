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
                
    # هنا نقوم بإيقاف السكريبت تماماً فلا يظهر أي شيء بالأسفل
    st.stop()


# --- بقية التطبيق تظهر فقط إذا تخطى شرط تسجيل الدخول بالأعلى ---
# 3. Making app tabs
questions_tab, quizzes_tab, planner_tab, account_tab = st.tabs(
    ['Q&A ⁉️', 'Quizzes 📃', 'Study Planner✅', 'Account 👤'])

# --- 4. QUESTIONS TAB ---
with questions_tab:
    # كود الـ Q&A القديم بتاعك هنا...
    pass

# --- 5. QUIZZES TAB ---
with quizzes_tab:
    # كود الـ Quizzes القديم بتاعك هنا...
    pass

# --- 6. STUDY PLANNER TAB ---
with planner_tab:
    # كود الـ Study Planner القديم بتاعك هنا...
    pass

# --- 7. ACCOUNT TAB (لعرض الحساب وتسجيل الخروج فقط) ---
with account_tab:
    st.header("👤 Account Settings")
    st.success(f"مرحباً بك! أنت مسجل الدخول حالياً بحساب: **{st.session_state.user_email}**")
    st.info(f"البريد الرسمي للمساعد الدراسي: {OFFICIAL_EMAIL}")
    
    if st.button("تسجيل الخروج 🚪"):
        # 1. تصفير متغيرات الجلسة أولاً
        st.session_state.logged_in = False
        st.session_state.generated_otp = None
        st.session_state.otp_sent = False
        st.session_state.user_email = None
        
        # 2. حذف الكوكيز بأمان بدون حدوث KeyError
        try:
            # نتحقق أولاً إذا كان الكوكيز موجوداً في المتصفح قبل حذفه
            if controller.get("remembered_user"):
                controller.remove("remembered_user")
        except Exception:
            # إذا حدث أي خطأ غير متوقع أثناء الحذف، يتجاهله الكود ويستمر بسلام
            pass
            
        # 3. إعادة تنشيط الصفحة لتطبيق التغييرات فوراً وحظر الدخول
        st.rerun()