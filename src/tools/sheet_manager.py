import re

class SheetManager:
    @staticmethod
    def format_sheet_context(raw_text: str) -> str:
        """
        Limpia el texto del PDF de forma básica.
        Simplemente elimina espacios excesivos para no saturar al modelo.
        """
        # Eliminamos espacios en blanco múltiples y normalizamos
        clean_text = re.sub(r'\s+', ' ', raw_text)

        # Retornamos el texto con un encabezado simple
        return f"--- CONTEXTO DE FICHA TÉCNICA ---\n{clean_text.strip()}"