import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# Load environment variables
load_dotenv()

# Create OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Model
MODEL = "gpt-4o-mini"

# System prompt
SYSTEM_PROMPT = """
You are a friendly and helpful travel agent specializing in Paris, France.

Your job is to help tourists plan their trip to Paris.

You can answer questions about:
- Famous landmarks
- Museums
- Restaurants
- Hotels
- Transportation
- Distances between attractions
- Things to do
- Tourist attractions
- Suggested itineraries
- Best times to visit
- Travel tips
- Paris neighborhoods

Keep your answers concise, practical, and easy to understand.

If the user asks for recommendations, provide a few good options
and briefly explain why they are worth visiting.

If you are unsure about something, clearly say that you are unsure
rather than making up information.

You should behave like a friendly professional travel agent.
"""


def travel_agent(message, history):
    """
    Generate a response from the OpenAI model.

    message:
        Current user message

    history:
        Previous Gradio conversation
    """

    history = history or []

    # Start with system message
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Add previous conversation
    for item in history:

        # New Gradio format
        if isinstance(item, dict):
            role = item.get("role")
            content = item.get("content")

            if role in ["user", "assistant"]:
                messages.append({
                    "role": role,
                    "content": content
                })

        # Older Gradio format
        elif isinstance(item, (list, tuple)) and len(item) == 2:

            user_message, assistant_message = item

            if user_message:
                messages.append({
                    "role": "user",
                    "content": user_message
                })

            if assistant_message:
                messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })

    # Add current user message
    messages.append({
        "role": "user",
        "content": message
    })

    # Call OpenAI
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.0,
        max_tokens=300
    )

    # Extract response
    answer = response.choices[0].message.content

    # gr.Chatbot(type="messages") expects the full history back, not just the reply
    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]

    return new_history, ""


# -----------------------------
# Gradio UI
# -----------------------------

with gr.Blocks(
    title="Paris Travel Agent"
) as demo:

    gr.Markdown(
        """
        # 🇫🇷 Paris Travel Agent

        Ask me anything about traveling to Paris.

        **Examples:**
        - What is the most famous landmark in Paris?
        - How far is the Louvre from the Eiffel Tower?
        - What should I see at the Louvre?
        - Can you create a 3-day Paris itinerary?
        - What are the best areas to stay in Paris?
        """
    )

    chatbot = gr.Chatbot(
        label="Travel Agent",
        height=500
    )

    message = gr.Textbox(
        placeholder="Ask your travel question...",
        label="Your Question"
    )

    with gr.Row():
        send_button = gr.Button(
            "Ask Travel Agent",
            variant="primary"
        )

        clear_button = gr.Button(
            "Clear Chat"
        )

    # Send message
    send_button.click(
        travel_agent,
        inputs=[message, chatbot],
        outputs=[chatbot, message]
    )

    # Allow Enter key
    message.submit(
        travel_agent,
        inputs=[message, chatbot],
        outputs=[chatbot, message]
    )

    # Clear conversation
    clear_button.click(
        lambda: ([], ""),
        inputs=None,
        outputs=[chatbot, message]
    )


# Start application
if __name__ == "__main__":
    demo.launch()