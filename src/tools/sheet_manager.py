import re
class SheetManager:
    @staticmethod
    def format_sheet_context(raw_text: str) -> str:
        """Limpia el texto del PDF para que el LLM lo entienda mejor."""
        # Eliminamos espacios excesivos y saltos de línea basura
        clean_text = re.sub(r'\s+', ' ', raw_text)
        # Priorizamos secciones clave para Wade
        sections = ["ATAQUES", "RASGOS", "EQUIPO", "CONJUROS"]
        formatted_text = "--- CONTEXTO DE FICHA TÉCNICA ---\n"
        formatted_text += clean_text
        return formatted_text