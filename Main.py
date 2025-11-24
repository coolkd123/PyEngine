import pygame
import pygame_gui as gui
import copy
from EngineGui import GuiElements
import pyperclip

pygame.init()
pygame.font.init()

winwidth = 800
winheight = 600
screen = pygame.display.set_mode((winwidth,winheight))
pygame.display.set_caption("PyEngine")
mainscene = None
gamerunning = False
scenes = []
nodemoving = False
cnode = None
colorpicker = None
selected = []
textfocused = False

class Scene():
    def __init__(self,rootnode,maincamera):
        self.rootnode = rootnode
        self.maincamera = maincamera
        self.save = copy.deepcopy(self.rootnode)
        scenes.append(self)

    def update(self,running = True):
        self.rootnode.update()
        if not running:
            self.save = copy.deepcopy(self.rootnode)

    def draw(self):
        self.rootnode.draw()

    def addnode(self,node,running = True):
        self.rootnode.addchild(node)
        if not running:
            self.save = copy.deepcopy(self.rootnode)

    def reset(self):
        self.rootnode = copy.deepcopy(self.save)

class Node:
    def __init__(self, parent = None, x = 0, y = 0):
        self.parent = parent
        self.name = self.__class__.__name__
        self.children = []
        self.wx = x
        self.wy = y
        self.sx = self.wx - self.parent.wx if self.parent else x
        self.sy = self.wy - self.parent.wy if self.parent else y
        self.rx = self.wx + mainscene.maincamera.ox if mainscene.maincamera else self.wx
        self.ry = self.wy + mainscene.maincamera.oy if mainscene.maincamera else self.wy
        self.expanded = True
        self.selected = False
        self.properties = {"wx": int,"wy": int,"name": str}

        if self.parent:
            self.parent.addchild(self)
    
    def get_child(self,name):
        for child in self.children:
            if child.name == name:
                return child
    
    def get_parent(self):
        return self.parent

    def get_children(self):
        return self.children

    def update(self):
        if self.parent:
            self.wx = self.parent.wx + self.sx
            self.wy = self.parent.wy + self.sy
        else:
            self.wx = self.sx
            self.wy = self.sy

        if isinstance(self,CameraNode):
            self.ox = -self.wx + winwidth / 2
            self.oy = -self.wy + winwidth / 2

        elif isinstance(self,MovementNode):
            if gamerunning:
                self.translate(self.xvel,self.yvel)
        
        elif isinstance(self,SpriteNode):
            if self.image and ((self.width,self.height) != self.image.get_size()):
                self.image = pygame.transform.scale(self.image, (self.width,self.height))
        
        self.rx = self.wx + mainscene.maincamera.ox if mainscene.maincamera else self.wx
        self.ry = self.wy + mainscene.maincamera.oy if mainscene.maincamera else self.wy

        for child in self.children:
            child.update()

    def draw(self):
        pygame.draw.circle(screen, (64,214,237) if self.selected else (255,255,255), (self.rx,self.ry),5)

        for child in self.children:
            child.draw()

    def addchild(self, child):
        self.children.append(child)
        child.parent = self
        child.sx = child.wx - self.wx
        child.sy = child.wy - self.wy
        mainscene.update(gamerunning)

    def translate(self, x, y):
        self.sx += x
        self.sy += y
        self.wx = self.parent.wx + self.sx
        self.wy = self.parent.wy + self.sy

    def setpos(self, x, y):
        self.wx = x
        self.wy = y
        self.sx = self.wx - self.parent.wx
        self.sy = self.wy - self.parent.wy

    def getroot(self):
        if self.parent == None:
            return self
        else:
            return self.parent.getroot()
    
    def delete(self):
        for child in self.children[:]:
            child.delete()
        self.children.clear()

        if self.parent:
            if self in self.parent.children:
                self.parent.children.remove(self)
            self.parent = None

def get_main_scene():
    return mainscene

def get_root_node():
    return mainscene.rootnode

class SpriteNode(Node):
    def __init__(self, parent = None, x = 0, y = 0, width = 100, height = 100, imgpath = "texture.png"):
        super().__init__(parent, x, y)
        self.width = width
        self.height = height
        self.image = None
        if imgpath:
            self.image = pygame.image.load(imgpath).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width,self.height))
        self.properties.update({"width": int,"height": int})

    def draw(self):
        if self.image:
            temp = self.image.copy()
            if self.selected:
                self.image.fill((64,214,237,150), None, pygame.BLEND_RGBA_MULT)
            screen.blit(self.image, (self.rx,self.ry))

            self.image = temp.copy()

        super().draw()

class CameraNode(Node):
    def __init__(self,parent = None,x = 0, y = 0):
        super().__init__(parent,x,y)
        self.ox = -self.wx + winwidth / 2
        self.oy = -self.wy + winheight / 2

