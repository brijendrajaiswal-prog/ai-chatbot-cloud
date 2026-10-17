import requests
import streamlit as st

# -------------------------------
# Application configuration
# -------------------------------

st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:1b"

st.title("🤖 My Own AI Chatbot")
st.caption("Powered by Python, Streamlit and a local AI model")

# -------------------------------
# Initialize conversation
# -------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! 👋 I am your personal AI chatbot. "
                "How can I help you today?"
            )
        }
    ]

# -------------------------------
# Sidebar
# -------------------------------

with st.sidebar:
    st.header("Settings")

    st.write("AI model:", MODEL_NAME)
    st.write("Mode: Local AI")

    if st.button("Clear conversation"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            }
        ]
        st.rerun()

    st.info(
        "Your chat requests are sent to the "
        "Ollama service running on this computer."
    )

# -------------------------------
# Display conversation
# -------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------------
# Process user input
# -------------------------------

user_input = st.chat_input("Type your message here...")

if user_input:
    # Save and display the user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare conversation for the local model
    conversation = [
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in st.session_state.messages
        if message["role"] in ("user", "assistant")
    ]

    # Call Ollama
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "messages": conversation,
                        "stream": False
                    },
                    timeout=300
                )

                response.raise_for_status()

                answer = response.json()["message"]["content"]

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to Ollama. "
                    "Please open Ollama and make sure "
                    "the local service is running."
                )

            except requests.exceptions.Timeout:
                st.error(
                    "The model took too long to respond. "
                    "Try a shorter question or a smaller model."
                )

            except requests.exceptions.RequestException as error:
                st.error(f"Request failed: {error}")

            except (KeyError, ValueError):
                st.error(
                    "The model returned an unexpected response."
                )

