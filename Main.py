import pygame
import pygame_gui as gui
import copy
from EngineGui import GuiElements
import pyperclip
import importlib
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import os
import random
import jsonpickle
import sys

pygame.init()
pygame.font.init()

root = tk.Tk()
root.withdraw()
winwidth,winheight = root.winfo_screenwidth(), root.winfo_screenheight()

screen = pygame.display.set_mode((1000,800), pygame.RESIZABLE)
pygame.display.set_caption("PyEngine")
mainscene = None
gamerunning = False
scenes = []
scenenames = []
nmode = "None"
cnode = None
colorpicker = None
selected = []
textfocused = False
scripts = {}
imagenames = {"texture.png": pygame.image.load("texture.png").convert_alpha()}
delta = 0

def getsign(number):
    return number / abs(number) if number != 0 else 0

def askfile():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title = "Select File")
    return path

def askinput(title,message):
    root = tk.Tk()
    root.withdraw()
    userinput = simpledialog.askstring(title = title, prompt = message)
    return userinput

class Scene():
    def __init__(self,rootnode,maincamera,name):
        self.rootnode = rootnode
        self.maincamera = maincamera
        self.name = name
        self.save = copy.deepcopy(self.rootnode)
        scenes.append(self)
        scenenames.append(self.name)

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
        self.sx = (self.wx - self.parent.wx) if self.parent else x
        self.sy = (self.wy - self.parent.wy) if self.parent else y
        self.rx = (self.wx + mainscene.maincamera.ox) if mainscene.maincamera else self.wx
        self.ry = (self.wy + mainscene.maincamera.oy) if mainscene.maincamera else self.wy
        self.expanded = True
        self.scriptname = None
        self.properties = {"wx": int,"wy": int,"name": str,"scriptname": str,"does_collide": bool}
        self.started = False
        self.colliding = False
        self.does_collide = False

        if self.parent:
            self.parent.addchild(self)
    
    def __repr__(self):
        return self.__class__.__name__
    
    def get_child(self,name):
        for child in self.children:
            if child.name == name:
                return child
    
    def get_parent(self):
        return self.parent

    def get_children(self):
        return self.children

    def update(self):
        mainscene.rootnode.factorpos()

        if gamerunning:
            if self.scriptname and self.scriptname in scripts:
                scriptobj = scripts[self.scriptname]
                if not self.started:
                    if hasattr(scriptobj,"start"):
                        try:
                            scriptobj.start(self)
                            self.started = True
                        except Exception as e:
                            errormessage(f"Error in {self.scriptname}: {e}")
                            self.started = False

                if hasattr(scriptobj,"forever"):
                    try:
                        scriptobj.forever(self)
                    except Exception as e:
                        errormessage(f"Error in {self.scriptname}: {e}")
        else:
            self.started = False

        mainscene.rootnode.factorpos()

        if isinstance(self,MovementNode):
            if gamerunning:
                self.translate(self.xvel,self.yvel)
        
        mainscene.rootnode.factorpos()
        
        if isinstance(self,TimerNode):
            if gamerunning:
                self.fulltime += delta * 1000
                if self.fulltime > self.interval:
                    self.fulltime -= self.interval
                    self.activated = True
                else:
                    self.activated = False
            else:
                self.activated = False
                self.fulltime = 0
        
        mainscene.rootnode.factorpos()
        
        if isinstance(self,CollisionRectNode):
            self.worldrect = pygame.Rect(self.wx,self.wy,self.width,self.height)
        
        if self.does_collide and gamerunning:
            self.collide()
        
        mainscene.rootnode.factorpos()

        if isinstance(self,CollisionRectNode):
            self.renderrect = pygame.Rect(self.rx,self.ry,self.width,self.height)

        for child in self.children:
            child.update()

    def draw(self):
        if not gamerunning:
            pygame.draw.circle(screen, (64,214,237) if (self in selected) else (255,255,255), (self.rx,self.ry),5)

        for child in self.children:
            child.draw()

    def addchild(self,child):
        self.children.append(child)
        child.parent = self
        child.sx = child.wx - self.wx
        child.sy = child.wy - self.wy
        mainscene.update(gamerunning)
    
    def factorpos(self,mode = 0):
        if mode == 0:
            if self.parent:
                self.wx = self.parent.wx + self.sx
                self.wy = self.parent.wy + self.sy
            else:
                self.wx = self.sx
                self.wy = self.sy
        elif mode == 1:
            if self.parent:
                self.sx = self.wx - self.parent.wx
                self.sy = self.wy - self.parent.wy
            else:
                self.sx = self.wx
                self.sx = self.wx

        self.rx = self.wx + mainscene.maincamera.ox if mainscene.maincamera else self.wx
        self.ry = self.wy + mainscene.maincamera.oy if mainscene.maincamera else self.wy

        if isinstance(self,CollisionRectNode):
            self.worldrect = pygame.Rect(self.wx,self.wy,self.width,self.height)
            self.renderrect = pygame.Rect(self.rx,self.ry,self.width,self.height)
        
        if isinstance(self,CameraNode):
            self.ox = -self.wx + winwidth / 2
            self.oy = -self.wy + winheight / 2

        for child in self.children:
            child.factorpos()

    def translate(self, x, y):
        self.sx += x
        self.sy += y
        self.factorpos()

    def setpos(self, x, y):
        self.wx = x
        self.wy = y
        self.factorpos(1)
    
    def collide(self):
        self.colliding = False

        if self.children:
            for child in self.children:
                if isinstance(child,CollisionRectNode):
                    allrects = []
                    getallrects(mainscene.rootnode,allrects)
                    noderects = nodetorect(allrects)
                    childrect = child.worldrect
                    child.collide_dirs = []

                    collisionindexes = childrect.collidelistall(noderects)
                    for cindex in collisionindexes:
                        if allrects[cindex] is not child and allrects[cindex].enabled:
                            colliderect = noderects[cindex]
                            overlapx = min(childrect.right,colliderect.right) - max(childrect.left,colliderect.left)
                            overlapy = min(childrect.bottom,colliderect.bottom) - max(childrect.top,colliderect.top)

                            if overlapx < overlapy:
                                if childrect.x < colliderect.x:
                                    self.translate(-overlapx, 0)
                                    child.collide_dirs.append("right")
                                else:
                                    self.translate(overlapx, 0)
                                    child.collide_dirs.append("left")
                            else:
                                if childrect.y < colliderect.y:
                                    self.translate(0, -overlapy)
                                    child.collide_dirs.append("down")
                                else:
                                    self.translate(0, overlapy)
                                    child.collide_dirs.append("up")

                    child.colliding = len(child.collide_dirs) > 0
                    if child.colliding:
                        self.colliding = True
                try:
                    child.collide()
                except Exception:
                    pass
        self.factorpos()

    def delete(self):
        for child in self.children[:]:
            child.delete()
        self.children.clear()

        if self.parent:
            if self in self.parent.children:
                self.parent.children.remove(self)
            self.parent = None

