
from deepseek import ask_ai

def ai_agent(user_question):
    try:
        return ask_ai(user_question)
    except Exception as e:
        return f"AI Error: {str(e)}"
