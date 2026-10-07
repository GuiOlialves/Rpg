"""Small authored pixel props for the abandoned route; integer world scale."""
import pygame

INK = (45, 44, 40)
WOOD = (117, 84, 55)
LIGHT = (167, 126, 78)
STONE = (113, 112, 101)
PALE = (157, 154, 132)


def prop(kind):
    size = (96, 108) if kind == "watchpost" else (64, 42) if kind == "cart" else (40, 28)
    im = pygame.Surface(size, pygame.SRCALPHA)
    def rect(color, box): pygame.draw.rect(im, color, box)
    def line(color, a, b, width=1): pygame.draw.line(im, color, a, b, width)
    def poly(color, pts): pygame.draw.polygon(im, color, pts)
    if kind == "cart":
        poly(INK, [(8,12),(46,9),(57,22),(50,31),(7,29)])
        poly(WOOD, [(10,13),(44,11),(51,21),(47,28),(10,26)])
        for y in (15,20,25): line(LIGHT, (12,y), (45,y-2))
        line(INK,(18,13),(18,26),2); line(INK,(38,12),(38,27),2)
        for x,y in ((14,30),(45,29)):
            pygame.draw.circle(im,INK,(x,y),8,2)
            pygame.draw.circle(im,LIGHT,(x,y),6,1)
            line(WOOD,(x-5,y-4),(x+5,y+4)); line(WOOD,(x+4,y-5),(x-4,y+5))
        line(LIGHT,(50,22),(62,28),2)
        rect((87,61,44),(25,7,12,8)); rect((169,149,107),(26,5,10,7))
        poly((90,61,48),[(8,12),(16,9),(21,16),(13,18)])
        # A splintered side and lost wheel, not a pristine transport prop.
        rect((0,0,0,0),(32,18,10,8)); line(LIGHT,(28,19),(33,15),2)
    elif kind in {"crate", "broken_crate"}:
        rect(INK,(8,7,25,18)); rect(WOOD,(10,9,21,13))
        for y in (10,14,18): line(LIGHT,(11,y),(29,y))
        line(INK,(11,9),(29,21),2); line(LIGHT,(12,9),(30,21))
        if kind == "broken_crate":
            rect((0,0,0,0),(20,6,13,10)); poly(LIGHT,[(24,19),(36,15),(35,17),(25,21)])
            line(WOOD,(3,24),(16,22),2); rect((185,166,118),(21,24,3,2))
    elif kind == "fence":
        for x in (3,23,35):
            rect(INK,(x,3,4,24)); rect(LIGHT,(x+1,5,2,18))
        line(WOOD,(5,9),(25,11),3); line(LIGHT,(5,9),(25,10))
        line(WOOD,(5,18),(15,22),3); line(LIGHT,(28,17),(37,12),2)
    elif kind == "wheel":
        pygame.draw.circle(im,INK,(20,14),11,2)
        pygame.draw.circle(im,LIGHT,(20,14),8,1)
        for a,b in (((11,11),(29,17)),((18,5),(22,23)),((13,21),(27,7))): line(WOOD,a,b,2)
    elif kind in {"red_cloth", "blue_shield"}:
        if kind == "red_cloth":
            poly(INK,[(7,11),(17,5),(31,11),(25,22),(13,22)])
            poly((135,55,51),[(9,12),(17,7),(29,12),(24,20),(14,20)])
            line((185,87,65),(12,13),(20,16),2)
            poly((210,174,103),[(18,9),(23,14),(20,18),(16,14)])
            line((74,38,35),(8,22),(24,22))
        else:
            poly(INK,[(9,7),(26,8),(30,17),(21,25),(9,19)])
            poly((57,83,113),[(11,9),(25,10),(27,17),(20,22),(11,18)])
            line((177,184,162),(18,10),(19,20),2)
            line((111,130,151),(11,12),(25,13))
            line((74,55,40),(28,5),(34,20)); rect(PALE,(31,3,3,5))
    elif kind == "fire":
        for x,y in ((8,19),(13,22),(23,23),(31,18),(28,12),(16,11)):
            rect(INK,(x,y,5,4)); rect(STONE,(x+1,y,3,2))
        pygame.draw.ellipse(im,(50,47,42),(12,13,19,9))
        line((93,75,52),(14,19),(28,16),2)
        rect((130,88,58),(22,17,2,1))
    elif kind == "bedroll":
        poly(INK,[(5,12),(27,7),(35,16),(12,23)])
        poly((142,128,96),[(7,13),(26,9),(32,16),(12,21)])
        line((191,175,128),(8,13),(27,10),2)
        line((98,94,77),(13,14),(18,20)); line((98,94,77),(25,12),(29,17))
        rect((200,185,151),(29,20,7,3)); rect((130,66,53),(31,21,2,1))
    elif kind == "supplies":
        rect(INK,(4,11,14,12)); rect((161,141,103),(5,13,11,8))
        line((199,181,137),(6,13),(14,12),2)
        rect((166,149,111),(21,19,5,3)); rect((98,73,45),(22,18,3,2))
        rect(PALE,(27,10,7,8)); rect((91,85,73),(29,11,5,2))
    elif kind == "map":
        poly(INK,[(8,6),(28,7),(32,21),(9,23)])
        poly((186,169,126),[(10,8),(26,9),(29,19),(11,21)])
        line((110,90,62),(13,17),(22,11)); line((143,69,50),(22,11),(25,13),2)
        line((134,116,79),(12,10),(16,11)); line((134,116,79),(14,19),(24,18))
    elif kind == "milestone":
        poly(INK,[(14,3),(26,5),(29,26),(10,26)])
        poly(STONE,[(15,5),(24,6),(26,23),(12,23)])
        line(PALE,(15,6),(14,20),2); line((76,76,68),(17,12),(23,12),2)
        line((82,81,70),(18,17),(22,17)); rect((95,104,67),(12,23,15,3))
    elif kind == "wall":
        for row in range(3):
            for col in range(4):
                x = col*9 + (4 if row%2 else 0)
                if row==0 and col==2: continue
                rect(INK,(x,12+row*5,9,5)); rect(STONE,(x+1,12+row*5,7,3))
                line(PALE,(x+1,12+row*5),(x+6,12+row*5))
    elif kind == "watchpost":
        # Weathered stone watchtower, broken battlements and a closed arch.
        poly(INK,[(22,28),(68,28),(78,91),(72,105),(17,105),(14,88)])
        poly(STONE,[(25,30),(66,30),(73,91),(69,101),(21,101),(19,88)])
        rect((130,128,111),(27,32,10,65))
        for y in range(38,100,8):
            line((84,86,81),(21,y),(71,y))
            for x in range(23+(y//8%2)*6,69,13): line((84,86,81),(x,y),(x,y+7))
            line(PALE,(25,y+1),(35,y+1))
        for x in (17,29,42,58,70):
            h = 8 if x==42 else 14
            rect(INK,(x,27-h,10,h+6)); rect(PALE,(x+1,28-h,7,h))
        poly((0,0,0,0),[(20,13),(27,13),(27,19),(24,17),(22,20)])
        rect((0,0,0,0),(71,13,8,4))
        for x,y in ((52,36),(62,50),(26,65),(62,84),(34,91)):
            rect((91,94,79),(x,y,6,3)); line((130,129,105),(x,y),(x+3,y))
        for x,y in ((21,96),(30,101),(61,98),(76,104)):
            rect((90,102,65),(x,y,4,2)); rect((139,139,83),(x+1,y-1,2,1))
        rect((43,46,46),(40,47,12,18)); rect((43,46,46),(44,76,15,26))
        poly((43,46,46),[(43,77),(46,70),(54,70),(59,77)])
        line(WOOD,(48,75),(48,100),2); line(WOOD,(54,74),(54,100),2)
        poly((113,113,92),[(8,103),(18,85),(29,100),(23,107)])
        rect((130,127,109),(69,99,12,7)); rect((150,146,122),(77,95,8,7))
        line((83,88,72),(33,34),(39,62)); line((83,88,72),(39,62),(35,69))
        line((63,64,59),(64,69),(59,74)); line((63,64,59),(64,69),(68,64))
        line(WOOD,(73,9),(73,30),2)
        poly((103,101,80),[(74,10),(89,13),(81,16),(84,20),(74,18)])
    return pygame.transform.scale_by(im, 2)