class SpriteNode(Node):
    def __init__(self, parent = None, x = 0, y = 0, width = 100, height = 100, imagepath = "texture.png"):
        super().__init__(parent, x, y)
        self.width = width
        self.height = height
        self.imagepath = imagepath

        self.properties.update({"width": int,"height": int,"imagepath": str})

    def draw(self):
        if self.imagepath:
            screen.blit(pygame.transform.smoothscale(imagenames[self.imagepath], (self.width,self.height)), (self.rx,self.ry))

        super().draw()

class CameraNode(Node):
    def __init__(self,parent = None,x = 0, y = 0):
        super().__init__(parent,x,y)
        self.ox = -self.wx + winwidth / 2
        self.oy = -self.wy + winheight / 2
        self.startcam = False

class MovementNode(Node):
    def __init__(self, parent = None, x = 0, y = 0, xvel = 0, yvel = 0):
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
                ps = pygame.Surface((winwidth,winheight))
                ps.fill(self.color)
                screen.blit(ps,(0,0))
        
        super().draw()

class BackgroundImageNode(Node):
    def __init__(self,parent = None, imagepath = None, x = 0, y = 0):
        super().__init__(parent,0,0)
        self.imagepath = imagepath
        self.properties.update({"imagepath": str})
    
    def draw(self):
        if self.imagepath:
            bgimg = pygame.transform.smoothscale(imagenames[self.imagepath], (winwidth,winheight))
            screen.blit(bgimg, (0,0))
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

