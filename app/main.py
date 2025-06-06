import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI # Ensure llm is specified for service context
from llama_index.embeddings.openai import OpenAIEmbedding # Ensure embeddings are specified

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file. This is required for LlamaIndex embeddings and LLM.")

# Constants for LlamaIndex
STORAGE_DIR = "./storage/vector_store"  # Directory to store the index
DATA_DIR = "./data/lunia_info"      # Directory containing knowledge documents

# Global variable for the query engine
query_engine = None

def initialize_query_engine():
    global query_engine
    if query_engine is not None:
        print("Query engine already initialized.")
        return

    print("Initializing LlamaIndex query engine...")
    # Configure service context (LLM and Embeddings)
    llm = OpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY)
    embed_model = OpenAIEmbedding(api_key=OPENAI_API_KEY)
    service_context = ServiceContext.from_defaults(llm=llm, embed_model=embed_model)

    # Check if storage directory and index files exist
    if os.path.exists(STORAGE_DIR) and os.path.exists(os.path.join(STORAGE_DIR, "docstore.json")):
        print(f"Loading existing index from {STORAGE_DIR}...")
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context, service_context=service_context)
        print("Index loaded successfully.")
    else:
        print(f"No existing index found at {STORAGE_DIR}. Creating new index...")
        if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
            print(f"ERROR: Data directory {DATA_DIR} is empty or does not exist. Cannot build index.")
            # In a real app, you might want to create placeholder docs or raise a more specific error
            # For this example, we'll let it proceed, but LlamaIndex will likely fail or build an empty index.
            # For now, we'll create the storage directory if it doesn't exist.
            os.makedirs(STORAGE_DIR, exist_ok=True)

        documents = SimpleDirectoryReader(DATA_DIR).load_data()
        if not documents:
            print(f"No documents found in {DATA_DIR}. Index will be empty.")
            # Create an empty index if no documents are found to prevent errors downstream
            # This is a simplified handling. Ideally, ensure documents exist.
            index = VectorStoreIndex([], service_context=service_context)
        else:
            print(f"Loaded {len(documents)} document(s) from {DATA_DIR}.")
            index = VectorStoreIndex.from_documents(documents, service_context=service_context)

        print(f"Persisting index to {STORAGE_DIR}...")
        index.storage_context.persist(persist_dir=STORAGE_DIR)
        print("Index created and persisted.")

    query_engine = index.as_query_engine(similarity_top_k=3) # Retrieve top 3 similar nodes
    print("Query engine initialized successfully.")

# Define the state for our graph
class AgentState(TypedDict):
    input_message: str
    response: str
    conversation_history: list[tuple[str, str]]

# Placeholder functions for nodes
def start_conversation(state: AgentState):
    print("---STARTING CONVERSATION---")
    initialize_query_engine() # Initialize LlamaIndex
    state['conversation_history'] = []
    # For the first message, we don't have a user input yet to process with the agent.
    # We can send a greeting or wait for the actual first user message.
    # For now, let's assume the graph is invoked with an initial user message.
    return state

def handle_input(state: AgentState):
    print(f"---HANDLING INPUT: {state['input_message']}---")
    global query_engine
    if query_engine is None:
        # This should not happen if start_conversation ran and initialized it.
        print("ERROR: Query engine not initialized!")
        state['response'] = "Sorry, I'm having trouble accessing my knowledge base right now."
        return state

    user_message = state['input_message']

    if 'conversation_history' not in state or state['conversation_history'] is None:
        state['conversation_history'] = []
    state['conversation_history'].append(("user", user_message))

    response_message = ""
    if "hello" in user_message.lower() or "hi" in user_message.lower():
        response_message = "Hello! I am the AI assistant for Lunia Soluciones. How can I help you learn more about our AI services or schedule a consultation?"
    elif "bye" in user_message.lower() or "goodbye" in user_message.lower():
        response_message = "Goodbye! Feel free to reach out if you have more questions about Lunia Soluciones."
    else:
        # Use LlamaIndex to answer other questions
        print(f"---QUERYING LLAMAINDEX WITH: {user_message}---")
        try:
            llm_response = query_engine.query(user_message)
            response_message = str(llm_response)
            print(f"---LLAMAINDEX RESPONSE: {response_message}---")
        except Exception as e:
            print(f"Error querying LlamaIndex: {e}")
            response_message = "I encountered an issue trying to answer your question. Could you please rephrase it or ask something else?"

    state['response'] = response_message
    state['conversation_history'].append(("ai", response_message))
    print(f"---GENERATED RESPONSE: {state['response']}---")
    return state

