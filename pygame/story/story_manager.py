"""Armazena flags narrativas simples em formato serializável.

Flags devem ser adicionadas quando uma cena real precisar delas; não há
conteúdo narrativo ou flags hipotéticas nesta infraestrutura inicial.
"""


class StoryManager:
    def __init__(self, flags=None):
        if flags is None:
            flags = {}
        self._validate(flags)
        self.flags = dict(flags)

    @staticmethod
    def _validate(flags):
        if not isinstance(flags, dict):
            raise TypeError("As flags da história devem ser um objeto/dicionário.")
        if any(not isinstance(name, str) or type(value) is not bool
               for name, value in flags.items()):
            raise ValueError("Cada flag deve ter nome texto e valor booleano.")

    def get(self, name, default=False):
        return self.flags.get(name, default)

    def set(self, name, value=True):
        self._validate({name: value})
        self.flags[name] = value

    def to_dict(self):
        return dict(self.flags)

    @classmethod
    def from_dict(cls, data):
        return cls(data)
