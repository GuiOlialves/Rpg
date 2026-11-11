"""Registry furniture, sealed correspondence and attempted destruction, at native 2x."""
import pygame
from world.regions.watchpost_art import INK, WOOD, PLANK, LIGHT, STONE


def prop(kind):
    size={'drawer':(66,48),'burner':(50,38),'sign':(106,34),'gate':(18,68)}.get(kind,(38,30))
    im=pygame.Surface(size,pygame.SRCALPHA)
    def rect(c,b): pygame.draw.rect(im,c,b)
    def line(c,a,b,w=1): pygame.draw.line(im,c,a,b,w)
    if kind == 'drawer':
        rect(INK,(4,4,58,40)); rect(WOOD,(6,6,54,35))
        for row in range(3):
            for col in range(3):
                x,y=8+col*17,9+row*10
                rect(INK,(x,y,15,8)); rect(PLANK,(x+1,y+1,13,6))
                rect(LIGHT,(x+5,y+3,5,2))
        rect((205,190,146),(10,33,5,4)); line(INK,(12,33),(14,33)); line(INK,(14,33),(12,36))
        line((128,55,50),(5,38),(58,38),2)
    elif kind == 'burner':
        pygame.draw.ellipse(im,(41,38,35),(2,14,46,22))
        for x,y in ((6,18),(15,13),(26,19),(32,12)):
            rect(INK,(x,y,12,8)); rect((143,129,99),(x+1,y+1,9,5))
            line((49,43,39),(x,y+4),(x+10,y+7),3)
            line((208,142,71),(x+3,y+6),(x+7,y+6))
        line((80,76,68),(3,28),(44,28),3)
    elif kind == 'sign':
        rect(INK,(1,1,104,28)); rect((71,70,59),(3,3,100,24))
        for text,y in (('DEPÓSITO DE REGISTROS',7),('MARGEM SECA',17)):
            font=pygame.font.Font(None,10)
            label=font.render(text,False,(218,200,157)); im.blit(label,label.get_rect(center=(53,y)))
        for x in (5,99): rect(LIGHT,(x,5,2,2))
    elif kind == 'gate':
        rect(INK,(3,0,12,68)); rect(WOOD,(5,1,8,66))
        for y in range(6,65,12): line(PLANK,(5,y),(13,y),2)
        line(STONE,(5,6),(12,59),3); rect(LIGHT,(10,33,2,4))
    else:
        for x,y in ((3,12),(15,4),(20,18)):
            rect(INK,(x,y,14,9)); rect((192,174,130),(x+1,y+1,12,7))
            for yy in (y+3,y+5): line((100,83,62),(x+3,yy),(x+9,yy))
        seal=(131,58,53) if kind in {'order','defense'} else (60,85,123)
        pygame.draw.circle(im,seal,(26,23),3)
        if kind == 'forgetting':
            line((68,65,59),(18,5),(25,10),3)
            line((76,82,76),(27,6),(27,12)); line((76,82,76),(24,9),(30,9))
    return pygame.transform.scale_by(im,2)
