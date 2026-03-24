import streamlit as st
import requests
import json
import uuid
import re
import os

st.set_page_config(page_title="Ojo de Lisary - UI Test", page_icon="👁️", layout="wide")

# --- Configuración Corregida ---
# Extraemos la base sin el path para evitar errores de barras
RAW_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BASE_URL = RAW_URL.replace('/chat', '').rstrip('/') # Limpia barras finales y el path /chat

if "messages" not in st.session_state: st.session_state.messages = []
if "thread_id" not in st.session_state: st.session_state.thread_id = str(uuid.uuid4())

st.title("👁️ Ojo de Lisary Assistant")

with st.sidebar:
    st.header("⚙️ Configuración")
    uploaded_file = st.file_uploader("Sube tu ficha (PDF)", type="pdf")
    if uploaded_file:
        try:
            # Quitamos el 'if not context' para permitir re-subir fichas si el usuario se equivoca
            with st.spinner("Vinculando ficha con el Oráculo..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}

                # Construcción limpia de la URL
                upload_url = f"{BASE_URL}/upload_sheet/{st.session_state.thread_id}"
                upload_response = requests.post(upload_url, files=files)

                if upload_response.status_code == 200:
                    st.session_state.sheet_context = "Ficha cargada en Backend"
                    st.success("✅ Ficha procesada correctamente.")
                else:
                    st.error(f"Error {upload_response.status_code}: {upload_response.text}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")

    if st.button("🗑️ Reiniciar Chat"):
        st.session_state.clear() # Forma más limpia de resetear
        st.rerun()

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("¿Qué deseas consultar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando los manuales antiguos..."):
            try:
                payload = {
                    "message": prompt,
                    "session_id": st.session_state.thread_id
                }

                # Llamada al endpoint de chat
                chat_url = f"{BASE_URL}/chat"
                response = requests.post(chat_url, json=payload, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("response", "Sin respuesta.")

                    # Tu limpieza de tags de pensamiento está perfecta
                    clean_pattern = re.compile(r'<(think|thought)>.*?</(think|thought)>', re.DOTALL)
                    answer = clean_pattern.sub('', answer).strip()

                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")
