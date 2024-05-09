import streamlit as st
import sqlite3

def init_db():
    conn = sqlite3.connect('activity_model_feedback.db')
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT,
                prompt_index INTEGER,
                prompt_detail TEXT,
                feedback TEXT,
                feedback TEXT
            )
        ''')

def get_connection():
    return sqlite3.connect('activity_model_feedback.db')

init_db()
st.set_page_config(layout="wide", page_title="Model Evaluation Interface")

if 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
if 'current_model_index' not in st.session_state:
    st.session_state['current_model_index'] = 0
if 'comparisons' not in st.session_state:
    st.session_state['comparisons'] = [['Select an option']*3 for _ in range(5)]
if 'feedbacks' not in st.session_state:
    st.session_state['feedbacks'] = [['']*3 for _ in range(5)]

models = ['Llama 7B', 'Llama 13B', 'Mistral 7B v1', 'Mistral 7B v2', 'StableBeluga 7B']

# Global prompts applicable to all models
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
responses = {
    'Llama 7B': [
        ('Response A1', 'Response B1'),
        ('Response A2', 'Response B2'),
        ('Response A3', 'Response B3')
    ],
    'Llama 13B': [
        ('Response A1', 'Response B1'),
        ('Response A2', 'Response B2'),
        ('Response A3', 'Response B3')
    ],
    'Mistral 7B v1': [
        ('Response A1', 'Response B1'),
        ('Response A2', 'Response B2'),
        ('Response A3', 'Response B3')
    ],
    'Mistral 7B v2': [
        ('Response A1', 'Response B1'),
        ('Response A2', 'Response B2'),
        ('Response A3', 'Response B3')
    ],
    'StableBeluga 7B': [
        ('Response A1', 'Response B1'),
        ('Response A2', 'Response B2'),
        ('Response A3', 'Response B3')
    ]
}


incomplete_prompts = []  # List to store prompts where selections are missing

for i in range(3):
    prompt_title = f'Prompt {i+1}: {global_prompts[i]}'
    st.subheader(prompt_title)
    response_pair = responses[models[st.session_state['current_model_index']]][i]
    col1, col2 = st.columns(2)
    with col1:
        st.write("Response (A)")
        st.write(response_pair[0])
    with col2:
        st.write("Response (B)")
        st.write(response_pair[1])

    comparison_options = ["Select an option", "A is better", "B is better", "Neither is better", "A and B are the same"]
    selected_option = st.radio(
        "Choose the best response:", comparison_options, index=0, key=f"comparison_{i}_{models[st.session_state['current_model_index']]}"
    )
    if selected_option == "Select an option":
        incomplete_prompts.append(prompt_title)  # Add the prompt title to the list if not completed

    st.session_state['comparisons'][st.session_state['current_model_index']][i] = selected_option
    feedback_key = f"feedback_{i}_{models[st.session_state['current_model_index']]}"
    st.session_state['feedbacks'][st.session_state['current_model_index']][i] = st.text_area(
        "Provide additional feedback for this prompt (Optional) :", key=feedback_key
    )

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
                            'INSERT INTO feedback (model, prompt_index, prompt_detail, comparison, feedback) VALUES (?, ?, ?, ?, ?)',
                            (model, i+1, global_prompts[i], st.session_state['comparisons'][idx][i], st.session_state['feedbacks'][idx][i])
                        )
            conn.commit()
            st.success("Thank you for completing all evaluations!")
        except Exception as e:
            st.error(f"An error occurred: {e}")
