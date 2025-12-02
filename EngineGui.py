import pygame
import pygame_gui as gui
import pyperclip
import os

class GuiElements:
    def __init__(self,manager: gui.UIManager,funcs: dict):
        self.manager = manager
        self.funcs = funcs

        self.utwindow = gui.elements.UIWindow(pygame.Rect(1000,10,230,140), self.manager, "Utilities", resizable = True)
        self.nodetreewindow = gui.elements.UIWindow(pygame.Rect(1000,170,300,500), self.manager, "Node Tree", resizable = True)
        self.propertieswindow = gui.elements.UIWindow(pygame.Rect(10,70,300,300), self.manager, "Properties", resizable = True, visible = 0)
        self.propertylist = []
        self.prlabels = []
        self.prbuttons = []

        self.quitbutton = gui.elements.UIButton(pygame.Rect(10,10,100,40),"Exit",self.manager)

        self.startbutton = gui.elements.UIButton(pygame.Rect(10,10,100,40),"Start",self.manager,self.utwindow)
        options = ["node","sprite","camera","movement","background","backgroundimage","rectangle","text","timer"]
        self.addobject = gui.elements.UIDropDownMenu(options_list = options, relative_rect = pygame.Rect(120,10,100,40), manager = self.manager, starting_option = "node",container = self.utwindow)
        self.addbutton = gui.elements.UIButton(pygame.Rect(10,60,100,40), "Add Object", self.manager,self.utwindow)
        self.delbutton = gui.elements.UIButton(pygame.Rect(120,60,100,40),"Delete",self.manager,self.utwindow)

        self.ntbutton = gui.elements.UIButton(pygame.Rect(110,10,100,40),"Node Tree",self.manager)
        self.utbutton = gui.elements.UIButton(pygame.Rect(210,10,100,40), "Utilities", self.manager)
        self.propbutton = gui.elements.UIButton(pygame.Rect(310,10,100,40), "Properties", self.manager)
        self.scbutton = gui.elements.UIButton(pygame.Rect(410,10,100,40), "Script Editor", self.manager)

        sceneoptions = ["new scene","delete scene","rename scene","open scene"]
        self.sceneaction = gui.elements.UIDropDownMenu(sceneoptions, "open scene", pygame.Rect(510,10,130,40), self.manager)
        self.colorpicker = None

        self.scriptwindow = gui.elements.UIWindow(pygame.Rect(10,70,400,350), self.manager, "Write Script",resizable = True,visible = 1)
        self.scriptbox = gui.elements.UITextEntryBox(pygame.Rect(10,50,380,260), manager = self.manager, container = self.scriptwindow)
        self.scriptnametext = gui.elements.UITextEntryLine(pygame.Rect(10,5,150,40), self.manager, self.scriptwindow)
        self.scriptsavebutton = gui.elements.UIButton(pygame.Rect(170,5,100,40), "Save Script", self.manager, self.scriptwindow)
        self.openscriptbutton = gui.elements.UIButton(pygame.Rect(280,5,100,40), "Open Script", self.manager, self.scriptwindow)

    def eventhandle(self,event: pygame.event.Event):
        if event.type == pygame.USEREVENT:
            if event.user_type == gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.startbutton:
                    gr = self.funcs["togglerun"]()
                    if gr:
                        self.startbutton.set_text("Stop")
                    else:
                        self.startbutton.set_text("Start")
                
                elif event.ui_element == self.delbutton:
                    confirm = gui.windows.UIConfirmationDialog(
                        pygame.Rect(300,200,300,200),
                        manager = self.manager,
                        window_title = "Confirm Delete",
                        action_short_name = "Delete",
                        action_long_desc = "Are you sure you want to delete the selected nodes?"
                    )
                
                elif event.ui_element == self.addbutton:
                    self.funcs["addnode"]()
                
                elif event.ui_element == self.ntbutton and not self.nodetreewindow.visible:
                    self.nodetreewindow = gui.elements.UIWindow(pygame.Rect(1000,170,300,500), self.manager, "Node Tree", resizable = True)
                
                elif event.ui_element == self.quitbutton:
                    self.funcs["exitengine"]()
                
                elif event.ui_element == self.utbutton and not self.utwindow.visible:
                    self.utwindow = gui.elements.UIWindow(pygame.Rect(1000,10,230,140), self.manager, "Utilities", resizable = True)
                    self.startbutton = gui.elements.UIButton(pygame.Rect(10,10,100,40),"Start",self.manager,self.utwindow)
                    options = ["node","sprite","camera","movement","background","rectangle","text"]
                    self.addobject = gui.elements.UIDropDownMenu(options_list = options, relative_rect = pygame.Rect(120,10,100,40), manager = self.manager, starting_option = "node",container = self.utwindow)
                    self.addbutton = gui.elements.UIButton(pygame.Rect(10,60,100,40), "Add Object", self.manager,self.utwindow)
                    self.delbutton = gui.elements.UIButton(pygame.Rect(120,60,100,40),"Delete",self.manager,self.utwindow)
                
                elif event.ui_element == self.propbutton and not self.propertieswindow.visible:
                    self.propertieswindow = gui.elements.UIWindow(pygame.Rect(10,70,300,300),self.manager,"Properties",resizable = True)
                
                elif event.ui_element == self.scbutton and not self.scriptwindow.visible:
                    self.scriptwindow = gui.elements.UIWindow(pygame.Rect(10,70,400,350), self.manager, "Write Script",resizable = True,visible = 1)
                    self.scriptbox = gui.elements.UITextEntryBox(pygame.Rect(10,50,380,260), manager = self.manager, container = self.scriptwindow)
                    self.scriptnametext = gui.elements.UITextEntryLine(pygame.Rect(10,5,150,40), self.manager, self.scriptwindow)
                    self.scriptsavebutton = gui.elements.UIButton(pygame.Rect(170,5,100,40), "Save Script", self.manager, self.scriptwindow)
                    self.openscriptbutton = gui.elements.UIButton(pygame.Rect(280,5,100,40), "Open Script", self.manager, self.scriptwindow)
                
                elif event.ui_element == self.scriptsavebutton:
                    scriptname = self.scriptnametext.get_text()

                    if not scriptname.endswith(".py"):
                        self.funcs["errormessage"]("Script needs to be a python file")
                    elif scriptname.lower() == "main.py" or scriptname.lower() == "enginegui.py":
                        self.funcs["errormessage"]("Cannot save script to file as it is reserved")
                    else:
                        with open(scriptname,"w") as file:
                            file.write(self.scriptbox.get_text())

                        self.funcs["addscript"](scriptname)
                
                elif event.ui_element == self.openscriptbutton:
                    scriptname = self.scriptnametext.get_text()
                    if not scriptname.endswith(".py"):
                        self.funcs["errormessage"]("Script needs to be a python file")
                    elif not self.funcs["inscripts"](scriptname):
                        self.funcs["errormessage"](f"Script '{scriptname}' not found")
                    else:
                        with open(scriptname,"r") as file:
                            self.scriptbox.set_text(file.read())
            
            elif event.user_type == gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == self.addobject:
                    self.funcs["changeadd"](event.text)
                elif event.ui_element == self.sceneaction:
                    self.funcs["sceneaction"](event.text)

            elif event.user_type == gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                self.funcs["deletenode"]()
            
            elif event.user_type == gui.UI_WINDOW_CLOSE:
                if event.ui_element == self.nodetreewindow:
                    self.nodetreewindow.hide()
                elif event.ui_element == self.utwindow:
                    self.utwindow.hide()
                elif event.ui_element == self.propertieswindow:
                    self.propertieswindow.hide()
                    self.propertylist = []
                    self.prbuttons = []
                    self.prlabels = []
                elif event.ui_element == self.scriptwindow:
                    self.scriptwindow.hide()
            
            elif event.user_type == gui.UI_COLOUR_PICKER_COLOUR_PICKED:
                if event.ui_element == self.colorpicker:
                    pickedcolor = event.colour
                    copycolor = f"#{pickedcolor.r:02x}{pickedcolor.g:02x}{pickedcolor.b:02x}"
                    pyperclip.copy(copycolor)
