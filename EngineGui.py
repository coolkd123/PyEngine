import pygame
import pygame_gui as gui
import pyperclip

class GuiElements:
    def __init__(self,manager: gui.UIManager,funcs: dict,nodes: dict):
        self.manager = manager
        self.funcs = funcs
        self.nodetypes = nodes

        self.utwindow = gui.elements.UIWindow(pygame.Rect(560,10,230,140),self.manager,"Utilities",resizable = True)
        self.nodetreewindow = gui.elements.UIWindow(pygame.Rect(560,170,230,140),self.manager,"Node Tree",resizable = True)
        self.propertieswindow = gui.elements.UIWindow(pygame.Rect(0,0,200,300),self.manager,"Properties",resizable = True, visible = 0)
        self.propertylist = []

        self.quitbutton = gui.elements.UIButton(pygame.Rect(10,10,100,40),"Exit",self.manager)

        self.startbutton = gui.elements.UIButton(pygame.Rect(10,10,100,40),"Start",self.manager,self.utwindow)
        options = ["node","sprite","camera","movement","background","rectangle","text"]
        self.addobject = gui.elements.UIDropDownMenu(options_list = options, relative_rect = pygame.Rect(120,10,100,40), manager = self.manager, starting_option = "node",container = self.utwindow)
        self.addbutton = gui.elements.UIButton(pygame.Rect(10,60,100,40), "Add Object", self.manager,self.utwindow)
        self.delbutton = gui.elements.UIButton(pygame.Rect(120,60,100,40),"Delete",self.manager,self.utwindow)

        self.ntbutton = gui.elements.UIButton(pygame.Rect(110,10,100,40),"Node Tree",self.manager)
        self.utbutton = gui.elements.UIButton(pygame.Rect(210,10,100,40), "Utilities", self.manager)
        self.propbutton = gui.elements.UIButton(pygame.Rect(310,10,100,40), "Properties", self.manager)
        self.colorpicker = None

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
                    self.nodetreewindow = gui.elements.UIWindow(pygame.Rect(560,170,230,140),self.manager,"Node Tree",resizable = True)
                
                elif event.ui_element == self.quitbutton:
                    self.funcs["exitengine"]()
                
                elif event.ui_element == self.utbutton and not self.utwindow.visible:
                    self.utwindow = gui.elements.UIWindow(pygame.Rect(560,10,230,140),self.manager,"Utilities",resizable = True)
                    self.startbutton = gui.elements.UIButton(pygame.Rect(10,10,100,40),"Start",self.manager,self.utwindow)
                    options = ["node","sprite","camera","movement","background","rectangle","text"]
                    self.addobject = gui.elements.UIDropDownMenu(options_list = options, relative_rect = pygame.Rect(120,10,100,40), manager = self.manager, starting_option = "node",container = self.utwindow)
                    self.addbutton = gui.elements.UIButton(pygame.Rect(10,60,100,40), "Add Object", self.manager,self.utwindow)
                    self.delbutton = gui.elements.UIButton(pygame.Rect(120,60,100,40),"Delete",self.manager,self.utwindow)
                
                elif event.ui_element == self.propbutton and not self.propertieswindow.visible:
                    self.propertieswindow = gui.elements.UIWindow(pygame.Rect(0,0,200,300),self.manager,"Properties",resizable = True)
            
            elif event.user_type == gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == self.addobject:
                    self.funcs["changeadd"](event.text)

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
            
            elif event.user_type == gui.UI_COLOUR_PICKER_COLOUR_PICKED:
                if event.ui_element == self.colorpicker:
                    pickedcolor = event.colour
                    copycolor = f"#{pickedcolor.r:02x}{pickedcolor.g:02x}{pickedcolor.b:02x}"
                    pyperclip.copy(copycolor)