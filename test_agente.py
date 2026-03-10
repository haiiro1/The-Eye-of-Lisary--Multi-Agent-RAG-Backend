# test_agente.py
import sys
import os

# test_agente.py
from src.agents.router import DnDRouter

def probar_sistema():
    router = DnDRouter()

    # Prueba 1: Charla
    print("\n--- TEST 1: CHAT ---")
    print(router.route("¡Hola! ¿Quién eres?", session_id="123"))

    # Prueba 2: Reglas (Activará el RAG automáticamente)
    print("\n--- TEST 2: REGLAS ---")
    print(router.route("¿Cómo se calcula la Clase de Armadura?", session_id="123"))

if __name__ == "__main__":
    probar_sistema()