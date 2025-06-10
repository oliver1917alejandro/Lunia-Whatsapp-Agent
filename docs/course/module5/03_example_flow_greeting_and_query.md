# 5.3 Example Flow: Greeting and Knowledge Base Query

Let's trace a simplified flow of how Lunia might handle a user greeting followed by a question that requires the knowledge base.

**Scenario:**

1.  User says: "Hola"
2.  User then asks: "¿Qué servicios ofrecen?"

**Flow Breakdown:**

**Message 1: "Hola"**

1.  **Webhook to API:** User sends "Hola" via WhatsApp. Evolution API forwards this to `/webhook` endpoint of the Lunia application.
2.  **`whatsapp_service.parse_webhook_message`:**
    *   Parses the incoming payload.
    *   Identifies the sender's phone number.
    *   Determines the message type as TEXT and content as "Hola".
    *   Returns a `WhatsAppMessage` object.
3.  **`LuniaAgent` Invocation (LangGraph):**
    *   An initial `AgentState` is created:
        *   `input_message`: "Hola"
        *   `sender_phone`: (user's phone)
        *   Other fields initialized (e.g., `conversation_history` might be loaded from `session_manager`).
    *   The LangGraph `compiled_graph.invoke(initial_state)` is called.

4.  **`_validate_input_node` (LangGraph Node):**
    *   Receives the `AgentState`.
    *   Validates "Hola" (not empty, not too long).
    *   No validation error.
    *   Returns state update (e.g., `message_length`).

5.  **Conditional Edge `_should_continue_after_validation`:**
    *   Checks `state.validation_error`. It's `None`.
    *   Returns `"continue"`. The graph transitions to `_process_message_node`.

6.  **`_process_message_node` (LangGraph Node):**
    *   Receives `AgentState`.
    *   Converts "Hola" to lowercase.
    *   `AgentServiceIntegration` is checked, but "hola" doesn't match service intents.
    *   Detects `is_greeting` as `True`.
    *   Sets `state.intent` to `"greeting"`.
    *   Sets `state.confidence` (e.g., 0.9).
    *   Returns updated `AgentState`.

7.  **`_generate_response_node` (LangGraph Node):**
    *   Receives `AgentState`.
    *   `state.intent` is "greeting".
    *   Calls `self._generate_greeting_response()` which returns a predefined greeting message (e.g., "¡Hola! Soy el Asistente AI de Lunia Soluciones...").
    *   Sets `state.response` to this greeting.
    *   Calls `_post_process_response` (e.g., adds "¿Hay algo más en lo que pueda ayudarte?").
    *   Returns updated `AgentState`.

8.  **`_send_response_node` (LangGraph Node):**
    *   Receives `AgentState`.
    *   Calls `whatsapp_service.send_message(state.sender_phone, state.response)`.
    *   The greeting message is sent to the user.
    *   Sets `state.response_sent` to `True`.
    *   Returns updated `AgentState`.

9.  **Graph Reaches `END`:** The flow for this message is complete.
10. **Session Update:** `LuniaAgent.process_message` calls `_update_session_async` to save "Hola" and the AI's greeting to the conversation history via `session_manager`.

**Message 2: "¿Qué servicios ofrecen?"**

1.  **Webhook & Parsing:** Similar to Message 1. `input_message` is "¿Qué servicios ofrecen?".
2.  **`LuniaAgent` Invocation (LangGraph):**
    *   Initial `AgentState` created. `conversation_history` now includes the first interaction.
3.  **`_validate_input_node`:** Validates the question. No error.
4.  **Conditional Edge:** Returns `"continue"`.
5.  **`_process_message_node`:**
    *   Lowercase: "¿qué servicios ofrecen?".
    *   `AgentServiceIntegration` checked; no direct service match.
    *   Intent detection: might set `state.intent` to `"service_inquiry"` or `"general_inquiry"` based on its rules. Let's assume it's `"service_inquiry"`.
    *   Returns updated `AgentState`.

6.  **`_generate_response_node`:**
    *   `state.intent` is `"service_inquiry"`.
    *   Calls `self._generate_service_response()`, which returns a predefined message listing services (e.g., "Lunia Soluciones ofrece servicios integrales de consultoría en IA...").
    *   Sets `state.response`.
    *   Post-processes the response.
    *   Returns updated `AgentState`.

    *Alternatively, if the intent was less clear or designed to go to KB for this:*
    *   `_generate_response_node` might not set `state.response` directly if the intent is "general_inquiry" or if it decides this specific question needs the KB. It might set a flag or leave `state.response` empty.

7.  **Knowledge Base Query (Post-Graph Step in `LuniaAgent.process_message`):**
    *   The `LuniaAgent.process_message` method checks if `state.response` is empty AND the intent is not something simple like "greeting".
    *   If `state.response` was *not* set by `_generate_response_node` (or if the logic dictated a KB lookup for "service_inquiry"), it now calls `self._query_knowledge_base_async(state.input_message, state)`.
    *   **`knowledge_base.query("¿Qué servicios ofrecen?", context=...)`:**
        *   The KB service takes the question. It might receive recent conversation turns as `context`.
        *   LlamaIndex creates an embedding of the question.
        *   It searches its vector index (built from `data/lunia_info/services.txt`, `faq.txt` etc.) for relevant text chunks.
        *   The top `k` chunks are retrieved.
        *   These chunks and the question are passed to an OpenAI LLM.
        *   The LLM generates an answer based *only* on the provided chunks. For example, it might find text in `services.txt` detailing the services and synthesize an answer.
        *   The answer is returned (e.g., "Ofrecemos desarrollo de estrategia en IA, soluciones de Machine Learning, y más.").
    *   This answer from KB is now set as `state.response`.

8.  **`_send_response_node`:**
    *   Sends the `state.response` (either from direct generation or from KB) to the user via `whatsapp_service`.
    *   Sets `state.response_sent` to `True`.

9.  **Graph Reaches `END`**.
10. **Session Update:** The user's question and AI's answer are saved to history.

This flow shows how LangGraph controls the steps, and how different services like the Knowledge Base are integrated into the overall agent logic. The agent can handle simple, predefined interactions quickly and fall back to the more powerful (but potentially slower) RAG system for complex queries.
