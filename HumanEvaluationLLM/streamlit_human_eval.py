import streamlit as st
import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('activity_model_feedback.db')
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                expert TEXT,
                model TEXT,
                prompt_index INTEGER,
                prompt_detail TEXT,
                comparison TEXT,
                feedback TEXT
            )
        ''')
        # Ensure all required columns exist, particularly new columns added after initial deployment
        try:
            conn.execute('SELECT prompt_detail FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN prompt_detail TEXT')

def get_connection():
    return sqlite3.connect('activity_model_feedback.db')

init_db()
st.set_page_config(layout="wide", page_title="Model Evaluation Interface")

models = ['Llama-2 13B', 'Mixtral 8*7B', 'LLama-3 8B', 'Mistral 7B v2', 'StableBeluga 7B']

if 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
if 'current_model_index' not in st.session_state:
    st.session_state['current_model_index'] = 0
if 'comparisons' not in st.session_state:
    st.session_state['comparisons'] = [['Select an option']*3 for _ in range(len(models))]
if 'feedbacks' not in st.session_state:
    st.session_state['feedbacks'] = [['']*3 for _ in range(len(models))]
if 'submission_complete' not in st.session_state:
    st.session_state['submission_complete'] = False  # Track if the submission has been completed
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ''  # Store the user's name
if 'expert_status' not in st.session_state:
    st.session_state['expert_status'] = 'Select an option'  # Store the user's expert status

# Checking if the submission has been completed
if st.session_state['submission_complete']:
    st.success("Thank you for completing all evaluations!")
else:
    # Input for user's name and expert status on the first page using sidebar
    if st.session_state['current_model_index'] == 0:
        st.sidebar.markdown(
            "<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>"
            "<strong>Please enter your full name or initials:</strong>"
            "</div>",
            unsafe_allow_html=True
        )
        user_name = st.sidebar.text_input("", key='user_name_input')

        st.sidebar.markdown(
            "<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>"
            "<strong>Are you an expert in the field of Activity or Cardiac Exercise?</strong>"
            "</div>",
            unsafe_allow_html=True
        )
        expert_status = st.sidebar.selectbox("", ["Select an option", "Yes", "No"], key='expert_status_input')

        if user_name and expert_status != "Select an option":
            if st.sidebar.button('Submit'):
                st.session_state['user_name'] = user_name
                st.session_state['expert_status'] = expert_status
        else:
            st.warning("Please fill in your full name and select your expert status before proceeding.")
            st.stop()

    # Continue with the evaluation process
    global_prompts = [
        "Is high intensity interval training only for healthy individuals?",
        "What is fitness age and is it relevant for me?",
        "What is cardiorespiratory fitness, and why does that matter for me?"
    ]

    st.markdown(
        f"<h1 style='text-align: center;'>Evaluating Activity Model: {models[st.session_state['current_model_index']]}</h1>", 
        unsafe_allow_html=True
    )

    # Define the responses dictionary with data for each model
    responses = {model: [] for model in models}

    # Load the new responses from the CSV file
    file_path = 'responses_doc_new.csv'
    data = pd.read_csv(file_path)
    model_count = {model: 0 for model in models}  # Dictionary to track occurrences of each model

    # Update the 'responses' dictionary with the new responses from the CSV file
    for index, row in data.iterrows():
        model = row['Model'].strip()
        response_a = row['Responses-A'].strip()
        response_b = row['Response-B'].strip()
        if model in responses and model_count[model] < 3:
            responses[model].append((response_a, response_b))
            model_count[model] += 1

    incomplete_prompts = []  # List to store prompts where selections are missing

    for i in range(3):
        prompt_title = f'Prompt {i+1}: {global_prompts[i]}'
        st.subheader(prompt_title)
        if i < len(responses[models[st.session_state['current_model_index']]]):
            response_pair = responses[models[st.session_state['current_model_index']]][i]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<h4 style='text-align: center; font-weight: bold;'>Response (A)</h4>", unsafe_allow_html=True)
                st.write(response_pair[0])
            with col2:
                st.markdown(f"<h4 style='text-align: center; font-weight: bold;'>Response (B)</h4>", unsafe_allow_html=True)
                st.write(response_pair[1])

            comparison_options = ["Select an option", "A is better", "B is better", "Neither is better"]
            st.markdown(f"<h5 style='font-weight: bold; margin-bottom: 0px;'>Choose the best response:</h5>", unsafe_allow_html=True)
            selected_option = st.radio(
                "", comparison_options, index=0, key=f"comparison_{i}_{models[st.session_state['current_model_index']]}"
            )
            if selected_option == "Select an option":
                incomplete_prompts.append(prompt_title)

            st.session_state['comparisons'][st.session_state['current_model_index']][i] = selected_option
            feedback_key = f"feedback_{i}_{models[st.session_state['current_model_index']]}"
            st.markdown(f"<h5 style='font-weight: bold;'>Provide additional feedback for this prompt (Optional):</h5>", unsafe_allow_html=True)
            st.session_state['feedbacks'][st.session_state['current_model_index']][i] = st.text_area("", key=feedback_key)

    if incomplete_prompts:
        st.warning(f"Please complete all selections before proceeding. Missing selections for: {', '.join(incomplete_prompts)}.")

    prev_button, next_button = st.columns(2)
    with prev_button:
        if st.button('Previous Model') and st.session_state['current_model_index'] > 0:
            st.session_state['current_model_index'] -= 1
            st.rerun()

    with next_button:
        if not incomplete_prompts and st.button('Next Model') and st.session_state['current_model_index'] < len(models) - 1:
            st.session_state['current_model_index'] += 1
            st.rerun()

    if st.session_state['current_model_index'] == len(models) - 1:
        if not incomplete_prompts and st.button('Submit All Evaluations'):
            try:
                conn = get_connection()
                with conn:
                    for idx, model in enumerate(models):
                        for i in range(3):
                            conn.execute(
                                'INSERT INTO feedback (name, expert, model, prompt_index, prompt_detail, comparison, feedback) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                (st.session_state['user_name'], st.session_state['expert_status'], model, i+1, global_prompts[i], st.session_state['comparisons'][idx][i], st.session_state['feedbacks'][idx][i])
                            )
                conn.commit()
                st.session_state['submission_complete'] = True  # Set submission complete to True
                st.experimental_rerun()  # Rerun to switch to the thank you page
            except Exception as e:
                st.error(f"An error occurred: {e}")