def should_continue(state: AgentState):
    print("---CHECKING IF CONVERSATION SHOULD CONTINUE---")
    # Check for more robust exit conditions
    if any(kw in state['input_message'].lower() for kw in ["bye", "goodbye", "exit", "quit"]):
        print("---ENDING CONVERSATION---")
        return END
    print("---CONTINUING CONVERSATION---")
    return "handle_input_node"

# Initialize the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("start_node", start_conversation)
workflow.add_node("handle_input_node", handle_input)

# Set entry point
workflow.set_entry_point("start_node")

# Add edges
workflow.add_edge("start_node", "handle_input_node") # Should go to handle_input after start
workflow.add_conditional_edges(
    "handle_input_node",
    should_continue,
    {
        "handle_input_node": "handle_input_node", # Loop back to handle_input for more messages
        END: END
    }
)

# Compile the graph
app_graph = workflow.compile()

# Example of how to run (for testing purposes)
if __name__ == "__main__":
    print("Testing the agent graph with LlamaIndex...")

    # Simulate triggering the start of a conversation (e.g. user sends first message)
    # The start_node will initialize LlamaIndex.
    # The first actual user message will then be processed by handle_input_node.

    # To properly test, we should ensure OPENAI_API_KEY is set in a .env file in the app directory
    # For example:
    # OPENAI_API_KEY="your_actual_openai_key_here"

    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY is not set. LlamaIndex functionality will fail.")
        print("Please create a .env file in the 'app' directory with your OPENAI_API_KEY.")
    else:
        # The graph is designed to be invoked per message.
        # `start_node` should ideally be called once at the beginning of a session.
        # Then `handle_input_node` for each subsequent message.
        # For this test, let's simulate a sequence.

        # Initial invocation to trigger start_node and initialize LlamaIndex.
        # We pass a dummy message because the start_node now transitions to handle_input_node,
        # which expects an 'input_message'.
        print("\n--- Simulating initial user connection (triggers LlamaIndex setup) ---")
        initial_state = {"input_message": "User connected", "conversation_history": []}
        current_state = app_graph.invoke(initial_state)
        # The response from this initial call might not be directly relevant if start_node doesn't set one.
        # The key is that LlamaIndex gets initialized.

        # Now simulate actual user messages
        inputs = [
            {"input_message": "Hello there!"},
            {"input_message": "What services does Lunia Soluciones offer?"},
            {"input_message": "Tell me more about your AI consulting."},
            {"input_message": "What makes Lunia different?"},
            {"input_message": "Thanks, goodbye!"}
        ]

        # Use the conversation_history from the state for continuous conversation context
        # (though LlamaIndex itself is stateless per query in this setup)
        conversation_history = current_state.get('conversation_history', [])

        for i, input_data in enumerate(inputs):
            print(f"\nSimulating message {i+1}: {input_data['input_message']}")

            # Pass the current conversation history for context if your agent uses it beyond LlamaIndex
            payload = {"input_message": input_data['input_message'], "conversation_history": conversation_history}
            current_state = app_graph.invoke(payload)

            print(f"Agent's response: {current_state.get('response')}")
            conversation_history = current_state.get('conversation_history', []) # Update history

            if "goodbye" in input_data['input_message'].lower() or "bye" in input_data['input_message'].lower() :
                print("End of conversation simulation.")
                break
        print("\nAgent graph test with LlamaIndex complete.")
