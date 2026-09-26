"""Static, repeatable scene interactions that reuse the NPC dialogue UI."""
import pygame


class Interactable:
    def __init__(self, uid, name, position, image, lines, *, prompt="[E] Examinar",
                 interaction_radius=66, transition_to=None, condition=None,
                 transition_on_interact=False):
        self.uid = uid
        self.name = name
        self.position = (float(position[0]), float(position[1]))
        self.x, self.y = self.position
        self.image = image
        self.dialogues = {"default": tuple(lines)}
        self.prompt = prompt
        self.interaction_radius = int(interaction_radius)
        self.transition_to = transition_to
        self.transition_on_interact = bool(transition_on_interact)
        self.condition = condition
        self.enabled = True
        self.opened = False

    @property
    def interaction_rect(self):
        diameter = self.interaction_radius * 2
        return pygame.Rect(round(self.x - self.interaction_radius),
                          round(self.y - self.interaction_radius), diameter, diameter)

    def available(self, context=None):
        if not self.enabled:
            return False
        return self.condition(context) if self.condition else True

    def dialogue_for(self, state, manager=None):
        return self.dialogues.get(state, self.dialogues["default"])

    def begin_interaction(self, dialogue, player, manager=None):
        dialogue.open(self, manager)

    def draw(self, canvas, camera):
        canvas.blit(self.image,
                    (round(self.x - self.image.get_width() / 2 - camera[0]),
                     round(self.y - self.image.get_height() / 2 - camera[1])))
