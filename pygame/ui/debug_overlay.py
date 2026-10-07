"""Read-only diagnostics shown by the existing F3 debug toggle."""
import pygame

_DEBUG_FONT = None


def _active(scene):
    return scene is not None and getattr(scene, "active", False)


def narrative_stage(region_id, story, quest):
    if story.get("pursuit_entered"):
        return "Capítulo 1D — O Homem que Deveria Estar Morto"
    if story.get("watchpost_entered"):
        return "Capítulo 1C — O Posto de Vigia"
    if story.get("old_road_entered"):
        return "Capítulo 1B — A Antiga Estrada"
    if story.get("chapter1_started"):
        return "Capítulo 1A — O Retorno"
    if not story.get("woke_up"):
        return "Prólogo 1 — Abertura"
    if story.get("red_officer_met"):
        return "Prólogo 2E — O Fantasma concluído"
    if story.get("blue_army_departed"):
        if (story.get("red_insignia_found")
                or story.get("forest_battle_progress", 0) >= 10):
            return "Prólogo 2E — O Fantasma"
        return "Prólogo 2D — Campo de batalha"
    if story.get("house_searched"):
        return "Prólogo 2C — A Marcha Azul"
    if story.get("house_investigation_unlocked"):
        return "Prólogo 2B — A Casa Vazia"
    if story.get("slime_quest_started"):
        if quest.progress >= quest.required:
            return "Prólogo 2A — Retorno dos Slimes"
        return "Prólogo 1 — Problemas na Floresta"
    if story.get("saw_silhouette"):
        return "Prólogo 1 — Vila"
    if region_id == "home":
        return "Prólogo 1 — Casa inicial"
    return "Prólogo 1"


def _scene_status(*, narrative, arrival_scene, alden_scene, house_memory_scene,
                  blue_march_scene, forest_ambush_scene, insignia_memory_scene,
                  red_officer_scene, transition_active, prologue_3c_scene=None,
                  chapter1_return_scene=None, old_road_scene=None, watchpost_scene=None, edrin_scene=None):
    if narrative is not None and narrative.active:
        return f"opening_sequence {narrative.index + 1}/{len(narrative.beats)}", True
    scene_rows = (
        (arrival_scene, lambda: f"arrival_scene:{arrival_scene.phase}"),
        (alden_scene, lambda: f"{getattr(alden_scene, 'debug_label', 'alden_post_slimes')}:{alden_scene.index + 1}/{len(alden_scene.STEPS)}"),
        (house_memory_scene, lambda: f"house_memory:{house_memory_scene.kind}:{house_memory_scene.index + 1}/{len(house_memory_scene.steps)}"),
        (blue_march_scene, lambda: f"blue_march:{blue_march_scene.phase}"),
        (forest_ambush_scene, lambda: "red_ambush"),
        (insignia_memory_scene, lambda: f"insignia_memory:{insignia_memory_scene.index + 1}/{len(insignia_memory_scene.steps)}"),
        (red_officer_scene, lambda: f"red_officer:{red_officer_scene.phase}"),
        (prologue_3c_scene, lambda: f"prologue_3c:{prologue_3c_scene.phase}"),
        (chapter1_return_scene, lambda: f"chapter1_return:{chapter1_return_scene.phase}"),
        (old_road_scene, lambda: f"old_road:{old_road_scene.kind}"),
        (watchpost_scene, lambda: f"watchpost:{watchpost_scene.kind}"),
        (edrin_scene, lambda: f"edrin:{edrin_scene.phase}"),
    )
    for scene, label in scene_rows:
        if _active(scene):
            return label(), True
    if transition_active:
        return "region_transition", True
    return "nenhuma", False


