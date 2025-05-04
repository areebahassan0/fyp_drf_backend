
from fyp.settings import MISTRAL_API_KEY
import requests
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, 'chatbot/faq.txt')) as f:
    faqs_content = f.read()

with open(os.path.join(BASE_DIR, 'chatbot/categories.txt')) as f:
    categories_content = f.read()

def improved_ask_mistral(prompt=None, chat_history=None, temperature=0.0):
    """Send full chat history or prompt to Mistral API"""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    # If chat_history is not provided, build it from single prompt
    if chat_history is None:
        chat_history = [{"role": "user", "content": prompt}]

    data = {
        "model": "mistral-medium",
        "messages": chat_history,
        "temperature": temperature
    }

    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"
    
def generate_final_response(user_query, chat_history=None):
    if chat_history is None:
        chat_history = []

    # Define the system prompt with all necessary background
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful, polite electricity company chatbot.\n\n"
            "You can answer customer questions and help them file complaints.\n"
            "Here are some FAQs:\n"
            f"{faqs_content}\n\n"
            "Here are complaint categories and subcategories:\n"
            f"{categories_content}\n\n"
            "Your job is to:\n"
            "- Answer using FAQs if possible.\n"
            "- If it's a complaint, classify it and suggest a category/subcategory with a complaint link.\n"
            "- If it doesn’t match anything, suggest filing under 'Other' at /complaints/loadshedding/other.\n"
            "- Never mention the source of information (no file names or tech references).\n"
            "- Speak clearly and politely."
        )
    }

    # Only add system prompt at the beginning of conversation
    if not chat_history or chat_history[0]["role"] != "system":
        chat_history.insert(0, system_message)

    # Add user's message
    chat_history.append({"role": "user", "content": user_query})

    # Call Mistral API
    bot_reply = improved_ask_mistral(chat_history=chat_history, temperature=0).strip()

    # Add bot response to history
    chat_history.append({"role": "assistant", "content": bot_reply})

    return bot_reply, chat_history