class TimerNode(Node):
    def __init__(self,parent = None, interval = 1000, x = 0, y = 0):
        super().__init__(parent,x,y)
        self.interval = interval
        self.fulltime = 0
        self.activated = False
        self.properties.update({"interval": int})

class CollisionRectNode(Node):
    def __init__(self,parent = None, x = 0, y = 0, width = 100, height = 100):
        super().__init__(parent,x,y)
        self.width = width
        self.height = height
        self.worldrect = pygame.Rect(self.wx,self.wy,self.width,self.height)
        self.renderrect = pygame.Rect(self.rx,self.ry,self.width,self.height)
        self.enabled = False
        self.properties.update({"width": int,"height": int,"enabled": bool})
        self.collide_dirs = []
    
    def draw(self):
        if not gamerunning and self in selected:
            pygame.draw.rect(screen, (0,255,0), self.renderrect, 3)
        super().draw()
    
    def is_colliding(self):
        return len(self.collide_dirs) > 0
    
    def collide_direction(self,direction):
        return direction in self.collide_dirs

def getallrects(node: Node,rectlist):
    if isinstance(node,CollisionRectNode):
        rectlist.append(node)
    for child in node.children:
        getallrects(child,rectlist)

def nodetorect(rectlist: list[CollisionRectNode]):
    newlist = []
    for node in rectlist:
        newlist.append(node.worldrect)
    return newlist

def getstartcamera(node: Node):
    if isinstance(node,CameraNode) and node.startcam:
        return node
    
    for child in node.children:
        getcam = getstartcamera(child)
        if getcam:
            return getcam
    
    return None

def keypressed(key: str):
    keys = pygame.key.get_pressed()
    keycode = getattr(pygame,f"K_{key.upper() if len(key) > 1 else key}",None)
    return keys[keycode] if keycode else False

def get_mouse_pos(screen = False):
    mx,my = pygame.mouse.get_pos()
    if mainscene.maincamera and not screen:
        mx -= maincamera.ox
        my -= maincamera.oy
    
    return mx,my

def get_main_scene():
    return mainscene

def get_root_node():
    return mainscene.rootnode

def random_number(start = 0,stop = 10):
    return random.randint(start,stop)
def random_float(start = 0.0,stop = 10.0):
    return random.uniform(start,stop)

def searchstring(string,instring):
    for char in string:
        if char not in instring:
            return False
    return True

def togglerun():
    global selected
    selected = []
    setmainprop()

    global gamerunning
    if gamerunning:
        for sc in scenes:
            sc.reset()
    gamerunning = not gamerunning
    if gamerunning:
        for sc in scenes:
            sc.maincamera = getstartcamera(sc.rootnode)
        for script in scripts.values():
            importlib.reload(script)
    else:
        for sc in scenes:
            sc.maincamera = maincamera

    return gamerunning

def deletenode():
    global selected

    for sn in selected:
        if sn == mainscene.maincamera:
            mainscene.maincamera = None
        sn.delete()
    selected = []
    setfocused()
    setmainprop()

cnode = Node

def changeadd(node):
    global cnode
    cnode = nodetypes[node]

def addnode():
    newnode = cnode(parent = None,x = 0,y = 0)
    if selected:
        selected[0].addchild(newnode)
        selected[0].children[-1].setpos(selected[0].wx,selected[0].wy)
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
    if searchstring(newvalue,"1234567890-.") and len(newvalue) > 0:
        newvalue = float(newvalue)
        if newvalue % 1 == 0: newvalue = int(newvalue)
    elif newvalue == "True":
        newvalue = True
    elif newvalue == "False":
        newvalue = False
    
    if type(newvalue) != sn.properties[convert]:
        errormessage(f"data type given ({type(newvalue).__name__}) does not match needed type ({sn.properties[convert].__name__})")
    elif type(newvalue) == str and len(newvalue) == 0:
        errormessage("no data was given")
    else:
        if convert == "wx" or convert == "wy":
            if convert == "wx":
                sn.setpos(int(newvalue),sn.wy)
            elif convert == "wy":
                sn.setpos(sn.wx,int(newvalue))

        elif convert == "imagepath":
            if newvalue == "None":
                sn.imagepath = None
            else:
                oldvalue = sn.imagepath

                try:
                    sn.imagepath = newvalue
                except FileNotFoundError:
                    errormessage(f"file '{newvalue}' not found")
                    sn.imagepath = oldvalue
                except pygame.error:
                    errormessage("unsupported file format")
                    sn.imagepath = oldvalue

        elif convert == "scriptname":
            if newvalue == "None":
                sn.scriptname = None
            else:
                if newvalue in scripts:
                    sn.scriptname = newvalue
                else:
                    errormessage(f"Script '{newvalue}' not found")

        else:
            setattr(sn,convert,newvalue)

