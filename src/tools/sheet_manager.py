import re

class SheetManager:
    @staticmethod
    def extract_stats(text: str) -> dict:
        """Extrae estadísticas clave usando patrones comunes en fichas de 5e."""
        stats = {
            "Fuerza": re.search(r"STR\s*(\d+)", text, re.I),
            "Destreza": re.search(r"DEX\s*(\d+)", text, re.I),
            "Constitución": re.search(r"CON\s*(\d+)", text, re.I),
            "Inteligencia": re.search(r"INT\s*(\d+)", text, re.I),
            "Sabiduría": re.search(r"WIS\s*(\d+)", text, re.I),
            "Carisma": re.search(r"CHA\s*(\d+)", text, re.I),
            "CA": re.search(r"(?:Armor Class|AC|CA)\s*(\d+)", text, re.I),
            "Nivel": re.search(r"(?:Level|Nivel)\s*(\d+)", text, re.I),
        }
        # Limpiamos el diccionario para obtener solo el número encontrado
        return {k: v.group(1) if v else "No detectado" for k, v in stats.items()}

    @staticmethod
    def format_sheet_context(raw_text: str) -> str:
        """Crea un resumen estructurado seguido del texto completo."""
        # 1. Limpieza básica
        clean_text = re.sub(r'\s+', ' ', raw_text)

        # 2. Extracción de Atributos
        stats = SheetManager.extract_stats(raw_text)

        # 3. Construcción del Bloque de Contexto
        header = "--- RESUMEN DE ATRIBUTOS DETECTADOS ---"
        stats_summary = "\n".join([f"{k}: {v}" for k, v in stats.items()])

        full_context = (
            f"{header}\n{stats_summary}\n\n"
            f"--- TEXTO COMPLETO DE LA FICHA ---\n{clean_text.strip()}"
        )

        return full_context