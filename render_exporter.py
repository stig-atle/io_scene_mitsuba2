import bpy
import bmesh
import os
import math
from math import *
import mathutils
from mathutils import Vector
import shutil

#render engine custom begin
class MitsubaRenderEngine(bpy.types.RenderEngine):
    bl_idname = 'Mitsuba2_Renderer'
    bl_label = 'Mitsuba2_Renderer'
    bl_use_preview = False
    bl_use_material = True
    bl_use_shading_nodes = False
    bl_use_shading_nodes_custom = False
    bl_use_texture_preview = True
    bl_use_texture = True
    

    def render(self, scene):
        self.report({'ERROR'}, "Use export function in Mitsuba2 panel.")
        
from bl_ui import properties_render
from bl_ui import properties_material
for member in dir(properties_render):
    subclass = getattr(properties_render, member)
    try:
        subclass.COMPAT_ENGINES.add('Mitsuba2_Renderer')
    except:
        pass

for member in dir(properties_material):
    subclass = getattr(properties_material, member)
    try:
        subclass.COMPAT_ENGINES.add('Mitsuba2_Renderer')
    except:
        pass

bpy.utils.register_class(MitsubaRenderEngine)
exportedMaterials = list()
exportedTextures = list()
#Camera code:
#https://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix
def measure(first, second):
    locx = second[0] - first[0]
    locy = second[1] - first[1]
    locz = second[2] - first[2]

    distance = sqrt((locx)**2 + (locy)**2 + (locz)**2)
    return distance

def export_point_lights(scene_file, scene):
    
    for object in scene.objects:
        
        if object is not None and object.type == 'LIGHT':
            #bpy.context.scene.objects.active = object
            print('\nTrying to export point light: ' + object.name + ' Type: ' + object.type)
            la = object.data
            print('Light TYPE: ' + la.type)
            if la.type == "POINT" :
                print('\n\nexporting lamp: ' + object.name + ' - type: ' + object.type)
                print('\nExporting point light: ' + object.name)
                #bpy.ops.object.select_all(action='DESELECT')
                scene_file.write("\t<emitter type = \"point\" >\n")
                #TODO: Fix so that lamp GUI shows up when mitsuba2 is selected as renderer.
                scene_file.write("\t\t<spectrum name=\"intensity\" value=\"%s\"/>\n" %(la.energy))
                scene_file.write("\t\t<transform name=\"to_world\">\n")
                from_point=object.matrix_world.col[3]
                scene_file.write("\t\t\t<translate value=\"%s, %s, %s\"/>\n" % (from_point.x, from_point.y, from_point.z))
                scene_file.write("\t\t</transform>\n")
                scene_file.write("\t</emitter>\n")

    return ''

