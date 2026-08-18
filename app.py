import logging
import os
import tempfile
from datetime import date
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
import gradio as gr

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("travel-agent")

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise SystemExit("OPENAI_API_KEY is not set. Add it to your .env file.")

# Create OpenAI client
client = OpenAI(api_key=API_KEY)

# Model and generation settings
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.4"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "800"))

# Caps how much conversation is replayed to the model, bounding cost per turn
MAX_HISTORY_MESSAGES = 20

# System prompt
SYSTEM_PROMPT = """
You are a friendly and helpful travel agent specializing in Paris, France.

Your job is to help tourists plan and enjoy their trip to Paris.

You can answer questions about:
- Famous landmarks and museums
- Restaurants, cafes, and food or drink recommendations
- Hotels and which neighborhoods suit different types of travelers
- Public transportation: Metro, RER, buses, taxis, and walking routes
- Distances and travel times between attractions
- Suggested itineraries for different trip lengths
- Best times of year to visit and how to avoid crowds
- Entry requirements: Schengen visa rules and ETIAS travel authorisation
    for eligible visa-exempt visitors
- Money matters: currency (Euro), typical payment methods, and tipping
    etiquette (service is usually already included; small extra tips for good
    service are appreciated but not required)
- Common tourist scams to watch out for: fake petitions or "gold ring" scams,
    friendship-bracelet scams, and distraction pickpocketing near major sights
    and on busy Metro lines
- Everyday practicalities: many museums close one day a week (for example the
    Louvre is closed on Tuesdays and the Musee d'Orsay is closed on Mondays),
    and many small restaurants and shops close on Sundays and/or for part of
    August
- Emergency numbers in France: 112 (general emergency), 15 (medical/SAMU),
    17 (police), 18 (fire brigade)
- Basic etiquette and a few useful French phrases (always greet with
    "Bonjour" before asking someone a question)
- Accessibility and family-friendly travel tips

Keep your answers concise, practical, and easy to understand.

If the user asks for recommendations, provide a few good options
and briefly explain why they are worth visiting.

Your knowledge has a training cutoff and you do not have live internet
access. Exact prices, opening hours, ticket availability, transport strikes,
and event dates change often. For anything time-sensitive like this, give
your best general guidance but clearly tell the user to confirm the current
details on the official website, app, or with their hotel/venue before
relying on it.

If you are unsure about something, clearly say that you are unsure
rather than making up information.

You should behave like a friendly professional travel agent.
"""


def _message_text(content):
    """gr.Chatbot message content can be a string or a list of parts; flatten to text."""

    if isinstance(content, list):
        return "".join(part if isinstance(part, str) else str(part) for part in content)

    return content if isinstance(content, str) else str(content)


def _current_date_note():
    """Grounds the model in the real current date/weekday for season and closure-day questions."""

    today = date.today()
    return f"\n\nToday's real date is {today:%A, %d %B %Y}."


def travel_agent(message, history):
    """
    Stream a response from the OpenAI model into the chat history.

    message:
        Current user message

    history:
        Previous Gradio conversation
    """

    history = list(history or [])

    if not message or not message.strip():
        yield history, "", ""
        return

    prior = [
        {"role": item["role"], "content": _message_text(item["content"])}
        for item in history
        if isinstance(item, dict) and item.get("role") in ("user", "assistant")
    ]

    messages = [{"role": "system", "content": SYSTEM_PROMPT + _current_date_note()}]
    messages.extend(prior[-MAX_HISTORY_MESSAGES:])
    messages.append({"role": "user", "content": message})

    # gr.Chatbot expects the full history back, not just the reply
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": ""},
    ]

    # Show the caller's message immediately, before waiting on the model
    yield history, "", ""

    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=True,
            stream_options={"include_usage": True},
        )

        usage = None

        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.content or ""

                if delta:
                    history[-1]["content"] += delta
                    yield history, "", gr.update()

            if chunk.usage:
                usage = chunk.usage

        footer = ""
        if usage:
            footer = (
                f"Last turn: {usage.prompt_tokens} prompt + "
                f"{usage.completion_tokens} completion = {usage.total_tokens} tokens"
            )

        yield history, "", footer
        return

    except OpenAIError:
        logger.exception("OpenAI request failed")
        history[-1]["content"] = (
            "Sorry, I couldn't reach the travel service just then. "
            "Please try again in a moment."
        )

    yield history, "", ""


