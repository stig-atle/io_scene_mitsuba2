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
        #Do not add the Mitsuba2 shader category if Mitsuba2 is not selected as renderer
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
    MitsubaNodeCategory("SHADER", "Mitsuba", items=[
        NodeItem("MitsubaBSDFDiffuse"),
        NodeItem("MitsubaBSDFPlastic"),
        NodeItem("MitsubaBSDFDielectric"),
        NodeItem("MitsubaBlackBody"),
        NodeItem("MitsubaBSDFConductor"),
        NodeItem("MitsubaBSDFMedium"),
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

class MitsubaBlackBody(Node, MitsubaTreeNode):
    '''A custom node'''
    bl_idname = 'MitsubaBlackBody'
    bl_label = 'Mitsuba2 BlackBody'
    bl_icon = 'INFO'

    def uda(self, context):
        self.update()
    
    def common_update(self, context, origin):
        print("common_update called...")
    
    def updateViewportColorNew(self):
        print("Trying to update color on material..")
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs[0].default_value
			
    temperature: bpy.props.FloatProperty(default=5000.0, min=0.1, max=99999.0)

    def init(self, context):
        self.outputs.new('NodeSocketFloat', "Mitsuba2 BlackBody")
		
    def draw(self, context):
        print("draw called")

    def draw_buttons(self, context, layout):
        layout.prop(self, "temperature",text = 'Temperature')
        
        
    def draw_label(self):
        return "Mitsuba2 BlackBody"

    def socket_value_update(self,context):
        print("Socket value changed..")

    def update(self):
        print("update(self) is called")

class MitsubaBSDF_Conductor(Node, MitsubaTreeNode):
    '''A custom node'''
    bl_idname = 'MitsubaBSDFConductor'
    bl_label = 'Mitsuba2 BSDF Conductor'
    bl_icon = 'INFO'

    def uda(self, context):
        self.update()
    
    def common_update(self, context, origin):
        print("common_update called...")

    def updateViewportColor(self,context):
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs["diffuse_reflectance"].default_value
            
    def updateViewportColorNew(self):
        print("Trying to update color on material..")
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs[0].default_value

    presets = [("a-C", "a-C", "", 1),("Na_palik", "Na_palik", "", 2),("Ag", "Ag", "", 3),("Nb", "Nb", "", 4),("Al", "Al", "", 5),("AlAs", "AlAs", "", 6),("Rh", "Rh", "", 7),("AlSb", "AlSb", "", 8),("Se", "Se", "", 9),("Au", "Au", "", 10),("SiC", "SiC", "", 11),("Be", "Be", "", 12),("SnTe", "SnTe", "", 13),("Cr", "Cr", "", 14),("Ta", "Ta", "", 15),("CsI", "CsI", "", 16),("Te", "Te", "", 17),("Cu", "Cu", "", 18),("ThF4", "ThF4", "", 19),("Cu2O", "Cu2O", "", 20),("TiC", "TiC", "", 21),("CuO", "CuO", "", 22),("TiN", "TiN", "", 23),("d-C", "d-C", "", 24),("TiO2", "TiO2", "", 25),("Hg", "Hg", "", 26),("VC", "VC", "", 27),("HgTe", "HgTe", "", 28),("V_palik", "V_palik", "", 29),("Ir", "Ir", "", 30),("VN", "VN", "", 31),("K", "K", "", 32),("W", "W", "", 33),("Li", "Li", "", 34),("MgO", "MgO", "", 35),("Mo", "Mo", "", 36)]
    named_preset : bpy.props.EnumProperty(name = "Preset", items=presets , default="Al")
    
    roughness : bpy.props.BoolProperty(name="Use roughness", description="Use version with roughness.", default = False)
    alpha_u: bpy.props.FloatProperty(default=0.05, min=0.0, max=9999.0)
    alpha_v: bpy.props.FloatProperty(default=0.3, min=0.0, max=9999.0)

    def init(self, context):
        self.outputs.new('NodeSocketFloat', "Mitsuba2 BSDF Conductor")
        specular_reflectance = self.inputs.new('NodeSocketColor', "Specular reflectance")    
        specular_reflectance.default_value=(1.0,1.0,1.0,1.0)

    def draw(self, context):
        print("draw called")

    def draw_buttons(self, context, layout):
        layout.prop(self, "roughness",text = 'Use roughness.')

        layout.prop(self, "named_preset",text = 'Named preset')
        if self.roughness == True:
            layout.prop(self, "alpha_u",text = 'alpha_u')
            layout.prop(self, "alpha_v",text = 'alpha_v')
        
    def draw_label(self):
        return "Mitsuba2 BSDF Conductor"

    def socket_value_update(self,context):
        print("Socket value changed..")

    def update(self):
        print("update(self) is called")

class MitsubaBSDF_Medium(Node, MitsubaTreeNode):
    '''A custom node'''
    bl_idname = 'MitsubaBSDFMedium'
    bl_label = 'Mitsuba2 BSDF Medium'
    bl_icon = 'INFO'

    def update_value(self, context):
        self.update ()

    mediumType = [("homogeneous","homogeneous","",1)]
    Type : bpy.props.EnumProperty(name = "Type", items=mediumType , default="homogeneous")
    sigma_t : bpy.props.FloatVectorProperty(name="sigma_t", description="sigma_t",default=(0.8, 0.8, 0.8, 1.0), min=0, max=1, subtype='COLOR', size=4)
    albedo : bpy.props.FloatVectorProperty(name="albedo", description="albedo",default=(0.8, 0.8, 0.8, 1.0), min=0, max=1, subtype='COLOR', size=4)
    density : bpy.props.FloatProperty(default=1.0, min=0.0, max=99999.0)
    #sigma_s : bpy.props.FloatProperty(default=1.0, min=0.0, max=99999.0)

    #g : bpy.props.FloatProperty(default=0.0, min=0.0001, max=1.0)

    def init(self, context):
        self.outputs.new('NodeSocketFloat', "Mitsuba2 BSDF Medium")
        
    def update(self):
        print('Updating Mitsuba2 BSDF Medium props..')
        try:
            can_continue = True
        except:
            can_continue = False
        if can_continue:
            print("continues in update rutine.")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Type",text = 'Type')
        layout.prop(self, "sigma_t",text = 'sigma_t')
        layout.prop(self, "albedo",text = 'albedo')
        layout.prop(self, "density",text = 'density')

    def draw_label(self):
        return "Mitsuba2 BSDF Medium"

class MitsubaBSDF_Dielectric(Node, MitsubaTreeNode):
    '''A custom node'''
    bl_idname = 'MitsubaBSDFDielectric'
    bl_label = 'Mitsuba2 BSDF Dielectric'
    bl_icon = 'INFO'

    def uda(self, context):
        self.update()
    
    def common_update(self, context, origin):
        print("common_update called...")

    def updateViewportColor(self,context):
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs["diffuse_reflectance"].default_value
        
    def updateViewportColorNew(self):
        print("Trying to update color on material..")
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs[0].default_value

    roughness = bpy.props.BoolProperty(name="Use roughness", description="Use version with roughness.", default = False)
    specular_sampling_weight : bpy.props.FloatProperty(default=1.0, min=0.0, max=1.0)
    fdr_int: bpy.props.FloatProperty(default=1.504, min=0.0, max=9999.0)
    fdr_ext: bpy.props.FloatProperty(default=1.0, min=0.0, max=9999.0)
    presets = [("vacuum", "vacuum", "", 1),("acetone", "acetone", "", 2),("bromine", "bromine", "", 3),("bk7", "bk7", "1.5046", 4),("helium", "helium", "", 5),("ethanol", "ethanol", "", 6),("water ice", "water ice", "", 7),("sodium chloride", "sodium chloride", "", 8),("hydrogen", "hydrogen", "", 9),("carbon tetrachloride", "carbon tetrachloride", "", 10),("fused quartz", "fused quartz", "", 11),("amber", "amber", "", 12),("air", "air", "", 13),("glycerol", "glycerol", "", 14),("pyrex", "pyrex", "", 15),("pet", "pet", "", 16),("carbon dioxide", "carbon dioxide", "", 17),("benzene", "benzene", "", 18),("acrylic glass", "acrylic glass", "", 19),("diamond", "diamond", "", 20),("water", "water", "", 21),("silicone oil", "silicone oil", "", 22),("polypropylene", "polypropylene", "", 23)]
    use_internal_ior = bpy.props.BoolProperty(name="Use internal IOR preset", description="Use internal IOR preset.", default = True)
    ior_internal_preset = bpy.props.EnumProperty(name = "Internal preset", items=presets , default="bk7")
    use_external_ior = bpy.props.BoolProperty(name="Use external IOR preset", description="Use external IOR preset.", default = True)
    ior_external_preset = bpy.props.EnumProperty(name = "External preset", items=presets , default="vacuum")
    alpha: bpy.props.FloatProperty(default=0.1, min=0.0, max=1.0)
    distributionModels = [("beckmann", "beckmann", "", 1), ("ggx", "ggx", "", 2)]
    distributionModel = bpy.props.EnumProperty(name = "Distribution model", items=distributionModels , default="beckmann")


    def init(self, context):
        self.outputs.new('NodeSocketFloat', "Mitsuba2 BSDF Dielectric")
        specular_reflectance = self.inputs.new('NodeSocketColor', "Specular reflectance")
        specular_reflectance.default_value=(1.0,1.0,1.0,1.0)
        specular_transmittance = self.inputs.new('NodeSocketColor', "Specular transmittance")
        specular_transmittance.default_value=(1.0,1.0,1.0,1.0)

    def draw(self, context):
        print("draw called")

    def draw_buttons(self, context, layout):

        layout.prop(self, "roughness",text = 'Use roughness.')
        if self.roughness == True:
            layout.prop(self, "alpha",text = 'alpha')
            layout.prop(self, "distributionModel",text = 'Distribution model')
            
        layout.prop(self, "use_internal_ior",text = 'Use Internal IOR preset')
        if self.use_internal_ior == False:
            layout.prop(self, "fdr_int",text = 'Internal IOR')
        else:
            layout.prop(self, "ior_internal_preset",text = 'IOR internal preset')
        
        layout.prop(self, "use_external_ior",text = 'Use external IOR preset')
        if self.use_external_ior == False:
            layout.prop(self, "fdr_ext",text = 'External IOR')
        else:
            layout.prop(self, "ior_external_preset",text = 'IOR external preset')
        
    def draw_label(self):
        return "Mitsuba2 BSDF Dielectric"

    def socket_value_update(self,context):
        print("Socket value changed..")

    def update(self):
        print("update(self) is called")
        

        #for skt in self.outputs:
        #    if skt.links:
        #        #self.diffuse_color = self.diffuse_reflectance
        #        if (skt.name == "diffuse_reflectance"):
        #            #updateViewportColor()
        #            print("Output socket {} is linked".format(skt.name))


# Derived from the Node base type.
class MitsubaBSDF_Plastic(Node, MitsubaTreeNode):
    '''A custom node'''
    bl_idname = 'MitsubaBSDFPlastic'
    bl_label = 'Mitsuba2 BSDF Plastic'
    bl_icon = 'INFO'

    def uda(self, context):
        self.update()
    
    def common_update(self, context, origin):
        print("common_update called...")

    def updateViewportColor(self,context):
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs["diffuse_reflectance"].default_value
        
    def updateViewportColorNew(self):
        print("Trying to update color on material..")
        mat = bpy.context.active_object.active_material
        if mat is not None:
            bpy.data.materials[mat.name].diffuse_color=self.inputs[0].default_value

    specular_sampling_weight : bpy.props.FloatProperty(default=1.0, min=0.0, max=1.0)
    fdr_int: bpy.props.FloatProperty(default=1.9, min=0.0, max=99.0)
    fdr_ext: bpy.props.FloatProperty(default=1.9, min=0.0, max=99.0)

    def init(self, context):
        self.outputs.new('NodeSocketFloat', "Mitsuba2 BSDF Plastic")
        diffuse_reflectance = self.inputs.new('NodeSocketColor', "Diffuse reflectance")
        diffuse_reflectance.default_value=(0.8,0.8,0.8,1.0)

        specular_reflectance = self.inputs.new('NodeSocketColor', "Specular reflectance")
        specular_reflectance.default_value=(1.0,1.0,1.0,1.0)

    def draw(self, context):
        print("draw called")

    def draw_buttons(self, context, layout):
        layout.prop(self, "specular_sampling_weight",text = 'specular sampling weight')
        layout.prop(self, "fdr_int",text = 'Internal IOR')
        layout.prop(self, "fdr_ext",text = 'External IOR')
        
    def draw_label(self):
        return "Mitsuba2 BSDF Plastic"

    def socket_value_update(self,context):
        print("Socket value changed..")

    def update(self):
        print("update(self) is called")

# Derived from the Node base type.
class MitsubaBSDF_Diffuse(Node, MitsubaTreeNode):
    '''A custom node'''
    bl_idname = 'MitsubaBSDFDiffuse'
    bl_label = 'Mitsuba2 BSDF Diffuse'
    bl_icon = 'INFO'

    def uda(self, context):
        self.update()
    
    #@classmethod
    #def poll(cls, ntree):
        #b = False
        #if ntree.bl_idname == 'ShaderNodeTree':
            #b = True
        #return b

    #def poll(cls, ntree):
    #    b = False
    #    # Make your node appear in different node trees by adding their bl_idname type here.
    #    if ntree.bl_idname == 'ShaderNodeTree': b = True
    #    return b

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

    def init(self, context):
        self.outputs.new('NodeSocketFloat', "Mitsuba2 BSDF Diffuse")
        reflectance = self.inputs.new('NodeSocketColor', "reflectance")
        reflectance.default_value=(0.8,0.8,0.8,1.0)

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
    nodeitems_utils.register_node_categories("MITSUBA2_CUSTOM_NODES", Mitsuba_node_categories)

def unregister():
    nodeitems_utils.unregister_node_categories("MITSUBA2_CUSTOM_NODES")