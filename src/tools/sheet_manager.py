import fitz
from typing import Dict, Any

class SheetManager:
    @staticmethod
    def process_pdf(pdf_path: str) -> Dict[str, Any]:
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            widgets = page.widgets()

            raw = {}
            if widgets:
                for w in widgets:
                    val = w.field_value
                    if val and str(val).strip() not in ["Off", "", "No"]:
                        raw[w.field_name] = val
            doc.close()
            return SheetManager._structure_data(raw)
        except Exception as e:
            return {"error": f"Error al leer el pergamino: {e}"}

    @staticmethod
    def _structure_data(raw: Dict[str, Any]) -> Dict[str, Any]:
        def get_mod(score):
            try:
                s = int(str(score).strip())
                return (s - 10) // 2
            except: return 0

        stats_keys = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        stats_data = {}
        for k in stats_keys:
            score = raw.get(k, raw.get(f"{k}score", "10"))
            has_save = raw.get(f"ST {k}") in ["Yes", "X", True]
            stats_data[k] = {"score": score, "mod": get_mod(score), "save_prof": has_save}

        armas = []
        for i in range(1, 4):
            name = raw.get(f"WepName{i}")
            if name:
                armas.append({
                    "nombre": name,
                    "bono": raw.get(f"WepAtkBonus{i}", "+0"),
                    "daño": raw.get(f"WepDamage{i}", "0")
                })

        return {
            "nombre": raw.get("CharacterName", "Atlas"),
            "clase_nivel": raw.get("ClassLevel", "Nivel 1"),
            "raza": raw.get("Race ", "Goliath"),
            "stats": stats_data,
            "armas": armas,
            "combate": {
                "ac": raw.get("AC", "10"),
                "hp_max": raw.get("HPMax", "10"),
                "prof_bonus": raw.get("ProfBonus", "+2"),
                "iniciativa": raw.get("Initiative", "+0")
            },
            "rasgos": raw.get("FeaturesTraits", "").split('\r')
        }

    @staticmethod
    def format_sheet_context(data: Dict[str, Any]) -> str:
        if "error" in data: return data["error"]
        s = data['stats']
        stats_str = " | ".join([f"{k}:{v['score']}({v['mod']:+}){'*' if v['save_prof'] else ''}" for k, v in s.items()])
        armas_str = "\n".join([f"- {w['nombre']}: {w['bono']} Daño: {w['daño']}" for w in data['armas']])
        rasgos = [r.strip() for r in data['rasgos'] if len(r.strip()) > 3][:12]

        return (
            f"--- DATOS DE LA FICHA ACTUAL ---\n"
            f"PERSONAJE: {data['nombre']} ({data['raza']} {data['clase_nivel']})\n"
            f"STATS: {stats_str}\n"
            f"COMBATE: CA {data['combate']['ac']} | HP {data['combate']['hp_max']}\n"
            f"ATAQUES:\n{armas_str if armas_str else '- Ninguno'}\n"
            f"RASGOS:\n" + "\n".join(rasgos) + "\n--------------------------------"
        )