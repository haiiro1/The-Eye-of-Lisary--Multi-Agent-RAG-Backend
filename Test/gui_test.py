import streamlit as st
import requests
import uuid
import re
import fitz  # PyMuPDF
import os

st.set_page_config(page_title="Ojo de Lisary - UI Test", page_icon="👁️", layout="wide")

# --- Configuración Dinámica ---
# Cambia a "http://backend:8000" si usas Docker Compose para la UI también
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/chat")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "sheet_context" not in st.session_state:
    st.session_state.sheet_context = ""

st.title("👁️ Ojo de Lisary: D&D 5e Assistant")

with st.sidebar:
    st.header("⚙️ Configuración")
    st.info(f"ID de Sesión: `{st.session_state.thread_id[:8]}`")

    uploaded_file = st.file_uploader("Sube tu ficha (PDF)", type="pdf")
    if uploaded_file:
        try:
            # Solo procesamos si el contexto está vacío para ahorrar recursos
            if not st.session_state.sheet_context:
                with st.spinner("Leyendo ficha..."):
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    full_text = ""
                    for page in doc:
                        full_text += page.get_text()
                    st.session_state.sheet_context = full_text[:3000] # Un poco más de margen
                st.success("✅ Ficha cargada.")
        except Exception as e:
            st.error(f"Error al leer el PDF: {e}")

    if st.button("🗑️ Reiniciar Chat"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.sheet_context = ""
        st.rerun()

# --- Interfaz de Chat ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pregunta sobre reglas, hechizos o tu personaje..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando los manuales antiguos..."):
            try:
                # IMPORTANTE: Enviamos el context de la ficha en cada mensaje 
                # si tu backend lo espera como parte del initial_state
                payload = {
                    "message": prompt,
                    "session_id": st.session_state.thread_id
                }

                response = requests.post(BACKEND_URL, json=payload, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("response", "Sin respuesta.")
                    agents = data.get("agents_involved", [])

                    # Limpieza de tokens de pensamiento (DeepSeek/Qwen)
                    answer = re.sub(r'<(?:think|thought)>.*?</(?:think|thought)>', '', answer, flags=re.DOTALL).strip()

                    st.markdown(answer)
                    if agents:
                        st.caption(f"🛡️ Especialistas: {', '.join(agents).upper()}")

                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")