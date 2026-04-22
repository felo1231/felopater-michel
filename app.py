# 1. Importing extensions
import streamlit as st
import google.generativeai as ai
import json

# --- APP CONFIG & SETUP ---
st.set_page_config(page_title="AI Study Assistant", layout="wide")
st.title('AI Studying Assistant✨')

# --- GEMINI SETUP ---
# بدلاً من كتابة المفتاح مباشرة، سنطلب من التطبيق أن يقرأه من الخزنة السرية
GEMINI_API_KEY = "AIzaSyBXI6jmht4nS6z5KcwYerfPlftcMQX8fR0"
api_key = st.secrets["GEMINI_API_KEY"]
ai.configure(api_key=api_key)

try:
    # استخدام النسخة المستقرة 'gemini-1.5-flash' بدلاً من 'preview'
    model = ai.GenerativeModel(model_name='gemini-1.5-flash')
except Exception as e:
    st.error(f"Model initialization failed: {e}")


# 3. Making app tabs
questions_tab, quizzes_tab, planner_tab = st.tabs(
    ['Q&A ⁉️', 'Quizzes 📃', 'Study Planner✅'])

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

# --- QUIZZES TAB WITH GRADE LEVELS ---
with quizzes_tab:
    st.header("Interactive Quiz 🧠")

    # Input fields
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        quiz_subject = st.text_input("Subject:", placeholder="e.g. Algebra or Python")
        # Adding the Grade Level selector
        grade_level = st.selectbox(
            "Select your Grade/Level:",
            options=["Grade 1","Grade 2","Grade 3","Grade 4","Grade 5","Grade 6","Grade 7", "Grade 8", "Grade 9", "High School", "University"],
            index=1 # Defaults to Grade 8
        )

    with col_q2:
        num_q = st.slider("Number of Questions:", 1, 10, 3)
        difficulty = st.select_slider("Style:", options=["Basic", "mediam", "Challenge"])

    # GENERATION LOGIC
    if st.button("Generate My Quiz 📝"):
        if quiz_subject:
            with st.spinner(f'Creating a {grade_level} quiz...'):
                # We update the prompt to include the grade_level
                quiz_prompt = f"""
                Create a {num_q} question multiple-choice quiz about {quiz_subject}.
                The difficulty must be strictly for {grade_level} students at a {difficulty} level.

                Return the response ONLY as a JSON list of objects.
                Format:
                [
                  {{
                    "question": "text",
                    "options": ["A", "B", "C", "D"],
                    "answer": "exact text of correct option"
                  }}
                ]
                """
                response = model.generate_content(quiz_prompt)

                try:
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state.quiz_data = json.loads(raw_json)
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                except Exception as e:
                    st.error("The AI had trouble formatting the quiz. Please try again!")
        else:
            st.warning("Please enter a subject first!")

    # DISPLAY & GRADING LOGIC (remains the same as before)
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

            # 1. Calculate Results
            for i, q_item in enumerate(st.session_state.quiz_data):
                user_choice = st.session_state.user_answers[i]
                if user_choice == q_item["answer"]:
                    st.success(f"Question {i+1}: Correct! 🌟")
                    score += 1
                else:
                    st.error(f"Question {i+1}: Not quite.")
                    st.info(f"The right answer was: **{q_item['answer']}**")

            # 2. Calculate Percentage
            total_questions = len(st.session_state.quiz_data)
            percentage = (score / total_questions) * 100

            # 3. Display Rewards & Encouragement
            st.header("Your Performance Report 📊")

            # Use columns to show score and percentage nicely
            col_res1, col_res2 = st.columns(2)
            col_res1.metric("Final Score", f"{score} / {total_questions}")
            col_res2.metric("Percentage", f"{percentage:g}%")

            # 4. Feedback Logic
            if percentage == 100:
                st.success("### 🏆 Mastermind Status!")
                st.write("Perfect score! You've completely mastered this topic. Time to level up to a 'Challenge' difficulty!")

            elif percentage >= 80:
                st.success("### 🚀 Outstanding Work!")
                st.write("You're a natural at this. Just a tiny bit more focus and you'll be at 100% in no time.")

            elif percentage >= 60:
                st.warning("### 📈 Great Progress!")
                st.write("You've got the core concepts down! Review the questions you missed to lock in that knowledge.")

            elif percentage >= 40:
                st.info("### 🧠 Brain Power Building!")
                st.write("Every mistake is just a data point for learning. Keep practicing—you're getting there!")

            else:
                st.error("### 🛡️ Don't Give Up!")
                st.write("This was a tough one, but persistence is the key to becoming a pro. Let's try a 'Basic' level quiz to build your confidence!")

            st.metric("Final Score", f"{score} / {len(st.session_state.quiz_data)}")

    # 1. Define the variable FIRST (even if empty)
    quiz_prompt = ""

    # 2. Only fill it when the button is clicked
    if st.button("Generate New Quiz 📝"):
        quiz_prompt = f"Create a {num_q} question multiple-choice quiz about {quiz_subject}."

        # 3. Only call the model INSIDE the same block
        with st.spinner('Generating...'):
            response = model.generate_content(quiz_prompt)
            # ... process response ...

# OR, if you need the variable elsewhere, ensure it is defined at the top of the tab
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
