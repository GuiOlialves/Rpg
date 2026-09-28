"""Pack validation and in-map scale/animation previews. Never reads/writes saves."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from PIL import Image, ImageColor
from core.assets import load
from core.debug_checkpoints import create_checkpoint
from entities.enemy import Enemy
from entities.npc import NPC
from entities.red_officer import RedOfficer
from entities.player import Player
from story.arrival_scene import restore_resident
from story.blue_march import BlueMarchScene
from story.forest_confrontation import create_waiting_officer
from story.prologue import opening_sequence
from ui.character_art import character_sheet, character_frame, draw_character
from ui.world_renderer import draw_world
from world.world_manager import WorldManager


def validate():
    manifest = json.loads((ROOT / "assets/vale_characters/manifest.json").read_text())
    palette = {ImageColor.getrgb(c) for c in manifest["palette"].values()}
    total, max_colors = 0, 0
    for look, actions in manifest["characters"].items():
        for action, spec in actions.items():
            im = Image.open(ROOT / "assets/vale_characters" / spec["file"]).convert("RGBA")
            count = spec["frames_per_direction"]
            assert im.size == (32 * count, 128), spec
            assert set(im.getchannel("A").tobytes()) == {0, 255}, spec
            for facing in range(4):
                for frame in range(count):
                    tile = im.crop((frame*32, facing*32, (frame+1)*32, (facing+1)*32))
                    colors = {c[:3] for _, c in tile.getcolors(1024) if c[3]}
                    assert colors <= palette and tile.getbbox(), (look, action, frame)
                    assert tile.getbbox()[3] == 28, (look, action, frame, tile.getbbox())
                    max_colors = max(max_colors, len(colors))
                    total += 1
    return manifest, {"characters": len(manifest["characters"]), "frames": total,
                      "palette_colors": len(palette), "max_colors_per_frame": max_colors}


def run(output):
    manifest, report = validate()
    pygame.init()
    pygame.display.set_mode((1, 1))
    output.mkdir(parents=True, exist_ok=True)
    world = WorldManager.for_game(load)
    font = pygame.font.Font(None, 20)
    heading = pygame.font.Font(None, 28)
    canvas = pygame.Surface((1024, 576))

    # Smoke only: check every existing player slot through the actual renderer.
    player = Player(load("assets/player/f_player_sheet.png"),
                    load("assets/player/f_player_attack_sheet.png"))
    player.x, player.y = 100, 100
    player_cases = 0
    for action, count in (("walk",6),("attack",8)):
        for facing in range(4):
            for index in range(count):
                player.facing, player.walk_frame = facing, index
                player.attack_timer = 16-index*2 if action == "attack" else 0
                actual, expected = [pygame.Surface((200,150),pygame.SRCALPHA) for _ in range(2)]
                player.draw(actual,(0,0))
                draw_character(expected,(0,0),character_sheet(load,"protagonist",action),
                               100,100,index,facing)
                assert actual.get_bounding_rect().bottom == 100
                assert pygame.image.tobytes(actual,"RGBA") == pygame.image.tobytes(expected,"RGBA")
                player_cases += 1
    report["player_render_slots"] = player_cases

    def checkpoint(name):
        return create_checkpoint(name, load=load, build_region=world.build_region,
                                 spawn_enemies=world.spawn_enemies,
                                 restore_resident=restore_resident, opening_sequence=opening_sequence)

    village = checkpoint("prologue_2a")
    forest = checkpoint("prologue_2e")
    sheets = {}

    def capture(name, runtime, actors, labels):
        # Preview placement only: world geometry, actor rendering and scale are real.
        region = dict(runtime.region)
        region["npcs"] = []
        region["red_contacts"] = []
        region["scenery"] = [obj for obj in region.get("scenery", [])
                             if not hasattr(obj, "group_index") and obj is not region.get("red_officer_actor")]
        camera = (510, 280)
        runtime.player.x, runtime.player.y = 1320, 572
        runtime.player.facing = 0
        draw_world(canvas, region, font, camera, player=runtime.player, enemies=[],
                   scene_actors=actors, show_controls=False, show_banner=False)
        pygame.draw.rect(canvas, (25, 29, 36), (0, 0, 1024, 54))
        canvas.blit(heading.render(name.replace("_", " "), True, (224, 205, 167)), (20, 12))
        for actor, label in zip(actors + [runtime.player], labels + ["Protagonista refinado"]):
            text = font.render(label, True, (244, 231, 202))
            pos = (round(actor.x-camera[0]-text.get_width()/2), round(actor.y-camera[1]+12))
            pygame.draw.rect(canvas, (31, 35, 38), (*pos, text.get_width(), 17))
            canvas.blit(text, pos)
        pygame.image.save(canvas, output / f"{name}.png")
        sheets[name] = canvas.copy()

    civilians = [NPC(look, look, (700+i*115, 572), {},
                     character_sheet(load, "civilian_"+look, "walk"),
                     frame_size=32, draw_size=48)
                 for i, look in enumerate(("man", "woman", "elder", "merchant", "worker"))]
    capture("01_civis_escala", village, civilians,
            ["Morador", "Mira", "Alden", "Comerciante", "Tomas"])
    blues = BlueMarchScene._make_column(load)
    for i, actor in enumerate(blues):
        actor.x, actor.y, actor.facing = 780+i*130, 572, 0
    capture("02_tropa_azul_escala", village, blues,
            ["Comandante", "Soldado A", "Soldado B", "Soldado C"])
    reds = [Enemy("red_soldier", (810+i*160, 572), load, seed=i) for i in range(3)]
    capture("03_tropa_vermelha_escala", forest, reds, ["Soldado A", "Soldado B", "Soldado C"])
    boss = RedOfficer((1120, 572), load, defeat_hp=1)
    for label, state, phase, timer in (("idle", "IDLE", None, 0),
                                     ("walk", "CHASE", None, 0),
                                     ("windup", "ATTACK", "windup", 14),
                                     ("attack", "ATTACK", "active", 5),
                                     ("hurt", "HURT", None, 0),
                                     ("defeated", "DEFEATED", None, 0)):
        boss.state, boss.attack_phase, boss.phase_timer = state, phase, timer
        boss.anim_tick, boss.attack_action, boss.attack_direction = 8, "normal", (1, 0)
        before = (boss.x, boss.y, boss.hp, boss.state, boss.attack_phase, boss.phase_timer)
        capture("04_oficial_" + label, forest, [boss], ["Oficial: " + label])
        assert before == (boss.x, boss.y, boss.hp, boss.state, boss.attack_phase, boss.phase_timer)

    # Dialogue and combat actors must use the identical defeated pose and pivot.
    npc = create_waiting_officer(load, (100, 100))
    npc.state, npc.facing = "DEFEATED", 2
    boss.x, boss.y, boss.facing = 100, 100, 1
    a, b = [pygame.Surface((200, 160), pygame.SRCALPHA) for _ in range(2)]
    npc.draw(a, (0, 0))
    boss.draw(b, (0, 0))
    assert pygame.image.tobytes(a, "RGBA") == pygame.image.tobytes(b, "RGBA")

    # Same pack, now including the harmonized protagonist, at 4x / 1x / 1.5x.
    contact = pygame.Surface((1050, 520))
    contact.fill((30, 35, 43))
    looks = list(manifest["characters"])
    for i, look in enumerate(looks):
        x, y = (i % 7)*150, (i // 7)*260
        image = character_frame(character_sheet(load, look), draw_size=128)
        contact.blit(image, (x+11,y+12))
        for j, part in enumerate(look.split("_", 1)):
            contact.blit(font.render(part, True, (219, 206, 178)), (x+10,y+158+j*18))
        native = character_frame(character_sheet(load, look), draw_size=32)
        contact.blit(native, (x+20,y+207))
        contact.blit(character_frame(character_sheet(load, look), facing=2), (x+72,y+195))
    pygame.image.save(contact, output / "catalogo.png")

    # Inspect the new hero's six walk/eight attack slots and all cardinal views.
    poses = pygame.Surface((960, 360))
    poses.fill((30,35,43))
    for facing, label in enumerate(("baixo", "esquerda", "direita", "cima")):
        poses.blit(font.render(label, True, (219,206,178)), (8, facing*90+35))
        column = 0
        for action, count in (("walk",6),("attack",8)):
            for index in range(count):
                x, y = 110+column*60, facing*90+64
                pygame.draw.line(poses,(62,72,73),(x-23,y),(x+23,y))
                draw_character(poses,(0,0),character_sheet(load,"protagonist",action),
                               x,y,index,facing)
                poses.blit(font.render(f"{action[0]}{index}",True,(219,206,178)),(x-8,y+6))
                column += 1
    pygame.image.save(poses, output / "05_protagonista_frames.png")

    # A lossless animated comparison of the actual 48 px game frames.
    frames = []
    for tick in range(16):
        strip = pygame.Surface((1120, 220))
        strip.fill((30,35,43))
        for i, look in enumerate(manifest["characters"]):
            x = 40+i*80
            draw_character(strip, (0,0), character_sheet(load, look, "walk"),
                           x, 90, tick//2, 2)
            action = "attack" if look.startswith("red") or look == "protagonist" else "idle"
            draw_character(strip, (0,0), character_sheet(load, look, action),
                           x, 180, tick//2, 2)
        strip.blit(font.render("Caminhada / ataque - escala real do jogo", False, (219,206,178)), (12,12))
        frames.append(Image.frombytes("RGB", strip.get_size(), pygame.image.tobytes(strip, "RGB")))
    frames[0].save(output / "animacoes.gif", save_all=True, append_images=frames[1:],
                   duration=120, loop=0, disposal=2)
    report["previews"] = list(sheets)
    (output / "validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "tools/visual_checks/vale_characters")
    run(parser.parse_args().output.resolve())