def _visible_player(player, narrative, transition_fade, scenes):
    visible = player.hp > 0 and (
        player.invulnerability_timer == 0
        or (player.invulnerability_timer // 4) % 2 == 0)
    sequences = [narrative]
    sequences.extend(getattr(scene, "sequence", None) for scene in scenes.values())
    for sequence in sequences:
        if sequence is None or not getattr(sequence, "active", False):
            continue
        beat = sequence.current
        visible = visible and beat is not None and beat.background == "world"
        visible = visible and sequence.fade.alpha < 250
    if transition_fade is not None and transition_fade.alpha >= 250:
        visible = False
    return visible


def _entity_counts(region, enemies, *, blue_march_scene, forest_ambush_scene,
                   red_officer_scene):
    alive = [enemy for enemy in enemies if getattr(enemy, "state", "") != "DEAD"]
    red_enemies = [enemy for enemy in alive if getattr(enemy, "kind", "") == "red_soldier"]
    blue_actors = (blue_march_scene.actors
                   if _active(blue_march_scene) else ())
    blue_soldiers = sum(1 for actor in blue_actors
                        if "azul" in getattr(actor, "name", "").lower()
                        and "comandante" not in actor.name.lower())
    red_ambush_actors = (forest_ambush_scene.actors
                         if _active(forest_ambush_scene) else ())
    red_soldiers = len(red_enemies) + len(red_ambush_actors)
    extra_npcs = len(blue_actors) + len(red_ambush_actors)
    if _active(red_officer_scene):
        extra_npcs += 2  # Oficial e comandante ferido.
    boss = any(getattr(enemy, "kind", "") == "forest_guardian"
               and getattr(enemy, "state", "") != "DEAD" for enemy in enemies)
    return {
        "npcs": len(region.get("npcs", ())) + extra_npcs,
        "enemies": len(alive),
        "slimes": sum(1 for enemy in alive if getattr(enemy, "kind", "") == "slime"),
        "blue": blue_soldiers,
        "red": red_soldiers,
        "boss": boss,
    }


def _story_flags(region_id, story):
    if story.get('pursuit_entered'):
        names = ('edrin_met', 'edrin_name_known', 'edrin_death_revealed', 'edrin_authority_revealed',
                 'edrin_forgetting_revealed', 'edrin_encounter_completed')
        return [(name, str(story.get(name))) for name in names]
    if story.get("watchpost_entered"):
        names = ("watchpost_entry_open","watchpost_roster_read","watchpost_personal_item_found",
                 "watchpost_flashback_seen","watchpost_blue_order_found","watchpost_trail_found")
    elif story.get("old_road_entered"):
        names = ("old_road_entered","road_red_clue_found","road_blue_trace_found",
                 "road_memory_seen","road_camp_found","watchpost_seen")
    elif story.get("chapter1_started"):
        names = ("prologue_completed", "chapter1_started", "chapter1_returned",
                 "chapter1_alden_talk", "old_road_unlocked")
    elif region_id == "forest":
        names = ("blue_army_departed", "forest_massacre_discovered",
                 "forest_battle_progress", "red_insignia_found", "red_officer_met")
    elif story.get("house_investigation_unlocked"):
        names = ("alden_post_slimes_talk", "house_investigation_unlocked",
                 "pendant_found", "house_searched", "blue_army_departed")
    elif region_id == "village":
        names = ("woke_up", "saw_silhouette", "slime_quest_started",
                 "alden_post_slimes_talk", "house_investigation_unlocked")
    else:
        names = ("woke_up", "saw_silhouette", "slime_quest_started")
    return [(name, (f"{story.get(name, 0)}/10" if name == "forest_battle_progress"
                    else str(story.get(name)))) for name in names]


def draw_debug_overlay(surface, *, current_region, region, player, enemies,
                       story, quests, narrative, scenes, dialogue, ui_mode,
                       transition_active, transition_fade, game_over_screen,
                       checkpoint_label=""):
    """Draw compact status text. This function only reads runtime objects."""
    global _DEBUG_FONT
    if _DEBUG_FONT is None:
        _DEBUG_FONT = pygame.font.Font(None, 16)
    quest = quests.get("forest_trouble")
    cutscene, scripted_lock = _scene_status(
        narrative=narrative, transition_active=transition_active, **scenes)
    counts = _entity_counts(region, enemies, **{
        key: scenes[key] for key in (
            "blue_march_scene", "forest_ambush_scene",
            "red_officer_scene")})
    rows = [("DEBUG F3", "accent")]
    if checkpoint_label:
        rows.extend((("DEBUG CHECKPOINT", "accent"),
                     (checkpoint_label.removeprefix("DEBUG — "), "accent")))
    rows.extend((
        (f"REGIÃO  {current_region} | {region.get('story_phase', 'sem estado')}", "normal"),
        (f"STORY  {narrative_stage(current_region, story, quest)}", "normal"),
        ("CORES  sólido laranja | saída rosa | story roxo", "accent"),
        ("Interação verde | NPC azul | jogador ciano", "accent"),
        ("Inimigo vermelho | ataque amarelo", "accent"),
    ))
    rows.extend((f"{name}: {value}", "flag") for name, value in _story_flags(current_region, story))
    rows.extend((
        (f"QUEST  {quest.name} | {quest.state} | {quest.progress}/{quest.required}", "normal"),
        (f"CUTSCENE  {cutscene}", "normal"),
    ))
    if dialogue.active and not scripted_lock:
        rows.append(("INPUT  parcial — E avança diálogo", "warning"))
    else:
        locked = scripted_lock or ui_mode is not None or game_over_screen is not None
        rows.append((f"INPUT  {'bloqueado' if locked else 'liberado'}", "warning"))
    rows.extend((
        (f"PLAYER  x={player.x:.0f} y={player.y:.0f}", "normal"),
        (f"HP {player.hp}/{player.max_hp}   SP {player.sp}/{player.max_sp}   visível {_visible_player(player, narrative, transition_fade, scenes)}", "normal"),
        (f"ENTIDADES  NPC {counts['npcs']} | inimigos {counts['enemies']}", "normal"),
        (f"Slimes {counts['slimes']} | Azuis {counts['blue']} | Vermelhos {counts['red']} | Boss {'ativo' if counts['boss'] else 'não'}", "normal"),
    ))

    font = _DEBUG_FONT
    line_height = 18
    panel_width = 352
    panel_height = 12 + len(rows) * line_height + 8
    panel = pygame.Rect(surface.get_width() - panel_width - 12, 50,
                        panel_width, min(panel_height, surface.get_height() - 60))
    bg = pygame.Surface(panel.size, pygame.SRCALPHA)
    bg.fill((10, 15, 18, 218))
    surface.blit(bg, panel.topleft)
    pygame.draw.rect(surface, (96, 116, 119), panel, 1)
    colors = {
        "normal": (223, 228, 219),
        "flag": (170, 213, 195),
        "accent": (248, 210, 128),
        "warning": (249, 173, 127),
    }
    for index, (text, kind) in enumerate(rows):
        while font.size(text)[0] > panel.width - 18 and len(text) > 4:
            text = text[:-4] + "..."
        rendered = font.render(text, True, colors[kind])
        y = panel.y + 7 + index * line_height
        if y + rendered.get_height() <= panel.bottom - 4:
            surface.blit(rendered, (panel.x + 9, y))