def export_camera(scene_file):
    print("Fetching camera..")
    cam_ob = bpy.context.scene.camera
    if cam_ob is None:
        print("no scene camera,aborting")
        self.report({'ERROR'}, "No camera in scene, aborting")
    elif cam_ob.type == 'CAMERA':
        print("regular scene cam")
        print("render res: ", bpy.data.scenes['Scene'].render.resolution_x , " x ", bpy.data.scenes['Scene'].render.resolution_y)
        print("Exporting camera: ", cam_ob.name)

        # https://blender.stackexchange.com/questions/13738/how-to-calculate-camera-direction-and-up-vector/13739#13739
        # https://www.randelshofer.ch/jpbrt/javadoc/org/jpbrt/io/package-summary.html#Cameras
        # https://blender.stackexchange.com/questions/16493/is-there-a-way-to-fit-the-viewport-to-the-current-field-of-view
        # https://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix
        # https://github.com/Volodymyrk/pbrtMayaPy/blob/master/PBRT/ExportModules/Camera.py
        # https://github.com/mmp/pbrt-v2/blob/master/exporters/blender/pbrtBlend.py
        # https://blenderartists.org/forum/showthread.php?268039-Converting-camera-orientation-to-up-vector-and-line-of-sight-vector


        cameramatrix = cam_ob.matrix_world.copy()
        matrixTransposed = cameramatrix.transposed()
        up_point = matrixTransposed[1]

        from_point=cam_ob.matrix_world.col[3]
        at_point=cam_ob.matrix_world.col[2]
        at_point=at_point * -1
        at_point=at_point + from_point

        scene_file.write('\t<sensor type="thinlens">\n')
        export_film(scene_file)
        # https://blender.stackexchange.com/questions/14745/how-do-i-change-the-focal-length-of-a-camera-with-python
        fov = bpy.data.cameras[0].angle * 180 / math.pi
        scene_file.write('<float name="fov" value="%s"/>\n' % fov)
        
        if bpy.data.scenes['Scene'].dofLookAt is not None:
            scene_file.write('<float name="focus_distance" value="%s"/>\n' % (measure(cam_ob.matrix_world.translation, bpy.data.scenes['Scene'].dofLookAt.matrix_world.translation)))
            scene_file.write('<float name="aperture_radius" value="%s"/>\n' % (bpy.data.scenes['Scene'].lensradius))
        else:
            scene_file.write('<float name="aperture_radius" value="0.0"/>\n')

        #Write out the sampler for the image.
        scene_file.write('\t\t<sampler type="independent">\n')
        scene_file.write('\t\t<integer name="sample_count" value="%s"/>\n' % bpy.data.scenes[0].spp)
        scene_file.write('\t\t</sampler>\n')
        
        scene_file.write('\t\t<transform name="to_world">\n')
        scene_file.write('\t\t\t<lookat\n origin="%s, %s, %s"\n target="%s, %s, %s"\n up="%s, %s, %s"\n/>\n' % \
                        (from_point.x, from_point.y, from_point.z, \
                         at_point.x, at_point.y, at_point.z, \
                         up_point[0],up_point[1],up_point[2]))
        scene_file.write('\t\t</transform>\n')
        scene_file.write('\t</sensor>\n')

    return ''

def export_film(scene_file):
    scene_file.write('<film type="hdrfilm">\n')
    scene_file.write('<integer name="width" value="%s"/>\n' % bpy.data.scenes[0].resolution_x)
    scene_file.write('<integer name="height" value="%s"/>\n' % bpy.data.scenes[0].resolution_y)
    scene_file.write('<string name="file_format" value = "openexr"/>\n')
    scene_file.write('</film>\n')
    return ''

def scene_begin(scene_file):
    scene_file.write('<scene version="2.0.0">\n')
    scene_file.write("\n\n")
    return ''

def scene_end(scene_file):
    scene_file.write("</scene>")
    scene_file.write("\n")
    return ''

def export_EnviromentMap(scene_file):
    if bpy.data.scenes[0].environmentmaptpath != "":
        environmentMapFileName= getTextureInSlotName(bpy.data.scenes[0].environmentmaptpath)
        
        #Copy the file by getting the full filepath:
        srcfile = bpy.path.abspath(bpy.data.scenes[0].environmentmaptpath)
        dstdir = bpy.path.abspath(bpy.data.scenes[0].exportpath + 'textures/' + environmentMapFileName)
        print("os.path.dirname...")
        print(os.path.dirname(srcfile))
        print("\n")
        print("srcfile: ")
        print(srcfile)
        print("\n")
        print("dstdir: ")
        print(dstdir)
        print("\n")
        print("File name is :")
        print(environmentMapFileName)
        print("Copying environment texture from source directory to destination directory.")
        shutil.copyfile(srcfile, dstdir)

        environmentmapscaleValue = bpy.data.scenes[0].environmentmapscale
        scene_file.write("\t<emitter type = \"envmap\" >\n")
        scene_file.write('<string name="filename" value="textures/%s"/>\n' % (environmentMapFileName))
        scene_file.write('\t\t\t<float name="scale" value="%s"/>\n' % (environmentmapscaleValue))
        scene_file.write("\t</emitter>\n")

