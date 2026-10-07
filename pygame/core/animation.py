"""Presentation timing at the game's existing 60 Hz; no gameplay stat changes."""
BODY_FRAME = 32
HERO_FRAME = (32, 36)
HERO_PIVOT = (16, 34)
BODY_PIVOT = (16, 28)
BODY_SCALE = 2
BODY_DRAW_SIZE = BODY_FRAME * BODY_SCALE
WEAPON_FRAME = 96
WEAPON_PIVOT = (48, 58)
HEAVY_WEAPON_FRAME = 160
HEAVY_WEAPON_PIVOT = (80, 90)
IDLE_DURATIONS = (50, 18, 5, 47)
ATTACK_DURATIONS = (2, 2, 1, 1, 2, 2, 2, 4)
ATTACK_ACTIVE_ELAPSED = (4, 9)
WALK_STRIDE_PIXELS = 64.0
HERO_WALK_STRIDE_PIXELS = 40.0
DASH_POSE_DURATIONS = (1, 2, 8)
DASH_RECOVERY_DURATIONS = (2, 3)
DASH_TRAIL_FRAMES = 5
DASH_TRAIL_SPACING = 3
DASH_TRAIL_ALPHA = 12
HURT_FRAMES = 9
DEATH_DURATIONS = (5, 7, 8, 16)
FX_FRAMES = 12
IMPACT_TEXT_HEADROOM = 32


def timed_frame(tick, durations, loop=True):
    tick = tick % sum(durations) if loop else min(max(0, tick), sum(durations)-1)
    for index, duration in enumerate(durations):
        if tick < duration:
            return index
        tick -= duration
    return len(durations)-1


def cardinal(dx, dy):
    return (2 if dx >= 0 else 1) if abs(dx) >= abs(dy) else (0 if dy >= 0 else 3)
