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
        self.P = float(chain_pitch)
        self.N = float(number_of_teeth)
        self.Dr = float(roller_diameter)
    
    # most functions were copied verbatim, but for some, I was able to simplify
    # them using the other functions    
    def Ds(self):
        return 1.0005 * self.Dr + 0.003
    def R(self):
        return self.Ds() / 2
    def A(self):
        return 35 + 60 / self.N
    def B(self):
        return 18 - 56 / self.N
    def ac(self):
        return 0.8 * self.Dr
    def M(self):
        return self.ac() * math.cos(math.radians(self.A()))
    def T(self):
        return self.ac() * math.sin(math.radians(self.A()))
    def E(self):
        return 1.3025 * self.Dr + 0.0015
    def yz(self):
        return self.Dr * (1.4 * math.sin(math.radians(17 - 64 / self.N)) - self.B)
    def ab(self):
        return 1.4 * self.Dr
    def W(self):
        return 1.4 * self.Dr * math.cos(math.radians(180 / self.N))
    def V(self):
        return 1.4 * self.Dr * math.sin(math.radians(180 / self.N))
    def F(self):
        return self.Dr * (0.8 * math.cos(math.radians(self.B())) + 1.4 * math.cos(math.radians(17 - 64 / self.N)) - 1.3025) - .0015
    def H(self):
        return math.sqrt(self.F() ** 2 - (1.4 * self.Dr - self.P / 2) ** 2)
    def S(self):
        return self.P / 2 * math.cos(math.radians(180 / self.N)) + self.H() * math.sin(math.radians(180 / self.N))
    def PD(self):
        return self.P / math.sin(math.radians(180 / self.N))

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
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox('New component failed to create', 'New Component Failed')
            return
            
        sketches = newComp.sketches
        plane = newComp.xYConstructionPlane 
        base_sketch = sketches.add(plane)
        sketch_curves = base_sketch.sketchCurves
        sketch_points = base_sketch.sketchPoints
        sketch_dimensions = base_sketch.sketchDimensions
        constraints = base_sketch.geometricConstraints
        
        origin = sketch_points.add(adsk.core.Point3D.create(0, 0, 0))
        origin.isFixed = True
        
        # start of creating sketch here
        # the "steps" refered to in the comments are based on "Designing and Drawing a Sprocket"
        # A link to the document is in the README
        
        #3
        pitch_circle_radius = .5 * self.PD()
        pitch_circle = sketch_curves.sketchCircles.addByCenterRadius(origin, pitch_circle_radius)
        sketch_dimensions.addDiameterDimension(pitch_circle, adsk.core.Point3D.create(0, pitch_circle_radius / 2, 0), True)
        pitch_circle.isConstruction = True
        
        #4, 5
        line12 = sketch_curves.sketchLines.addByTwoPoints(origin, adsk.core.Point3D.create(0, pitch_circle_radius * 2, 0))
        line34 = sketch_curves.sketchLines.addByTwoPoints(
                        adsk.core.Point3D.create(pitch_circle_radius, pitch_circle_radius, 0), 
                        adsk.core.Point3D.create(-pitch_circle_radius, pitch_circle_radius, 0))
        line12.isConstruction = True
        line34.isConstruction = True
        constraints.addVertical(line12)
        constraints.addHorizontal(line34)
        constraints.addTangent(pitch_circle, line34)
        
        # 6
        circle1_centerpoint = sketch_points.add(adsk.core.Point3D.create(0, pitch_circle_radius, 0))
        constraints.addCoincident(circle1_centerpoint, line12)
        constraints.addCoincident(circle1_centerpoint, line34)
        circle1 = sketch_curves.sketchCircles.addByCenterRadius(circle1_centerpoint, self.R())
        
        # 7
        line12_offset = sketch_curves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(self.M(), 0, 0), 
                                                                 adsk.core.Point3D.create(self.M(), pitch_circle_radius * 2, 0))
        line34_offset = sketch_curves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(-pitch_circle_radius, pitch_circle_radius + self.T(), 0), 
                                                                 adsk.core.Point3D.create(pitch_circle_radius, pitch_circle_radius + self.T(), 0))
        line12_offset.isConstruction = True
        line34_offset.isConstruction = True
        constraints.addParallel(line12, line12_offset)
        constraints.addParallel(line34, line34_offset)
        sketch_dimensions.addOffsetDimension(line12, line12_offset, adsk.core.Point3D.create(self.M() / 2, pitch_circle_radius - self.M(), 0))
        sketch_dimensions.addOffsetDimension(line34, line34_offset, adsk.core.Point3D.create(-self.T(), pitch_circle_radius + self.T() / 2, 0))
        
        # 8
        point_c = sketch_points.add(adsk.core.Point3D.create(self.M(), pitch_circle_radius + self.T(), 0))
        constraints.addCoincident(point_c, line12_offset)
        constraints.addCoincident(point_c, line34_offset)
        
        circle1_radius = self.R()
        # linecx_length is this because linecx should terminate on the circumference of circle1
        linecx_length = circle1_radius + math.sqrt(self.M() ** 2 + self.T() ** 2)
        point_x_x = self.M() - abs(linecx_length * math.cos(math.radians(self.A())))
        point_x_y = pitch_circle_radius + self.T() - abs(linecx_length * math.sin(math.radians(self.A())))
        point_x = sketch_points.add(adsk.core.Point3D.create(point_x_x, point_x_y, 0))
        linecx = sketch_curves.sketchLines.addByTwoPoints(point_c, point_x)
        linecx.isConstruction = True
        constraints.addCoincident(point_x, circle1)
        sketch_dimensions.addAngularDimension(linecx, line34_offset, adsk.core.Point3D.create(0, pitch_circle_radius, 0))
        
        # 9
        point_y_x = self.M() - abs(self.E() * math.cos(math.radians(self.A() - self.B())))
        point_y_y = pitch_circle_radius + self.T() - abs(self.E() * math.sin(math.radians(self.A() - self.B())))
        point_y = sketch_points.add(adsk.core.Point3D.create(point_y_x, point_y_y, 0))
        linecy = sketch_curves.sketchLines.addByTwoPoints(point_c, point_y)
        linecy.isConstruction = True
        sketch_dimensions.addAngularDimension(linecy, line34_offset, adsk.core.Point3D.create(point_y_x, point_y_y, 0))
        linecy.isFixed = True
        
        # 10
        # arc is created using ThreePoints because otherwise its endpoints cant be tied to point_x and point_y
        # middlepoint will be overridden when setting the radius in the next line, so its value doesnt matter
        arc_xy = sketch_curves.sketchArcs.addByThreePoints(point_x, adsk.core.Point3D.create(point_y_x * .9999, point_y_y * .9999, 0), point_y)
        arc_xy.radius = self.E()
        
        # 11 is done after 13 because 11 can't be fully completed until 13
        
        # 12
        line12_offset_2_x = -self.W()
        line12_offset_2 = sketch_curves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(line12_offset_2_x, 2 * pitch_circle_radius, 0), 
                                                                    adsk.core.Point3D.create(line12_offset_2_x, 0, 0))
        constraints.addParallel(line12_offset_2, line12)
        sketch_dimensions.addOffsetDimension(line12_offset_2, line12, adsk.core.Point3D.create(self.W() / 2, 0, 0))
        line12_offset_2.isConstruction = True
        
        line34_offset_2_y = pitch_circle_radius - self.V()
        line34_offset_2 = sketch_curves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(-pitch_circle_radius, line34_offset_2_y, 0), 
                                                                    adsk.core.Point3D.create(pitch_circle_radius, line34_offset_2_y, 0))
        constraints.addParallel(line34_offset_2, line34)
        sketch_dimensions.addOffsetDimension(line34_offset_2, line34, adsk.core.Point3D.create(0, pitch_circle_radius + self.V() / 2, 0))
        line34_offset_2.isConstruction = True
        
        # 13
        point_b = sketch_points.add(adsk.core.Point3D.create(self.W() / 2, 0, 0))
        constraints.addCoincident(point_b, line12_offset_2)
        constraints.addCoincident(point_b, line34_offset_2)
        
        circle2 = sketch_curves.sketchCircles.addByCenterRadius(point_b, self.F())
        
        # 11
        # doesnt matter where, will be moved when connected with circle2
        point_z = sketch_points.add(adsk.core.Point3D.create(0, 0, 0))
        lineyz = sketch_curves.sketchLines.addByTwoPoints(point_y, point_z)
        constraints.addPerpendicular(lineyz, linecy)
        constraints.addCoincident(point_z, circle2)
        
        #14
        toothtip_line_angle = 180 / self.N + 90
        toothtip_line_length = 2 * pitch_circle_radius
        toothtip_endpoint = adsk.core.Point3D.create(-abs(toothtip_line_length * math.cos(math.radians(toothtip_line_angle))), 
                                                    abs(toothtip_line_length * math.sin(math.radians(toothtip_line_angle))), 0)
        toothtip_line = sketch_curves.sketchLines.addByTwoPoints(origin, toothtip_endpoint)
        toothtip_line.isConstruction = True
        toothtip_line.isFixed = True
        
        
        
        
        

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
                    chain_pitch = input.value
                elif input.id == 'number_of_teeth':
                    number_of_teeth = input.value
                elif input.id == 'roller_diameter':
                    roller_diameter = input.value
                    
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
