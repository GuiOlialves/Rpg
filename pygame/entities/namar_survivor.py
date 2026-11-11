"""Two civilians with distinct authored clothing and contextual conversation."""
import pygame
from entities.npc import NPC


class RecordsCarrier(NPC):
    """A small packet of indexed papers distinguishes the porter from the guards."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bag = pygame.Surface((9, 11), pygame.SRCALPHA)
        pygame.draw.rect(bag, (37, 43, 60), (0, 2, 9, 9))
        pygame.draw.rect(bag, (112, 79, 57), (1, 4, 7, 6))
        for x in (2, 5):
            pygame.draw.rect(bag, (220, 205, 163), (x, 0, 2, 6))
            pygame.draw.line(bag, (128, 115, 83), (x, 1), (x+1, 1))
        pygame.draw.line(bag, (172, 140, 87), (1, 7), (7, 7))
        self.records_bag = pygame.transform.scale_by(bag, 2)

    def draw(self, canvas, camera):
        super().draw(canvas, camera)
        dx = -12 if self.facing == 1 else 8
        x, y = round(self.x-camera[0]+dx), round(self.y-camera[1]-32)
        pygame.draw.line(canvas, (103, 75, 52), (x-3,y-12), (x+9,y+2), 2)
        canvas.blit(self.records_bag, (x,y))


class NamarSurvivor(NPC):
    def __init__(self, uid, name, position, load):
        super().__init__(uid, name, position, {'default': ()},
                         load(f'assets/vale_characters/{uid}_idle.png'),
                         run_sprite=load(f'assets/vale_characters/{uid}_walk.png'),
                         frame_size=32, draw_size=64)
        self.story = None

    def dialogue_for(self, state, manager=None):
        if self.story and self.story.get('namar_completed'):
            if self.uid == 'mara':
                return (('A farinha chegou ao abrigo. Desta vez, pelo menos.'
                         if self.story.get('namar_choice_protect') else
                         'Perdemos as sacas. Ainda temos as mãos para começar de novo.'),
                        'O depósito fica além da margem seca. Leve o que encontrou.')
            return (('A roda aguentou. Vou levar Mara antes que voltem.'
                     if self.story.get('namar_choice_protect') else
                     'Meu braço vai sarar. A carroça ficou, mas nós saímos.'),
                    'Se descobrir por que fecharam Namar, volte e nos diga.')
        if self.uid == 'mara':
            return ('Mara. Eu tinha uma padaria do outro lado da ponte.',
                    'Sobrou farinha para dois dias. Precisamos levá-la ao abrigo.',
                    'Essa placa no seu cinto... Vermelha. Não me peça confiança de uma vez.')
        return ('Téo. Conserto rodas; hoje só consigo amarrar o que quebrou.',
                'Ela quer salvar as sacas. Eu quero chegar com os dois braços inteiros.',
                'A muralha tem uma passagem baixa. Se precisarmos correr, iremos por lá.')
