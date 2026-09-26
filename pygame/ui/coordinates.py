"""Conversões de coordenadas entre janela e tela lógica."""
from core.config import VIEW, WINDOW

def logical_mouse_position(position):
    return (position[0] * VIEW[0] // WINDOW[0], position[1] * VIEW[1] // WINDOW[1])
