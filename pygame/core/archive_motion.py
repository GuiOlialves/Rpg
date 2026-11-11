"""Native grip coordinates shared by the archive veteran's body and blade."""
import math

COUNTS = {'idle': 4, 'walk': 8, 'quick': 8, 'wide': 8, 'advance': 8, 'hurt': 3, 'defeated': 4}
ANGLES = {'quick': (-65, -55, -35, 0, 20, 35, 40, 42),
          'wide': (-125, -115, -85, -25, 25, 70, 85, 90),
          'advance': (-25, -15, 0, 0, 0, 15, 30, 40)}


def pose(action, index, facing):
    forward = ((0, 1), (-1, 0), (1, 0), (0, -1))[facing]
    angle = math.atan2(forward[1], forward[0]) + math.radians(ANGLES.get(action, (25,)*8)[index])
    lean = (0, -1, 0, 2, 2, 1, 1, 0)[index] if action in ANGLES else 0
    center = (24 + forward[0]*lean, 36 + forward[1]*lean)
    # Shoulder -> bent elbow -> grip, never a blade attached to the shoulder.
    grip = (center[0] + math.cos(angle)*9, center[1] - 14 + math.sin(angle)*9)
    tip = (grip[0] + math.cos(angle)*30, grip[1] + math.sin(angle)*30)
    return center, grip, tip