def errormessage(message: str):
    global gamerunning
    if gamerunning:
        togglerun()
        guielements.startbutton.set_text("Start")
    gui.windows.UIMessageWindow(pygame.Rect(200,200,250,160), message, guielements.manager)

def addscript(scriptname: str):
    if scriptname not in scripts:
        try:
            module = importlib.import_module(scriptname.removesuffix(".py"))
            module.keypressed = keypressed
            module.get_main_scene = get_main_scene
            module.get_root_node = get_root_node
            module.get_mouse_pos = get_mouse_pos
            module.random_number = random_number
            module.random_float = random_float

            scripts[scriptname] = module
        except Exception as e:
            errormessage(f"Error in {scriptname}: {e}")
    else:
        try:
            newmodule = importlib.reload(scripts[scriptname])
        except Exception as e:
            errormessage(f"Error in {scriptname}: {e}")

def inscripts(scriptname):
    return scriptname in scripts

def sceneaction(action):
    global mainscene
    global maincamera
    global gamerunning

    if gamerunning:
        errormessage("cannot perform scene action while game is running")
        return

    if action == "new scene":
        scname = askinput("Create New Scene", "Enter scene name: ")
        mainscene = Scene(None,None,scname)
        mainscene.rootnode = Node(None,0,0)
        mainscene.maincamera = maincamera

    elif action == "delete scene":
        if len(scenes) == 1:
            errormessage("cannot delete scene")
            return

        scname = askinput("Delete scene","Enter scene name: ")
        if scname in scenenames:
            getscene = scenes[scenenames.index(scname)]
            if getscene == mainscene:
                mainscene = [sc for sc in scenes if sc != mainscene][0]
            scenes.remove(getscene)
        else:
            errormessage(f"Scene '{scname}' not found")
    
    elif action == "rename scene":
        scname = askinput("Rename scene", "Enter scene name: ")
        if scname in scenenames:
            newname = askinput("Rename Scene","Enter new scene name: ")
            getscene = scenes[scenenames.index(scname)]
            getscene.name = newname
        else:
            errormessage(f"Scene '{scname}' not found")
    
    elif action == "open scene":
        scname = askinput("Open scene", "Enter scene name: ")
        if scname in scenenames:
            getscene = scenes[scenenames.index(scname)]
            mainscene = getscene
        else:
            errormessage(f"Scene '{scname}' not found")

funcs = {
    "togglerun": togglerun,
    "deletenode": deletenode,
    "changeadd": changeadd,
    "addnode": addnode,
    "exitengine": exitengine,
    "changeprop": changeprop,
    "getselected": getselected,
    "errormessage": errormessage,
    "addscript": addscript,
    "inscripts": inscripts,
    "sceneaction": sceneaction
}
nodetypes = {
    "node": Node,
    "sprite": SpriteNode,
    "camera": CameraNode,
    "movement": MovementNode,
    "background": BackgroundNode,
    "backgroundimage": BackgroundImageNode,
    "rectangle": RectangleNode,
    "text": TextNode,
    "timer": TimerNode,
    "collisionrect": CollisionRectNode
}

manager = gui.UIManager((winwidth,winheight))
guielements = GuiElements(manager,funcs)

def drawtext(text,x,y,size,color,surface):
    font = pygame.font.SysFont("Arial",size)
    textsurface = font.render(text,True,color)
    surface.blit(textsurface,(x,y))
    rect = textsurface.get_rect()
    return pygame.Rect(x,y,rect.width,rect.height)

