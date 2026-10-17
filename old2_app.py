import requests
import streamlit as st

import database as db


# --------------------------------
# Configuration
# --------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:1b"

st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Create database tables if needed.
db.initialize_database()


# --------------------------------
# Session state
# --------------------------------

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None


def start_new_chat():
    """Create a new conversation in SQLite."""

    conversation_id = db.create_conversation()

    st.session_state.conversation_id = conversation_id


# --------------------------------
# Sidebar
# --------------------------------

with st.sidebar:
    st.title("🤖 My AI Chatbot")

    if st.button("➕ New Chat", use_container_width=True):
        start_new_chat()
        st.rerun()

    st.divider()

    st.subheader("Chat History")

    conversations = db.get_conversations()

    if not conversations:
        st.caption("No previous conversations yet.")

    for conversation in conversations:

        conversation_id = conversation["id"]
        title = conversation["title"]

        col1, col2 = st.columns([5, 1])

        with col1:
            if st.button(
                title,
                key=f"open_{conversation_id}",
                use_container_width=True
            ):
                st.session_state.conversation_id = conversation_id
                st.rerun()

        with col2:
            if st.button(
                "🗑️",
                key=f"delete_{conversation_id}",
                help="Delete this conversation"
            ):
                db.delete_conversation(conversation_id)

                if (
                    st.session_state.conversation_id
                    == conversation_id
                ):
                    st.session_state.conversation_id = None

                st.rerun()

    st.divider()

    st.caption(f"AI Model: {MODEL_NAME}")
    st.caption("History stored locally in SQLite.")


# --------------------------------
# Ensure a conversation exists
# --------------------------------

conversation_id = st.session_state.conversation_id

if (
    conversation_id is None
    or db.get_conversation(conversation_id) is None
):
    start_new_chat()
    st.rerun()


conversation = db.get_conversation(
    st.session_state.conversation_id
)


# --------------------------------
# Main chat area
# --------------------------------

st.title(conversation["title"])
st.caption("Your conversations are saved automatically.")

messages = db.get_messages(
    st.session_state.conversation_id
)

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------
# Process user message
# --------------------------------

user_input = st.chat_input("Ask me anything...")

if user_input:

    conversation_id = st.session_state.conversation_id

    # Save the user's message immediately.
    db.add_message(
        conversation_id,
        "user",
        user_input
    )

    # Use the first question as the chat title.
    if conversation["title"] == "New Chat":
        title = user_input.strip().replace("\n", " ")

        if len(title) > 45:
            title = title[:42] + "..."

        db.update_conversation_title(
            conversation_id,
            title or "New Chat"
        )

    # Load complete conversation history for model context.
    saved_messages = db.get_messages(conversation_id)

    model_messages = [
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in saved_messages
    ]

    # Generate AI response.
    with st.spinner("AI is thinking..."):

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": model_messages,
                    "stream": False
                },
                timeout=300
            )

            response.raise_for_status()

            answer = response.json()["message"]["content"]

            # Save AI response in SQLite.
            db.add_message(
                conversation_id,
                "assistant",
                answer
            )

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to Ollama. "
                "Make sure Ollama is running."
            )

        except requests.exceptions.Timeout:
            st.error(
                "The AI model took too long to respond. "
                "Try again or use a smaller model."
            )

        except requests.exceptions.RequestException as error:
            st.error(f"Request failed: {error}")

        except (KeyError, ValueError):
            st.error("Ollama returned an unexpected response.")

        else:
            st.rerun()

