import pygame
import Main
import json
pygame.init()
screen = pygame.display.set_mode((1000,800),pygame.RESIZABLE)
pygame.display.set_caption("My Game")

scene = Main.Scene(None,None,"My Scene")
Main.mainscene = scene
Main.scenes = [scene]

def node_decode(obj: dict,parent = None):
    usenode = Main.nodetypes[obj["node"]]()
    usenode.parent = parent

    for prop in obj:
        if prop not in ["parent","node","children","x","y","xvel","yvel"]:
            setattr(usenode,prop,obj[prop])
        elif prop == "xvel":
            usenode.velocity.x = obj[prop]
        elif prop == "yvel":
            usenode.velocity.y = obj[prop]

    usenode.children = [node_decode(child,usenode) for child in obj.get("children", [])]
    usenode.setpos(obj.get("x", parent.position.x if parent else 0), obj.get("y", parent.position.y if parent else 0))
    usenode.factorpos()

    return usenode

with open("scene.json","r") as file:
    scene_data = json.load(file)
    rootnode = node_decode(scene_data)
    Main.mainscene.rootnode = rootnode

Main.togglerun()

running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill((0,0,0))
    Main.mainscene.update()
    Main.mainscene.draw()

    clock.tick(60)
    pygame.display.update()