def drawnodetree(node: Node,x,y,clickrects):
    global guielements
    nodetreerect = guielements.nodetreewindow.get_relative_rect()
    nodetreesurface = pygame.Surface((nodetreerect.width - 15,nodetreerect.height - 15),pygame.SRCALPHA)
    nodetreesurface.fill((0,0,0,0))

    nodename = node.name
    tcolor = (64,214,237) if (node in selected) else (255,255,255)
    textrect = drawtext(nodename,x,y,15,tcolor,nodetreesurface)
    currenty = textrect.y + 15

    if nodetreerect.y + nodetreesurface.get_rect().bottom - 15 > textrect.y and nodetreerect.x + nodetreesurface.get_rect().right - 15 > textrect.x:
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
    for el in guielements.prlabels:
        el.kill()
    for el in guielements.prbuttons:
        el.kill()
    guielements.propertylist = []
    guielements.prlabels = []
    guielements.prbuttons = []

    for i in range(len(objprop)):
        temp = f"{objprop[i]}:"
        temp = temp[1:] if temp == "wx:" or temp == "wy:" else temp
        proptext = objprop[i]
        objprop[i] = getattr(node,objprop[i])

        pt = gui.elements.UILabel(pygame.Rect(0, i * 40 + 5, len(temp) * 9.5, 40), temp, guielements.manager, guielements.propertieswindow)
        ce = gui.elements.UITextEntryLine(pygame.Rect(len(temp) * 9.5, i * 40 + 5, 100, 40), guielements.manager, guielements.propertieswindow, initial_text = str(objprop[i]))

        if proptext == "imagepath":
            sb = gui.elements.UIButton(pygame.Rect(len(temp) * 9.5 + 110, i * 40 + 5, 100, 40), "Upload File", guielements.manager, guielements.propertieswindow)
            guielements.prbuttons.append(sb)

        guielements.propertylist.append(ce)
        guielements.prlabels.append(pt)
    guielements.propertieswindow.set_display_title(f"Properties - {node.name}")

def setmainprop():
    global guielements

    if len(selected) == 1 and guielements.propertieswindow.visible:
        setproperties(selected[0])
    else:
        for el in guielements.propertylist:
            el.kill()
        for pt in guielements.prlabels:
            pt.kill()
        for pb in guielements.prbuttons:
            pb.kill()
        guielements.propertylist = []
        guielements.prlabels = []
        guielements.prbuttons = []
        guielements.propertieswindow.set_display_title("Properties")

def setfocused():
    global textfocused
    textfocused = False

    if guielements.scriptbox.is_focused:
        textfocused = True
        return guielements.scriptbox
    elif guielements.scriptnametext.is_focused:
        textfocused = True
        return guielements.scriptnametext

    for tl in guielements.propertylist:
        if tl.is_focused:
            textfocused = True
            return tl

def selectnodes(node: Node):
    mx,my = pygame.mouse.get_pos()
    mousepos = pygame.math.Vector2(mx,my)
    nodepos = pygame.math.Vector2(node.rx,node.ry)
    
    if nodepos.distance_to(mousepos) <= 5:
        if node in selected:
            selected.remove(node)
        else:
            selected.append(node)
        setmainprop()
    
    if node.children:
        for child in node.children:
            selectnodes(child)

mainscene = Scene(None,None,"Scene")
mainscene.rootnode = Node(None,0,0)
maincamera = CameraNode(None,0,0)
mainscene.maincamera = maincamera

clock = pygame.time.Clock()
running = True