def regenerate(history):
    """Drop the last exchange and resend the same user message."""

    history = list(history or [])
    last_user_message = None

    for i in range(len(history) - 1, -1, -1):
        if history[i].get("role") == "user":
            last_user_message = _message_text(history[i]["content"])
            history = history[:i]
            break

    if last_user_message is None:
        yield history, "", ""
        return

    yield from travel_agent(last_user_message, history)


def export_transcript(history):
    """Write the conversation to a temp Markdown file for gr.DownloadButton."""

    lines = ["# Paris Travel Agent - Conversation Transcript", ""]

    for item in history or []:
        role = item.get("role", "").capitalize()
        lines.append(f"**{role}:** {_message_text(item.get('content', ''))}")
        lines.append("")

    path = os.path.join(tempfile.gettempdir(), "travel-agent-transcript.md")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return path


def log_feedback(data: gr.LikeData):
    logger.info("Feedback liked=%s value=%r", data.liked, data.value)


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
        """
    )

    chatbot = gr.Chatbot(
        label="Travel Agent",
        height=500,
        resizable=True,
        placeholder="<h3>Bonjour! Ask me anything about visiting Paris.</h3>",
        buttons=["copy", "copy_all"],
    )

    message = gr.Textbox(
        placeholder="Ask your travel question...",
        label="Your Question"
    )

    token_footer = gr.Markdown("")

    gr.Examples(
        examples=[
            "What is the most famous landmark in Paris?",
            "How far is the Louvre from the Eiffel Tower?",
            "What should I see at the Louvre?",
            "Can you create a 3-day Paris itinerary?",
            "What are the best areas to stay in Paris?",
            "Do I need a visa or ETIAS to visit Paris?",
            "What common tourist scams should I watch out for in Paris?",
            "What's the tipping etiquette at French restaurants?",
        ],
        inputs=message,
        label="Try one of these",
    )

    with gr.Row():
        send_button = gr.Button(
            "Ask Travel Agent",
            variant="primary"
        )

        clear_button = gr.Button(
            "Clear Chat"
        )

        regenerate_button = gr.Button(
            "Regenerate"
        )

        export_button = gr.DownloadButton(
            "Export Transcript"
        )

    # Lock the controls while a response streams, so a turn can't be submitted twice
    for trigger in (send_button.click, message.submit):
        trigger(
            lambda: (gr.update(interactive=False), gr.update(interactive=False)),
            inputs=None,
            outputs=[send_button, message],
        ).then(
            travel_agent,
            inputs=[message, chatbot],
            outputs=[chatbot, message, token_footer],
        ).then(
            lambda: (gr.update(interactive=True), gr.update(interactive=True)),
            inputs=None,
            outputs=[send_button, message],
        )

    # Regenerate re-sends the last user message after dropping the last reply
    regenerate_button.click(
        lambda: gr.update(interactive=False),
        inputs=None,
        outputs=regenerate_button,
    ).then(
        regenerate,
        inputs=[chatbot],
        outputs=[chatbot, message, token_footer],
    ).then(
        lambda: gr.update(interactive=True),
        inputs=None,
        outputs=regenerate_button,
    )

    export_button.click(
        export_transcript,
        inputs=[chatbot],
        outputs=export_button,
    )

    chatbot.like(log_feedback, inputs=None, outputs=None)

    # Clear conversation
    clear_button.click(
        lambda: ([], "", ""),
        inputs=None,
        outputs=[chatbot, message, token_footer]
    )


# Start application
if __name__ == "__main__":
    demo.launch()