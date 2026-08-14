# travel-ai-agent

A small chat app that acts as a friendly travel agent specialising in **Paris, France**. It pairs an OpenAI chat model with a [Gradio](https://www.gradio.app/) web UI so you can ask trip-planning questions in your browser.

## What it does

Ask it anything about visiting Paris and it will answer concisely and practically:

- Landmarks, museums, restaurants and hotels
- Transportation and distances between attractions
- Neighbourhoods and where to stay
- Suggested itineraries and best times to visit
- General travel tips

The system prompt keeps the assistant on-topic and instructs it to say when it is unsure rather than inventing details.

## How it works

- `app.py` holds everything: the system prompt, the OpenAI call, and the Gradio UI.
- Responses are **streamed**, so text appears token by token instead of after a long pause.
- Each turn replays the recent conversation to the model, capped at `MAX_HISTORY_MESSAGES` so cost stays bounded on long chats.
- API failures are caught and shown as a friendly message rather than a raw Gradio error.
- The UI is built with `gr.Blocks`: a `gr.Chatbot` transcript, a textbox, clickable examples, and **Ask Travel Agent** / **Clear Chat** buttons. Controls lock while a response streams.
- Thumbs up/down feedback is logged to the console via `chatbot.like` — this is a debugging aid only, not persisted anywhere.

> **Note on Gradio versions:** this project targets Gradio 6, where `gr.Chatbot` only supports the *messages* format. Handlers must return the **full history** as a list of `{"role": ..., "content": ...}` dictionaries — returning a bare string raises `Data incompatible with messages format`.

## Limitations

- The model has no live data: opening hours, prices, availability and weather can be out of date or wrong.
- It cannot book anything — flights, hotels, restaurants or tickets are outside its scope.
- It only covers Paris; the system prompt is not currently parameterised for other destinations.
- Streaming with `OPENAI_MAX_TOKENS=800` on every turn has a real per-message API cost — lower it if you want to control spend.

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
   python -m pip install -r requirements.txt
   ```

3. Create a `.env` file next to `app.py` with your key:

   ```env
   OPENAI_API_KEY=sk-your-key-here
   ```

   `.env` is listed in `.gitignore` — never commit your API key.

### Optional settings

These can also go in `.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_MODEL` | `gpt-4o-mini` | Which chat model to call |
| `OPENAI_TEMPERATURE` | `0.4` | Higher is more varied, lower is more repeatable |
| `OPENAI_MAX_TOKENS` | `800` | Response length cap |

The app exits with a clear message at startup if `OPENAI_API_KEY` is missing.

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

## Troubleshooting

- **`gradio.exceptions.Error: Data incompatible with messages format...`** — the chat handler returned a bare string instead of the full history as a list of `{"role", "content"}` dictionaries. Gradio 6's `gr.Chatbot` only accepts the messages format.
- **`TypeError: Chatbot.__init__() got an unexpected keyword argument 'type'`** — Gradio 6 removed `type="messages"` from `gr.Chatbot` because it's now the only supported format; drop the argument.
- **App exits immediately with `OPENAI_API_KEY is not set`** — add the key to `.env` next to `app.py`, or set it as an environment variable before running.

## Project structure

```
travel-ai-agent/
├── app.py             # Prompt, OpenAI client and Gradio UI
├── requirements.txt   # Pinned dependencies
├── .env               # OPENAI_API_KEY (not committed)
├── .gitignore
├── LICENSE
└── README.md
```

## Licence

Released under the [MIT Licence](LICENSE).