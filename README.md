# travel-ai-agent

A small chat app that acts as a friendly travel agent specialising in **Paris, France**. It pairs an OpenAI chat model with a [Gradio](https://www.gradio.app/) web UI so you can ask trip-planning questions in your browser.

## What it does

Ask it anything about visiting Paris and it will answer concisely and practically:

- Landmarks, museums, restaurants and hotels
- Getting around and distances between attractions
- Neighbourhoods and where to stay
- Suggested itineraries and best times to visit
- General travel tips

The system prompt keeps the assistant on-topic and instructs it to say when it is unsure rather than inventing details.

## How it works

- `app.py` holds everything: the system prompt, the OpenAI call, and the Gradio UI.
- The model is `gpt-4o-mini`, called with `temperature=0.0` and `max_tokens=300` for short, consistent answers.
- Each turn, the full conversation history is replayed to the model so it keeps context.
- The UI is built with `gr.Blocks`: a `gr.Chatbot` transcript, a textbox, and **Ask Travel Agent** / **Clear Chat** buttons.

> **Note on Gradio versions:** this project targets Gradio 6, where `gr.Chatbot` only supports the *messages* format. Handlers must return the **full history** as a list of `{"role": ..., "content": ...}` dictionaries — returning a bare string raises `Data incompatible with messages format`.

## Requirements

- Python 3.10+
- An OpenAI API key

## Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install the dependencies:

   ```powershell
   python -m pip install openai gradio python-dotenv
   ```

3. Create a `.env` file next to `app.py` with your key:

   ```env
   OPENAI_API_KEY=sk-your-key-here
   ```

   `.env` is listed in `.gitignore` — never commit your API key.

## Running

```powershell
python app.py
```

Gradio prints a local URL (typically `http://127.0.0.1:7860`). Open it in your browser and start asking questions.

## Example questions

- What is the most famous landmark in Paris?
- How far is the Louvre from the Eiffel Tower?
- What should I see at the Louvre?
- Can you create a 3-day Paris itinerary?
- What are the best areas to stay in Paris?

## Project structure

```
travel-ai-agent/
├── app.py       # Prompt, OpenAI client and Gradio UI
├── .env         # OPENAI_API_KEY (not committed)
├── .gitignore
├── LICENSE
└── README.md
```

Consider adding `venv/` and `__pycache__/` to `.gitignore` — they are not currently excluded.

## Licence

Released under the [MIT Licence](LICENSE).