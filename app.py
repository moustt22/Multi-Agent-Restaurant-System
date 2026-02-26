import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))

from Orchestrator.orch import chat


st.set_page_config(
    page_title="NovaBite AI Assistant",
    page_icon="🍽️",
    layout="centered"
)

st.title("🍽️ NovaBite AI Assistant")
st.caption("Ask about our menu, make a reservation, check your loyalty points, and more.")


if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_session"


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if user_input := st.chat_input("How can I help you today?"):

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat(user_input, session_id=st.session_state.session_id)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})