def main():
    global gamerunning
    global textfocused
    global clickrects
    global running
    global delta
    global mainscene
    global nmode

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
            
            if event.type == gui.UI_BUTTON_PRESSED:
                if event.ui_element in guielements.prbuttons:
                    index = guielements.prbuttons.index(event.ui_element)
                    filename = askfile()
                    changeprop(filename,"imagepath")

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    for rect,node in clickrects.items():
                        temprect = pygame.Rect(rect)
                        if temprect.collidepoint(event.pos):
                            if node.children:
                                node.expanded = not node.expanded
                            break

                elif event.button == 1:
                    if not gamerunning:
                        selectnodes(mainscene.rootnode)

                    for rect,node in clickrects.items():
                        temprect = pygame.Rect(rect)
                        if temprect.collidepoint(event.pos):
                            if node in selected:
                                selected.remove(node)
                            else:
                                selected.append(node)
                            setmainprop()
                            setfocused()

            elif event.type == pygame.KEYDOWN and textfocused:
                if event.key == pygame.K_TAB:
                    fe = setfocused()
                    fe.set_text(fe.get_text() + "   ")
            
            elif event.type == pygame.KEYUP and not textfocused:
                if event.key == pygame.K_m and len(selected) > 0:
                    if nmode == "moving":
                        nmode = "None"
                    else:
                        nmode = "moving"

                elif event.key == pygame.K_c and len(selected) > 0:
                    snode = selected[0]
                    snode.parent.addchild(copy.deepcopy(snode))

                elif event.key == pygame.K_p and len(selected) > 1:
                    for i in range(len(selected) - 1):
                        if selected[i].parent != selected[-1]:
                            selected[i].parent.children.remove(selected[i])
                            selected[i].parent = selected[-1]
                            selected[-1].addchild(selected[i])
                
                elif event.key == pygame.K_f:
                    guielements.colorpicker = gui.windows.UIColourPickerDialog(pygame.Rect(300,200,390,390), guielements.manager, initial_colour = pygame.Color(255,0,0))

                elif event.key == pygame.K_d and len(selected) > 0:
                    for sn in selected:
                        if isinstance(sn,CameraNode):
                            pcam = getstartcamera(mainscene.rootnode)
                            if pcam:
                                pcam.startcam = False
                            sn.startcam = True
                            errormessage(f"The camera node '{sn.name}' has been set to the start camera of the scene")
                            break
                
                elif event.key == pygame.K_s and len(selected) > 0:
                    if nmode == "resizing":
                        nmode = "None"
                    else:
                        nmode = "resizing"

        if nmode == "moving":
            mx,my = get_mouse_pos()
            for sn in selected:
                if sn == mainscene.rootnode:
                    errormessage("The root node of the scene cannot be moved")
                    nmode = "None"
                    break
                else:
                    sn.setpos(mx,my)
                
            setmainprop()
            setfocused()
        elif nmode == "resizing":
            for sn in selected:
                mx,my = get_mouse_pos()
                if hasattr(sn,"width") and hasattr(sn,"height"):
                    offx =  mx - sn.wx
                    offy = my - sn.wy
                    if offx > 0:
                        sn.width = offx
                    if offy > 0:
                        sn.height = offy

        if not gamerunning and not textfocused:
            if keypressed("right"):
                maincamera.translate(3,0)
            if keypressed("left"):
                maincamera.translate(-3,0)
            if keypressed("up"):
                maincamera.translate(0,-3)
            if keypressed("down"):
                maincamera.translate(0,3)

        maincamera.update()
        mainscene.update(gamerunning)
        manager.update(delta)
        screen.fill((35,35,35))
        mainscene.draw()
        manager.draw_ui(screen)

        if guielements.nodetreewindow.visible:
            drawnodetree(mainscene.rootnode, 30, 50,clickrects)
        
        drawtext(f"Current Scene: {mainscene.name}", winwidth - 200, 10, 15, (255,255,255), screen)
        snodetext = selected[0].name if len(selected) == 1 else ("None" if not selected else "Multiple")
        drawtext(f"Selected Node: {snodetext}", winwidth - 200, 30, 15, (255,255,255), screen)

        mx,my = pygame.mouse.get_pos()
        msp = f"Mouse screen position: {mx}, {my}"
        mx,my = get_mouse_pos(False)
        msw = f"Mouse world position: {mx}, {my}"
        drawtext(msp, winwidth - 200, 50, 15, (255,255,255), screen)
        drawtext(msw, winwidth - 200, 70, 15, (255,255,255), screen)

        pygame.display.update()

if __name__ == "__main__":
    main()

for script in scripts:
    if os.path.exists(script):
        os.remove(script)

pygame.quit()
