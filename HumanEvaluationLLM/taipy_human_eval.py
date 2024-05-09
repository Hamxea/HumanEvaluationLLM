from taipy import Gui, Config

# Create the GUI
gui = Gui()

# Configuring the main page
md = """
# Model Evaluation Interface

Select a Model: ^{model_selector}
## Base Model Response
{responses[model_selector][0]}
## Fine-tuned Model Response
{responses[model_selector][1]}
Feedback: ^{feedback_area}
<button onclick='submit'>Submit Evaluation</button>
"""

# Model responses and selector
models = ['Llama 7B', 'Llama 13B', 'Mistral 7B v1', 'Mistral 7B v2', 'StableBeluga 7B']
responses = {
    'Llama 7B': ['Response 1 from base model', 'Response 1 from fine-tuned model'],
    # Add other models responses similarly
}

gui.add_page(name="Main Page", markdown=md, bind={'model_selector': models[0], 'feedback_area': ""})

# Callback for the submit button
def submit(gui):
    feedback = gui.feedback_area
    # Process the feedback (store in database, etc.)
    gui.feedback_area = ""
    gui.show_toast("Thank you for your feedback!")

gui.run()
