import streamlit as st
import sqlite3
import pandas as pd
import smtplib as sm
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import string
from datetime import datetime
import logging
import csv

# Set up logging
logging.basicConfig(filename='evaluation_log.txt', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

# Initialize the database
def init_db():
    conn = sqlite3.connect('activity_model_feedback.db')
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                code TEXT,
                expert TEXT,
                model_name TEXT,
                model_index INTEGER,
                prompt_index INTEGER,
                prompt_detail TEXT,
                comparison TEXT,
                feedback TEXT,
                satisfaction INTEGER,
                response_a TEXT,
                response_b TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Ensure all required columns exist
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
        try:
            conn.execute('SELECT response_a FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN response_a TEXT')
        try:
            conn.execute('SELECT response_b FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN response_b TEXT')
        try:
            conn.execute('SELECT timestamp FROM feedback LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE feedback ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP')

# Get a connection to the database
def get_connection():
    return sqlite3.connect('activity_model_feedback.db')

# Send an email with the evaluation code
def send_email(to_email, code):
    email_user = "hamzasharoon@gmail.com"  # Replace with your email
    email_password = "cxvs nzhz njug vncy"  # Replace with your email password

    subject_user = "Your Evaluation Activity Models Code"
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
        logging.info(f"Sent email to {to_email} with code {code}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")
        return False

# Generate a random code for the user
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

# Fetch user data from the database based on the code
def fetch_user_data(code):
    conn = get_connection()
    user_data = pd.read_sql_query(f"SELECT * FROM feedback WHERE code='{code}'", conn)
    return user_data

# Save or update user responses in the database and log to CSV
def save_responses(model_name, model_index, comparisons, feedbacks, satisfaction_scores, global_prompts, response_assignments):
    conn = get_connection()
    with conn:
        for i in range(3):
            response_a, response_b = response_assignments[i]
            prompt_index = i + 1
            cursor = conn.execute(
                'SELECT id FROM feedback WHERE code = ? AND model_name = ? AND model_index = ? AND prompt_index = ?',
                (st.session_state['user_code'], model_name, model_index, prompt_index)
            )
            row = cursor.fetchone()
            if row:
                conn.execute(
                    'UPDATE feedback SET comparison = ?, feedback = ?, satisfaction = ?, response_a = ?, response_b = ?, timestamp = ? WHERE id = ?',
                    (comparisons[i], feedbacks[i], satisfaction_scores[i], response_a, response_b, datetime.now(), row[0])
                )
                action = 'UPDATED'
            else:
                conn.execute(
                    'INSERT INTO feedback (name, code, expert, model_name, model_index, prompt_index, prompt_detail, comparison, feedback, satisfaction, response_a, response_b, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (st.session_state['user_name'], st.session_state['user_code'], st.session_state['expert_status'], model_name, model_index, prompt_index, global_prompts[i], comparisons[i], feedbacks[i], satisfaction_scores[i], response_a, response_b, datetime.now())
                )
                action = 'INSERTED'
            
            # Log the action
            logging.info(f"{action} feedback for user {st.session_state['user_code']} - Model: {model_name}, Prompt: {prompt_index}")
            
            # Log to CSV
            with open('feedback_log.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now(), st.session_state['user_name'], st.session_state['user_code'], st.session_state['expert_status'], model_name, model_index, prompt_index, global_prompts[i], comparisons[i], feedbacks[i], satisfaction_scores[i], response_a, response_b, action])
    
    conn.commit()

# Load previous responses from the database
def load_previous_responses(code, model_index):
    conn = get_connection()
    user_data = pd.read_sql_query(f"SELECT * FROM feedback WHERE code='{code}' AND model_index={model_index}", conn)
    if not user_data.empty:
        for i in range(3):
            st.session_state['comparisons'][model_index][i] = user_data['comparison'].iloc[i]
            st.session_state['feedbacks'][model_index][i] = user_data['feedback'].iloc[i]
            st.session_state['satisfaction'][model_index][i] = user_data['satisfaction'].iloc[i]
            st.session_state['response_assignments'][model_index].append((user_data['response_a'].iloc[i], user_data['response_b'].iloc[i]))
        logging.info(f"Loaded previous responses for user {code} - Model Index: {model_index}")

# Initialize the database
init_db()
st.set_page_config(layout="wide", page_title="Model Evaluation Interface")

models = ['Llama-2 13B', 'Mixtral 8*7B', 'LLama-3 8B', 'Mistral 7B v2', 'StableBeluga 7B']

# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
if 'current_model_index' not in st.session_state:
    st.session_state['current_model_index'] = 0
if 'comparisons' not in st.session_state:
    st.session_state['comparisons'] = [['Select an option']*3 for _ in range(len(models))]
if 'feedbacks' not in st.session_state:
    st.session_state['feedbacks'] = [['']*3 for _ in range(len(models))]
if 'satisfaction' not in st.session_state:
    st.session_state['satisfaction'] = [['Please enter your chosen response rating satisfaction']*3 for _ in range(len(models))]
if 'submission_complete' not in st.session_state:
    st.session_state['submission_complete'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ''
if 'user_code' not in st.session_state:
    st.session_state['user_code'] = ''
if 'expert_status' not in st.session_state:
    st.session_state['expert_status'] = 'Select an option'
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False
if 'invalid_code' not in st.session_state:
    st.session_state['invalid_code'] = False
if 'display_code_message' not in st.session_state:
    st.session_state['display_code_message'] = False
if 'generated_code' not in st.session_state:
    st.session_state['generated_code'] = ''
if 'response_assignments' not in st.session_state:
    st.session_state['response_assignments'] = [[] for _ in range(len(models))]
if 'responses' not in st.session_state:
    st.session_state['responses'] = {model: [] for model in models}
if 'email_failed' not in st.session_state:
    st.session_state['email_failed'] = False

# Load responses from the CSV file
if not any(st.session_state['responses'].values()):  # If responses are not loaded yet
    file_path = 'responses_doc_new.csv'
    data = pd.read_csv(file_path)
    model_count = {model: 0 for model in models}  # Dictionary to track occurrences of each model

    for index, row in data.iterrows():
        model = row['Model'].strip()
        response_base = row['Response-Base'].strip()
        response_finetuned = row['Response-FineTuned'].strip()
        if model in st.session_state['responses'] and model_count[model] < 3:
            st.session_state['responses'][model].append((response_base, response_finetuned))
            model_count[model] += 1

# Display title and project description on the first page if not submitted
if st.session_state['current_model_index'] == 0 and not st.session_state['submitted']:
    st.markdown(
        "<h1 style='text-align: center;'>Evaluating Activity Models</h1>", 
        unsafe_allow_html=True
    )
    st.markdown(
     """
        <h2>Project Description:</h2>
        <p>Welcome to the Human Evaluation of Large Language Models platform, designed to evaluate the performance of advanced AI models fine-tuned with domain-specific data. Our focus is on enhancing the capabilities of models like LLaMA, Mistral, and StableBeluga using specialized datasets from the Cardiac Exercise Research Group (CERG) at NTNU. This fine-tuning process aims to improve the models' accuracy and relevance in generating responses related to activity-health, fitness, and well-being. Compare outputs from various models and gain insights into their effectiveness in the healthcare sector.</p>
        <h2>Evaluation Steps:</h2>
        <ol>
            <li><b>Enter Your Email & Expert Status:</b> Provide your email and select your expertise status. Click "Submit" to receive a unique evaluation code.</li>
            <li><b>Evaluation Code:</b> This code will be sent to your email and displayed on the screen. <b style="color: lightcoral;">NOTE: Use this code to resume your evaluation from where you stop later if needed.</b></li>
            <li><b>Start Evaluation:</b> Read the project description and proceed with the evaluation.</li>
            <li><b>Compare Responses:</b> For each prompt, review two responses (A and B) generated by different models.</li>
            <li><b>Select the Best Response:</b> Choose the better response using the radio buttons ("A is better" or "B is better").</li>
            <li><b>Rate Your Satisfaction:</b> Rate your satisfaction with the chosen response on a scale from 1 (Very Dissatisfied) to 5 (Very Satisfied).</li>
            <li><b>Provide Feedback (Optional):</b> Add any additional feedback in the text area provided.</li>
            <li><b>Navigate Between Models:</b> Use "Previous Model" and "Next Model" buttons to evaluate different models.</li>
            <li><b>Submit Evaluations:</b> Once all evaluations are complete, click "Submit All Evaluations."</li>
        </ol>
        <p>Thank you for your participation! Your feedback is essential for improving AI models in the healthcare sector.</p>
        """,
        unsafe_allow_html=True
    )

# Checking if the submission has been completed
if st.session_state['submission_complete']:
    st.success("Thank you for completing all evaluations!")
else:
    # Check if a code is provided for resuming evaluation
    if not st.session_state['invalid_code'] and not st.session_state['email_failed']:
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
                st.session_state['user_code'] = resume_code
                st.session_state['expert_status'] = user_data['expert'].iloc[0]
                st.session_state['current_model_index'] = int(user_data['model_index'].max())
                st.session_state['user_name'] = user_data['name'].iloc[0]
                for i, model in enumerate(models):
                    model_data = user_data[user_data['model_index'] == i]
                    for j in range(3):
                        if j < len(model_data):
                            st.session_state['comparisons'][i][j] = model_data['comparison'].iloc[j]
                            st.session_state['feedbacks'][i][j] = model_data['feedback'].iloc[j]
                            st.session_state['satisfaction'][i][j] = model_data['satisfaction'].iloc[j]
                            st.session_state['response_assignments'][i].append((model_data['response_a'].iloc[j], model_data['response_b'].iloc[j]))
                st.session_state['submitted'] = True
                st.session_state['invalid_code'] = False
                st.experimental_rerun()
            else:
                st.session_state['invalid_code'] = True
                st.sidebar.error("Invalid code. Please check and try again.")
                logging.warning(f"Invalid code entered: {resume_code}")

    if st.session_state['invalid_code']:
        st.sidebar.error("Invalid code. Please check and try again.")
        if st.sidebar.button('Generate New Code'):
            st.session_state['invalid_code'] = False
            st.session_state['display_code_message'] = False

    # Display the stored code and message if they exist
    if st.session_state['display_code_message']:
        st.sidebar.markdown(
            f"<div style='background-color: #d3f9d8; padding: 10px; border-radius: 5px; text-align: center;'>"
            f"<strong>Your new code is: {st.session_state['generated_code']}</strong><br>"
            f"Please use this code to resume your evaluation later from where you stopped."
            f"<strong>\t \n The new code is sent to your email</strong><br>"
            f"</div>",
            unsafe_allow_html=True
        )

    # Display the form to enter email and generate a new code if email sending failed
    if st.session_state['email_failed']:
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
                st.session_state['expert_status'] = expert_status
                st.session_state['user_code'] = user_code
                if send_email(user_email, user_code):
                    st.sidebar.success(f"Your new code is: {user_code}\nPlease don't forget this code.")
                    st.sidebar.info("A new code has been sent to your email.")

                    # Store the code and message in session state
                    st.session_state['generated_code'] = user_code
                    st.session_state['display_code_message'] = True
                    st.session_state['email_failed'] = False

                    # Save the new code to the database
                    conn = get_connection()
                    with conn:
                        conn.execute(
                            'INSERT INTO feedback (name, code, expert, model_name, model_index, prompt_index, prompt_detail, comparison, feedback, satisfaction, response_a, response_b, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (st.session_state['user_name'], user_code, expert_status, models[st.session_state['current_model_index']], st.session_state['current_model_index'], None, '', '', '', 'Please enter your chosen response rating satisfaction', '', '', datetime.now())
                        )
                    conn.commit()
                    st.session_state['submitted'] = True
                    st.experimental_rerun()
                else:
                    st.sidebar.error("Failed to send email. Please try again.")
                    st.session_state['email_failed'] = True
                    logging.error(f"Failed to send email to {user_email}")
        else:
            st.markdown(
                "<div style='color: red; text-align: center; font-weight: bold;'>"
                "Please enter your email and select your expert status before proceeding."
                "</div>", 
                unsafe_allow_html=True
            )
            st.stop()

    # Input for user's email and expert status on the first page using sidebar
    if st.session_state['current_model_index'] == 0 and not st.session_state['user_code'] and not st.session_state['submitted'] and not st.session_state['invalid_code'] and not st.session_state['email_failed']:
        st.sidebar.markdown(
            "<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>"
            "<strong>Please enter your email to generate an ID (code):</strong>"
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
        expert_status = st.sidebar.selectbox("", ["Select an option", "Yes", "Some Domain", "No"], key='expert_status_input')

        if user_email and expert_status != "Select an option":
            if st.sidebar.button('Submit'):
                user_code = generate_code()
                st.session_state['expert_status'] = expert_status
                st.session_state['user_code'] = user_code
                if send_email(user_email, user_code):
                    st.sidebar.success(f"Your code is: {user_code}\nPlease don't forget this code.")
                    st.sidebar.info("A code has been sent to your email.")

                    # Store the code and message in session state
                    st.session_state['generated_code'] = user_code
                    st.session_state['display_code_message'] = True

                    # Save the code to the database
                    conn = get_connection()
                    with conn:
                        conn.execute(
                            'INSERT INTO feedback (name, code, expert, model_name, model_index, prompt_index, prompt_detail, comparison, feedback, satisfaction, response_a, response_b, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (st.session_state['user_name'], user_code, expert_status, models[st.session_state['current_model_index']], st.session_state['current_model_index'], None, '', '', '', 'Please enter your chosen response rating satisfaction', '', '', datetime.now())
                        )
                    conn.commit()
                    st.session_state['submitted'] = True
                    st.session_state['email_failed'] = False  # Reset the email failed flag
                    st.experimental_rerun()
                else:
                    st.sidebar.error("Failed to send email. Please try again.")
                    st.session_state['email_failed'] = True
                    logging.error(f"Failed to send email to {user_email}")
        else:
            st.markdown(
                "<div style='color: red; text-align: center; font-weight: bold;'>"
                "Please enter your email and select your expert status before proceeding."
                "</div>", 
                unsafe_allow_html=True
            )
            st.stop()

    # Randomize responses only if it hasn't been done for the current user and model
    if not st.session_state['response_assignments'][int(st.session_state['current_model_index'])]:
        current_model = models[int(st.session_state['current_model_index'])]
        for i in range(3):
            response_base, response_finetuned = st.session_state['responses'][current_model][i]
            response_pair = [(response_base, "base"), (response_finetuned, "finetuned")]
            random.shuffle(response_pair)  # Randomly shuffle the responses
            st.session_state['response_assignments'][int(st.session_state['current_model_index'])].append((response_pair[0][1], response_pair[1][1]))

    # Continue with the evaluation process if the code is generated and email has not failed
    if (st.session_state['submitted'] or st.session_state['user_code']) and not st.session_state['email_failed']:
        st.markdown(
            f"<h1 style='text-align: center;'>Evaluating: {models[int(st.session_state['current_model_index'])]}</h1>", 
            unsafe_allow_html=True
        )

        global_prompts = [
            "Is high intensity interval training only for healthy individuals?",
            "What is fitness age and is it relevant for me?",
            "What is cardiorespiratory fitness, and why does that matter for me?"
        ]

        satisfaction_labels = {
            1: 'Very Dissatisfied',
            2: 'Dissatisfied',
            3: 'Neutral',
            4: 'Satisfied',
            5: 'Very Satisfied'
        }

        incomplete_prompts = []  # List to store prompts where selections are missing

        for i in range(3):
            prompt_title = f'Prompt {i+1}: {global_prompts[i]}'
            st.subheader(prompt_title)
            response_base, response_finetuned = st.session_state['responses'][models[int(st.session_state['current_model_index'])]][i]
            response_assignment = st.session_state['response_assignments'][int(st.session_state['current_model_index'])][i]

            if response_assignment[0] == "base":
                response_a, response_b = response_base, response_finetuned
            else:
                response_a, response_b = response_finetuned, response_base

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<h4 style='text-align: center; font-weight: bold;'>Response (A)</h4>", unsafe_allow_html=True)
                st.write(response_a)
            with col2:
                st.markdown(f"<h4 style='text-align: center; font-weight: bold;'>Response (B)</h4>", unsafe_allow_html=True)
                st.write(response_b)

            comparison_options = ["Select an option", "A is better", "B is better"]
            selected_comparison = st.session_state['comparisons'][int(st.session_state['current_model_index'])][i]
            if selected_comparison not in comparison_options:
                selected_comparison = "Select an option"
            st.markdown(f"<h5 style='font-weight: bold; margin-bottom: 0px;'>Choose the best response:</h5>", unsafe_allow_html=True)
            selected_option = st.radio(
                "", comparison_options, index=comparison_options.index(selected_comparison), key=f"comparison_{i}_{models[int(st.session_state['current_model_index'])]}"
            )
            if selected_option != "Select an option":
                st.markdown(
                    """
                    <style>
                        .stRadio label {
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            width: 100%;
                            padding: 5px 0;
                            background-color: #f0f0f0;
                            border: 1px solid #ccc;
                            border-radius: 5px;
                            cursor: pointer;
                            transition: background-color 0.2s ease;
                        }
                        .stRadio input[type="radio"]:checked + label {
                            background-color: #007bff;
                            color: white;
                        }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                satisfaction_options = ["Please enter your chosen response rating satisfaction", 1, 2, 3, 4, 5]
                selected_satisfaction = st.session_state['satisfaction'][int(st.session_state['current_model_index'])][i]
                if selected_satisfaction not in satisfaction_options:
                    selected_satisfaction = "Please enter your chosen response rating satisfaction"
                st.markdown("<b style='color: red;'>Please rate your satisfaction with the selected best response on a scale from 1 to 5, where 1 means 'Very Dissatisfied' and 5 means 'Very Satisfied':</b>", unsafe_allow_html=True)
                satisfaction_score = st.selectbox(
                    "", satisfaction_options, 
                    index=satisfaction_options.index(selected_satisfaction),
                    format_func=lambda x: f"{x} {satisfaction_labels[x]}" if isinstance(x, int) else x,
                    key=f"satisfaction_{i}_{models[int(st.session_state['current_model_index'])]}"
                )
                st.session_state['satisfaction'][int(st.session_state['current_model_index'])][i] = satisfaction_score
            else:
                incomplete_prompts.append(prompt_title)

            st.session_state['comparisons'][int(st.session_state['current_model_index'])][i] = selected_option
            feedback_key = f"feedback_{i}_{models[int(st.session_state['current_model_index'])]}"
            st.markdown(f"<h5 style='font-weight: bold;'>Provide additional feedback for this prompt (Optional):</h5>", unsafe_allow_html=True)
            st.session_state['feedbacks'][int(st.session_state['current_model_index'])][i] = st.text_area("", st.session_state['feedbacks'][int(st.session_state['current_model_index'])][i], key=feedback_key)

        missing_satisfaction = [f'Prompt {i+1}' for i, satisfaction in enumerate(st.session_state['satisfaction'][int(st.session_state['current_model_index'])]) if satisfaction == "Please enter your chosen response rating satisfaction"]
        if incomplete_prompts or missing_satisfaction:
            st.warning(f"Please complete all selections before proceeding. Missing selections for: {', '.join(incomplete_prompts + missing_satisfaction)}.")
            logging.warning(f"User {st.session_state['user_code']} has incomplete selections: {', '.join(incomplete_prompts + missing_satisfaction)}")

        prev_button, next_button = st.columns(2)
        with prev_button:
            if st.button('Previous Model') and int(st.session_state['current_model_index']) > 0:
                save_responses(models[int(st.session_state['current_model_index'])], int(st.session_state['current_model_index']), st.session_state['comparisons'][int(st.session_state['current_model_index'])], st.session_state['feedbacks'][int(st.session_state['current_model_index'])], st.session_state['satisfaction'][int(st.session_state['current_model_index'])], global_prompts, st.session_state['response_assignments'][int(st.session_state['current_model_index'])])
                st.session_state['current_model_index'] = int(st.session_state['current_model_index']) - 1
                load_previous_responses(st.session_state['user_code'], st.session_state['current_model_index'])
                st.experimental_rerun()

        if int(st.session_state['current_model_index']) < len(models) - 1:
            with next_button:
                if not incomplete_prompts and not missing_satisfaction and st.button('Next Model'):
                    save_responses(models[int(st.session_state['current_model_index'])], int(st.session_state['current_model_index']), st.session_state['comparisons'][int(st.session_state['current_model_index'])], st.session_state['feedbacks'][int(st.session_state['current_model_index'])], st.session_state['satisfaction'][int(st.session_state['current_model_index'])], global_prompts, st.session_state['response_assignments'][int(st.session_state['current_model_index'])])
                    st.session_state['current_model_index'] = int(st.session_state['current_model_index']) + 1
                    st.experimental_rerun()

        if int(st.session_state['current_model_index']) == len(models) - 1:
            if not incomplete_prompts and not missing_satisfaction:
                st.markdown("<br>", unsafe_allow_html=True)  # Add a space before the submit button
                if st.button('Submit All Evaluations'):
                    try:
                        save_responses(models[int(st.session_state['current_model_index'])], int(st.session_state['current_model_index']), st.session_state['comparisons'][int(st.session_state['current_model_index'])], st.session_state['feedbacks'][int(st.session_state['current_model_index'])], st.session_state['satisfaction'][int(st.session_state['current_model_index'])], global_prompts, st.session_state['response_assignments'][int(st.session_state['current_model_index'])])
                        st.session_state['submission_complete'] = True  # Set submission complete to True
                        st.experimental_rerun()  # Rerun to switch to the thank you page
                        logging.info(f"User {st.session_state['user_code']} completed all evaluations.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        logging.error(f"An error occurred during submission: {e}")