def export_texture_from_input (scene_file, inputSlot):
    textureName = ""
    links = inputSlot.links
    print('Number of links: ')
    print(len(links))
    for x in inputSlot.links:
        textureName = x.from_node.image.name
        #If the texture has not been defined yet - we export it
        if x.from_node.image.name not in exportedTextures:
            exportedTextures.append(x.from_node.image.name)
            print("Checking input named: " + inputSlot.name)
            #if x == inputSlotName:
            print("Has a image named:" + x.from_node.image.name)
            print("at path: " + bpy.path.abspath(x.from_node.image.filepath))
            #print("going to named node:" + x.from_node.image.name)
            print("going to type node:" + x.from_node.type)
            shutil.copyfile(bpy.path.abspath(x.from_node.image.filepath), bpy.path.abspath(bpy.data.scenes[0].exportpath + 'textures/' + x.from_node.image.name))
            scene_file.write('<texture type="bitmap" id="%s">\n' % x.from_node.image.name)
            scene_file.write('<string name="filename" value="textures/%s"/>\n' % x.from_node.image.name)
            scene_file.write('<transform name="to_uv">\n')
            scene_file.write('</transform>\n')
            scene_file.write('</texture>\n')
    return textureName

def export_mitsuba_conductor_material (scene_file, mat, materialName):
    
    specular_reflectance_texture_name = ""
    specular_reflectance_texture_name = export_texture_from_input(scene_file,mat.inputs[0])
    
    if mat.roughness:
        scene_file.write('<bsdf type="roughconductor" id="%s">\n' % materialName)
        scene_file.write('<float name="alpha_u" value="%s"/>\n' % mat.alpha_u)
        scene_file.write('<float name="alpha_v" value="%s"/>\n' % mat.alpha_v)
    else:
        scene_file.write('<bsdf type="conductor" id="%s">\n' % materialName)

    if specular_reflectance_texture_name == "" :
        scene_file.write('<rgb name="specular_reflectance" value="%s %s %s"/>\n' %(mat.inputs[0].default_value[0], mat.inputs[0].default_value[1], mat.inputs[0].default_value[2]))
    else:
        scene_file.write('<ref id="%s" name="specular_reflectance"/>\n' %(specular_reflectance_texture_name))

    scene_file.write('<string name="material" value="%s"/>\n' %(mat.named_preset))
    scene_file.write('</bsdf>\n')
    return ''

def export_mitsuba_blend_material (scene_file, mat, materialName):
    print("Exporting blend material node!")
    
    slot1Name = ""
    slot2Name = ""
    #Define the material nodes assigned before we export the blend.
    links = mat.inputs[1].links
    print('Number of links in slot1: ')
    print(len(links))
    for x in mat.inputs[1].links:
        slot1Name = x.from_node.name
        if x.from_node.name not in exportedMaterials:
            export_material_node(scene_file,x.from_node, x.from_node.name)
            exportedMaterials.append(slot1Name)
    
    links = mat.inputs[2].links
    print('Number of links in slot2: ')
    print(len(links))
    for x in mat.inputs[2].links:
        slot2Name = x.from_node.name
        if x.from_node.name not in exportedMaterials:
            export_material_node(scene_file, x.from_node, x.from_node.name)
            exportedMaterials.append(slot2Name)

    blend_texture_name = ""
    blend_texture_name = export_texture_from_input(scene_file,mat.inputs[0])
    if blend_texture_name != "" and slot1Name != "" and slot2Name != "" :
        scene_file.write('<bsdf type="blendbsdf" id="%s">\n' % materialName)
        scene_file.write('<texture name="weight" type="bitmap">\n')
        scene_file.write('<boolean name="raw" value="true"/>\n')
        scene_file.write('<string name="filename" value="textures/%s"/>\n' %(blend_texture_name))
        scene_file.write('<transform name="to_uv">\n')
        scene_file.write('</transform>\n')
        scene_file.write('</texture>\n')
        scene_file.write('<ref id="%s"/>\n' % slot1Name)
        scene_file.write('<ref id="%s"/>\n' % slot2Name)
        scene_file.write('</bsdf>\n')
    


    return ''

