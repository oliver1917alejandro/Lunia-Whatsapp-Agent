# 6.4 Project Setup and Contribution Ideas

## Setting Up This Project Locally (Generic Guidance)

Setting up a complex Python project like this one usually involves the following steps. **Specific steps for this project might vary, and you should look for a `README.md` in the project's root or a `CONTRIBUTING.md` file for precise instructions.**

1.  **Prerequisites:**
    *   **Python:** Ensure you have Python installed (usually 3.8+ for modern AI projects). Refer to Module 1 for Python installation.
    *   **Git:** You'll need Git to clone the repository.
    *   **`pip`:** Python's package installer, usually comes with Python.
    *   **(Optional but Recommended) Virtual Environment Tool:** Python's `venv` or tools like `conda`.

2.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory_name>
    ```

3.  **Create and Activate a Virtual Environment (Recommended):**
    *   Using `venv`:
        ```bash
        python -m venv venv  # Creates a virtual environment named 'venv'
        # Activate it:
        # Windows (cmd): venv\Scripts\activate.bat
        # Windows (PowerShell): .\venv\Scripts\Activate.ps1 (might need Set-ExecutionPolicy)
        # macOS/Linux: source venv/bin/activate
        ```
    *   Your terminal prompt should change to indicate the active environment.

4.  **Install Dependencies:**
    *   Look for a `requirements.txt` file or a `pyproject.toml` file (if using Poetry or similar tools).
    *   If `requirements.txt` exists:
        ```bash
        pip install -r requirements.txt
        ```
    *   If `pyproject.toml` and `poetry.lock` exist (uses Poetry):
        ```bash
        pip install poetry
        poetry install
        ```
    *   This step will download and install all necessary libraries (LangChain, LangGraph, LlamaIndex, OpenAI client, FastAPI, Uvicorn, etc.).

5.  **Set Up Environment Variables (Crucial!):**
    *   This project requires API keys and other configurations. There's likely a `.env.example` or `.env_example` file.
    *   **Copy this file to `.env`**: `cp .env.example .env`
    *   **Edit the `.env` file** and fill in your actual API keys and configurations:
        *   `OPENAI_API_KEY`: Your API key from OpenAI.
        *   `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_NAME`: For the WhatsApp Evolution API.
        *   `DATABASE_URL` or Supabase credentials if used.
        *   Any other necessary settings.
    *   **Never commit your actual `.env` file with real keys to Git.** The `.gitignore` file should already list `.env`.

6.  **Initialize Data and Knowledge Base (If Applicable):**
    *   The project uses LlamaIndex for a knowledge base, likely sourcing data from `data/lunia_info/`.
    *   There might be a script or command to build the initial vector store index, or it might be built on the first run if it doesn't exist. Check `src/services/knowledge_base.py`'s `initialize` method and `Config.VECTOR_STORE_DIR`.
    *   Ensure the data files in `data/lunia_info/` are present.

7.  **Run Database Migrations (If a database is used with migrations):**
    *   If the project uses a SQL database with a migration tool (like Alembic), you might need to run migrations. Look for instructions.

8.  **Run the Application:**
    *   The application is likely a web server (FastAPI is common for such projects).
    *   There might be a `main.py` or an `app/main.py` that you run with Uvicorn.
    *   Example command (check `run_server.py` or similar scripts in the project):
        ```bash
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        # or using a script:
        # python scripts/run_server.py
        ```
    *   This will start the web server. You'll see output in your terminal, including the address where it's running (e.g., `http://localhost:8000`).

9.  **Set up Ngrok or a Public URL for Webhooks (for WhatsApp testing):**
    *   To receive messages from WhatsApp, the Evolution API needs to send webhooks to your local machine.
    *   Tools like `ngrok` can create a public URL that tunnels to your local server.
        ```bash
        ngrok http 8000 # If your app runs on port 8000
        ```
    *   You'll get a public `https://xxxx.ngrok.io` URL. Configure this URL in your Evolution API WhatsApp webhook settings.

10. **Testing:**
    *   Send a message to your WhatsApp number connected to the Evolution API instance.
    *   Check the terminal logs of your running Lunia application for activity.
    *   Look for any errors.

**Contribution Ideas (Small Projects/Tasks):**

Once you have the project running, here are some ideas to modify or extend the codebase, building on what you've learned:

1.  **Add a New Intent to `LuniaAgent`:**
    *   In `src/agents/lunia_agent_enhanced.py`:
        *   Modify `_process_message_node` to detect a new, simple intent (e.g., asking for the current time or a fun fact).
        *   Add a new response generation method (like `_generate_fun_fact_response`).
        *   Update `_generate_response_node` to call your new method if the intent is detected.
    *   *Challenge:* Make the "fun fact" come from a simple list or a basic LLM call (using `LLMChain`).

2.  **Improve an Existing Response:**
    *   Pick a response in `_generate_..._response()` methods in `LuniaAgent`.
    *   Make it more dynamic or informative.
    *   *Challenge:* Instead of a fixed string, use a `PromptTemplate` and an `LLMChain` to generate a slightly varied response each time for that intent.

3.  **Add a New FAQ to the Knowledge Base:**
    *   Add a new text file to `data/lunia_info/` with a question and answer.
    *   Rebuild the knowledge base index (you might need to add a script or manually trigger `knowledge_base.rebuild_index()`).
    *   Test if the agent can answer questions based on your new FAQ.

4.  **Extend `AgentServiceIntegration` (More Advanced):**
    *   Think of a new simple service (e.g., "get today's headlines" from a news API, or "check weather").
    *   Add a new pattern to `AgentServiceIntegration` to detect this intent.
    *   Implement a method (like `_check_news_intent`) that would (conceptually or actually, if you set up the API) call an external service.
    *   Update `LuniaAgent`'s `_process_message_node` to potentially use this new service action.
    *   *Note:* This is more involved as it might require new service classes and API key handling.

5.  **Write More Unit Tests:**
    *   Explore the `tests/` directory.
    *   Try to write a new unit test for one of the functions in `LuniaAgent` or `AgentServiceIntegration`. For example, test the intent detection logic in `_process_message_node` with various inputs.

**Important Learning Tips:**

*   **Read the Code:** Spend time reading the existing code, especially `lunia_agent_enhanced.py`, `knowledge_base.py`, and `agent_service_integration.py`.
*   **Use `print()`/Logging:** Add temporary print statements or use the existing logger (`from src.core.logger import logger; logger.debug("My message")`) to understand the flow of data and state changes.
*   **Experiment in Isolation:** If you want to understand a specific LangChain or LangGraph feature, try it out in a separate small Python script first before integrating it into the main project.
*   **Break Down Problems:** If you're tackling a contribution, break it into the smallest possible steps.

Good luck, and happy coding!
