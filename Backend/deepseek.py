import 'dotenv/config';
import requests

process.env.API_KEY


def ask_ai(question):
    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {process.env.API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful financial advisor in Pakistan. Give clear, practical, and relevant answers about expenses, savings, and budgeting in PKR. Keep responses concise (under 100 words)."
            },
            {
                "role": "user",
                "content": question
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            return f"Financial Tip: Start by tracking your small daily spends. (API Error {response.status_code})"

        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "The AI is taking a bit longer to think. Please try again with a simpler question!"
    except Exception as e:
        return f"Budget Tip: Try to save 20% of your income. (Could not connect to AI Agent: {str(e)})"
