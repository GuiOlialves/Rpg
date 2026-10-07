"""Render all of 1D with the real renderer; never reads or writes the user save."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from PIL import Image, ImageDraw
from core.camera import camera_for
from tests.test_edrin import EdrinTests
from ui.game_renderer import GameRenderer
from ui.world_renderer import draw_world


def run():
    fixture = EdrinTests()
    fixture.setUp()
    try:
        p, region, dialogue = fixture.p, fixture.p.region, fixture.dialogue
        out = ROOT / 'tools/visual_checks/edrin'
        out.mkdir(parents=True, exist_ok=True)
        font, title = pygame.font.Font(None, 22), pygame.font.Font(None, 30)
        canvas, renderer = pygame.Surface((1024, 576)), GameRenderer()
        def draw(scene=None):
            renderer.draw(canvas, region=region, player=p.player, enemies=[], drops=[],
                camera=camera_for(p.player, region['terrain'].get_size()), debug=False,
                damage_numbers=[], hitstop_frames=0, font=font, title_font=title,
                dialogue=dialogue, quest_manager=p.quests, ui_mode=None, inventory=p.inventory,
                inventory_ui={}, game_over_screen=None, story=p.story, edrin_scene=scene)
            return Image.frombytes('RGB', canvas.get_size(), pygame.image.tobytes(canvas, 'RGB'))
        full = pygame.Surface(region['terrain'].get_size())
        draw_world(full, region, font, (0, 0), None, [], [], show_controls=False, show_banner=False)
        pygame.image.save(full, out / 'trail.png')
        poses = Image.new('RGB', (576, 200), '#20292b')
        labels = ImageDraw.Draw(poses)
        for i, mode in enumerate(('idle', 'guard', 'alert', 'walk')):
            labels.text((i*144+12, 8), mode.upper(), fill='#e9d7b1')
            atlas = Image.open(ROOT / f'assets/vale_characters/edrin_{mode}.png')
            for j, facing in enumerate((0, 1)):
                im = atlas.crop((0, facing*36, 32, facing*36+36)).resize((64, 72), Image.Resampling.NEAREST)
                poses.paste(im, (i*144+12, 28+j*80), im)
        poses.save(out / 'edrin_poses.png')
        p.player.x, p.player.y = 305, 544
        target = region['interactables'][0]; dialogue.open(target)
        draw().save(out / 'tracking.png'); dialogue.npc = None
        p.player.x, p.player.y = 900, 400
        scene = fixture.start()
        frames, transcript, captures = [], [], {}
        previous_line, held_ms = None, 0
        for _ in range(900):
            if not scene.active: break
            line = (scene.index, dialogue.index) if dialogue.active else None
            if line != previous_line:
                held_ms = 0
                if line is not None:
                    transcript.append(dialogue.npc.lines[dialogue.index])
            previous_line = line
            image = draw(scene)
            phase = scene.phase
            if dialogue.active:
                speaker, text = dialogue.npc.lines[dialogue.index]
                for name, phrase in (('recognition', 'Você está morto.'), ('testimony', 'Eu vi você morrer.'),
                                     ('authority', 'Você dava as ordens.'),
                                     ('forgetting', 'Você já estava procurando um jeito de esquecer.'),
                                     ('clue', 'Ponte de Namar. Procure'), ('alone', 'Do que eu estava fugindo?')):
                    if text.startswith(phrase) and name not in captures:
                        image.save(out / f'{name}.png'); captures[name] = f'{name}.png'
            if phase in {'patrol', 'escape'} and 1000 <= scene.elapsed_ms < 1250 and phase not in captures:
                image.save(out / f'{phase}.png'); captures[phase] = f'{phase}.png'
            frames.append(image.resize((768, 432), Image.Resampling.NEAREST).convert(
                'P', palette=Image.Palette.ADAPTIVE, colors=128))
            held_ms += 250
            if dialogue.active and held_ms >= max(1500, min(3000, len(dialogue.npc.lines[dialogue.index][1])*35)):
                scene.advance()
            scene.update(250)
        assert not scene.active, 'A sequência não terminou.'
        draw().save(out / 'objective.png')
        frames[0].save(out / 'encounter.gif', save_all=True, append_images=frames[1:], duration=250,
                       loop=0, optimize=True, disposal=2)
        order = ('recognition', 'testimony', 'authority', 'forgetting', 'patrol', 'clue', 'escape', 'alone')
        board = Image.new('RGB', (1024, 1248), '#111b20')
        labels = ImageDraw.Draw(board)
        for i, name in enumerate(order):
            x, y = (i % 2)*512, (i // 2)*312
            im = Image.open(out / captures[name]).resize((512, 288), Image.Resampling.NEAREST)
            board.paste(im, (x, y+24)); labels.text((x+12, y+7), name.upper(), fill='#e9d7b1')
        board.save(out / 'storyboard.png')
        (out / 'review.json').write_text(json.dumps({'dialogue': transcript, 'flags': p.story.to_dict(),
            'objective': p.story.objective_text, 'snapshots': captures, 'duration_ms': len(frames)*250},
            ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'1D renderizado: {len(transcript)} falas, {len(captures)} cenas, {len(frames)*250} ms.')
    finally:
        fixture.tearDown()


if __name__ == '__main__': run()