class MovementNode(Node):
    def __init__(self, parent = None, x = 0, y = 0, xvel = 1, yvel = 0):
        super().__init__(parent, x, y)
        self.xvel = xvel
        self.yvel = yvel
        self.properties.update({"xvel": int,"yvel": int})

class BackgroundNode(Node):
    def __init__(self, parent = None, color = (255,0,0), x = 0, y = 0):
        super().__init__(parent,0,0)
        self.color = color
        self.properties.update({"color": str})
    
    def draw(self):
        if self.parent:
            if isinstance(self.parent,SpriteNode):
                ps = pygame.Surface((self.parent.width,self.parent.height))
                ps.fill(self.color)

                screen.blit(ps,(self.parent.rx,self.parent.ry))
            else:
                ps = pygame.Surface((800,600))
                ps.fill(self.color)
                screen.blit(ps,(0,0))
        
        super().draw()

class RectangleNode(Node):
    def __init__(self, parent = None, x = 0, y = 0, width = 100, height = 100, color = (255,0,0)):
        super().__init__(parent,x,y)
        self.width = width
        self.height = height
        self.color = color
        self.properties.update({"width": int,"height": int,"color": str})
    
    def draw(self):
        pygame.draw.rect(screen,self.color,pygame.Rect(self.rx,self.ry,self.width,self.height))
        super().draw()

class TextNode(Node):
    def __init__(self,parent = None, text = "Hello World", x = 0, y = 0, color = (255,255,255), size = 30):
        super().__init__(parent,x,y)
        self.text = text
        self.color = color
        self.size = size
        self.properties.update({"text": str,"color": str,"size": int})
    
    def draw(self):
        drawtext(self.text,self.rx,self.ry,self.size,self.color,screen)
        super().draw()

def keypressed(key):
    keys = pygame.key.get_pressed()
    keycode = getattr(pygame,f"K_{key}",None)
    return keys[keycode] if keycode else False

def searchstring(string,instring):
    for char in string:
        if char not in instring:
            return False
    return True

def togglerun():
    global gamerunning
    if gamerunning:
        for sc in scenes:
            sc.reset()
    gamerunning = not gamerunning
    return gamerunning

def deletenode():
    global selected

    for sn in selected:
        sn.delete()
    selected = []

def changeadd(node):
    global cnode
    cnode = nodetypes[node]

def addnode():
    newnode = cnode(parent = None,x = 0,y = 0)
    if selected:
        selected[0].addchild(newnode)
    else:
        mainscene.addnode(newnode,gamerunning)

def exitengine():
    global running
    running = False

def getselected():
    return selected[0]

def changeprop(value: str,convert: str):
    global selected

    sn = selected[0]
    newvalue = value
    if searchstring(newvalue,"1234567890-."):
        newvalue = int(newvalue)
    
    if type(newvalue) != sn.properties[convert]:
        errormessage(f"data type given ({type(newvalue).__name__}) does not match needed type ({sn.properties[convert].__name__})")
    else:
        if convert == "wx" or convert == "wy":
            if convert == "wx":
                sn.setpos(int(newvalue),sn.wy)
            elif convert == "wy":
                sn.setpos(sn.wx,int(newvalue))
        else:
            setattr(sn,convert,newvalue)

funcs = {
    "togglerun": togglerun,
    "deletenode": deletenode,
    "changeadd": changeadd,
    "addnode": addnode,
    "exitengine": exitengine,
    "changeprop": changeprop,
    "getselected": getselected
}
nodetypes = {
    "node": Node,
    "sprite": SpriteNode,
    "camera": CameraNode,
    "movement": MovementNode,
    "background": BackgroundNode,
    "rectangle": RectangleNode,
    "text": TextNode
}

manager = gui.UIManager((winwidth,winheight))
guielements = GuiElements(manager,funcs,nodetypes)

def drawtext(text,x,y,size,color,surface):
    font = pygame.font.SysFont("Arial",size)
    textsurface = font.render(text,True,color)
    surface.blit(textsurface,(x,y))
    rect = textsurface.get_rect()
    return pygame.Rect(x,y,rect.width,rect.height)

def drawnodetree(node: Node,x,y,clickrects):
    global guielements
    nodetreerect = guielements.nodetreewindow.get_relative_rect()
    nodetreesurface = pygame.Surface((nodetreerect.width,nodetreerect.height - 15),pygame.SRCALPHA)
    nodetreesurface.fill((0,0,0,0))

    nodename = node.name
    tcolor = (64,214,237) if node.selected else (255,255,255)
    textrect = drawtext(nodename,x,y,15,tcolor,nodetreesurface)
    currenty = textrect.y + 15

    if nodetreerect.y + nodetreesurface.get_rect().bottom - 15 > textrect.y:
        clickrects[(textrect.x,textrect.y,textrect.width,textrect.height)] = node

    if node.children:
        intext = "-" if node.expanded else "+"
        drawtext(intext, x - 5, y, 15, (255,255,255),nodetreesurface)

    if node.expanded and node.children:
        pygame.draw.line(nodetreesurface,"#ffffff",(x,currenty + 3),(x,currenty + 15))
        currenty += 15
        for i in range(len(node.children)):
            child = node.children[i]
            pygame.draw.line(nodetreesurface,"#ffffff",(x,currenty),(x + 15,currenty))
            oy = currenty
            currenty = drawnodetree(child,x + 20,currenty - 7,clickrects)

            if i != len(node.children) - 1:
                pygame.draw.line(nodetreesurface,"#ffffff",(x,oy),(x,currenty))
    
    screen.blit(nodetreesurface,(nodetreerect.x,nodetreerect.y))
    return currenty + 15

