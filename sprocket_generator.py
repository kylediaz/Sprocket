#Author-Kyle Diaz
#Description-Creates a sprocket from given parameters

import adsk.core, adsk.fusion, adsk.cam, traceback
import math

# Gobal variables used to maintain a reference to all event handlers
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface
    unitsMgr = app.activeProduct.unitsManager

default_sprocket_name = "Sprocket"
default_chain_pitch = 0.635 # cm, .25 in
default_number_of_teeth = 30
default_roller_diameter = 0.3302 # cm, .130 in

class Sprocket:
    # the names used in here follow the convention used in  "Chains for Power Transmission
    # and Material Handling handbook", which is considered the industry standard
    def __init__(self, chain_pitch, number_of_teeth, roller_diameter):
        self.P = chain_pitch
        self.N = number_of_teeth
        self.Dr = roller_diameter
    
    # most functions were copied verbatim, but for some, I was able to simplify
    # them using the other functions    
    def Ds(self):
        return 1.0005 * self.Dr + 0.003
    def R(self):
        return self.Ds / 2
    def A(self):
        return 35 + 60 / self.N
    def B(self):
        return 18 - 56 / self.N
    def ac(self):
        return 0.8 * self.Dr
    def M(self):
        return self.ac * math.cos(self.A)
    def T(self):
        return self.ac * math.sin(self.A)
    def E(self):
        return 1.3025 * self.Dr + 0.0015
    def yz(self):
        return self.Dr * (1.4 * math.sin(17 - 64 / self.N) - self.B)
    def ab(self):
        return 1.4 * self.Dr
    def W(self):
        return 1.4 * self.Dr * math.cos(180 / self.N)
    def V(self):
        return 1.4 * self.Dr * math.sin(180 / self.N)
    def F(self):
        return self.Dr * (0.8 * math.cos(self.B) + 1.4 * math.cos(17 - 64 / self.N) - 1.3025) - .0015
    def H(self):
        return math.sqrt(self.F ** 2 - (1.4 * self.Dr - self.P / 2) ** 2)
    def S(self):
        return self.P / 2 * math.cos(180 / self.N) + self.H * math.sin(180 / self.N)
    def PD(self):
        return self.P / math.sin(180 / self.N)

def createNewComponent():
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component

class SprocketComponent(Sprocket):
    def __init__(self, name, chain_pitch, number_of_teeth, roller_diameter):
        super().__init__(chain_pitch, number_of_teeth, roller_diameter)
        self._name = name
    def build_sprocket(self):
        pass

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            inputs = command.commandInputs

            for input in inputs:
                if input.id == 'sprocket_name':
                    sprocket_name = input.value
                elif input.id == 'chain_pitch':
                    chain_pitch = input.expression
                elif input.id == 'number_of_teeth':
                    number_of_teeth = input.expression
                elif input.id == 'roller_diameter':
                    roller_diameter = input.expression
                    
            sprocket = SprocketComponent(sprocket_name, chain_pitch, number_of_teeth, roller_diameter)
            sprocket.build_sprocket()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            on_execute_preview = CommandExecuteHandler()
            cmd.executePreview.add(on_execute_preview)
            on_destroy = CommandDestroyHandler()
            cmd.destroy.add(on_destroy)
            
            handlers.append(on_execute)
            handlers.append(on_execute_preview)
            handlers.append(on_destroy)
            
            inputs = cmd.commandInputs

            inputs.addStringValueInput('sprocket_name', 'Sprocket Name', default_sprocket_name)
            inputs.addValueInput('chain_pitch', 'Chain Pitch', 'in', adsk.core.ValueInput.createByReal(default_chain_pitch))
            inputs.addValueInput('number_of_teeth', 'Number Of Teeth', '', adsk.core.ValueInput.createByReal(default_number_of_teeth))
            inputs.addValueInput('roller_diameter', 'Roller Diameter', 'in', adsk.core.ValueInput.createByReal(default_roller_diameter))
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return
            
        command = ui.commandDefinitions.itemById('sprocket_generator')
        if not command:
            command = ui.commandDefinitions.addButtonDefinition('sprocket_generator', 
                                                                'Create sprocket', 
                                                                'Create sprocket sketch', 
                                                                './resources')
        on_command_created = CommandCreatedHandler()
        command.commandCreated.add(on_command_created)
        handlers.append(on_command_created)
        
        inputs = adsk.core.NamedValues.create()
        command.execute(inputs)

        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
