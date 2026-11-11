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
            elif name == "forest_battle_casualties":
                if type(value) is not int or not 0 <= value <= 1023:
                    raise ValueError("Máscara de soldados derrotados inválida.")
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

    def soldier_defeated(self, index):
        # Old saves only recorded complete pairs; retain that interpretation.
        completed = self.get("forest_battle_progress", 0) // 2 * 2
        return bool((self.get("forest_battle_casualties", 0) | ((1 << completed) - 1))
                    & (1 << index))

    def record_soldier_defeat(self, index):
        self.set("forest_battle_casualties",
                 self.get("forest_battle_casualties", 0) | (1 << index))

    @property
    def objective_text(self):
        if self.get('chapter2_started'):
            from story.chapter2 import objective
            return objective(self)
        if self.get('chapter1_completed'):
            return 'Fale com Alden antes de seguir ao Posto de Convalescença da Encosta.'
        if self.get('encosta_receipt_found'):
            return 'Volte à sua casa e examine R-17 junto da segunda via.'
        if self.get('chapter1_final_alden_talk'):
            return 'Confira o recibo no livro de recebimento que Alden abriu.'
        if self.get('chapter1_final_returned'):
            return 'Converse com Alden sobre a ordem de Namar.'
        if self.get('archive_completed'):
            return 'Volte ao Vale com a segunda via e procure Alden.'
        if self.get('archive_memory_seen'):
            return 'Examine a ficha chamuscada anexada à ordem.'
        if self.get('archive_order_obtained'):
            return 'Reconheça a decisão registrada na segunda via.'
        if self.get('archive_veteran_defeated'):
            return 'Abra a Gaveta 7 na sala seca do depósito.'
        if self.get('archive_confrontation_started'):
            return 'Desarme Soren para alcançar os registros.'
        if self.get('archive_entered'):
            return ('Avance pelo pátio de triagem até a sala seca.' if self.get('archive_defense_report')
                    and self.get('archive_petition') else 'Investigue os papéis queimados e as duas versões da retirada.')
        if self.get('namar_completed'):
            return 'Encontre a segunda via da ordem de Namar no Depósito de Registros da Margem Seca.'
        if self.get('namar_combat_completed'):
            return ('Alcance o portador no pedágio.' if self.get('namar_choice_pursue')
                    and not self.get('namar_dispatch_detail') else 'Volte até Mara e Téo.')
        if self.get('namar_choice_protect'):
            return 'Defenda a carroça de Mara e Téo.'
        if self.get('namar_choice_pursue'):
            return 'Afaste os guardas e alcance o portador pelo pedágio.'
        if self.get('namar_entered'):
            return ('Encontre Mara e Téo junto à carroça.' if self.get('namar_military_clue')
                    and self.get('namar_civilian_clue') else 'Investigue a casa de pedágio e as ruínas da padaria.')
        if self.get("edrin_encounter_completed"):
            return "Descubra o que aconteceu na Ponte de Namar."
        if self.get("watchpost_trail_found"):
            return "Encontre quem estava no posto."
        if self.get("watchpost_seen"):
            return "Investigue o antigo posto de vigia."
        if self.get("chapter1_returned"):
            return ("Investigue a antiga estrada." if self.get("chapter1_alden_talk")
                    else "Fale com Alden.")
        if self.get("prologue_completed") or self.get("red_officer_defeated"):
            return ""
        if self.get("red_officer_boss_ready"):
            return "Enfrente o Oficial Vermelho."
        if self.get("red_insignia_found"):
            return "Avance pela Floresta."
        if self.get("blue_army_departed"):
            return ("Examine a insígnia vermelha." if self.get("forest_battle_progress", 0) == 10
                    else "Explore a Floresta.")
        if self.get("house_searched"):
            return "Saia da casa."
        return ("Investigue a casa." if self.get("house_investigation_unlocked") else "")

    @property
    def objective_title(self):
        if self.get('chapter2_started'): return 'O PREÇO DA MEMÓRIA'
        if self.get('chapter1_completed'): return 'PRÓXIMA PISTA'
        return "Ecos da Guerra" if self.get("chapter1_returned") else "OBJETIVO ATUAL"

    @property
    def home_phase(self):
        return "home_investigation" if self.get("house_investigation_unlocked") else "home_initial"

    @property
    def wounded_commander_ready(self):
        return (self.get("blue_army_departed")
                and self.get("forest_battle_progress", 0) == 10
                and self.get("red_insignia_found"))

    def apply_to_region(self, region):
        if self.get('archive_completed'):
            from story.chapter1_ending import apply_state
            from core.assets import load
            apply_state(region,self,load)
        if self.get('chapter1_completed'):
            from story.chapter2 import apply_state
            apply_state(region,self)
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
            if self.get("house_searched"):
                region["interactables"] = [
                    obj for obj in region.get("interactables", [])
                    if obj.uid != "broken_pendant"]

        elif region.get("ambient_kind") == "village" and self.get("chapter1_returned"):
            from story.chapter1_return import apply_village_aftermath
            apply_village_aftermath(region, self)

        elif region.get("ambient_kind") == "old_road":
            from story.old_road import apply_road_state
            apply_road_state(region, self)

        elif region.get("ambient_kind") == "pursuit":
            from story.edrin_encounter import apply_state
            apply_state(region, self)

        elif region.get('ambient_kind') == 'namar':
            from story.namar import apply_state
            apply_state(region, self)

        elif region.get('ambient_kind') == 'archive':
            from story.archive import apply_state
            apply_state(region, self)

        elif region.get("ambient_kind") == "watchpost":
            from story.watchpost import apply_post_state
            apply_post_state(region, self)

        elif region.get("ambient_kind") == "forest":
            post_march = self.get("blue_army_departed")
            region["story_phase"] = "forest_post_march" if post_march else "forest_initial"
            commander_prop = region.get("wounded_commander_object")
            if not post_march and commander_prop in region.get("objects", []):
                region["objects"].remove(commander_prop)
            if not post_march:
                return
            region["enemy_spawns"] = []
            if not region.get("forest_post_march_applied"):
                region["objects"].extend(region.get("forest_battlefield_objects", ()))
                region["forest_post_march_applied"] = True
            if "red_contacts" not in region and "prepare_red_contacts" in region:
                region["red_contacts"] = region["prepare_red_contacts"]()
                region.setdefault("scenery", []).extend(region["red_contacts"])
            progress = self.get("forest_battle_progress", 0)
            for contact in region.get("red_contacts", ()):
                contact.visible = (not self.get("red_insignia_found")
                                   and contact.group_index * 2 >= progress
                                   and not self.soldier_defeated(contact.actor.scripted_id))
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
            # The fallen commander belongs to the battlefield scenery; only
            # the final scene uses wounded_commander_ready to gate progression.
            if commander_prop is not None and commander_prop not in region["objects"]:
                region["objects"].append(commander_prop)

            if self.get("red_officer_escaped"):
                officer = region.pop("red_officer_actor", None)
                if officer in region.get("scenery", []):
                    region["scenery"].remove(officer)
                region["boss_battle_active"] = False
            elif self.get("red_officer_met") and "create_waiting_officer" in region:
                if "red_officer_actor" not in region:
                    region["red_officer_actor"] = region["create_waiting_officer"]()
                officer = region["red_officer_actor"]
                officer.guarded = self.get("red_officer_boss_ready")
                if self.get("red_officer_defeated"):
                    region["boss_battle_active"] = False
                    officer.state = "DEFEATED"
                    officer.hp = 1
                    # Enemy.alive is a read-only property derived from state.
                    if not isinstance(getattr(type(officer), "alive", None), property):
                        officer.alive = True
                    officer.hostile = officer.boss_battle_active = False
                    officer.guarded = False
                if officer not in region.setdefault("scenery", []):
                    region["scenery"].append(officer)

    @classmethod
    def from_dict(cls, data):
        return cls(data)
