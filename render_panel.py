import bpy
from . import render_exporter

class ExportScene(bpy.types.Operator):
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
        engine = context.scene.render.engine
        if engine != 'Mitsuba2_Renderer':
            bpy.utils.unregister_class(MitsubaRenderSettingsPanel)

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

        #layout.label(text="Light strategy:")
        #row = layout.row()
        #row.prop(scene,"lightsamplestrategy")
        
        layout.label(text="Export:")
        row = layout.row()
        layout.operator("scene.export", icon='MESH_CUBE', text="Export scene")

def register():
    
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