def export_mitsuba_blackbody_material (scene_file, mat, materialName):
    scene_file.write('<emitter type="area" id="%s">\n' % materialName)
    scene_file.write('<spectrum type="blackbody" name="radiance">\n')
    scene_file.write('<float name="temperature" value="%s"/>\n' %(mat.temperature))
    scene_file.write('</spectrum>\n')
    scene_file.write('</emitter>\n')
    return ''

def export_medium(scene_file, inputNode):
    if inputNode is not None:
        for node_links in inputNode.links:
            if node_links.from_node.bl_idname == "MitsubaBSDFMedium":
                myNode = node_links.from_node
                scene_file.write('<medium type="homogeneous" name="interior">\n')
                scene_file.write('<rgb name="sigma_t" value="%s, %s, %s"/>\n' %(myNode.sigma_t[0], myNode.sigma_t[1], myNode.sigma_t[2]))
                scene_file.write('<rgb name="albedo" value="%s, %s, %s"/>\n' %(myNode.albedo[0], myNode.albedo[1], myNode.albedo[2]))
                scene_file.write('<float name="density" value="%s"/>\n' %(myNode.density))
                scene_file.write('</medium>\n')
    return ''

#TODO: Add alpha, alpha_u, alpha_v parameters
def export_mitsuba_bsdf_dielectric_material (scene_file, mat, materialName):

    specular_reflectance_texture_name = ""
    specular_reflectance_texture_name = export_texture_from_input(scene_file,mat.inputs[0])
    
    specular_transmittance_texture_name = ""
    specular_transmittance_texture_name = export_texture_from_input(scene_file,mat.inputs[1])

    if (mat.roughness == False):
        scene_file.write('<bsdf type="dielectric" id="%s">\n' % materialName)
    else:
        scene_file.write('<bsdf type="roughdielectric" id="%s">\n' % materialName)
        scene_file.write('<float name="alpha" value="%s"/>\n' %(mat.alpha))
        scene_file.write('<string name="distribution" value="%s"/>\n' %(mat.distributionModel))
    
    if (mat.use_internal_ior == False):
        scene_file.write('<float name="int_ior" value="%s"/>\n' %(mat.fdr_int))
    else:
        scene_file.write('<string name="int_ior" value="%s"/>\n' %(mat.ior_internal_preset))

    if(mat.use_external_ior == False):
        scene_file.write('<float name="ext_ior" value="%s"/>\n' %(mat.fdr_ext))
    else:
        scene_file.write('<string name="ext_ior" value="%s"/>\n' %(mat.ior_external_preset))

    if specular_reflectance_texture_name == "" :
        scene_file.write('<rgb name="specular_reflectance" value="%s %s %s"/>\n' %(mat.inputs[0].default_value[0], mat.inputs[0].default_value[1], mat.inputs[0].default_value[2]))
    else:
        scene_file.write('<ref id="%s" name="specular_reflectance"/>\n' %(specular_reflectance_texture_name))
    
    if specular_transmittance_texture_name == "":
        scene_file.write('<rgb name="specular_transmittance"  value="%s, %s, %s"/>\n' %(mat.inputs[1].default_value[0], mat.inputs[1].default_value[1], mat.inputs[1].default_value[2]))
    else:
        scene_file.write('<ref id="%s" name="specular_transmittance"/>\n' %(specular_transmittance_texture_name))

    scene_file.write('</bsdf>\n')
    
    return ''

def export_mitsuba_bsdf_plastic_material (scene_file, mat, materialName):
    diffuse_reflectance_texture_name = ""
    diffuse_reflectance_texture_name = export_texture_from_input(scene_file,mat.inputs[0])
    
    specular_reflectance_texture_name = ""
    specular_reflectance_texture_name = export_texture_from_input(scene_file,mat.inputs[1])

    scene_file.write('<bsdf type="plastic" id="%s">\n' % materialName)
    
    if diffuse_reflectance_texture_name == "" :
        scene_file.write('<rgb name="diffuse_reflectance" value="%s %s %s"/>\n' %(mat.inputs[0].default_value[0], mat.inputs[0].default_value[1], mat.inputs[0].default_value[2]))
    else:
        scene_file.write('<ref id="%s" name="diffuse_reflectance"/>\n' %(diffuse_reflectance_texture_name))

    if specular_reflectance_texture_name == "":
        scene_file.write('<rgb name="specular_reflectance"  value="%s, %s, %s"/>\n' %(mat.inputs[1].default_value[0], mat.inputs[1].default_value[1], mat.inputs[1].default_value[2]))
    else:
        scene_file.write('<ref id="%s" name="specular_reflectance"/>\n' %(specular_reflectance_texture_name))
    
    scene_file.write('<float name="int_ior" value="%s"/>\n' %(mat.fdr_int))
    scene_file.write('<float name="ext_ior" value="%s"/>\n' %(mat.fdr_ext))
    scene_file.write('</bsdf>\n')
    return ''


