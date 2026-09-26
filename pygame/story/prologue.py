"""Only the approved opening beats: CENA 00 and the start of CENA 01."""
from story.sequence import Beat, NarrativeSequence


def opening_sequence():
    beats = [
        Beat("Corre.", 2100),
        Beat("Não olha para trás.", 2400),
        Beat("Você prometeu.", 2400),
        Beat("*****", 3000),
        Beat("...", 1500),
        Beat(None, 1250, background="world", fade_in_ms=1200),
        Beat("Onde...", 1800, background="world"),
        Beat("...", 1200, background="world"),
        Beat("Quem sou eu?", 2000, background="world"),
        Beat("Meu nome...", 1800, background="world"),
        Beat("*****", 2600, background="world"),
        Beat(None, 900, background="world"),
        Beat("Esse nome...", 1800, background="world"),
        Beat("Não.", 1400, background="world"),
        Beat("Nem isso.", 2200, background="world"),
    ]
    sequence = NarrativeSequence(beats)
    sequence.start()
    return sequence
