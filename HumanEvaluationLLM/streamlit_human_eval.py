import streamlit as st
import sqlite3
import pandas as pd
import smtplib as sm
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import string

def init_db():
    conn = sqlite3.connect('activity_model_feedback.db')
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                code TEXT,
                expert TEXT,
                model_name TEXT,
                model_index INTEGER,
                prompt_index INTEGER,
                prompt_detail TEXT,
                comparison TEXT,
                feedback TEXT,
                satisfaction INTEGER
            )
        ''')
        # Ensure all required columns exist, particularly new columns added after initial deployment
        try:
            conn.execute('SELECT email FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN email TEXT')
        try:
            conn.execute('SELECT code FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN code TEXT')
        try:
            conn.execute('SELECT model_name FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN model_name TEXT')
        try:
            conn.execute('SELECT model_index FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN model_index INTEGER')
        try:
            conn.execute('SELECT satisfaction FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN satisfaction INTEGER')

def get_connection():
    return sqlite3.connect('activity_model_feedback.db')

def send_email(to_email, code):
    email_user = "hamzasharoon@gmail.com"  # Replace with your email
    email_password = "cxvs nzhz njug vncy"  # Replace with your email password

    subject_user = "Your Evaluation Code"
    html_body = f"Your code to continue the evaluation later is: {code}\nPlease don't forget this code."
    html_body = html_body.replace('\n', '<br>')

    try:
        server = sm.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_user, email_password)

        message = MIMEMultipart("alternative")
        message['Subject'] = subject_user
        message['From'] = email_user
        message['To'] = to_email

        html = MIMEText(html_body, "html")
        message.attach(html)

        server.sendmail(email_user, to_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def fetch_user_data(code):
    conn = get_connection()
    user_data = pd.read_sql_query(f"SELECT * FROM feedback WHERE code='{code}'", conn)
    return user_data

def save_responses(model_name, model_index, comparisons, feedbacks, satisfaction_scores, global_prompts):
    conn = get_connection()
    with conn:
        for i in range(3):
            conn.execute(
                'INSERT INTO feedback (name, email, code, expert, model_name, model_index, prompt_index, prompt_detail, comparison, feedback, satisfaction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (st.session_state['user_name'], st.session_state['user_email'], st.session_state['user_code'], st.session_state['expert_status'], model_name, model_index, i+1, global_prompts[i], comparisons[i], feedbacks[i], satisfaction_scores[i])
            )
    conn.commit()

def load_previous_responses(code, model_index):
    conn = get_connection()
    user_data = pd.read_sql_query(f"SELECT * FROM feedback WHERE code='{code}' AND model_index={model_index}", conn)
    if not user_data.empty:
        for i in range(3):
            st.session_state['comparisons'][model_index][i] = user_data['comparison'].iloc[i]
            st.session_state['feedbacks'][model_index][i] = user_data['feedback'].iloc[i]
            st.session_state['satisfaction'][model_index][i] = user_data['satisfaction'].iloc[i]

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
if 'satisfaction' not in st.session_state:
    st.session_state['satisfaction'] = [[1]*3 for _ in range(len(models))]
if 'submission_complete' not in st.session_state:
    st.session_state['submission_complete'] = False  # Track if the submission has been completed
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ''  # Store the user's name
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = ''  # Store the user's email
if 'user_code' not in st.session_state:
    st.session_state['user_code'] = ''  # Store the user's code
if 'expert_status' not in st.session_state:
    st.session_state['expert_status'] = 'Select an option'  # Store the user's expert status
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False  # Track if the email and code have been submitted
if 'invalid_code' not in st.session_state:
    st.session_state['invalid_code'] = False  # Track if an invalid code was entered

# Display title on the first page if not submitted
if st.session_state['current_model_index'] == 0 and not st.session_state['submitted']:
    st.markdown(
        "<h1 style='text-align: center;'>Evaluating Activity Models</h1>", 
        unsafe_allow_html=True
    )

# Checking if the submission has been completed
if st.session_state['submission_complete']:
    st.success("Thank you for completing all evaluations!")
else:
    # Check if a code is provided for resuming evaluation
    if not st.session_state['invalid_code']:
        st.sidebar.markdown(
            "<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>"
            "<strong>Enter your code to resume evaluation:</strong>"
            "</div>",
            unsafe_allow_html=True
        )
        resume_code = st.sidebar.text_input("")

        if st.sidebar.button('Resume') and resume_code:
            user_data = fetch_user_data(resume_code)
            if not user_data.empty:
                st.session_state['user_email'] = user_data['email'].iloc[0]
                st.session_state['expert_status'] = user_data['expert'].iloc[0]
                st.session_state['user_code'] = resume_code
                st.session_state['current_model_index'] = int(user_data['model_index'].max())
                st.session_state['user_name'] = user_data['name'].iloc[0]
                for i, model in enumerate(models):
                    model_data = user_data[user_data['model_index'] == i]
                    for j in range(3):
                        if j < len(model_data):
                            st.session_state['comparisons'][i][j] = model_data['comparison'].iloc[j]
                            st.session_state['feedbacks'][i][j] = model_data['feedback'].iloc[j]
                            st.session_state['satisfaction'][i][j] = model_data['satisfaction'].iloc[j]
                st.session_state['submitted'] = True
                st.session_state['invalid_code'] = False
                st.experimental_rerun()
            else:
                st.session_state['invalid_code'] = True
                st.sidebar.error("Invalid code. Please check and try again.")

    if st.session_state['invalid_code']:
        st.sidebar.error("Invalid code. Please check and try again.")
        st.sidebar.markdown(
            "<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>"
            "<strong>Please enter your email to generate an ID:</strong>"
            "</div>",
            unsafe_allow_html=True
        )
        user_email = st.sidebar.text_input("Enter your email", key='user_email_input_invalid')

        st.sidebar.markdown(
            "<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>"
            "<strong>Are you an expert in the field of Activity or Cardiac Exercise?</strong>"
            "</div>",
            unsafe_allow_html=True
        )
        expert_status = st.sidebar.selectbox("", ["Select an option", "Yes", "No"], key='expert_status_input_invalid')

        if user_email and expert_status != "Select an option":
            if st.sidebar.button('Generate New Code'):
                user_code = generate_code()
                st.session_state['user_email'] = user_email
                st.session_state['expert_status'] = expert_status
                st.session_state['user_code'] = user_code
                st.session_state['invalid_code'] = False
                if send_email(user_email, user_code):
                    st.sidebar.success(f"Your new code is: {user_code}\nPlease don't forget this code.")
                    st.sidebar.info("A new code has been sent to your email.")

                    # Save the new code and email to the database
                    conn = get_connection()
                    with conn:
                        conn.execute(
                            'INSERT INTO feedback (name, email, code, expert, model_name, model_index, prompt_index, prompt_detail, comparison, feedback, satisfaction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (st.session_state['user_name'], user_email, user_code, expert_status, models[st.session_state['current_model_index']], st.session_state['current_model_index'], None, '', '', '', 1)
                        )
                    conn.commit()
                    st.session_state['submitted'] = True
                    st.experimental_rerun()
                else:
                    st.sidebar.error("Failed to send email. Please try again.")
        else:
            st.markdown(
                "<div style='color: red; text-align: center; font-weight: bold;'>"
                "Please enter your email and select your expert status before proceeding."
                "</div>", 
                unsafe_allow_html=True
            )
            st.stop()

    # Input for user's email and expert status on the first page using sidebar
    if st.session_state['current_model_index'] == 0 and not st.session_state['user_code'] and not st.session_state['submitted'] and not st.session_state['invalid_code']:
        st.sidebar.markdown(
            "<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>"
            "<strong>Please enter your email to generate an ID:</strong>"
            "</div>",
            unsafe_allow_html=True
        )
        user_email = st.sidebar.text_input("Enter your email", key='user_email_input')

        st.sidebar.markdown(
            "<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>"
            "<strong>Are you an expert in the field of Activity or Cardiac Exercise?</strong>"
            "</div>",
            unsafe_allow_html=True
        )
        expert_status = st.sidebar.selectbox("", ["Select an option", "Yes", "No"], key='expert_status_input')

        if user_email and expert_status != "Select an option":
            if st.sidebar.button('Submit'):
                user_code = generate_code()
                st.session_state['user_email'] = user_email
                st.session_state['expert_status'] = expert_status
                st.session_state['user_code'] = user_code
                if send_email(user_email, user_code):
                    st.sidebar.success(f"Your code is: {user_code}\nPlease don't forget this code.")
                    st.sidebar.info("A code has been sent to your email.")

                    # Save the code and email to the database
                    conn = get_connection()
                    with conn:
                        conn.execute(
                            'INSERT INTO feedback (name, email, code, expert, model_name, model_index, prompt_index, prompt_detail, comparison, feedback, satisfaction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (st.session_state['user_name'], user_email, user_code, expert_status, models[st.session_state['current_model_index']], st.session_state['current_model_index'], None, '', '', '', 1)
                        )
                    conn.commit()
                    st.session_state['submitted'] = True
                    st.experimental_rerun()
                else:
                    st.sidebar.error("Failed to send email. Please try again.")
        else:
            st.markdown(
                "<div style='color: red; text-align: center; font-weight: bold;'>"
                "Please enter your email and select your expert status before proceeding."
                "</div>", 
                unsafe_allow_html=True
            )
            st.stop()

    # Continue with the evaluation process if the code is generated
    if st.session_state['submitted'] or st.session_state['user_code']:
        st.markdown(
            f"<h1 style='text-align: center;'>Evaluating: {models[int(st.session_state['current_model_index'])]}</h1>", 
            unsafe_allow_html=True
        )

        global_prompts = [
            "Is high intensity interval training only for healthy individuals?",
            "What is fitness age and is it relevant for me?",
            "What is cardiorespiratory fitness, and why does that matter for me?"
        ]

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

        satisfaction_labels = {
            1: 'A little satisfied',
            2: 'Some how satisfied',
            3: 'Satisfied',
            4: 'Very Satisfied',
            5: 'Extremely Satisfied'
        }

        incomplete_prompts = []  # List to store prompts where selections are missing

        for i in range(3):
            prompt_title = f'Prompt {i+1}: {global_prompts[i]}'
            st.subheader(prompt_title)
            if i < len(responses[models[int(st.session_state['current_model_index'])]]):
                response_pair = responses[models[int(st.session_state['current_model_index'])]][i]
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<h4 style='text-align: center; font-weight: bold;'>Response (A)</h4>", unsafe_allow_html=True)
                    st.write(response_pair[0])
                with col2:
                    st.markdown(f"<h4 style='text-align: center; font-weight: bold;'>Response (B)</h4>", unsafe_allow_html=True)
                    st.write(response_pair[1])

                comparison_options = ["Select an option", "A is better", "B is better"]
                st.markdown(f"<h5 style='font-weight: bold; margin-bottom: 0px;'>Choose the best response:</h5>", unsafe_allow_html=True)
                selected_option = st.radio(
                    "", comparison_options, index=0, key=f"comparison_{i}_{models[int(st.session_state['current_model_index'])]}"
                )
                if selected_option != "Select an option":
                    satisfaction_score = st.slider("Rate your satisfaction with the response (1-5):", 1, 5, st.session_state['satisfaction'][int(st.session_state['current_model_index'])][i], format="%d: %s" % (st.session_state['satisfaction'][int(st.session_state['current_model_index'])][i], satisfaction_labels[st.session_state['satisfaction'][int(st.session_state['current_model_index'])][i]]), key=f"satisfaction_{i}_{models[int(st.session_state['current_model_index'])]}")
                    st.session_state['satisfaction'][int(st.session_state['current_model_index'])][i] = satisfaction_score
                else:
                    incomplete_prompts.append(prompt_title)

                st.session_state['comparisons'][int(st.session_state['current_model_index'])][i] = selected_option
                feedback_key = f"feedback_{i}_{models[int(st.session_state['current_model_index'])]}"
                st.markdown(f"<h5 style='font-weight: bold;'>Provide additional feedback for this prompt (Optional):</h5>", unsafe_allow_html=True)
                st.session_state['feedbacks'][int(st.session_state['current_model_index'])][i] = st.text_area("", key=feedback_key)

        if incomplete_prompts:
            st.warning(f"Please complete all selections before proceeding. Missing selections for: {', '.join(incomplete_prompts)}.")

        prev_button, next_button = st.columns(2)
        with prev_button:
            if st.button('Previous Model') and int(st.session_state['current_model_index']) > 0:
                load_previous_responses(st.session_state['user_code'], int(st.session_state['current_model_index']) - 1)
                st.session_state['current_model_index'] = int(st.session_state['current_model_index']) - 1
                st.experimental_rerun()

        with next_button:
            if not incomplete_prompts and st.button('Next Model') and int(st.session_state['current_model_index']) < len(models) - 1:
                save_responses(models[int(st.session_state['current_model_index'])], int(st.session_state['current_model_index']), st.session_state['comparisons'][int(st.session_state['current_model_index'])], st.session_state['feedbacks'][int(st.session_state['current_model_index'])], st.session_state['satisfaction'][int(st.session_state['current_model_index'])], global_prompts)
                st.session_state['current_model_index'] = int(st.session_state['current_model_index']) + 1
                st.experimental_rerun()

        if int(st.session_state['current_model_index']) == len(models) - 1:
            if not incomplete_prompts and st.button('Submit All Evaluations'):
                try:
                    save_responses(models[int(st.session_state['current_model_index'])], int(st.session_state['current_model_index']), st.session_state['comparisons'][int(st.session_state['current_model_index'])], st.session_state['feedbacks'][int(st.session_state['current_model_index'])], st.session_state['satisfaction'][int(st.session_state['current_model_index'])], global_prompts)
                    st.session_state['submission_complete'] = True  # Set submission complete to True
                    st.experimental_rerun()  # Rerun to switch to the thank you page
                except Exception as e:
                    st.error(f"An error occurred: {e}")
