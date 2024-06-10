

# Evaluating Activity Models

#### Models Interface Trial: https://cergdigitaltwinchat.idi.ntnu.no/
#### Models Feedback Evaluation: https://humanevaluationllm.onrender.com/ 

## Project Description:
Welcome to the Human Evaluation of Large Language Models platform, designed to evaluate the performance of advanced AI models fine-tuned with domain-specific data. Our focus is on enhancing the capabilities of models like LLaMA, Mistral, and StableBeluga using specialized datasets from the Cardiac Exercise Research Group (CERG) at NTNU. This fine-tuning process aims to improve the models' accuracy and relevance in generating responses related to activity-health, fitness, and well-being. Compare outputs from various models and gain insights into their effectiveness in the healthcare sector.
# Activity Model Evaluation Interface

This interface is designed to facilitate the evaluation of advanced AI models fine-tuned with domain-specific data. The evaluation process involves comparing responses generated by different models for specific prompts related to health, fitness, and well-being.

## Key Features

### Database Initialization and Connection
- **Database Initialization**: The `init_db` function initializes the SQLite database, creating the necessary tables and ensuring all required columns exist.
- **Database Connection**: The `get_connection` function provides a connection to the SQLite database.

### Email Functionality
- **Send Email**: The `send_email` function sends an email containing an evaluation code to the user.
- **Generate Code**: The `generate_code` function generates a random code for user identification.

### Data Handling
- **Fetch User Data**: The `fetch_user_data` function retrieves user data from the database based on the provided code.
- **Save Responses**: The `save_responses` function saves or updates user responses in the database and logs the actions to a CSV file.
- **Load Previous Responses**: The `load_previous_responses` function loads previous responses from the database if the evaluation is resumed.

### Session Management
- **Session State Variables**: Session state variables are initialized to manage the current state of the evaluation process.
- **Load Responses**: Responses are loaded from a CSV file and assigned to session state variables to ensure the continuity of the evaluation.

### Evaluation Process
- **User Authentication**: Users are prompted to enter their email and expert status to generate a unique code for evaluation.
- **Resume Evaluation**: Users can resume their evaluation by entering their code.
- **Evaluation Steps**:
  - Compare responses from different models for specific prompts.
  - Select the best response and rate satisfaction.
  - Provide additional feedback for each prompt if desired.

### Navigation and Submission
- **Navigate Models and Prompts**: Users can navigate between different models and prompts.
- **Incremental Save**: Responses are saved incrementally.
- **Final Submission**: Final submission of all evaluations is logged and saved.

### Logging
- **Action and Error Logging**: Actions and errors are logged to ensure traceability and troubleshooting.

## Evaluation Interface Structure

### Introduction and Project Description
- **Title and Description**: Title and project description are displayed on the first page.
- **Sidebar Prompts**: Sidebar prompts for email and expert status to generate a unique evaluation code.

### Evaluation Process
- **Response Comparison**: Users compare responses from different models for specific prompts.
- **Randomization**: Responses are randomized to prevent bias.
- **Selection and Rating**: Users select the best response and rate their satisfaction.
- **Feedback**: Additional feedback can be provided for each prompt.

### Navigation and Submission
- **Model and Prompt Navigation**: Users can navigate between different models and prompts.
- **Incremental Saving**: Responses are saved incrementally.
- **Final Submission**: All evaluations are submitted, logged, and saved.

### Error Handling and Logging
- **Graceful Handling**: Invalid codes and email sending failures are handled gracefully with appropriate messages.
- **Traceability**: All actions are logged for traceability.

This interface ensures a structured and efficient evaluation process, capturing user feedback and ratings comprehensively.

## Evaluation Steps

1. **Enter Your Email & Expert Status**: Provide your email and select your expertise status. Click "Submit" to receive a unique evaluation code.
2. **Evaluation Code**: This code will be sent to your email and displayed on the screen. **NOTE**: Use this code to resume your evaluation from where you stop later if needed.
3. **Start Evaluation**: Read the project description and proceed with the evaluation.
4. **Compare Responses**: For each prompt, review two responses (A and B) generated by different models.
5. **Select the Best Response**: Choose the better response using the radio buttons ("A is better" or "B is better").
6. **Rate Your Satisfaction**: Rate your satisfaction with the chosen response on a scale from 1 (Very Dissatisfied) to 5 (Very Satisfied).
7. **Provide Feedback (Optional)**: Add any additional feedback in the text area provided.
8. **Navigate Between Models**: Use "Previous Model" and "Next Model" buttons to evaluate different models.
9. **Submit Evaluations**: Once all evaluations are complete, click "Submit All Evaluations."

Thank you for your participation! Your feedback is essential for improving AI models in the healthcare sector.

**Note**: Ensure to replace placeholders for email credentials with actual values for the email functionality to work correctly.
