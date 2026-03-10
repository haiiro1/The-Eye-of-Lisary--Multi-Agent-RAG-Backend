from src.core.logging_config import logger

class ConditionExpertTool:
    def __init__(self):
        # Base de datos atómica de condiciones (RAW - Rules As Written)
        self.conditions = {
            "apresado": "Velocidad 0. Las ventajas de ataque contra ti no cambian, pero no puedes beneficiarte de bonificadores a la velocidad.",
            "asustado": "Desventaja en pruebas de característica y tiradas de ataque mientras la fuente del miedo esté a la vista. No puedes acercarte voluntariamente a la fuente.",
            "aturdido": "Incapacitado, fallas automáticamente salvaciones de Fuerza y Destreza. Las tiradas de ataque contra ti tienen ventaja.",
            "cegado": "Fallas automáticamente cualquier prueba de característica que requiera la vista. Ataques contra ti tienen ventaja; tus ataques tienen desventaja.",
            "derribado": "Tu única opción de movimiento es gatear. Tienes desventaja en ataques. Ataques a 5 pies de ti tienen ventaja; más lejos tienen desventaja.",
            "envenenado": "Tienes desventaja en las tiradas de ataque y en las pruebas de característica.",
            "Cansancio": "Nivel 1: Desventaja en pruebas de característica. Nivel 2: Velocidad a la mitad. Nivel 3: Desventaja en ataques/salvaciones. Nivel 4: PG máximos a la mitad. Nivel 5: Velocidad 0. Nivel 6: Muerte.",
            "incapacitado": "No puedes realizar acciones ni reacciones.",
            "inconsciente": "Incapacitado, sueltas lo que tengas, caes derribado. Fallas salvaciones de FUE/DES. Ataques contra ti tienen ventaja y son críticos si están a 5 pies.",
            "invisible": "Eres imposible de ver sin ayuda mágica. Se te considera totalmente cubierto para esconderte. Tienes ventaja en ataques; ataques contra ti tienen desventaja.",
            "paralizado": "Incapacitado, no puedes moverte ni hablar. Fallas salvaciones de FUE/DES. Ataques contra ti tienen ventaja y son críticos si están a 5 pies.",
            "petrificado": "Tu peso se multiplica por 10 y dejas de envejecer. Eres inmune al veneno/enfermedad. Tienes resistencia a todo el daño. Fallas salvaciones de FUE/DES automáticamente.",
            "ensordecido": "Fallas automáticamente cualquier prueba de característica que requiera el oído.",
            "hechizado": "No puedes atacar a quien te hechizó. El hechizador tiene ventaja en pruebas de característica para interactuar socialmente contigo."
        }

    def lookup(self, condition_name: str) -> str:
        """Busca una condición específica por nombre."""
        name = condition_name.lower().strip()
        logger.info(f"⚖️ [ConditionTool] Buscando estado: {name}")

        # Intento de búsqueda directa
        result = self.conditions.get(name)

        if result:
            return f"[REGLA OFICIAL - {name.upper()}]: {result}"

        # Búsqueda parcial (por si el usuario escribe 'está apresado')
        for key, value in self.conditions.items():
            if key in name:
                return f"[REGLA OFICIAL - {key.upper()}]: {value}"

        return "Condición no encontrada en el manual básico. Consulta el RAG para efectos específicos de hechizos."

    def list_all(self):
        return list(self.conditions.keys())