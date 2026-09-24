"""Composição visual pré-renderizada; nenhuma regra de movimento ou combate."""
from dataclasses import dataclass, field
from functools import lru_cache
import math
import random
import pygame


def resize(image, scale):
    return pygame.transform.scale(image, (round(image.width * scale), round(image.height * scale)))


def crop(sheet, rect, scale=1):
    return resize(sheet.subsurface(rect).copy(), scale)


def tint(image, color):
    result = image.copy()
    result.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return result


def tiled(size, tiles, seed=0):
    rng = random.Random(seed)
    result = pygame.Surface(size)
    width, height = tiles[0].get_size()
    for y in range(0, size[1], height):
        for x in range(0, size[0], width):
            result.blit(rng.choice(tiles), (x, y))
    return result


def ground(size, tile, seed, palette, detail_tiles=()):
    """Asset base + variação contínua em blocos de 2 px, sem faixas de tiles."""
    result = tiled(size, [tile], seed)
    rng = random.Random(seed)
    modulation = pygame.Surface((size[0] // 4, size[1] // 4))
    for y in range(modulation.height):
        for x in range(modulation.width):
            value = math.sin(x * .031 + seed) * .25 + math.sin(y * .045 - x * .011) * .20
            value += math.sin(x * .095 + y * .081) * .08 + rng.uniform(-.12, .12)
            t = max(0, min(1, .5 + value))
            modulation.set_at((x, y), tuple(round(a + (b-a)*t) for a, b in zip(*palette)))
    modulation = pygame.transform.scale(modulation, size)
    modulation.set_alpha(165)
    result.blit(modulation, (0, 0))
    for _ in range(size[0] * size[1] // 480):
        x, y = rng.randrange(size[0]), rng.randrange(size[1])
        density=(math.sin(x*.019+seed)+math.sin(y*.026-x*.007)+2)/4
        if detail_tiles and rng.random() < .24*density*density:
            result.blit(rng.choice(detail_tiles), (x, y))
        else:
            color = result.get_at((x, y))
            delta = rng.choice((-7, 6, 10))
            pygame.draw.line(result, tuple(max(0, min(255, c+delta)) for c in color[:3]), (x, y), (x+rng.randrange(2, 5), y), 1)
    return result


def curve(points, spacing=7):
    """Catmull-Rom conserva os pontos de passagem e arredonda as mudanças de direção."""
    padded = [points[0], *points, points[-1]]
    for index in range(1, len(padded)-2):
        a,b,c,d = padded[index-1:index+3]
        steps = max(2, round(math.dist(b,c)/spacing))
        for step in range(steps):
            t = step/steps
            yield tuple(.5*((2*b[k])+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in (0,1))
    yield points[-1]


def paths(terrain, routes, texture, seed, clearings=(), edge_tiles=()):
    """Máscara orgânica com textura real e borda picotada; retorna a área pintada."""
    rng = random.Random(seed)
    small = pygame.Surface((terrain.width//2, terrain.height//2), pygame.SRCALPHA)
    for route, width in routes:
        for i, (x,y) in enumerate(curve(route)):
            radius = width/4 + math.sin(i*.42+seed)*2 + math.sin(i*.13)*3
            pygame.draw.circle(small, 'white', (round(x/2), round(y/2)), max(3, round(radius)))
    for (x,y),(w,h) in clearings:
        points=[]
        for i in range(32):
            angle=i*math.tau/32
            radius=1+.12*math.sin(angle*3+seed)+.07*math.sin(angle*7)
            points.append((round((x+math.cos(angle)*w*.5*radius)/2),round((y+math.sin(angle)*h*.5*radius)/2)))
        pygame.draw.polygon(small,'white',points)
    mask = pygame.mask.from_surface(small)
    outline = mask.outline(5)
    # Dentes de poucos pixels quebram a silhueta sem criar um contorno escuro.
    for x,y in outline:
        if rng.random()<.7:
            pygame.draw.circle(small, (255,255,255,0), (x,y), rng.randrange(1,4))
    full = pygame.transform.scale(small, terrain.get_size())
    texture = tiled(terrain.get_size(), [texture,pygame.transform.flip(texture,True,False),pygame.transform.flip(texture,False,True)], seed)
    layer = texture.convert_alpha()
    layer.blit(full,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    terrain.blit(layer,(0,0))
    if edge_tiles:
        for x,y in outline[::4]:
            if rng.random()<.65:
                tile=rng.choice(edge_tiles)
                terrain.blit(tile,(x*2-tile.width//2,y*2-tile.height//2))
    return pygame.mask.from_surface(full)


def patch(terrain, center, size, color, seed=0):
    """Mancha translúcida irregular para ligar a base de um objeto ao chão."""
    rng=random.Random(seed)
    w,h=size
    layer=pygame.Surface((w,h),pygame.SRCALPHA)
    for _ in range(22):
        x,y=rng.randrange(w//5,w*4//5),rng.randrange(h//5,h*4//5)
        pygame.draw.ellipse(layer,color,(x-w//5,y-h//5,w//2,h//2))
    terrain.blit(layer,(center[0]-w//2,center[1]-h//2))


def worn_texture(tile, color, strength=55, seed=0):
    """Conserva o desenho do asset, reduzindo o contraste de padrões repetidos."""
    base=pygame.Surface((128,128));base.fill(color)
    detail=tiled(base.get_size(),[tile,pygame.transform.flip(tile,True,False)],seed)
    detail.set_alpha(strength);base.blit(detail,(0,0))
    rng=random.Random(seed)
    for _ in range(380):
        x,y=rng.randrange(128),rng.randrange(128)
        value=rng.choice((-8,-5,6,10));c=base.get_at((x,y))
        pygame.draw.line(base,tuple(max(0,min(255,v+value)) for v in c[:3]),(x,y),(x+rng.randrange(1,4),y))
    return base


@lru_cache(maxsize=80)
def shadow_image(width, height, alpha=45):
    image=pygame.Surface((width+8,height+6),pygame.SRCALPHA)
    pygame.draw.ellipse(image,(18,29,26,alpha//3),(0,0,width+8,height+6))
    pygame.draw.ellipse(image,(18,29,26,alpha),(4,3,width,height))
    return image


def shadow(canvas, foot, width=34, height=10, alpha=45):
    im=shadow_image(width,height,alpha)
    canvas.blit(im,(round(foot[0]-im.width/2),round(foot[1]-im.height/2)))


@dataclass
class Scenery:
    image: pygame.Surface
    pos: tuple
    depth: float
    canopy: bool=False
    sway: float=0
    phase: float=0
    faded: pygame.Surface=field(init=False,repr=False)

    def __post_init__(self):
        self.faded=self.image.copy()
        self.faded.set_alpha(85)

    def draw(self, canvas, camera, player=None, ticks=None):
        rect=self.image.get_rect(topleft=(round(self.pos[0]-camera[0]),round(self.pos[1]-camera[1])))
        if not rect.colliderect(canvas.get_rect().inflate(4,4)):
            return
        ticks=pygame.time.get_ticks() if ticks is None else ticks
        image=self.image
        if self.canopy and player and player.y < self.depth:
            body=pygame.Rect(round(player.x-camera[0]-16),round(player.y-camera[1]-42),32,43)
            if rect.colliderect(body): image=self.faded
        # Oscilação de apenas 1 px, com base/tronco ancorados no mesmo lugar.
        split=max(1,image.height*2//3)
        offset=round(math.sin(ticks*.0013+self.phase)*self.sway)
        if self.sway:
            canvas.blit(image,(rect.x+offset,rect.y),(0,0,image.width,split))
            canvas.blit(image,(rect.x,rect.y+split),(0,split,image.width,image.height-split))
        else:
            canvas.blit(image,rect)


def anchored(image, foot, canopy=False, sway=0, phase=0):
    return Scenery(image,(round(foot[0]-image.width/2),round(foot[1]-image.height+4)),foot[1],canopy,sway,phase)


def free_woods(load):
    """Sprites gratuitos individuais; nenhum preview de licença premium é carregado."""
    return {name:load(f'assets/forest/free_{name}.png')
            for name in ('tree','bush','sapling','stump','rock','sign')}


def lake(terrain, solid_rect, seed, margin=(112,96)):
    """Água cobre toda a colisão existente, com margem irregular por fora dela."""
    rng=random.Random(seed)
    outer=solid_rect.inflate(*margin)
    im=pygame.Surface(outer.size,pygame.SRCALPHA)
    w,h=im.get_size();points=[]
    for x in range(40,w-39,14):points.append((x,round(20+9*math.sin(x*.047)+6*math.sin(x*.091))))
    for y in range(38,h-37,14):points.append((round(w-20+12*math.sin(y*.041)),y))
    for x in reversed(range(40,w-39,14)):points.append((x,round(h-20+10*math.sin(x*.051))))
    for y in reversed(range(38,h-37,14)):points.append((round(20+10*math.sin(y*.061)),y))
    pygame.draw.polygon(im,(76,102,65),points)
    for inset,color in [(6,(135,140,85)),(11,(172,164,112)),(15,(73,139,132)),(19,(55,146,150)),(25,(44,111,131))]:
        inner=[(round(w/2+(x-w/2)*(w-inset*2)/w),round(h/2+(y-h/2)*(h-inset*2)/h)) for x,y in points]
        pygame.draw.polygon(im,color,inner)
    local=solid_rect.move(-outer.x,-outer.y)
    pygame.draw.rect(im,(44,111,131),local)
    for _ in range(220):
        x,y=rng.randrange(local.left,local.right),rng.randrange(local.top,local.bottom)
        pygame.draw.line(im,rng.choice([(47,121,137),(48,127,141),(52,133,145)]),(x,y),(x+rng.randrange(3,14),y),2)
    terrain.blit(im,outer.topleft)
    return {'rect':solid_rect.copy(), 'color':(143,219,201), 'seed':seed}
