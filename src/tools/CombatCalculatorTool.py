from src.core.logging_config import logger

class CombatCalculatorTool:
    @staticmethod
    def calculate_ac(base_ac: int, dex_mod: int, armor_type: str = "none", has_shield: bool = False) -> dict:
        """
        Calcula la Clase de Armadura según el tipo de armadura y destreza.
        """
        final_ac = base_ac

        if armor_type.lower() == "light":
            final_ac = base_ac + dex_mod
        elif armor_type.lower() == "medium":
            final_ac = base_ac + min(dex_mod, 2)  # Máximo +2 en armadura media
        elif armor_type.lower() == "heavy":
            final_ac = base_ac  # La armadura pesada ignora Destreza
        else: # Sin armadura (10 + Dex)
            final_ac = 10 + dex_mod

        if has_shield:
            final_ac += 2

        logger.info(f"🛡️ [CombatCalc] CA calculada: {final_ac} (Tipo: {armor_type})")
        return {"ac": final_ac, "formula": f"Base({base_ac}) + Dex({dex_mod} limitado) + Escudo({2 if has_shield else 0})"}

    @staticmethod
    def calculate_save_dc(ability_mod: int, prof_bonus: int, magic_bonus: int = 0) -> int:
        """Calcula la CD de salvación (8 + Prof + Mod)."""
        dc = 8 + prof_bonus + ability_mod + magic_bonus
        return dc

    @staticmethod
    def calculate_attack_bonus(ability_mod: int, prof_bonus: int, magic_bonus: int = 0) -> int:
        """Calcula el bonificador de ataque (Mod + Prof + Magia)."""
        return ability_mod + prof_bonus + magic_bonus

    def get_standard_proficiency(self, level: int) -> int:
        """Devuelve el bono de competencia por nivel."""
        if level < 5: return 2
        if level < 9: return 3
        if level < 13: return 4
        if level < 17: return 5
        return 6