def export_mitsuba_bsdf_diffuse_material (scene_file, mat, materialName):
    print('Currently exporting Mitsuba BSDF diffuse material')
    print (mat.name)
    
    mat.use_nodes = True
    reflectanceTextureName = ""
    reflectanceTextureName = export_texture_from_input(scene_file,mat.inputs[0])
    
    scene_file.write('<bsdf type="diffuse" id="%s">\n' % materialName)
    if reflectanceTextureName == "" :
        scene_file.write('<rgb name="reflectance" value="%s %s %s"/>\n' %(mat.inputs[0].default_value[0], mat.inputs[0].default_value[1], mat.inputs[0].default_value[2]))
    else:
        scene_file.write('<ref id="%s" name="reflectance"/>\n' %(reflectanceTextureName))
    scene_file.write('</bsdf>\n')
    return ''

def getTextureInSlotName(textureSlotParam):
    srcfile = textureSlotParam
    head, tail = os.path.split(srcfile)
    print("File name is :")
    print(tail)

    return tail

def exportObject_medium(scene_file, material):
    if material is None:
        print("no material on object")
        return ''

    print ('Exporting material named: ', material.name)

    if material and material.use_nodes:
        print('Exporting materal named: ', material.name)
        
        #Find the surface output node, then export the connected medium.
        for node in material.node_tree.nodes:
            if node.name == 'Material Output':
                export_medium(scene_file,node.inputs[1])
    return ''

def export_material_node(scene_file,currentMaterial, materialName):
    print("export_material_node : " + currentMaterial.name)
    #print("export_material_node bl_idname :" + currentMaterial.bl_idname)
    if currentMaterial.bl_idname == 'MitsubaBSDFDiffuse':
        export_mitsuba_bsdf_diffuse_material(scene_file,currentMaterial, materialName)
    if currentMaterial.bl_idname == 'MitsubaBSDFPlastic':
        export_mitsuba_bsdf_plastic_material(scene_file,currentMaterial, materialName)
    if currentMaterial.bl_idname == 'MitsubaBSDFDielectric':
        export_mitsuba_bsdf_dielectric_material(scene_file,currentMaterial, materialName)
    if currentMaterial.bl_idname == 'MitsubaBlackBody':
        export_mitsuba_blackbody_material(scene_file,currentMaterial,materialName)
    if currentMaterial.bl_idname == 'MitsubaBSDFConductor':
        export_mitsuba_conductor_material(scene_file,currentMaterial,materialName)
    if currentMaterial.bl_idname == 'MitsubaBSDFBlend':
        export_mitsuba_blend_material(scene_file, currentMaterial, materialName)
    return ''

def export_material(scene_file, material):
    if material is None:
        print("no material on object")
        return ''

    print ('Exporting material named: ', material.name)
    global hastexture
    hastexture = False
    currentMaterial = None
    material.use_nodes = True
    if material and material.use_nodes: #if it is using nodes
        print('Exporting materal named: ', material.name)
        #Find the surface output node, then export the connected material
        for node in material.node_tree.nodes:
            if node.name == 'Material Output':
                for input in node.inputs:
                    for node_links in input.links:
                        currentMaterial =  node_links.from_node
                        export_material_node(scene_file,currentMaterial, material.name)
    return''

