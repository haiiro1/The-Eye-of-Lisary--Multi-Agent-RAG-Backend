import streamlit as st
import requests
import json
import uuid
import re
import os

st.set_page_config(page_title="Ojo de Lisary", page_icon="👁️")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/chat")

if "messages" not in st.session_state: st.session_state.messages = []
if "thread_id" not in st.session_state: st.session_state.thread_id = str(uuid.uuid4())

st.title("👁️ Ojo de Lisary Assistant")

with st.sidebar:
    st.header("⚙️ Configuración")
    uploaded_file = st.file_uploader("Sube tu ficha (PDF)", type="pdf")
    if uploaded_file and "file_sent" not in st.session_state:
        with st.spinner("Vinculando ficha..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            r = requests.post(f"{BACKEND_URL}/upload_sheet/{st.session_state.thread_id}", files=files)
            if r.status_code == 200:
                st.session_state.file_sent = True
                st.success("✅ Ficha vinculada.")

    if st.button("🗑️ Reiniciar"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        if "file_sent" in st.session_state: del st.session_state.file_sent
        st.rerun()

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("¿Qué deseas consultar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        # Petición de Streaming al Backend
        payload = {"message": prompt, "session_id": st.session_state.thread_id}
        with requests.post(BACKEND_URL, json=payload, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: "):
                        data_str = decoded[6:]
                        if data_str == "[DONE]": break

                        try:
                            token = json.loads(data_str).get("token", "")
                            full_response += token
                            # Limpieza visual inmediata de pensamientos internos
                            clean_view = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL)
                            response_placeholder.markdown(clean_view + "▌")
                        except: continue

        final_text = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
        response_placeholder.markdown(final_text)
        st.session_state.messages.append({"role": "assistant", "content": final_text})