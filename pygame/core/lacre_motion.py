"""Shared authored pose geometry; blade lengths stay constant across swing frames."""
import math
COUNTS={'idle':4,'walk':8,'windup':4,'cut':8,'sweep':8,'charge':8,'hurt':3,'death':6,'transition':6}
def pose(action,i,facing):
    stride=(0,1,2,1,0,-1,-2,-1)[i%8] if action=='walk' else 0
    lean=(0,-1,-2,0,2,3,1,0)[i%8] if action in ('cut','sweep','charge') else (-i//2 if action=='windup' else 0)
    if action=='transition':lean=(0,-1,-1,0,1,0)[i%6]
    cx=40+(-lean if facing==1 else lean);foot=46-abs(stride)//2
    base=(math.pi/2,math.pi,0,-math.pi/2)[facing]
    angle=base
    if action in ('cut','sweep'):
        angles=(-1.3,-1.2,-.85,-.1,.6,1.05,1.2,1.25)
        angle+=angles[i%8]*(1 if action=='sweep' else .65)
    elif action=='windup':angle-=1.15
    elif action=='transition':angle+=(-.15,-.45,-.8,-1.2,-1.05,-.9)[i%6]
    grip=(cx+math.cos(angle)*10,foot-14+math.sin(angle)*5)
    tip=(grip[0]+math.cos(angle)*23,grip[1]+math.sin(angle)*23)
    return (cx,foot,stride,lean),grip,tip
