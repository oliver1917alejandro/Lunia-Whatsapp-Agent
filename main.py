import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Tuple # Added List, Tuple

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.embeddings.openai import OpenAIEmbedding as LlamaOpenAIEmbedding

from whatsapp_client import send_message, receive_message_webhook_handler

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("CRITICAL_ERROR: OPENAI_API_KEY not found in .env. Key functions will fail.")

LLAMA_STORAGE_DIR = "./storage/vector_store"
LLAMA_DATA_DIR = "./data/lunia_info"
llama_query_engine = None

def init_llama_engine():
    global llama_query_engine
    if llama_query_engine: return
    if not OPENAI_API_KEY:
        print("main.py_error: Cannot init LlamaIndex - OPENAI_API_KEY missing.")
        return
    print("main.py: Initializing LlamaIndex...")
    try:
        llm = LlamaOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY)
        embed_model = LlamaOpenAIEmbedding(api_key=OPENAI_API_KEY)
        service_context = ServiceContext.from_defaults(llm=llm, embed_model=embed_model)
        if os.path.exists(LLAMA_STORAGE_DIR) and os.path.exists(os.path.join(LLAMA_STORAGE_DIR, "docstore.json")):
            storage_context = StorageContext.from_defaults(persist_dir=LLAMA_STORAGE_DIR)
            index = load_index_from_storage(storage_context, service_context=service_context)
        else:
            os.makedirs(LLAMA_STORAGE_DIR, exist_ok=True)
            documents = SimpleDirectoryReader(LLAMA_DATA_DIR).load_data()
            index = VectorStoreIndex.from_documents(documents, service_context=service_context) if documents else VectorStoreIndex([], service_context=service_context)
            index.storage_context.persist(persist_dir=LLAMA_STORAGE_DIR)
        llama_query_engine = index.as_query_engine(similarity_top_k=3)
        print("main.py: LlamaIndex initialized.")
    except Exception as e:
        print(f"main.py_error: Failed to init LlamaIndex: {type(e).__name__} - {e}")

class AgentState(TypedDict):
    input_message: str
    sender_phone: str
    response: str
    conversation_history: List[Tuple[str, str]] # Uses List, Tuple

def agent_node(state: AgentState):
    print(f"agent_node: Processing for {state['sender_phone']}: '{state['input_message'][:100]}'")
    global llama_query_engine
    if not llama_query_engine and OPENAI_API_KEY: init_llama_engine()

    user_input_text = state['input_message']
    user_msg_lower = user_input_text.lower()
    history = state.get('conversation_history', [])
    history.append(("user", user_input_text))

    reply_text = ""
    # Handle specific known non-LlamaIndex responses first
    if "hello" in user_msg_lower or "hi" in user_msg_lower or "hola" in user_msg_lower:
        reply_text = "Hello! Lunia Soluciones AI here. How can I help with your AI strategy or scheduling?"
    elif "bye" in user_msg_lower or "adios" in user_msg_lower:
        reply_text = "Goodbye! Have a great day."
    # Handle cases where transcription might have failed or indicated issues
    elif user_input_text in ["[Audio transcription failed]", "[Audio file not found for transcription]",
                             "[Audio file was a placeholder, not transcribed]", "[OpenAI client not available for transcription]",
                             "[Audio message URL received, but live download/processing is not part of this simulation step]",
                             "[Transcription resulted in empty text]"]:
        reply_text = "I received an audio message, but there was an issue processing it. Could you please try sending a text message, or ensure the audio is clear and not silent?"
    else: # Default to LlamaIndex query
        if llama_query_engine:
            try:
                print(f"agent_node: Querying LlamaIndex with: '{user_input_text}'")
                response_obj = llama_query_engine.query(user_input_text)
                reply_text = str(response_obj).strip() if response_obj and str(response_obj).strip() else "I looked into that, but I'm not quite sure how to answer. Could you rephrase?"
            except Exception as e:
                print(f"agent_node_error: LlamaIndex query error: {type(e).__name__} - {e}")
                reply_text = "Sorry, I encountered an error trying to find an answer."
        else:
            reply_text = "My knowledge base is currently unavailable. Please try basic commands or try again later."

    history.append(("ai", reply_text))
    state['response'] = reply_text
    state['conversation_history'] = history

    if state.get('sender_phone') and reply_text:
        print(f"agent_node: Sending to WhatsApp ({state['sender_phone']}): '{reply_text}'")
        send_message(state['sender_phone'], reply_text)

    return state

def should_continue_logic(state: AgentState):
    msg_lower = state['input_message'].lower()
    return END if "bye" in msg_lower or "adios" in msg_lower else "agent_node"

graph_workflow = StateGraph(AgentState)
graph_workflow.add_node("agent_node", agent_node)
graph_workflow.set_entry_point("agent_node")
graph_workflow.add_conditional_edges("agent_node", should_continue_logic, {END: END, "agent_node": "agent_node"})
compiled_agent = graph_workflow.compile()

if __name__ == "__main__":
    print("--- Test main.py Agent Simulation (Audio Capable) ---")
    if OPENAI_API_KEY: init_llama_engine()
    else: print("main_test_warning: OPENAI_API_KEY missing. LlamaIndex and Transcription will not work fully.")

    sim_message_payloads = [
        {"event": "messages.upsert", "data": {"key": {"remoteJid": "text_user@s.whatsapp.net"}, "message": {"conversation": "Hola"}}},
        {"event": "messages.upsert", "data": {"key": {"remoteJid": "audio_user_good@s.whatsapp.net"}, "message": {"audioMessage": {"url": "use_sample_audio.mp3"}}}},
        {"event": "messages.upsert", "data": {"key": {"remoteJid": "text_user@s.whatsapp.net"}, "message": {"conversation": "What is AI consulting?"}}},
        {"event": "messages.upsert", "data": {"key": {"remoteJid": "audio_user_bad@s.whatsapp.net"}, "message": {"audioMessage": {"url": "some_other_audio.ogg"}}}}, # Will use placeholder text
        {"event": "messages.upsert", "data": {"key": {"remoteJid": "text_user@s.whatsapp.net"}, "message": {"conversation": "Adios"}}},
    ]

    user_sessions = {}
    for i, payload in enumerate(sim_message_payloads):
        print(f"\nSIM_MSG {i+1}: Processing payload...")
        parsed_input = receive_message_webhook_handler(payload)

        if not parsed_input or parsed_input.get("text") is None or not parsed_input.get("sender"):
            print(f"SIM_ERROR: Failed to parse/transcribe payload: {payload}")
            # If sender is known, could send error, but handler might not return sender if it fails early
            if parsed_input and parsed_input.get("sender"):
                 send_message(parsed_input.get("sender"), "Sorry, I couldn't process your last message.")
            continue

        sender_id = parsed_input["sender"]
        text_input = parsed_input["text"]
        print(f"SIM_MSG {i+1}: From {sender_id}, Text (after parse/transcribe): '{text_input[:100]}'")

        current_history = user_sessions.get(sender_id, [])
        graph_state_payload = {"input_message": text_input, "sender_phone": sender_id, "conversation_history": current_history}

        result_state = compiled_agent.invoke(graph_state_payload)
        user_sessions[sender_id] = result_state.get('conversation_history', [])
        print(f"SIM_MSG {i+1}: Agent replied to {sender_id}: '{result_state.get('response')}'")

        if "bye" in text_input.lower() or "adios" in text_input.lower():
            if sender_id in user_sessions: del user_sessions[sender_id] # Clear session
    print("--- End Test main.py ---")
