import bpy
from . import render_exporter
from bl_ui.properties_render import RENDER_PT_context

class ExportMitsuba2Scene(bpy.types.Operator):
    bl_idname = 'scene.export'
    bl_label = 'Export Scene'
    bl_options = {"REGISTER", "UNDO"}
    COMPAT_ENGINES = {'Mitsuba2_Renderer'}
    
    def execute(self, context):
        print("Starting calling mitsuba_export")
        print("Output path:")
        print(bpy.data.scenes[0].exportpath)
        for frameNumber in range(bpy.data.scenes['Scene'].batch_frame_start, bpy.data.scenes['Scene'].batch_frame_end +1):
            bpy.data.scenes['Scene'].frame_set(frameNumber)
            print("Exporting frame: %s" % (frameNumber))
            render_exporter.export_Mitsuba(bpy.data.scenes['Scene'].exportpath, bpy.data.scenes['Scene'], '{0:05d}'.format(frameNumber))
        self.report({'INFO'}, "Export complete.")
        return {"FINISHED"}

class MitsubaRenderSettingsPanel(bpy.types.Panel):
    """Creates a Mitsuba settings panel in the render context of the properties editor"""
    bl_label = "Mitsuba Render settings"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    COMPAT_ENGINES = {'Mitsuba2_Renderer'}


    #Hide the Mitsuba render panel if Mitsuba render engine is not currently selected.
    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if engine != 'Mitsuba2_Renderer':
            return False
        else:
            return True

    def draw(self, context):

        layout = self.layout

        scene = context.scene

        layout.label(text="Output folder path")
        row = layout.row()
        
        row.prop(scene, "exportpath")

        layout.label(text="Environment Map")
        row = layout.row()
        row.prop(scene,"environmentmaptpath")

        layout.label(text="Environment map scale:")
        row = layout.row()
        row.prop(scene, "environmentmapscale")

        layout.label(text="Frame settings:")
        row = layout.row()
        row.prop(scene, "batch_frame_start")
        row.prop(scene, "batch_frame_end")

        layout.label(text="Resolution:")
        row = layout.row()
        row.prop(scene, "resolution_x")
        row.prop(scene, "resolution_y")

        row = layout.row()
        row.prop(scene,"spp")

        layout.label(text="Depth of field:")
        row = layout.row()
        row.prop(scene,"dofLookAt")
        row = layout.row()
        row.prop(scene, "lensradius")

        layout.label(text="Integrator settings:")
        row = layout.row()

        row.prop(scene,"integrators")

        if scene.integrators == 'path':
            row = layout.row()
            row.prop(scene,"path_integrator_hide_emitters")
            row = layout.row()
            row.prop(scene,"path_integrator_max_depth")
            row.prop(scene,"path_integrator_rr_depth")
        
        if scene.integrators == 'volpathsimple':
            row = layout.row()
            row.prop(scene,"path_integrator_max_depth")
            row.prop(scene,"path_integrator_rr_depth")

        if scene.integrators == 'volpath':
            row = layout.row()
            row.prop(scene,"path_integrator_max_depth")
            row.prop(scene,"path_integrator_rr_depth")

        if scene.integrators == 'direct':
            row = layout.row()
            row.prop(scene,"path_integrator_hide_emitters")
            row = layout.row()
            row.prop(scene,"direct_integrator_emitter_samples")
            row = layout.row()
            row.prop(scene,"direct_integrator_bsdf_samples")
            
            

        #layout.label(text="Light strategy:")
        #row = layout.row()
        #row.prop(scene,"lightsamplestrategy")
        
        layout.label(text="Export:")
        row = layout.row()
        layout.operator("scene.export", icon='MESH_CUBE', text="Export scene")

def compatible_panels():
    panels = [
        "RENDER_PT_color_management",
        "RENDER_PT_color_management_curves",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]

def register():

    # We append our draw function to the existing Blender render panel
    RENDER_PT_context.append(MitsubaRenderSettingsPanel)
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add('Mitsuba2_Renderer')

    bpy.types.Scene.exportpath = bpy.props.StringProperty(
        name="",
        description="Export folder",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')

    bpy.types.Scene.environmentmaptpath = bpy.props.StringProperty(
        name="",
        description="Environment map",
        default="",
        maxlen=1024,
        subtype='FILE_PATH')

    #bpy.types.Scene.outputfilename = bpy.props.StringProperty(
    #    name="",
    #    description="Image output file name",
    #    default="output.exr",
    #    maxlen=1024,
    #    subtype='FILE_NAME')

    bpy.types.Scene.spp = bpy.props.IntProperty(name = "Samples per pixel", description = "Set spp", default = 100, min = 1, max = 9999)
    bpy.types.Scene.environmentmapscale = bpy.props.FloatProperty(name = "Env. map scale", description = "Env. map scale", default = 1, min = 0.001, max = 9999)
    bpy.types.Scene.resolution_x = bpy.props.IntProperty(name = "X", description = "Resolution x", default = 1366, min = 1, max = 9999)
    bpy.types.Scene.resolution_y = bpy.props.IntProperty(name = "Y", description = "Resolution y", default = 768, min = 1, max = 9999)
    bpy.types.Scene.dofLookAt = bpy.props.PointerProperty(name="Target", type=bpy.types.Object)
    bpy.types.Scene.lensradius = bpy.props.FloatProperty(name = "Lens radius", description = "Lens radius", default = 0, min = 0.001, max = 9999)
    bpy.types.Scene.batch_frame_start = bpy.props.IntProperty(name = "Frame start", description = "Frame start", default = 1, min = 1, max = 9999999)
    bpy.types.Scene.batch_frame_end = bpy.props.IntProperty(name = "Frame end", description = "Frame end", default = 1, min = 1, max = 9999999)

    integrators = [("direct", "direct", "", 1),("path", "path", "", 2),("volpath", "volpath", "", 3),("volpathsimple", "volpathsimple", "", 4)]
    bpy.types.Scene.integrators = bpy.props.EnumProperty(name = "Name", items=integrators , default="path")

    #path integrator settings:
    bpy.types.Scene.path_integrator_max_depth = bpy.props.IntProperty(name = "Max depth", description = "Specifies the longest path depth in the generated output image (where -1 corresponds to infty). A value of 1 will only render directly visible light sources. 2 will lead to single-bounce (direct-only) illumination, and so on.", default = -1, min = -1, max = 9999)
    bpy.types.Scene.path_integrator_rr_depth = bpy.props.IntProperty(name = "Rr depth", description = "Specifies the minimum path depth, after which the implementation will start to use the *russian roulette* path termination criterion.", default = 5, min = 0, max = 9999)
    bpy.types.Scene.path_integrator_hide_emitters = bpy.props.BoolProperty(name="Hide emitters", description="Hide directly visible emitters.", default = False)

    bpy.types.Scene.direct_integrator_emitter_samples = bpy.props.IntProperty(name = "Emitter samples", description = "specifies the number of samples that should be generated using the direct illumination strategies implemented by the scene's emitters. (Default: set to the value of 'shading samples')", default = 1, min = 1, max = 9999)
    bpy.types.Scene.direct_integrator_bsdf_samples = bpy.props.IntProperty(name = "BSDF samples", description = "specifies the number of samples that should be generated using the BSDF sampling strategies implemented by the scene's surfaces.", default = 1, min = 1, max = 9999)
    


def unregister():
    RENDER_PT_context.remove(MitsubaRenderSettingsPanel)
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove('Mitsuba2_Renderer')