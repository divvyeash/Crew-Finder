import os
import anthropic

# Real AI assistant for the CrewFinder widget, powered by Claude.
# Requires ANTHROPIC_API_KEY to be set in the environment (see .env.example).

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

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def get_chatbot_reply(user_message):
    client = _get_client()
    if client is None:
        return ("AI assistant isn't configured yet — ask the site admin to set "
                "ANTHROPIC_API_KEY. Meanwhile: use the tabs above to find Groups, "
                "Events, or Student Portfolios, and the filters to narrow results.")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()
    except Exception as e:
        print(f"[chatbot] Claude API error: {e}")
        return "Sorry, I'm having trouble thinking right now — please try again in a moment."