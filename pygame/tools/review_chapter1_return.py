"""Render Chapter 1A with current runtime art, without touching the real save."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw
import pygame
from core.assets import load
from core.camera import camera_for
from core.debug_checkpoints import create_checkpoint
from story.arrival_scene import restore_resident, ScriptedDialogue
from story.chapter1_return import Chapter1ReturnScene, Chapter1AldenScene
from story.prologue import opening_sequence
from story.prologue_3c import EPILOGUE
from systems.dialogue import DialogueBox
from ui.game_renderer import GameRenderer
from world.world_manager import WorldManager


def run():
    pygame.init()
    pygame.display.set_mode((1, 1))
    out = ROOT / "tools/visual_checks/chapter1_return"
    out.mkdir(parents=True, exist_ok=True)
    world = WorldManager.for_game(load)
    p = create_checkpoint("prologue_2e", load=load, build_region=world.build_region,
        spawn_enemies=world.spawn_enemies, restore_resident=restore_resident,
        opening_sequence=opening_sequence)
    for flag in ("red_officer_met", "red_officer_boss_ready", "red_officer_defeated",
                 "red_officer_memory_seen", "red_officer_escaped", "prologue_completed"):
        p.story.set(flag)
    p.story.apply_to_region(p.region)
    dialogue, renderer = DialogueBox(), GameRenderer()
    canvas = pygame.Surface((1024, 576))
    font, title_font = pygame.font.Font(None, 22), pygame.font.Font(None, 30)

    def draw(return_scene=None, alden_scene=None):
        renderer.draw(canvas, region=p.region, player=p.player, enemies=[], drops=[],
            camera=camera_for(p.player, p.region["terrain"].get_size()), debug=False,
            damage_numbers=[], hitstop_frames=0, font=font, title_font=title_font,
            dialogue=dialogue, quest_manager=p.quests, ui_mode=None,
            inventory=p.inventory, inventory_ui={}, game_over_screen=None,
            story=p.story, chapter1_return_scene=return_scene, alden_scene=alden_scene)
        return Image.frombytes("RGB", canvas.get_size(), pygame.image.tobytes(canvas, "RGB"))

    def return_home():
        p.region_id = "village"
        p.region = world.build_region("village")
        restore_resident(p.region, load("assets/npc/civilian_customer.png"))
        p.player.x, p.player.y = p.region["spawn"]["forest"]
        return p.region

    dialogue.open(ScriptedDialogue((EPILOGUE[2],)))
    draw().save(out / "last_question.png")
    dialogue.npc = None
    scene = Chapter1ReturnScene(p.player, p.story, p.quests, return_home)
    frames = []
    captures = {1100: "title_fade_in", 1900: "chapter_title", 3500: "title_fade_out",
                4100: "black_return", 4800: "village_fade_in"}
    elapsed = 0
    frames.append(draw(scene))
    while scene.active:
        scene.update(100)
        elapsed += 100
        image = draw(scene if scene.active else None)
        frames.append(image)
        if elapsed in captures:
            image.save(out / (captures[elapsed] + ".png"))
    draw().save(out / "village_return.png")
    frames.extend([frames[-1]] * 14)
    palette = [im.convert("P", palette=Image.Palette.ADAPTIVE, colors=128) for im in frames]
    palette[0].save(out / "transition.gif", save_all=True, append_images=palette[1:],
                    duration=100, loop=0, optimize=True)

    alden = next(n for n in p.region["npcs"] if n.uid == "alden")
    p.player.x, p.player.y = 1830, 560
    talk = Chapter1AldenScene(alden, p.player, dialogue, p.region)
    for _ in range(400):
        if not talk.active:
            break
        if dialogue.active:
            line = dialogue.npc.dialogue_for("default")[dialogue.index]
            if line == "Eu fazia parte deles.":
                draw(alden_scene=talk).save(out / "alden_admission.png")
            if "Não entraram no Vale." in line:
                draw(alden_scene=talk).save(out / "alden_lead.png")
            talk.advance(dialogue)
        talk.update(100, dialogue, p.story, p.quests, p.inventory)
    draw().save(out / "objective_road.png")
    p.player.x, p.player.y = 180, 575
    draw().save(out / "road_connection.png")
    names = ("chapter_title", "village_return", "alden_admission", "objective_road")
    plate = Image.new("RGB", (1024, 616), "#111a20")
    labels = ImageDraw.Draw(plate)
    for i, name in enumerate(names):
        x, y = (i % 2) * 512, (i // 2) * 308
        plate.paste(Image.open(out / (name + ".png")).resize((512, 288)), (x, y))
        labels.text((x + 12, y + 290), name.replace("_", " "), fill="#e6d7b8")
    plate.save(out / "storyboard.png")
    report = {"title_ms": sum(b.duration_ms for b in scene.TITLE_BEATS),
              "return_ms": scene.RETURN_MS, "objective": p.story.objective_text,
              "flags": {key: p.story.get(key) for key in
                        ("prologue_completed", "chapter1_started", "chapter1_returned",
                         "chapter1_alden_talk", "old_road_unlocked")},
              "regions": world.region_ids, "transition_frames": len(frames),
              "dialogue_finished": not talk.active}
    (out / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    pygame.quit()


if __name__ == "__main__":
    run()
