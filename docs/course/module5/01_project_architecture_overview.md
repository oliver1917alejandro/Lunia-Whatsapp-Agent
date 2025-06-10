# Module 5: Understanding the Project Structure

## 5.1 Project Architecture Overview

This project implements an AI assistant named Lunia, primarily designed to interact via WhatsApp. It can understand user messages, respond to inquiries, integrate with external services (like email and calendar), and retrieve information from a knowledge base.

**Key Components:**

*   **`src/api/main.py` (Presumed):** Likely the entry point for web requests, handling incoming WhatsApp webhooks and routing them to the agent. (Details would require inspecting this file).
*   **`src/agents/lunia_agent_enhanced.py`:** The core "brain" of the assistant. It uses LangGraph to manage the conversation flow and decide on actions.
*   **`src/services/` Directory:** Contains various services that the agent uses:
    *   **`whatsapp_service.py`:** Manages communication with the WhatsApp platform (sending/receiving messages, audio transcription).
    *   **`knowledge_base.py`:** Manages a knowledge base using LlamaIndex, allowing the agent to answer questions based on stored documents.
    *   **`agent_service_integration.py`:** Acts as a bridge for the agent to use other services like email and calendar.
    *   **`email_service.py`, `calendar_service.py` (Presumed):** Handle the actual sending of emails and interaction with calendar APIs.
    *   **`session_manager.py`, `supabase_service.py` (Presumed):** Likely manage user session data and database interactions (e.g., storing conversation history, user preferences).
*   **`src/core/` Directory:** Contains core configurations (`config.py`) and logging (`logger.py`).
*   **`src/models/schemas.py`:** Defines data structures, including `AgentState` which is crucial for the LangGraph implementation.
*   **`data/lunia_info/` (Presumed from `ls` output):** Likely contains the raw text files (`about.txt`, `faq.txt`, `services.txt`) that are indexed by the `KnowledgeBaseService`.

**General Flow:**

1.  A user sends a WhatsApp message.
2.  The WhatsApp platform sends a webhook to the project's API (`src/api/main.py`).
3.  The API parses the message using `whatsapp_service.py` (including potential audio transcription).
4.  The parsed message (and sender information) is passed to the `LuniaAgent` (`lunia_agent_enhanced.py`).
5.  The `LuniaAgent`'s LangGraph workflow processes the message:
    *   Validates input.
    *   Determines user intent (e.g., greeting, service request, general query).
    *   If it's a service request (e.g., "send an email"), it might use `agent_service_integration.py` to perform the action.
    *   If it's a general query, it might use `knowledge_base.py` to find an answer.
    *   Generates a response.
    *   Sends the response back via `whatsapp_service.py`.
6.  Session data (conversation history) is updated via `session_manager.py`.

This architecture allows for a modular design where different responsibilities are handled by specific components.
