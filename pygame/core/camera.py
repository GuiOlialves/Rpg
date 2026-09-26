"""Camera framing for the current player position."""
from core.config import VIEW, WORLD

def camera_for(player, bounds=WORLD):
    return (max(0, min(bounds[0] - VIEW[0], round(player.x - VIEW[0] / 2))), max(0, min(bounds[1] - VIEW[1], round(player.y - VIEW[1] / 2))))