def createDefaultExportDirectories(scene_file, scene):
    texturePath = bpy.path.abspath(bpy.data.scenes[0].exportpath + 'textures')
    print("Exporting textures to: ")
    print(texturePath)

    if not os.path.exists(texturePath):
        print('Texture directory did not exist, creating: ')
        print(texturePath)
        os.makedirs(texturePath)

def export_gometry_as_obj(scene_file, scene):
    objects = bpy.data.objects
    for object in objects:
        print("exporting:")
        print(object.name)

        for i in range(len(object.material_slots)):
            material = object.material_slots[i].material
            if material.name not in exportedMaterials:
                export_material(scene_file, material)
                exportedMaterials.append(material.name)

        if object is not None and object.type != 'CAMERA' and object.type == 'MESH':
            bpy.ops.object.select_all(action="DESELECT")
            object.select_set(True) # 2.8+ selection method.

            objFilePath = bpy.data.scenes[0].exportpath + 'meshes/' + object.name + '.obj'
            objFolderPath = bpy.data.scenes[0].exportpath + 'meshes/'
            if not os.path.exists(objFolderPath):
                print('Meshes directory did not exist, creating: ')
                print(objFolderPath)
                os.makedirs(objFolderPath)

            bpy.ops.export_scene.obj(filepath=objFilePath, use_selection=True, axis_forward='Y', axis_up='Z', use_materials=False)
            
            scene_file.write('<shape type="obj">\n')
            scene_file.write('<string name="filename" value="meshes/%s"/>\n' % (object.name + '.obj'))
            scene_file.write('<ref id="%s"/>\n' % object.material_slots[i].material.name)
            exportObject_medium(scene_file, object.material_slots[0].material)
            scene_file.write('</shape>\n')
    return ''
            

def export_integrator(scene_file, scene):
    
    scene_file.write('<integrator type="%s">\n' % (scene.integrators))
    if scene.integrators == 'path':
        scene_file.write('<integer name="max_depth" value="%s"/>\n' %((bpy.data.scenes[0].path_integrator_max_depth)))
        scene_file.write('<integer name="rr_depth" value="%s"/>\n' %((bpy.data.scenes[0].path_integrator_rr_depth)))
        
        if scene.path_integrator_hide_emitters :
            scene_file.write('<boolean name="hide_emitters" value="true"/>\n')
        else:
            scene_file.write('<boolean name="hide_emitters" value="false"/>\n')

    if scene.integrators == 'volpathsimple':
        scene_file.write('<integer name="max_depth" value="%s"/>\n' %((bpy.data.scenes[0].path_integrator_max_depth)))
        scene_file.write('<integer name="rr_depth" value="%s"/>\n' %((bpy.data.scenes[0].path_integrator_rr_depth)))

    if scene.integrators == 'volpath':
        scene_file.write('<integer name="max_depth" value="%s"/>\n' %((bpy.data.scenes[0].path_integrator_max_depth)))
        scene_file.write('<integer name="rr_depth" value="%s"/>\n' %((bpy.data.scenes[0].path_integrator_rr_depth)))

    if scene.integrators == 'direct':
        scene_file.write('<integer name="emitter_samples" value="%s"/>\n' %((bpy.data.scenes[0].direct_integrator_emitter_samples)))
        scene_file.write('<integer name="bsdf_samples" value="%s"/>\n' %((bpy.data.scenes[0].direct_integrator_bsdf_samples)))

    scene_file.write('</integrator>\n')

    return ''

def export_Mitsuba(filepath, scene , frameNumber):
    out = os.path.join(filepath, "test" + frameNumber +".xml")
    if not os.path.exists(filepath):
        print('Output directory did not exist, creating: ')
        print(filepath)
        os.makedirs(filepath)

    with open(out, 'w') as scene_file:
        exportedMaterials.clear()
        exportedTextures.clear()
        createDefaultExportDirectories(scene_file,scene)
        scene_begin(scene_file)
        export_integrator(scene_file, scene)
        export_camera(scene_file)
        export_EnviromentMap(scene_file)
        export_point_lights(scene_file,scene)
        export_gometry_as_obj(scene_file,scene)
        scene_end(scene_file)
        scene_file.close()
