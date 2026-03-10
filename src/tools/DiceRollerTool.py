import random
import re

class DiceRollerTool:
    def roll(self, dice_string: str) -> dict:
        # Regex para capturar: cantidad, caras y modificador (ej: 2d20 + 5)
        match = re.match(r"(\d+)d(\d+)(?:\s*([+-])\s*(\d+))?", dice_string.replace(" ", ""))
        if not match:
            return {"error": "Formato de dados inválido (ej: 1d20+5)"}

        num, sides, sign, mod = match.groups()
        rolls = [random.randint(1, int(sides)) for _ in range(int(num))]
        total = sum(rolls)

        if mod:
            total = total + int(mod) if sign == "+" else total - int(mod)

        return {
            "total": total,
            "rolls": rolls,
            "modifier": f"{sign}{mod}" if mod else "0",
            "formula": dice_string
        }