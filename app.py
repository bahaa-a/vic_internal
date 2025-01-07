import streamlit as st
from essay_grader import EssayGrader


st.set_page_config("Victoria Internal Tester", page_icon="📚", layout="centered")
st.title("Victoria Internal Tester")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

with st.form("login form"):
    col1, col2 = st.columns(2)
    with col1:
        user = st.text_input("username")
    with col2:
        pw = st.text_input("password", type="password")
    login = st.form_submit_button("login")

if login:
    if st.secrets["usernames"].get(user, None) == pw:
        st.session_state["logged_in"] = True
    else:
        st.error("wrong user/pw")

if st.session_state.get("logged_in"):
    with st.form("call_vic_models"):
        col1, col2 = st.columns(2)
        with col1:
            task_type = st.radio("task type", ["narrative", "persuasive"])
        with col2:
            student_year_level = st.slider("student year level", 2, 10, 5, 1)

        student_essay = st.text_area("student response")

        submitted = st.form_submit_button(
            "submit response", icon="🚨", use_container_width=True
        )

    if submitted:
        essay_grader: EssayGrader = EssayGrader(
            task_type=task_type,
            student_essay=student_essay,
            student_year_level=student_year_level,
            openai_config=st.secrets["openai_config"],
            prompts_config=st.secrets["prompts_config"],
        )
        with st.status("getting grades and feedback"):
            st.write("🚀 **calling grading model**")
            essay_grader.get_openai_score()
            st.write(f"✅ grades received in **{essay_grader.score_time} seconds**")
            st.write("🚀 calling feedback model")
            essay_grader.get_openai_feedback()
            st.write(
                f"✅ feedback received in **{essay_grader.feedback_time} seconds**"
            )
        st.subheader("feedback flesch metrics")
        col1, col2 = st.columns(2)
        col1.metric(
            "expected flesch based on age",
            essay_grader.student_expected_flesch,
            help="higher number = easier to read - based on student age - ideally the difference between expected and feedback should be 0 - more info: ask chatgpt to explain flesch_reading_ease",
        )
        col2.metric(
            "unoptimized flesch",
            essay_grader.feedback_flesch,
            essay_grader.feedback_flesch - essay_grader.student_expected_flesch,
        )
        st.info("""A higher flesch indicates that a piece of text is easier to read 
                    - a score of 100 is roughly the score for a fifth grader
                    - a score of 10 is roughly the score for a professional (university graduate)
                    """)
        st.divider()
        rubric_dims = list(essay_grader.marks.keys())
        for dim in rubric_dims:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(dim)
                st.metric(dim, essay_grader.marks[dim], label_visibility="hidden")
            with col2:
                st.subheader("Feedback")
                st.write(essay_grader.feedback[dim]["feedback"])
                st.subheader("Progression")
                st.write(essay_grader.feedback[dim]["progression"])
            st.divider()
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("raw marks json"):
                st.json(essay_grader.marks)
        with col2:
            with st.expander("raw feedback json"):
                st.json(essay_grader.feedback)
