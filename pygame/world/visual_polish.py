"""Authored dressing for every campaign map; no gameplay geometry or state changes."""
import random
import pygame
import environment as env
from world import asset_art as art


def apply(region_id, region):
    if region.get('_asset_polish'):
        return region
    region['_asset_polish'] = True
    terrain = region['terrain']
    scenery = region.setdefault('scenery', [])

    def place(name, foot, size, crop=None, color=None, canopy=False):
        im=art.fitted(name,size,crop,color)
        scenery.append(env.anchored(im,foot,canopy))
        env.shadow(terrain,foot,max(12,size[0]//3),7,26)

    def garden(centers, dry=False, desert=False):
        for i,(cx,cy) in enumerate(centers):
            for j,(dx,dy) in enumerate(((-22,0),(14,8),(34,-6))):
                name = ('Cactus1_1','Cactus2_1','Fern2_1')[j] if desert else (
                    ('Autumn_bush2','Broken_tree1','Chanterelles1')[j] if dry else
                    ('Fern1_1','Bush_blue_flowers2','Bush_pink_flowers2')[(i+j)%3])
                place(name,(cx+dx,cy+dy),(38,32) if j!=1 else (46,38))

    def debris(centers, pale=False):
        for i,foot in enumerate(centers):
            place('White_ruins4' if pale else 'Brown_ruins5',foot,(38+i%3*8,26))
            place('Rock4_2_no_shadow',(foot[0]+24,foot[1]+8),(24,20))

    def ivy(x,y):
        place('temple_exterior',(x,y),(32,86),(192,352,16,80))

    def glow(center, radius=72):
        # Light belongs to the floor: it cannot wash out actors or the HUD.
        layer=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA)
        for r in range(radius,2,-4):
            pygame.draw.circle(layer,(225,176,95,round(16*(1-r/radius))),(radius,radius),r)
        terrain.blit(layer,(center[0]-radius,center[1]-radius))

    if region_id=='home':
        for foot in ((340,180),(715,474)):
            place('assets/prologue/interior.png',foot,(34,58),(80,200,32,40))
        for center in ((370,160),(620,160)):glow(center,85)
    elif region_id=='village':
        garden([(422,463),(618,459),(754,486),(1218,474),(462,846),(1098,976),(1532,861)])
    elif region_id=='forest':
        garden([(510,430),(780,660),(1030,860),(1580,805),(1360,466),(1720,471),(1845,160)])
        for i,foot in enumerate(((460,690),(590,350),(1050,785),(1790,870))):
            place('Chanterelles1' if i%2 else 'White-red_mushroom3',foot,(34,38))
    elif region_id=='desert':
        garden([(340,740),(1100,884),(1770,430),(1780,820)],desert=True)
        for foot in ((770,493),(1130,518),(1190,442)):
            place('Fern2_1',foot,(46,40))
        debris([(1500,792),(1640,807),(480,990)])
    elif region_id=='old_road':
        garden([(1815,970),(1660,698),(1435,895),(800,875),(1090,840),(1055,213),(1320,196)],dry=True)
        debris([(1380,605),(1500,688),(733,747),(905,263),(1240,1000)])
        for foot in ((300,220),(395,650),(1780,190)):
            place('Brown_ruins1',foot,(164,178))
        ivy(813,199)
    elif region_id=='watchpost':
        garden([(300,850),(1325,870),(1360,485),(280,330)],dry=True)
        debris([(448,347),(716,680),(1115,465),(1130,767)])
        for x,y in ((465,376),(729,396),(796,212),(1100,223)):
            ivy(x,y)
        for point in ((483,425),(1058,274),(1058,590)):glow(point)
    elif region_id=='pursuit':
        garden([(225,316),(540,262),(740,596),(1110,275)],dry=True)
        debris([(410,68),(670,716),(1170,675)])
    elif region_id=='namar':
        garden([(208,422),(515,460),(1165,424),(1210,668)],dry=True)
        debris([(290,435),(512,440),(566,294),(1115,394),(460,679),(1224,578)],pale=True)
        # Roof remains sit over the closed rear walls; interiors and clues stay exposed.
        for name,foot,size in [('Brown_ruins2',(370,276),(240,82)),
                               ('White_ruins3',(1090,194),(116,96)),
                               ('Brown_ruins2',(366,489),(210,70))]:
            place(name,foot,size,canopy=True)
        for x,y in ((247,516),(575,217),(1154,238)):ivy(x,y)
    elif region_id=='archive':
        debris([(530,702),(611,821),(1126,860)],pale=True)
        for x,y in ((105,351),(516,377),(667,167),(1195,465)):ivy(x,y)
        for point in ((162,400),(1060,246),(171,591)):glow(point,84)
    elif region_id=='forgotten_route':
        garden([(200,709),(390,585),(750,458),(1170,582),(1375,935),(1830,945)])
        debris([(917,1022),(1099,1048),(655,246),(1720,166)],pale=True)
        # Abutment caps fit the already solid rail strips, never the traversable deck.
        for x in (940,1094):
            for y in (720,832):
                place('temple_exterior',(x,y),(24,40),(264,224,24,32))
    elif region_id=='encosta':
        garden([(330,411),(523,416),(725,331),(848,335),(1325,947),(1808,716),(961,341)])
        debris([(411,456),(1486,947),(1070,590)])
        art.floor(terrain,(940,350,328,222),wooden=True)
        for x,y in ((944,421),(1280,420)):ivy(x,y)
        glow((1050,494),85)
    elif region_id=='threshold':
        garden([(640,640),(720,1050),(1780,960)])
        debris([(978,415),(1635,410),(1300,730),(1210,1015)],pale=True)
        for foot in ((1165,566),(1730,566)):
            place('temple_exterior',foot,(62,136),(8,352,48,112))
        glow((1435,570),110)
    else:
        # Five dungeon sectors share stonework, with distinct regional accents.
        from story.lacre_content import REGIONS
        if region_id in REGIONS:
            index=REGIONS.index(region_id)
            left=420 if index==1 else 500; right=1628 if index==1 else 1548
            for x in (left+40,right-40):
                place('temple_exterior',(x,330),(68,132),(8,352,48,112),(159,191,192))
                glow((x,352),95)
            debris([(left+70,908),(right-70,918)],pale=True)
            for x,y in ((left+18,554),(right-18,759)):ivy(x,y)
            if index in (0,1,3):
                # A faded processional carpet uses the real interior atlas.
                rug=art.sprite('assets/prologue/interior.png',(128,256,32,48))
                rug=pygame.transform.scale(rug,(116,320));rug.set_alpha(85)
                terrain.blit(rug,(966,490))
            if index==4:
                for x in (884,1164):glow((x,465),125)
    return region