def setproperties(node: Node):
    objprop = list(node.properties.keys())[:]

    for el in guielements.propertylist:
        el.kill()
    guielements.propertylist = []
    for i in range(len(objprop)):
        objprop[i] = getattr(node,objprop[i])
        ce = gui.elements.UITextEntryLine(pygame.Rect(0,i * 40 + 5,100,40), guielements.manager, guielements.propertieswindow, initial_text = str(objprop[i]))
        guielements.propertylist.append(ce)
    guielements.propertieswindow.set_display_title(f"Properties - {node.name}")

def setmainprop():
    global guielements

    if len(selected) == 1 and guielements.propertieswindow.visible:
        setproperties(selected[0])
    else:
        for el in guielements.propertylist:
            el.kill()
        guielements.propertylist = []
        guielements.propertieswindow.set_display_title("Properties")

def setfocused():
    global textfocused
    textfocused = False

    for tl in guielements.propertylist:
        if tl.is_focused:
            textfocused = True

def selectnodes(node: Node):
    mx,my = pygame.mouse.get_pos()
    mousepos = pygame.math.Vector2(mx,my)
    nodepos = pygame.math.Vector2(node.rx,node.ry)
    
    if nodepos.distance_to(mousepos) <= 5:
        node.selected = not node.selected
        if node.selected:
            selected.append(node)
            setmainprop()
        elif node in selected:
            selected.remove(node)
            setmainprop()
    
    if node.children:
        for child in node.children:
            selectnodes(child)

def errormessage(message):
    gui.windows.UIMessageWindow(pygame.Rect(200,200,250,160), message, guielements.manager)

mainscene = Scene(None,None)
mainscene.rootnode = Node(None,0,0)

clock = pygame.time.Clock()
running = True
while running:
    delta = clock.tick(60) / 1000.0
    clickrects = {}

    nodetreerect = guielements.nodetreewindow.get_relative_rect()
    drawnodetree(mainscene.rootnode, nodetreerect.x + 30, nodetreerect.y + 50,clickrects)
    setfocused()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        guielements.eventhandle(event)
        manager.process_events(event)

        if event.type == gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element in guielements.propertylist:
                changeprop(event.text, list(selected[0].properties.keys())[guielements.propertylist.index(event.ui_element)])
                setfocused()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                for rect,node in clickrects.items():
                    temprect = pygame.Rect(rect)
                    if temprect.collidepoint(event.pos):
                        if node.children:
                            node.expanded = not node.expanded
                        break

            elif event.button == 1:
                selectnodes(mainscene.rootnode)

                for rect,node in clickrects.items():
                    temprect = pygame.Rect(rect)
                    if temprect.collidepoint(event.pos):
                        node.selected = not node.selected
                        if node.selected:
                            selected.append(node)
                            setmainprop()
                            setfocused()
                        elif node in selected:
                            selected.remove(node)
                            setmainprop()
                            setfocused()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m and len(selected) > 0 and not textfocused:
                nodemoving = not nodemoving
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_c and len(selected) > 0 and not textfocused:
                snode = selected[0]
                snode.parent.addchild(copy.deepcopy(snode))

            elif event.key == pygame.K_p and len(selected) > 1 and not textfocused:
                for i in range(len(selected) - 1):
                    if selected[i].parent != selected[-1]:
                        selected[i].parent.children.remove(selected[i])
                        selected[i].parent = selected[-1]
                        selected[-1].addchild(selected[i])
            
            if event.key == pygame.K_f and not textfocused:
                guielements.colorpicker = gui.windows.UIColourPickerDialog(pygame.Rect(300,200,390,390), guielements.manager, initial_colour = pygame.Color(255,0,0))

    if nodemoving:
        mx,my = pygame.mouse.get_pos()
        for sn in selected:
            sn.setpos(mx,my)
        setmainprop()
        setfocused()

    mainscene.update(gamerunning)
    manager.update(delta)
    screen.fill((50,50,50))
    mainscene.draw()
    manager.draw_ui(screen)

    if guielements.nodetreewindow.visible:
        drawnodetree(mainscene.rootnode, 30, 50,clickrects)

    pygame.display.update()

pygame.quit()