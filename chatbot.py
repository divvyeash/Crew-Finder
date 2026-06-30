import os
import google.generativeai as genai

SYSTEM_PROMPT = """You are the CrewFinder Assistant, a friendly helper embedded in
CrewFinder, a website for Multimedia University (MMU) students to find group
project teammates, browse campus events, and message each other.

Help users with things like:
- How to search/filter for groups, events, or student profiles
- How to post a group or event
- How to message another student
- General encouragement about finding teammates

Keep answers short (2-4 sentences), warm, and specific to CrewFinder's features:
tabs are "Find Groups", "Events", and "Student Portfolios"; users can filter
profiles by Course/Skill; "Post Group"/"Post Event" buttons are in the navbar;
clicking "Message Leader" or "Send Message" opens a private chat.
If asked something unrelated to CrewFinder, answer briefly and steer back."""

_model = None

def _get_model():
    global _model
    if _model is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )
    return _model

def get_chatbot_reply(user_message):
    model = _get_model()
    if model is None:
        return ("AI assistant isn't configured yet — ask the site admin to set "
                "GEMINI_API_KEY. Meanwhile: use the tabs above to find Groups, "
                "Events, or Student Portfolios, and the filters to narrow results.")
    try:
        response = model.generate_content(user_message)
        return response.text.strip()
    except Exception as e:
        print(f"[chatbot] Gemini API error: {e}")
        return "Sorry, I'm having trouble thinking right now — please try again in a moment."