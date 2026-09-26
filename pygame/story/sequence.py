"""Small, data-driven timed sequence; gameplay ownership stays in Game."""
from dataclasses import dataclass

from story.fade import FadeOverlay


@dataclass(frozen=True)
class Beat:
    text: str | None
    duration_ms: int
    background: str = "black"
    fade_in_ms: int = 0

    def __post_init__(self):
        if self.duration_ms <= 0 or self.background not in {"black", "world"}:
            raise ValueError("Fragmento narrativo inválido.")


class NarrativeSequence:
    def __init__(self, beats):
        self.beats = tuple(beats)
        if not self.beats:
            raise ValueError("A sequência precisa ter ao menos um fragmento.")
        self.fade = FadeOverlay()
        self.active = False
        self.index = 0
        self.remaining_ms = 0

    @property
    def current(self):
        return self.beats[self.index] if self.active else None

    def start(self):
        self.index = 0
        self.remaining_ms = self.beats[0].duration_ms
        self.fade = FadeOverlay()
        self.active = True

    def update(self, delta_ms):
        """Advance by elapsed time; return True exactly when the sequence ends."""
        if not self.active:
            return False
        remaining_delta = max(0, int(delta_ms))
        while self.active and remaining_delta >= self.remaining_ms:
            step = self.remaining_ms
            self.fade.update(step)
            remaining_delta -= step
            self.index += 1
            if self.index >= len(self.beats):
                self.active = False
                self.remaining_ms = 0
                return True
            beat = self.beats[self.index]
            self.remaining_ms = beat.duration_ms
            if beat.fade_in_ms:
                self.fade.start("in", beat.fade_in_ms)
        if self.active and remaining_delta:
            self.fade.update(remaining_delta)
            self.remaining_ms -= remaining_delta
        return False
