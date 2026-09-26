"""Flags narrativas serializáveis e estado derivado do objetivo e da casa."""


class StoryManager:
    def __init__(self, flags=None):
        if flags is None:
            flags = {}
        self._validate(flags)
        self.flags = dict(flags)

    @staticmethod
    def _validate(flags):
        if not isinstance(flags, dict):
            raise TypeError("As flags da história devem ser um objeto/dicionário.")
        for name, value in flags.items():
            if not isinstance(name, str):
                raise ValueError("Cada estado narrativo deve ter um nome texto.")
            if name == "forest_battle_progress":
                if type(value) is not int or not 0 <= value <= 10:
                    raise ValueError("O progresso da batalha da Floresta deve estar entre 0 e 10.")
            elif type(value) is not bool:
                raise ValueError("Cada flag da história deve ter valor booleano.")

    def get(self, name, default=False):
        return self.flags.get(name, default)

    def set(self, name, value=True):
        self._validate({name: value})
        self.flags[name] = value

    def set_forest_battle_progress(self, value):
        self._validate({"forest_battle_progress": value})
        self.flags["forest_battle_progress"] = value

    def to_dict(self):
        return dict(self.flags)

    @property
    def objective_text(self):
        return ("Investigue a casa." if self.get("house_investigation_unlocked")
                and not self.get("house_searched") else "")

    @property
    def home_phase(self):
        return "home_investigation" if self.get("house_investigation_unlocked") else "home_initial"

    def apply_to_region(self, region):
        if region.get("ambient_kind") == "home":
            region["story_phase"] = self.home_phase
            if self.get("house_investigation_unlocked"):
                existing = {obj.uid for obj in region.get("interactables", [])}
                region["interactables"].extend(
                    obj for obj in region.get("investigation_interactables", [])
                    if obj.uid not in existing)
                existing_visuals = region.get("objects", [])
                region["objects"].extend(
                    obj for obj in region.get("investigation_objects", [])
                    if obj not in existing_visuals)
            if self.get("pendant_found"):
                region["interactables"] = [
                    obj for obj in region.get("interactables", [])
                    if obj.uid != "broken_pendant"]

        elif region.get("ambient_kind") == "forest":
            post_march = self.get("blue_army_departed")
            region["story_phase"] = "forest_post_march" if post_march else "forest_initial"
            if not post_march:
                return
            region["enemy_spawns"] = []
            if not region.get("forest_post_march_applied"):
                region["objects"].extend(region.get("forest_battlefield_objects", ()))
                region["forest_post_march_applied"] = True
            interactables = region.setdefault("interactables", [])
            body = next((obj for obj in interactables if obj.uid == "battlefield_body"), None)
            if self.get("forest_massacre_discovered"):
                if body is not None:
                    interactables.remove(body)
            elif body is None:
                body_prop = region.get("forest_battlefield_interactables", {}).get("body")
                if body_prop is not None:
                    interactables.append(body_prop)
            insignia = next((obj for obj in interactables if obj.uid == "red_insignia"), None)
            if self.get("red_insignia_found") or self.get("forest_battle_progress", 0) < 10:
                if insignia is not None:
                    interactables.remove(insignia)
            elif insignia is None:
                insignia_prop = region.get("forest_battlefield_interactables", {}).get("insignia")
                if insignia_prop is not None:
                    interactables.append(insignia_prop)
            if self.get("red_insignia_found"):
                commander_prop = region.get("wounded_commander_object")
                if commander_prop is not None and commander_prop not in region["objects"]:
                    region["objects"].append(commander_prop)

    @classmethod
    def from_dict(cls, data):
        return cls(data)
