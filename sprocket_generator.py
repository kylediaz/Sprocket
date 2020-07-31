# Author-Kyle Diaz
# Description-Creates a sprocket from given parameters

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math

# Gobal variables used to maintain a reference to all event handlers
handlers = []

app = adsk.core.Application.get()
if app:
    ui = app.userInterface
    unitsMgr = app.activeProduct.unitsManager

default_sprocket_name = "Sprocket"
default_chain_pitch = 1.27  # cm, .5 in
default_number_of_teeth = 40
default_roller_diameter = 0.79502  # cm, .313 in
default_thickness = 0.635  # cm


def createNewComponent():
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component


class SprocketComponent:

    def __init__(self, name, chain_pitch, number_of_teeth, roller_diameter, thickness):
        self.name = name
        self.chain_pitch = chain_pitch
        self.number_of_teeth = number_of_teeth
        self.roller_diameter = roller_diameter
        self.thickness = thickness
        self._comp = createNewComponent()
        if self._comp is None:
            ui.messageBox('New component failed to create',
                          'New Component Failed')
            return
        else:
            self._comp.name = self.name

    def __arc1_center_x(self):
        return self.chain_pitch / (2 * math.tan(math.pi / self.number_of_teeth))

    def __arc1_radius(self):
        return (self.roller_diameter + .005) / 2

    def __create_arc1s(self, sketch):
        center_x = self.__arc1_center_x()
        center_dy = .5 * self.chain_pitch

        top_arc_center = adsk.core.Point3D.create(center_x, center_dy, 0)
        bottom_arc_center = adsk.core.Point3D.create(center_x, -center_dy, 0)

        radius = self.__arc1_radius()

        top_arc_start_point = adsk.core.Point3D.create(
            center_x - radius, center_dy, 0)
        bottom_arc_start_point = adsk.core.Point3D.create(
            center_x - radius, -center_dy, 0)

        sweep_angle = math.acos((radius - .2 * self.chain_pitch) / radius)

        sketch_arcs = sketch.sketchCurves.sketchArcs
        top_arc = sketch_arcs.addByCenterStartSweep(
            top_arc_center, top_arc_start_point, sweep_angle)
        bottom_arc = sketch_arcs.addByCenterStartSweep(
            bottom_arc_center, bottom_arc_start_point, -sweep_angle)
        return top_arc, bottom_arc

    def __create_teeth_tip_line(self, sketch):
        """returns (top_point, bottom_point), line"""
        x = self.__arc1_center_x() - self.__arc1_radius() + .6 * self.chain_pitch
        dy = .05 * self.chain_pitch

        top_point = adsk.core.Point3D.create(x, dy, 0)
        bottom_point = adsk.core.Point3D.create(x, -dy, 0)
        line = sketch.sketchCurves.sketchLines.addByTwoPoints(
            top_point, bottom_point)
        # While I have the top and bottom points already, those are Point3D objects. I need to give SketchPoint because when I create
        # the arc2s, I need to constrain the arcs to the point, and I can't do that with the Point3D
        # The SketchPoints are included with the line object, but they are returned separately in a tube to avoid obscurity
        return (line.startSketchPoint, line.endSketchPoint), line

    def __create_arc2s(self, sketch, top_arc1, bottom_arc1, top_teeth_tip_point, bottom_teeth_tip_point):
        sketch_arcs = sketch.sketchCurves.sketchArcs
        constraints = sketch.geometricConstraints
        output = []
        # Since the bottom arc had a negative sweep angle, the top point and the bottom point are reversed, so arc2 needs to connect to the start point
        for arc1, arc1_point, tip_point in (top_arc1, top_arc1.endSketchPoint, top_teeth_tip_point), \
                                           (bottom_arc1, bottom_arc1.startSketchPoint, bottom_teeth_tip_point):
            # the middle point of the 3 point arc is arbitrarily at the midpoint of the start and end point
            average_x = (arc1_point.geometry.x + tip_point.geometry.x) / 2
            average_y = (arc1_point.geometry.y + tip_point.geometry.y) / 2
            average_y *= .995  # It can't be the exact geometric midpoint because it would technically have an infinite radius
            midpoint = adsk.core.Point3D.create(average_x, average_y, 0)
            arc2 = sketch_arcs.addByThreePoints(
                arc1_point, midpoint, tip_point)
            # The tip point needs to be fixed or else they will move when the constraint is applied
            tip_point.isFixed = True
            constraints.addTangent(arc1, arc2)
            output.append(arc2)
        return tuple(output)

    def __copy_circular_pattern(self, sketch, entities, count):
        normal = sketch.xDirection.crossProduct(sketch.yDirection)
        normal.transformBy(sketch.transform)
        origin = sketch.origin
        origin.transformBy(sketch.transform)

        rotationMatrix = adsk.core.Matrix3D.create()
        step = 2 * math.pi / count

        for i in range(1, int(count)):
            rotationMatrix.setToRotation(step * i, normal, origin)
            sketch.copy(entities, rotationMatrix)

    def __extrude(self, sketch):
        extrudes = self._comp.features.extrudeFeatures
        prof = sketch.profiles[0]
        ext_input = extrudes.createInput(
            prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        distance = adsk.core.ValueInput.createByReal(self.thickness)
        ext_input.setDistanceExtent(False, distance)

        extrudes.add(ext_input)

    def build_sprocket(self):
        sketches = self._comp.sketches
        xy_plane = self._comp.xYConstructionPlane

        base_sketch = sketches.add(xy_plane)

        # see ./doc/base_sketch.png to see a diagram of these variables

        # the arc1s and the line for the tip of the teeth are created first because they
        # will create points that can be used to create the arc2s
        top_arc1, bottom_arc1 = self.__create_arc1s(base_sketch)
        (top_tip_point, bottom_tip_point), tip_line = self.__create_teeth_tip_line(
            base_sketch)
        top_arc2, bottom_arc2 = self.__create_arc2s(
            base_sketch, top_arc1, bottom_arc1, top_tip_point, bottom_tip_point)

        entities = adsk.core.ObjectCollection.create()
        for entity in top_arc1, bottom_arc1, tip_line, top_arc2, bottom_arc2:
            entities.add(entity)
        self.__copy_circular_pattern(
            base_sketch, entities, self.number_of_teeth)

        self.__extrude(base_sketch)


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
                    chain_pitch = unitsMgr.evaluateExpression(
                        input.expression, "in")
                elif input.id == 'number_of_teeth':
                    number_of_teeth = int(input.value)
                elif input.id == 'roller_diameter':
                    roller_diameter = unitsMgr.evaluateExpression(
                        input.expression, "in")
                elif input.id == 'sprocket_thickness':
                    thickness = unitsMgr.evaluateExpression(
                        input.expression, "in")

            if (sprocket_name and chain_pitch and number_of_teeth and roller_diameter and thickness) \
                    and (chain_pitch > 0 and number_of_teeth > 0 and roller_diameter > 0):
                sprocket = SprocketComponent(
                    sprocket_name, chain_pitch, number_of_teeth, roller_diameter, thickness)
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

            inputs.addStringValueInput(
                'sprocket_name', 'Sprocket Name', default_sprocket_name)
            inputs.addValueInput('chain_pitch', 'Chain Pitch', 'in',
                                 adsk.core.ValueInput.createByReal(default_chain_pitch))
            inputs.addValueInput('number_of_teeth', 'Number Of Teeth', '',
                                 adsk.core.ValueInput.createByReal(default_number_of_teeth))
            inputs.addValueInput('roller_diameter', 'Roller Diameter', 'in',
                                 adsk.core.ValueInput.createByReal(default_roller_diameter))
            inputs.addValueInput('sprocket_thickness', 'Sprocket Thickness',
                                 'in', adsk.core.ValueInput.createByReal(default_thickness))
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox(
                'It is not supported in current workspace, please change to MODEL workspace and try again.')
            return

        command = ui.commandDefinitions.itemById('sprocket_generator')
        if not command:
            command = ui.commandDefinitions.addButtonDefinition(
                'sprocket_generator', 'Create sprocket', 'Create sprocket sketch', './resources')

        on_command_created = CommandCreatedHandler()
        command.commandCreated.add(on_command_created)
        handlers.append(on_command_created)

        inputs = adsk.core.NamedValues.create()
        command.execute(inputs)

        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
