import streamlit as st
import sys
import os
import re
import io
import PyPDF2

# Asegurar que el directorio raíz esté en el path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import graph
from src.core.logging_config import logger
from src.tools.sheet_manager import SheetManager

st.set_page_config(page_title="Ojo de Lisary - Test UI", page_icon="👁️", layout="wide")

# --- Inicialización de Sesión ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sheet_context" not in st.session_state:
    st.session_state.sheet_context = "No hay ficha cargada."
# Creamos un ID único para esta pestaña del navegador para la DB de SQLite
if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())

st.title("👁️ Ojo de Lisary: D&D 5e Assistant")
st.subheader("Laboratorio de Pruebas de Agentes")

# --- Barra Lateral ---
with st.sidebar:
    st.header("⚙️ Panel de Control")
    st.info(f"Sesión activa: `{st.session_state.thread_id[:8]}`")

    uploaded_file = st.file_uploader("Sube tu ficha (PDF)", type="pdf")
    if uploaded_file:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            raw_text = "".join([page.extract_text() for page in pdf_reader.pages])
            st.session_state.sheet_context = SheetManager.format_sheet_context(raw_text)
            st.success("✅ Ficha procesada.")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.button("🗑️ Borrar Historial"):
        st.session_state.messages = []
        # Opcional: podrías generar un nuevo thread_id aquí para empezar de cero en la DB
        st.rerun()

# --- Interfaz de Chat ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("¿Qué duda tienes sobre D&D 5e?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando fuentes oficiales..."):
            try:
                # 1. Configuración de persistencia (SQLite)
                config = {"configurable": {"thread_id": st.session_state.thread_id}}

                # 2. Input del Grafo
                # IMPORTANTE: Pasamos el historial de mensajes de st.session_state
                # para que el Router pueda contextualizar.
                input_data = {
                    "messages": [("human", prompt)],
                    "sheet_context": st.session_state.sheet_context,
                    "language": "es"
                }

                # 3. Invocación
                final_state = graph.invoke(input_data, config=config)

                # 4. Procesamiento de Respuesta
                last_msg = final_state["messages"][-1]
                raw_text = last_msg[1] if isinstance(last_msg, tuple) else last_msg.content

                # Limpiar bloque de pensamiento <think>
                clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
                agent_name = final_state.get("next_step", "Orquestador")

                st.markdown(clean_text)
                st.caption(f"🛡️ Responde: **{agent_name}**")

                st.session_state.messages.append({"role": "assistant", "content": clean_text})

            except Exception as e:
                st.error(f"Error: {e}")
                logger.error(f"UI Error: {e}", exc_info=True)