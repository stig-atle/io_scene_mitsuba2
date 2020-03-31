#NOTE: Run this code first then use SHIFT-A, below, to add Custom Float node type.

import bpy
from bpy.types import NodeTree, Node, NodeSocket
import nodeitems_utils
from nodeitems_utils import (
    NodeCategory,
    NodeItem,
    NodeItemCustom,
)


#nodecategory begin
class MitsubaNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        #Do not add the PBRT shader category if PBRT is not selected as renderer
        engine = context.scene.render.engine
        if engine != 'Mitsuba2_Renderer':
            return False
        else:
            b = False
            if context.space_data.tree_type == 'ShaderNodeTree': b = True
            return b

# all categories in a list
Mitsuba_node_categories = [
    # identifier, label, items list
    #MitsubaNodeCategory("SOMENODES", "PBRT", items=[
    MitsubaNodeCategory("MSHADER", "Mitsuba", items=[
        NodeItem("MitsubaCustomNodeType"),
        ]),
    ]

#nodecategory end


# Implementation of custom nodes from Python
# Derived from the NodeTree base type, similar to Menu, Operator, Panel, etc.
class MitsubaTree(NodeTree):
    bl_idname = 'CustomTreeMitsuba'
    bl_label = 'Mitsuba Node Tree'
    bl_icon = 'NODETREE'

# Defines a poll function to enable filtering for various node tree types.
class MitsubaTreeNode :
    bl_icon = 'INFO'
    @classmethod
    def poll(cls, ntree):
        b = False
        # Make your node appear in different node trees by adding their bl_idname type here.
        if ntree.bl_idname == 'ShaderNodeTree': b = True
        return b

# Derived from the Node base type.
class MitsubaBSDF(Node,MitsubaTreeNode):
    '''A custom node'''
    bl_idname = 'MitsubaCustomNodeType'
    bl_label = 'Mitsuba2 BSDF'
    bl_icon = 'INFO'

    def uda(self, context):
        self.update()

# SEE HERE : https://docs.blender.org/api/current/bpy.types.Node.html?highlight=node#bpy.types.Node.socket_value_update
# https://blender.stackexchange.com/questions/74645/alternative-update-callback-for-pointerproperty
# tex_image.show_texture = True
    def common_update(self, context, origin):
        print("common_update called...")

    def updateViewportColor(self,context):
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs["kd"].default_value
        
    def updateViewportColorNew(self):
        print("Trying to update color on material..")
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs[0].default_value
            #node_tree.nodes["Mitsuba BSDF"].inputs[0].default_value

    #Sigma : bpy.props.FloatProperty(default=0.0, min=0.0, max=1.0)
    #Kd : bpy.props.FloatVectorProperty(name="Kd", description="Kd",default=(0.8, 0.8, 0.8, 1.0), min=0, max=1, subtype='COLOR', size=4,update=updateViewportColor)

    def init(self, context):
        self.outputs.new('NodeSocketFloat', "Mitsuba2 BSDF")
        #KdTexture_node = self.inputs.new('NodeSocketColor', "Kd Texture")
        #KdTexture_node.hide_value = True
        kd = self.inputs.new('NodeSocketColor', "kd")
        kd.default_value=(0.8,0.8,0.8,1.0)
        #Set up a callback for the material
        #self.kd.callback(self.name, "uda")
        #self.draw.callback_enable()

    def draw(self, context):
        print("draw called")

    #def draw_buttons(self, context, layout):
        #layout.prop(self, "Sigma",text = 'Sigma')
        #layout.prop(self, "Kd",text = 'Kd')
        #layout.prop(self,"kd_tex" , text = 'kdTexture')
        
    def draw_label(self):
        return "Mitsuba2 BSDF"

    def socket_value_update(self,context):
        print("Socket value changed..")

    def update(self):
        # your code here
        print("update(self) is called")
        #if self.inputs is not None:
        #    if self.inputs[0] is not None:
        #self.diffuse_color = self.kd
        #for skt in self.inputs:
        #    if skt.links:
        #        #self.diffuse_color = self.kd
        #        if (skt.name == "kd"):
        #            #updateViewportColor()
        #            print("Input socket {} is linked".format(skt.name))
        #            print("Trying to update color on material..")
        #            mat = bpy.context.active_object.active_material
        #            if mat is not None:
        #                bpy.data.materials[mat.name].diffuse_color=self.inputs[0].default_value

        

        for skt in self.outputs:
            if skt.links:
                #self.diffuse_color = self.kd
                if (skt.name == "kd"):
                    #updateViewportColor()
                    print("Output socket {} is linked".format(skt.name))


def register():
    nodeitems_utils.register_node_categories("MitsubaCustomNodes", Mitsuba_node_categories)
    #bpy.utils.register_class(PbrtRenderSettingsPanel)
    # bpy.utils.register_class(PbrtMatte)
    # bpy.utils.register_class(PbrtMirror)
    # bpy.utils.register_class(PbrtGlass)
    # bpy.utils.register_class(PbrtDisney)
    # bpy.utils.register_class(PbrtMetal)
    # bpy.utils.register_class(PbrtUber)
    # bpy.utils.register_class(PbrtSubsurface)
    # bpy.utils.register_class(PbrtSubstrate)
    # bpy.utils.register_class(PbrtPlastic)

def unregister():
    nodeitems_utils.unregister_node_categories("MitsubaCustomNodes")
    #bpy.utils.unregister_class(PbrtRenderSettingsPanel)
    # bpy.utils.unregister_class(PbrtMatte)
    # bpy.utils.unregister_class(PbrtMirror)
    # bpy.utils.unregister_class(PbrtGlass)
    # bpy.utils.unregister_class(PbrtDisney)
    # bpy.utils.unregister_class(PbrtMetal)
    # bpy.utils.unregister_class(PbrtUber)
    # bpy.utils.unregister_class(PbrtSubsurface)
    # bpy.utils.unregister_class(PbrtSubstrate)
    # bpy.utils.unregister_class(PbrtPlastic)