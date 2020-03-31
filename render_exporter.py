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

#Camera code:
#https://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix
def measure(first, second):
    locx = second[0] - first[0]
    locy = second[1] - first[1]
    locz = second[2] - first[2]

    distance = sqrt((locx)**2 + (locy)**2 + (locz)**2)
    return distance

def export_spot_lights(scene_file, scene):
    for ob in scene.objects:
            print('OB TYPE: ' + ob.type)
            if ob.type == "LIGHT" :
                la = ob.data
                print('LA TYPE: ' + la.type)
                if la.type == "SPOT" :
                    # Example:
                    # LightSource "spot" "point from" [0 5 9] "point to" [-5 2.75 0] "blackbody I" [5500 125]
                    print('\n\nexporting light: ' + la.name + ' - type: ' + la.type)
                    #spotmatrix = ob.matrix_world.copy()
                    #matrixTransposed = spotmatrix.transposed()
                    from_point=ob.matrix_world.col[3]
                    at_point=ob.matrix_world.col[2]
                    at_point=at_point * -1
                    at_point=at_point + from_point
                    scene_file.write("AttributeBegin\n")
                    scene_file.write(" LightSource \"spot\"\n \"point from\" [%s %s %s]\n \"point to\" [%s %s %s]\n" % (from_point.x, from_point.y, from_point.z,at_point.x, at_point.y, at_point.z))
                    
                    #TODO: Parse the values from the light \ color and so on. also add falloff etc.
                    scene_file.write("\"blackbody I\" [5500 125]\n")

                    scene_file.write("AttributeEnd\n\n")
    return ''

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
                bpy.ops.object.select_all(action='DESELECT')
                
                
                scene_file.write("\t<emitter type = \"point\" >\n")
                scene_file.write("\t\t<transform name=\"to_world\">\n")
                from_point=object.matrix_world.col[3]
                scene_file.write("\t\t\t<translate value=\"%s, %s, %s\"/>\n" % (from_point.x, from_point.y, from_point.z))
                scene_file.write("\t\t</transform>\n")
                scene_file.write("\t</emitter>\n")
            #<emitter type = "point" >
            #    <transform name="to_world">
            #        <translate value="7.358891487121582, -6.925790786743164, 4.958309173583984"/>
            #    </transform>
			#    <!-- intensity="1.0"-->
            #</emitter>

            #scene_file.write("AttributeBegin")
            #scene_file.write("\n")
            #from_point=object.matrix_world.col[3]
            #scene_file.write("Translate\t%s %s %s\n" % (from_point.x, from_point.y, from_point.z))
            #scene_file.write("LightSource \"point\"\n\"rgb I\" [%s %s %s]\n" % (bpy.data.objects[object.name].color[0], bpy.data.objects[object.name].color[1], bpy.data.objects[object.name].color[2]))
            ##scene_file.write("LightSource \"point\"\n\"rgb I\" [%s %s %s]\n" % (nodes["Emission"].inputs[0].default_value[0], nodes["Emission"].inputs[0].default_value[1], nodes["Emission"].inputs[0].default_value[2]))
            #scene_file.write("AttributeEnd")
            #scene_file.write("\n\n")

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

        scene_file.write('\t<sensor type="perspective">\n')
        scene_file.write('\t\t<transform name="to_world">\n')
        scene_file.write('\t\t\t<lookat\n origin="%s, %s, %s"\n target="%s, %s, %s"\n up="%s, %s, %s"\n/>\n' % \
                        (from_point.x, from_point.y, from_point.z, \
                         at_point.x, at_point.y, at_point.z, \
                         up_point[0],up_point[1],up_point[2]))
        scene_file.write('\t\t</transform>\n')
        scene_file.write('\t</sensor>\n')

        #https://blender.stackexchange.com/questions/14745/how-do-i-change-the-focal-length-of-a-camera-with-python
       # fov = bpy.data.cameras[0].angle * 180 / math.pi * bpy.data.scenes['Scene'].render.resolution_y / bpy.data.scenes['Scene'].render.resolution_x
       # scene_file.write('Camera "perspective"\n')
       # scene_file.write('"float fov" [%s]\n' % (fov))

       # if bpy.data.scenes['Scene'].dofLookAt is not None:
       #     scene_file.write('"float lensradius" [%s]\n' % (bpy.data.scenes['Scene'].lensradius))
       #     scene_file.write('"float focaldistance" [%s]\n\n' % (measure(cam_ob.matrix_world.translation, bpy.data.scenes['Scene'].dofLookAt.matrix_world.translation)))
    return ''

def export_film(scene_file, frameNumber):
    outputFileName = os.path.splitext(os.path.basename(bpy.data.scenes[0].outputfilename))
    print("Outputfilename:")
    print(outputFileName[0])
    print(outputFileName[1])

    finalFileName = outputFileName[0] + frameNumber  + outputFileName[1]
    scene_file.write(r'Film "image" "integer xresolution" [%s] "integer yresolution" [%s] "string filename" "%s"' % (bpy.data.scenes[0].resolution_x, bpy.data.scenes[0].resolution_y, finalFileName))
    scene_file.write("\n")

    scene_file.write(r'PixelFilter "%s" "float xwidth" [%s] "float ywidth" [%s] ' % (bpy.data.scenes[0].filterType, bpy.data.scenes[0].filter_x_width, bpy.data.scenes[0].filter_y_width))
    if bpy.data.scenes[0].filterType == 'sinc':
        scene_file.write(r'"float tau" [%s]' % (bpy.data.scenes[0].filter_tau))
    if bpy.data.scenes[0].filterType == 'mitchell':
        scene_file.write(r'"float B" [%s]' % (bpy.data.scenes[0].filter_b))
        scene_file.write(r'"float C" [%s]' % (bpy.data.scenes[0].filter_c))
    if bpy.data.scenes[0].filterType == 'gaussian':
        scene_file.write(r'"float alpha" [%s]' % (bpy.data.scenes[0].filter_alpha))
    scene_file.write("\n")

    scene_file.write(r'Accelerator "%s" ' % (bpy.data.scenes[0].accelerator))
    scene_file.write("\n")
    if  bpy.data.scenes[0].accelerator == 'kdtree':
        scene_file.write('"integer intersectcost" [%s]\n' % (bpy.data.scenes['Scene'].kdtreeaccel_intersectcost))
        scene_file.write('"integer traversalcost" [%s]\n' % (bpy.data.scenes['Scene'].kdtreeaccel_traversalcost))
        scene_file.write('"float emptybonus" [%s]\n' % (bpy.data.scenes['Scene'].kdtreeaccel_emptybonus))
        scene_file.write('"integer maxprims" [%s]\n' % (bpy.data.scenes['Scene'].kdtreeaccel_maxprims))
        scene_file.write('"integer maxdepth" [%s]\n' % (bpy.data.scenes['Scene'].kdtreeaccel_maxdepth))
    if bpy.data.scenes[0].accelerator == 'bvh':
        scene_file.write(r'"string splitmethod" "%s"' % (bpy.data.scenes[0].splitmethod))
        scene_file.write("\n")
        scene_file.write('"integer maxnodeprims" [%s]\n' % (bpy.data.scenes['Scene'].maxnodeprims))
    return ''

def export_sampler(scene_file):
    scene_file.write(r'Sampler "%s"'% (bpy.data.scenes[0].sampler))
    scene_file.write("\n")

    if bpy.data.scenes[0].sampler == 'halton':
        scene_file.write(r'"integer pixelsamples" [%s]'% (bpy.data.scenes[0].spp))
        scene_file.write("\n")
        if bpy.data.scenes[0].samplepixelcenter:
            scene_file.write(r'"bool samplepixelcenter" "true"')
        else:
            scene_file.write(r'"bool samplepixelcenter" "false"')
        scene_file.write("\n")

    if bpy.data.scenes[0].sampler == 'maxmin':
        scene_file.write(r'"integer pixelsamples" [%s]'% (bpy.data.scenes[0].spp))
        scene_file.write("\n")
        scene_file.write(r'"integer dimensions" [%s]'% (bpy.data.scenes[0].dimension))
        scene_file.write("\n")

    if bpy.data.scenes[0].sampler == 'random':
        scene_file.write(r'"integer pixelsamples" [%s]'% (bpy.data.scenes[0].spp))
        scene_file.write("\n")

    if bpy.data.scenes[0].sampler == 'sobol':
        scene_file.write(r'"integer pixelsamples" [%s]'% (bpy.data.scenes[0].spp))
        scene_file.write("\n")

    if bpy.data.scenes[0].sampler == 'lowdiscrepancy':
        scene_file.write(r'"integer pixelsamples" [%s]'% (bpy.data.scenes[0].spp))
        scene_file.write("\n")
        scene_file.write(r'"integer dimensions" [%s]'% (bpy.data.scenes[0].dimension))
        scene_file.write("\n")

    if bpy.data.scenes[0].sampler == 'stratified':
        scene_file.write(r'"integer xsamples" [%s]'% (bpy.data.scenes[0].xsamples))
        scene_file.write("\n")
        scene_file.write(r'"integer ysamples" [%s]'% (bpy.data.scenes[0].ysamples))
        scene_file.write("\n")
        scene_file.write(r'"integer dimensions" [%s]'% (bpy.data.scenes[0].dimension))
        scene_file.write("\n")
        if bpy.data.scenes[0].jitter:
            scene_file.write(r'"bool jitter" "true"')
        else:
            scene_file.write(r'"bool jitter" "false"')
        scene_file.write("\n")

    return ''

def export_integrator(scene_file, scene):
    scene_file.write(r'Integrator "%s"' % (bpy.data.scenes[0].integrators))
    scene_file.write("\n")
    scene_file.write(r'"integer maxdepth" [%s]' % (bpy.data.scenes[0].maxdepth))
    scene_file.write("\n")

    if scene.integrators == 'bdpt':
        if scene.bdpt_visualizestrategies :
            scene_file.write(r'"bool visualizestrategies" "true"')
            scene_file.write("\n")
        if scene.bdpt_visualizeweights :
            scene_file.write(r'"bool visualizeweights" "true"')
            scene_file.write("\n")

    if scene.integrators == 'mlt':
        scene_file.write(r'"integer bootstrapsamples" [%s]' % (bpy.data.scenes[0].mlt_bootstrapsamples))
        scene_file.write("\n")
        scene_file.write(r'"integer chains" [%s]' % (bpy.data.scenes[0].mlt_chains))
        scene_file.write("\n")
        scene_file.write(r'"integer mutationsperpixel" [%s]' % (bpy.data.scenes[0].mlt_mutationsperpixel))
        scene_file.write("\n")
        scene_file.write(r'"float largestepprobability" [%s]' % (bpy.data.scenes[0].mlt_largestepprobability))
        scene_file.write("\n")
        scene_file.write(r'"float sigma" [%s]' % (bpy.data.scenes[0].mlt_sigma))
        scene_file.write("\n")

    if scene.integrators == 'sppm':
        scene_file.write(r'"integer numiterations" [%s]' % (bpy.data.scenes[0].sppm_numiterations))
        scene_file.write("\n")
        scene_file.write(r'"integer photonsperiteration" [%s]' % (bpy.data.scenes[0].sppm_photonsperiteration))
        scene_file.write("\n")
        scene_file.write(r'"integer imagewritefrequency" [%s]' % (bpy.data.scenes[0].sppm_imagewritefrequency))
        scene_file.write("\n")
        scene_file.write(r'"float radius" [%s]' % (bpy.data.scenes[0].sppm_radius))
        scene_file.write("\n")
    
        

    return ''

def export_LightSampleDistribution(scene_file, scene):
    scene_file.write(r'"string lightsamplestrategy" "%s"' % (bpy.data.scenes[0].lightsamplestrategy))
    scene_file.write("\n")
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
        scene_file.write("AttributeBegin\n")
        scene_file.write(r'LightSource "infinite" "string mapname" "%s" "color scale" [%s %s %s]' % ("textures/" + environmentMapFileName,environmentmapscaleValue,environmentmapscaleValue,environmentmapscaleValue))
        scene_file.write("\n")
        scene_file.write("AttributeEnd")
        scene_file.write("\n\n")

def export_environmentLight(scene_file):
    print("image texture type: ")
    scene_file.write("\n")
    environmenttype = bpy.data.worlds['World'].node_tree.nodes['Background'].inputs['Color'].links[0].from_node.type
    environmentMapPath = ""
    environmentMapFileName = ""
    print(environmenttype)
    scene_file.write("AttributeBegin\n")

    if environmenttype == "TEX_IMAGE":
        print(environmenttype)
        environmentMapPath = bpy.data.worlds['World'].node_tree.nodes['Background'].inputs['Color'].links[0].from_node.image.filepath
        environmentMapFileName= getTextureInSlotName(environmentMapPath)
        print(environmentMapPath)
        print(environmentMapFileName)
        print("background strength: value:")
        backgroundStrength = bpy.data.worlds['World'].node_tree.nodes['Background'].inputs[1].default_value
        print(backgroundStrength)
        scene_file.write(r'LightSource "infinite" "string mapname" "%s" "color scale" [%s %s %s]' % ("textures/" + environmentMapFileName,backgroundStrength,backgroundStrength,backgroundStrength))


    scene_file.write("\n")
    #scene_file.write(r'Rotate 10 0 0 1 Rotate -110 1 0 0 LightSource "infinite" "string mapname" "textures/20060807_wells6_hd.exr" "color scale" [2.5 2.5 2.5]')
    if environmenttype == "RGB":
        print(bpy.data.worlds['World'].node_tree.nodes['Background'].inputs['Color'].default_value[0])
        scene_file.write(r'LightSource "infinite" "color L" [%s %s %s] "color scale" [%s %s %s]' %(bpy.data .worlds['World'].node_tree.nodes['Background'].inputs['Color'].default_value[0],bpy.data .worlds['World'].node_tree.nodes['Background'].inputs['Color'].default_value[1],bpy.data .worlds['World'].node_tree.nodes['Background'].inputs['Color'].default_value[2],backgroundStrength,backgroundStrength,backgroundStrength))

    scene_file.write("\n")
    scene_file.write("AttributeEnd")
    scene_file.write("\n\n")
    return ''

def export_defaultMaterial(scene_file):
    scene_file.write(r'Material "plastic"')
    scene_file.write("\n")
    scene_file.write(r'"color Kd" [.1 .1 .1]')
    scene_file.write("\n")
    scene_file.write(r'"color Ks" [.7 .7 .7] "float roughness" .1')
    scene_file.write("\n\n")
    return ''

def exportTextureInSlotNew(scene_file,textureSlotParam,isFloatTexture):
    scene_file.write("\n")
    srcfile = bpy.path.abspath(textureSlotParam)
    texturefilename = getTextureInSlotName(srcfile)
    if isFloatTexture :
        scene_file.write(r'Texture "%s" "float" "imagemap" "string filename" ["%s"]' % (texturefilename, ("textures/" + texturefilename)))
    else:
        scene_file.write(r'Texture "%s" "color" "imagemap" "string filename" ["%s"]' % (texturefilename, ("textures/" + texturefilename)))

    scene_file.write("\n")
    dstdir = bpy.path.abspath(bpy.data.scenes[0].exportpath + 'textures/' + texturefilename)
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
    print(texturefilename)
    print("Copying texture from source directory to destination directory.")
    shutil.copyfile(srcfile, dstdir)
    return ''

def export_texture_from_input (scene_file, inputSlot, mat, isFloatTexture):
    kdTextureName = ""
    slot = inputSlot
    print(mat)
    print(mat.inputs)
    print(mat.outputs[0].name)
    print(mat.inputs[0].name)
    matnodes = mat.node_tree.nodes
    imgnodes = 0
    imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']
    if (len(imgnodes) == 0):
        print("We have no texture defined, exporting RGB")
        return ""
    else:
        print('number of image nodes connected:')
        print(len(imgnodes))
        print('image nodes')
        print(imgnodes)


    links = mat.node_tree.links
    print('Number of links: ')
    print(len(links))

    #link = next(l for l in links if l.to_socket == slot)
    link = None
    for currentLink in links:
        print(currentLink)
        if currentLink.to_socket == slot:
            print('Found the texture')
            link = currentLink
    
    if link is None:
        return ""
    
    if link:
        print('Current link type:')
        print(link.from_node.type)
        if link.from_node.type == 'TEX_IMAGE':
            image = link.from_node.image
            print('Found image!')
            print(image.name)
            print('At index:')
            kdTextureName  = image.name
            exportTextureInSlotNew(scene_file,image.filepath,isFloatTexture)
    return kdTextureName

def followLinks(node_in):
    for n_inputs in node_in.inputs:
        for node_links in n_inputs.links:
            print("followLinks going from " + node_links.from_node.name)
            followLinks(node_links.from_node)

def followLinksOutput(node_in):
    for n_inputs in node_in.outputs:
        for node_links in n_inputs.links:
            print("followLinks going to " + node_links.to_node.name)
            followLinksOutput(node_links.to_node)

def export_mitsuba_bsdf_material (scene_file, mat, materialName):
    print('Currently exporting Mitsuba BSDF material')
    print (mat.name)
    #print(mat.inputs[0].name)
    #print(mat.KdTexture_node.name)
    #print(mat.inputs[0].links)
    for n in mat.inputs:
        print(n.name)
    
    for n in mat.outputs:
        print(n.name)
    #print(mat.links)
    #followLinks(mat)
    #followLinksOutput(mat)
    
    #nodes = mat.node_tree.nodes
    #print(mat.outputs[0].name)
    #print(mat.inputs[0].name)
    
    scene_file.write('<bsdf type="diffuse" id="%s">\n' % materialName)
    #node_tree.nodes["Mitsuba2 BSDF"].Kd[1]
    
    scene_file.write('<rgb name="reflectance" value="%s %s %s"/>\n' %(mat.inputs[0].default_value[0], mat.inputs[0].default_value[1], mat.inputs[0].default_value[2]))
    #scene_file.write('<rgb name="reflectance" value="%s %s %s"/>\n' %(nodes["Mitsuba2 BSDF"].inputs[0].default_value[0], nodes["Mitsuba2 BSDF"].inputs[0].default_value[1], nodes["Mitsuba2 BSDF"].inputs[0].default_value[2]))
    scene_file.write('</bsdf>\n')
    #New code begin
    #nodes = mat.node_tree.nodes
    #Export used textures BEFORE we define the material itself.
    #kdTextureName = ""
    #kdTextureName = export_texture_from_input(scene_file,mat.inputs[0],mat, False)

    #scene_file.write(r'Material "matte"')
    #scene_file.write("\n")
    #scene_file.write(r'"float sigma" [%s]' %(mat.Sigma))
    #scene_file.write("\n")
    
    #if kdTextureName != "" :
       #scene_file.write(r'"texture %s" "%s"' % ("Kd", kdTextureName))

#    else:
#        scene_file.write(r'"color Kd" [ %s %s %s]' %(mat.Kd[0],mat.Kd[1],mat.Kd[2]))

#    scene_file.write("\n")
    return ''

def export_pbrt_mirror_material (scene_file, mat):
    print('Currently exporting Pbrt mirror material')
    print (mat.name)
    nodes = mat.node_tree.nodes
    
    krTextureName = export_texture_from_input(scene_file,nodes["Pbrt Mirror"].inputs[0],mat,False)

    scene_file.write(r'Material "mirror"')
    scene_file.write("\n")

    if krTextureName != "":
       scene_file.write(r'"texture %s" "%s"' % ("Kr", krTextureName))
    else:
        scene_file.write(r'"color Kr" [ %s %s %s]' %(nodes["Pbrt Mirror"].Kr[0],nodes["Pbrt Mirror"].Kr[1],nodes["Pbrt Mirror"].Kr[2]))
    
    scene_file.write("\n")
    return ''

def export_principled_bsdf_material(scene_file, mat):
    print('Currently exporting principled_bsdf material, converting the material to pbrt disney on export.')
    print (mat.name)
    nodes = mat.node_tree.nodes
    scene_file.write(r'Material "disney"')
    scene_file.write("\n")
    
    scene_file.write(r'"color color" [%s %s %s]' %(nodes["Principled BSDF"].inputs[0].default_value[0], nodes["Principled BSDF"].inputs[0].default_value[1], nodes["Principled BSDF"].inputs[0].default_value[2]))
    scene_file.write("\n")
    scene_file.write(r'"float metallic" [%s]' %(nodes["Principled BSDF"].inputs[4].default_value))
    scene_file.write("\n")
    scene_file.write(r'"float speculartint" [%s]' %(nodes["Principled BSDF"].inputs[6].default_value))
    scene_file.write("\n")
    scene_file.write(r'"float roughness" [%s]' %(nodes["Principled BSDF"].inputs[7].default_value))
    scene_file.write("\n")
    scene_file.write(r'"float sheen" [%s]' %(nodes["Principled BSDF"].inputs[10].default_value))
    scene_file.write("\n")
    scene_file.write(r'"float sheentint" [%s]' %(nodes["Principled BSDF"].inputs[11].default_value))
    scene_file.write("\n")
    scene_file.write(r'"float clearcoat" [%s]' %(nodes["Principled BSDF"].inputs[12].default_value))
    scene_file.write("\n")
    scene_file.write(r'"float difftrans" [%s]' %(nodes["Principled BSDF"].inputs[15].default_value))
    scene_file.write("\n")

    return ''

def export_pbrt_translucent_material(scene_file, mat):
    print('Currently exporting Pbrt Translucent material')
    print (mat.name)

    nodes = mat.node_tree.nodes
    kdTextureName = ""
    kdTextureName = export_texture_from_input(scene_file,nodes["Pbrt Translucent"].inputs[0],mat, False)
    ksTextureName = ""
    ksTextureName = export_texture_from_input(scene_file,nodes["Pbrt Translucent"].inputs[1],mat, False)
    ReflectTextureName = ""
    ReflectTextureName = export_texture_from_input(scene_file,nodes["Pbrt Translucent"].inputs[2],mat, False)
    TransmitTextureName = ""
    TransmitTextureName = export_texture_from_input(scene_file,nodes["Pbrt Translucent"].inputs[3],mat, False)
    
    scene_file.write(r'Material "translucent"')
    scene_file.write("\n")
    scene_file.write(r'"float roughness" [%s]' %(nodes["Pbrt Translucent"].Roughness))
    scene_file.write("\n")
    
    if kdTextureName != "" :
       scene_file.write(r'"texture %s" "%s"' % ("Kd", kdTextureName))
       scene_file.write("\n")
    else:
        scene_file.write(r'"color Kd" [ %s %s %s]' %(nodes["Pbrt Translucent"].Kd[0],nodes["Pbrt Translucent"].Kd[1],nodes["Pbrt Translucent"].Kd[2]))
        scene_file.write("\n")
    if ksTextureName != "" :
       scene_file.write(r'"texture %s" "%s"' % ("Ks", ksTextureName))
       scene_file.write("\n")
    else:
        scene_file.write(r'"color Ks" [ %s %s %s]' %(nodes["Pbrt Translucent"].Ks[0],nodes["Pbrt Translucent"].Ks[1],nodes["Pbrt Translucent"].Ks[2]))
        scene_file.write("\n")
    if ReflectTextureName != "" :
        scene_file.write(r'"texture %s" "%s"' % ("reflect", ReflectTextureName))
        scene_file.write("\n")
    else:
        scene_file.write(r'"color reflect" [ %s %s %s]' %(nodes["Pbrt Translucent"].Reflect[0],nodes["Pbrt Translucent"].Reflect[1],nodes["Pbrt Translucent"].Reflect[2]))
        scene_file.write("\n")
    if TransmitTextureName != "" :
        scene_file.write(r'"texture %s" "%s"' % ("transmit", TransmitTextureName))
        scene_file.write("\n")
    else:
        scene_file.write(r'"color transmit" [ %s %s %s]' %(nodes["Pbrt Translucent"].Transmit[0],nodes["Pbrt Translucent"].Transmit[1],nodes["Pbrt Translucent"].Transmit[2]))
    if nodes["Pbrt Translucent"].Remaproughness == True :
        scene_file.write(r'"bool remaproughness" "true"')
        scene_file.write("\n")
    else:
        scene_file.write(r'"bool remaproughness" "false"')
        scene_file.write("\n")
    return ''

def export_medium(scene_file, inputNode ,nodes):
    if inputNode is not None:
        mediumNode = nodes.get("Pbrt Medium")
        if mediumNode:
            print('We have a node connected to medium slot.')
            print('The name of the connected node is: ')
            print(mediumNode.name)
            scene_file.write(r'MakeNamedMedium "%s"' % (mediumNode.name))
            scene_file.write("\n")
            scene_file.write(r'"string type" ["%s"]' % (mediumNode.Type))
            scene_file.write("\n")
            sigma_a = mediumNode.inputs[0].default_value
            scene_file.write(r'"rgb sigma_a" [ %s %s %s]' %(sigma_a[0],sigma_a[1],sigma_a[2]))
            scene_file.write("\n")
            sigma_s = mediumNode.inputs[1].default_value
            scene_file.write(r'"rgb sigma_s" [ %s %s %s]' %(sigma_s[0],sigma_s[1],sigma_s[2]))
            scene_file.write("\n")
            scene_file.write(r'"float g" [ %s ]' % (mediumNode.g))
            scene_file.write("\n")
            scene_file.write(r'"float scale" [ %s ]' % (mediumNode.Scale))
            scene_file.write("\n")
            scene_file.write("\n")
            return mediumNode.name
    return None

def export_pbrt_glass_material (scene_file, mat):
    print('Currently exporting Pbrt Glass material')
    print (mat.name)
    nodes = mat.node_tree.nodes
    
    krTextureName = export_texture_from_input(scene_file,nodes["Pbrt Glass"].inputs[2],mat,False)
    ktTextureName = export_texture_from_input(scene_file,nodes["Pbrt Glass"].inputs[3],mat,False)
    uRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Glass"].inputs[0],mat,True)
    vRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Glass"].inputs[1],mat, True)

    mediumNodeName = export_medium(scene_file,nodes["Pbrt Glass"].inputs[4],nodes)
    if mediumNodeName is not None:
        scene_file.write(r'MediumInterface "%s" ""' % (mediumNodeName))
        scene_file.write("\n")

    scene_file.write(r'Material "glass"')
    scene_file.write("\n")

    if krTextureName != "":
       scene_file.write(r'"texture %s" "%s"' % ("Kr", krTextureName))
    else:
        scene_file.write(r'"color Kr" [ %s %s %s]' %(nodes["Pbrt Glass"].kr[0],nodes["Pbrt Glass"].kr[1],nodes["Pbrt Glass"].kr[2]))
    scene_file.write("\n")
    
    if ktTextureName != "":
       scene_file.write(r'"texture %s" "%s"' % ("Kt", ktTextureName))
    else:
        scene_file.write(r'"color Kt" [ %s %s %s]' %(nodes["Pbrt Glass"].kt[0],nodes["Pbrt Glass"].kt[1],nodes["Pbrt Glass"].kt[2]))
    scene_file.write("\n")
    
    if(uRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("uroughness", uRoughnessTextureName))
    else:
        scene_file.write(r'"float uroughness" [%s]' %(nodes["Pbrt Glass"].uRoughness))
    scene_file.write("\n")
    
    if (vRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("vroughness", vRoughnessTextureName))
    else:
        scene_file.write(r'"float vroughness" [%s]' %(nodes["Pbrt Glass"].vRoughness))
    scene_file.write("\n")

    scene_file.write(r'"float index" [%s]' %(nodes["Pbrt Glass"].Index))
    scene_file.write("\n")

    return ''

def export_pbrt_substrate_material (scene_file, mat):

    print('Currently exporting Pbrt Substrate material')
    print (mat.name)
    nodes = mat.node_tree.nodes

    uRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Substrate"].inputs[0],mat,True)
    vRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Substrate"].inputs[1],mat, True)
    kdTextureName = export_texture_from_input(scene_file,nodes["Pbrt Substrate"].inputs[2],mat,False)
    ksTextureName = export_texture_from_input(scene_file,nodes["Pbrt Substrate"].inputs[3],mat,False)

    scene_file.write(r'Material "substrate"')
    scene_file.write("\n")

    if(uRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("uroughness", uRoughnessTextureName))
    else:
        scene_file.write(r'"float uroughness" [%s]'\
        %(nodes["Pbrt Substrate"].uRoughness))
    scene_file.write("\n")

    if (vRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("vroughness", vRoughnessTextureName))
    else:
        scene_file.write(r'"float vroughness" [%s]'\
        %(nodes["Pbrt Substrate"].vRoughness))
    scene_file.write("\n")

    if (kdTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Kd", kdTextureName))
    else :
        scene_file.write(r'"color Kd" [ %s %s %s]' %(nodes["Pbrt Substrate"].Kd[0],nodes["Pbrt Substrate"].Kd[1],nodes["Pbrt Substrate"].Kd[2]))
    scene_file.write("\n")

    if (ksTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Ks", ksTextureName))
    else :
        scene_file.write(r'"color Ks" [ %s %s %s]' %(nodes["Pbrt Substrate"].Ks[0],nodes["Pbrt Substrate"].Ks[1],nodes["Pbrt Substrate"].Ks[2]))
    scene_file.write("\n")
    return ''


#TODO: export sigma_a sigma_s texture and color

def export_pbrt_subsurface_material (scene_file, mat):
    print('Currently exporting Pbrt Subsurface material.')
    print (mat.name)
    nodes = mat.node_tree.nodes

    uRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Subsurface"].inputs[0],mat,True)
    vRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Subsurface"].inputs[1],mat, True)
    krTextureName = export_texture_from_input(scene_file,nodes["Pbrt Subsurface"].inputs[2],mat,False)
    ktTextureName = export_texture_from_input(scene_file,nodes["Pbrt Subsurface"].inputs[3],mat,False)

    sigma_aTextureName = export_texture_from_input(scene_file,nodes["Pbrt Subsurface"].inputs[4],mat,False)
    sigma_sTextureName = export_texture_from_input(scene_file,nodes["Pbrt Subsurface"].inputs[5],mat,False)

    mediumNodeName = export_medium(scene_file,nodes["Pbrt Subsurface"].inputs[6],nodes)

    if mediumNodeName is not None:
        scene_file.write(r'MediumInterface "%s" ""' % (mediumNodeName))
        scene_file.write("\n")

    scene_file.write(r'Material "subsurface"')
    scene_file.write("\n")
    if (nodes["Pbrt Subsurface"].presetName != "None"):
        scene_file.write(r'"string name" ["%s"]' % (nodes["Pbrt Subsurface"].presetName))
        scene_file.write("\n")

    scene_file.write(r'"float scale" [%s]'\
    %(nodes["Pbrt Subsurface"].scale))
    scene_file.write("\n")
    scene_file.write(r'"float eta" [%s]'\
    %(nodes["Pbrt Subsurface"].eta))
    scene_file.write("\n")

    if(uRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("uroughness", uRoughnessTextureName))
    else:
        scene_file.write(r'"float uroughness" [%s]'\
        %(nodes["Pbrt Subsurface"].uRoughness))
    scene_file.write("\n")
    if (vRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("vroughness", vRoughnessTextureName))
    else:
        scene_file.write(r'"float vroughness" [%s]'\
        %(nodes["Pbrt Subsurface"].vRoughness))
    scene_file.write("\n")

    if (krTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Kr", krTextureName))
    else :
            if (nodes["Pbrt Subsurface"].presetName == "None"):
                scene_file.write(r'"color Kr" [ %s %s %s]' %(nodes["Pbrt Subsurface"].kr[0],nodes["Pbrt Subsurface"].kr[1],nodes["Pbrt Subsurface"].kr[2]))
    scene_file.write("\n")

    if (ktTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Kt", ktTextureName))
    else :
            if (nodes["Pbrt Subsurface"].presetName == "None"):
                scene_file.write(r'"color Kt" [ %s %s %s]' %(nodes["Pbrt Subsurface"].kt[0],nodes["Pbrt Subsurface"].kt[1],nodes["Pbrt Subsurface"].kt[2]))
    scene_file.write("\n")
    
    if (nodes["Pbrt Subsurface"].presetName == "None"):
        if (sigma_aTextureName != ""):
            scene_file.write(r'"texture %s" "%s"' % ("Sigma_a", sigma_aTextureName))
        else:
            scene_file.write(r'"color sigma_a" [ %s %s %s]' %(nodes["Pbrt Subsurface"].sigma_a[0],nodes["Pbrt Subsurface"].sigma_a[1],nodes["Pbrt Subsurface"].sigma_a[2]))
        scene_file.write("\n")
        if (sigma_sTextureName != ""):
            scene_file.write(r'"texture %s" "%s"' % ("Sigma_s", sigma_sTextureName))
        else:
            scene_file.write(r'"color sigma_s" [ %s %s %s]' %(nodes["Pbrt Subsurface"].sigma_s[0],nodes["Pbrt Subsurface"].sigma_s[1],nodes["Pbrt Subsurface"].sigma_a[2]))
        scene_file.write("\n")

        if nodes["Pbrt Subsurface"].remaproughness == True :
            scene_file.write(r'"bool remaproughness" "true"')
            scene_file.write("\n")
        else:
            scene_file.write(r'"bool remaproughness" "false"')
            scene_file.write("\n")

        

    return ''

def export_pbrt_uber_material (scene_file, mat):
    print('Currently exporting Pbrt Uber material.')
    print (mat.name)
    nodes = mat.node_tree.nodes
    
    kdTextureName = export_texture_from_input(scene_file,nodes["Pbrt Uber"].inputs[0],mat,False)
    ksTextureName = export_texture_from_input(scene_file,nodes["Pbrt Uber"].inputs[1],mat,False)
    krTextureName = export_texture_from_input(scene_file,nodes["Pbrt Uber"].inputs[2],mat,False)
    ktTextureName = export_texture_from_input(scene_file,nodes["Pbrt Uber"].inputs[3],mat,False)
    uRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Uber"].inputs[4],mat,True)
    vRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Uber"].inputs[5],mat, True)
    opacityTextureName = export_texture_from_input(scene_file,nodes["Pbrt Uber"].inputs[6],mat, True)

    scene_file.write(r'Material "uber"')
    scene_file.write("\n")
    if (kdTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Kd", kdTextureName))
    else :
        scene_file.write(r'"color Kd" [ %s %s %s]' %(nodes["Pbrt Uber"].kd[0],nodes["Pbrt Uber"].kd[1],nodes["Pbrt Uber"].kd[2]))
    scene_file.write("\n")

    if (ksTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Ks", ksTextureName))
    else :
        scene_file.write(r'"color Ks" [ %s %s %s]' %(nodes["Pbrt Uber"].ks[0],nodes["Pbrt Uber"].ks[1],nodes["Pbrt Uber"].ks[2]))
    scene_file.write("\n")
    if (krTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Kr", krTextureName))
    else :
        scene_file.write(r'"color Kr" [ %s %s %s]' %(nodes["Pbrt Uber"].kr[0],nodes["Pbrt Uber"].kr[1],nodes["Pbrt Uber"].kr[2]))
    scene_file.write("\n")
    if (ktTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Kt", ktTextureName))
    else :
        scene_file.write(r'"color Kt" [ %s %s %s]' %(nodes["Pbrt Uber"].kt[0],nodes["Pbrt Uber"].kt[1],nodes["Pbrt Uber"].kt[2]))
    scene_file.write("\n")
    if(uRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("uroughness", uRoughnessTextureName))
    else:
        scene_file.write(r'"float uroughness" [%s]'\
        %(nodes["Pbrt Uber"].uRoughness))
    scene_file.write("\n")
    if (vRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("vroughness", vRoughnessTextureName))
    else:
        scene_file.write(r'"float vroughness" [%s]' %(nodes["Pbrt Uber"].vRoughness))
    scene_file.write("\n")
    if nodes["Pbrt Uber"].eta != 0.0:
        scene_file.write(r'"float eta" [%s]' %(nodes["Pbrt Uber"].eta))
    scene_file.write("\n")
    if (opacityTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("opacity", opacityTextureName))
        scene_file.write("\n")
    return ''


def export_pbrt_plastic_material (scene_file, mat):
    print('Currently exporting Pbrt Plastic material.')
    print (mat.name)
    nodes = mat.node_tree.nodes
    
    kdTextureName = export_texture_from_input(scene_file,nodes["Pbrt Plastic"].inputs[0],mat,False)
    ksTextureName = export_texture_from_input(scene_file,nodes["Pbrt Plastic"].inputs[1],mat,False)
    roughnessTextureName=export_texture_from_input(scene_file,nodes["Pbrt Plastic"].inputs[2],mat,True)

    scene_file.write(r'Material "plastic"')
    scene_file.write("\n")

    if (kdTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Kd", kdTextureName))
    else :
        scene_file.write(r'"color Kd" [ %s %s %s]' %(nodes["Pbrt Plastic"].Kd[0],nodes["Pbrt Plastic"].Kd[1],nodes["Pbrt Plastic"].Kd[2]))
    scene_file.write("\n")

    if (ksTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Ks", ksTextureName))
    else :
        scene_file.write(r'"color Ks" [ %s %s %s]' %(nodes["Pbrt Plastic"].Ks[0],nodes["Pbrt Plastic"].Ks[1],nodes["Pbrt Plastic"].Ks[2]))
    scene_file.write("\n")

    if (roughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("Roughness", roughnessTextureName))
    else:
        scene_file.write(r'"float roughness" [%s]' %(nodes["Pbrt Plastic"].Roughness))
    scene_file.write("\n")

    return ''

def export_pbrt_metal_material (scene_file, mat):
    print('Currently exporting Pbrt Metal material')
    print (mat.name)
    nodes = mat.node_tree.nodes
    etaTextureName = export_texture_from_input(scene_file,nodes["Pbrt Metal"].inputs[0],mat,False)
    kTextureName = export_texture_from_input(scene_file,nodes["Pbrt Metal"].inputs[1],mat,False)
    uRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Metal"].inputs[2],mat,True)
    vRoughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Metal"].inputs[3],mat, True)
    bumpTextureName = export_texture_from_input(scene_file,nodes["Pbrt Metal"].inputs[4],mat, True)

    scene_file.write(r'Material "metal"')
    scene_file.write("\n")

    if (etaTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("eta", etaTextureName))
    else :
        scene_file.write(r'"color eta" [ %s %s %s]' %(nodes["Pbrt Metal"].eta[0],nodes["Pbrt Metal"].eta[1],nodes["Pbrt Metal"].eta[2]))
    scene_file.write("\n")

    if (kTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("k", kTextureName))
    else :
        scene_file.write(r'"color k" [ %s %s %s]' %(nodes["Pbrt Metal"].kt[0],nodes["Pbrt Metal"].kt[1],nodes["Pbrt Metal"].kt[2]))
    scene_file.write("\n")

    scene_file.write(r'"float roughness" [%s]' %(nodes["Pbrt Metal"].roughness))
    scene_file.write("\n")
    
    if(uRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("uroughness", uRoughnessTextureName))
    else:
        scene_file.write(r'"float uroughness" [%s]'\
        %(nodes["Pbrt Metal"].uRoughness))
    scene_file.write("\n")

    if (vRoughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("vroughness", vRoughnessTextureName))
    else:
        scene_file.write(r'"float vroughness" [%s]'\
        %(nodes["Pbrt Metal"].vRoughness))
    scene_file.write("\n")

    if (bumpTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("bumpmap", bumpTextureName))

    return ''

def export_pbrt_disney_material (scene_file, mat):
    print('Currently exporting Pbrt Disney material.')
    print (mat.name)
    nodes = mat.node_tree.nodes

    colorTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[0],mat,False)
    metallicTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[1],mat,True)
    etaTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[2],mat,True)
    roughnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[3],mat,True)
    speculartintTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[4],mat,True)
    anisotropicTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[5],mat,True)
    sheenTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[6],mat,True)
    sheenTintTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[7],mat,True)
    clearCoatTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[8],mat,True)
    clearCoatGlossTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[9],mat,True)
    specTransTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[10],mat,True)
    flatnessTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[11],mat,True)
    diffTransTextureName = export_texture_from_input(scene_file,nodes["Pbrt Disney"].inputs[12],mat,True)

    scene_file.write(r'Material "disney"')
    scene_file.write("\n")
    
    if (colorTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("color", colorTextureName))
    else :    
        scene_file.write(r'"color color" [%s %s %s]' %(nodes["Pbrt Disney"].color[0], nodes["Pbrt Disney"].color[1], nodes["Pbrt Disney"].color[2]))
    scene_file.write("\n")

    if (metallicTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("metallic", metallicTextureName))
    else :
        scene_file.write(r'"float metallic" [%s]' %(nodes["Pbrt Disney"].metallic))
    scene_file.write("\n")

    if (etaTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("eta", etaTextureName))
    else :
        scene_file.write(r'"float eta" [%s]' %(nodes["Pbrt Disney"].eta))
    scene_file.write("\n")

    if (roughnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("roughness", roughnessTextureName))
    else :
        scene_file.write(r'"float roughness" [%s]' %(nodes["Pbrt Disney"].roughness))
    scene_file.write("\n")
    
    if (speculartintTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("speculartint", speculartintTextureName))
    else :
        scene_file.write(r'"float speculartint" [%s]' %(nodes["Pbrt Disney"].specularTint))
    scene_file.write("\n")
    
    if (anisotropicTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("anisotropic", anisotropicTextureName))
    else :
        scene_file.write(r'"float anisotropic" [%s]' %(nodes["Pbrt Disney"].anisotropic))
    scene_file.write("\n")

    if (sheenTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("sheen", sheenTextureName))
    else :
        scene_file.write(r'"float sheen" [%s]' %(nodes["Pbrt Disney"].sheen))
    scene_file.write("\n")

    if (sheenTintTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("sheentint", sheenTintTextureName))
    else :
        scene_file.write(r'"float sheentint" [%s]' %(nodes["Pbrt Disney"].sheenTint))
    scene_file.write("\n")
    
    if (clearCoatTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("clearcoat", clearCoatTextureName))
    else :
        scene_file.write(r'"float clearcoat" [%s]' %(nodes["Pbrt Disney"].clearCoat))
    scene_file.write("\n")

    if (clearCoatGlossTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("clearcoatgloss", clearCoatGlossTextureName))
    else :
        scene_file.write(r'"float clearcoatgloss" [%s]' %(nodes["Pbrt Disney"].clearCoatGloss))
    scene_file.write("\n")

    if (specTransTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("spectrans", specTransTextureName))
    else :
        scene_file.write(r'"float spectrans" [%s]' %(nodes["Pbrt Disney"].specTrans))
    scene_file.write("\n")

    if (flatnessTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("flatness", flatnessTextureName))
    else :
        scene_file.write(r'"float flatness" [%s]' %(nodes["Pbrt Disney"].flatness))
    scene_file.write("\n")
    
    if (diffTransTextureName != ""):
        scene_file.write(r'"texture %s" "%s"' % ("difftrans", diffTransTextureName))
    else :
        scene_file.write(r'"float difftrans" [%s]' %(nodes["Pbrt Disney"].diffTrans))
    scene_file.write("\n")

    #TODO: scatter distance causes crash for some stupid reason.
    #r = nodes["Pbrt Disney"].inputs[11].default_value[0]
    #g = nodes["Pbrt Disney"].inputs[11].default_value[1]
    #b = nodes["Pbrt Disney"].inputs[11].default_value[2]
    #scene_file.write(r'"color scatterdistance" [%s %s %s]' %(r,g,b))
    #scene_file.write("\n")
    return ''

    # https://blender.stackexchange.com/questions/80773/how-to-get-the-name-of-image-of-image-texture-with-python

def export_pbrt_blackbody_material (scene_file, mat):
    print('Currently exporting Pbrt BlackBody material')
    print (mat.name)
    nodes = mat.node_tree.nodes
    scene_file.write(r'AreaLightSource "diffuse" "blackbody L" [%s ' %(nodes["Pbrt BlackBody"].Temperature))
    scene_file.write(r'%s]' %(nodes["Pbrt BlackBody"].Lambda))
    scene_file.write("\n")
    return ''

def export_pbrt_mix_material(scene_file, mat):
    print('Currently exporting Pbrt Mix material')
    print (mat.name)
    nodes = mat.node_tree.nodes
    scene_file.write(r'Material "mix"')
    scene_file.write("\n")

    scene_file.write(r'"string namedmaterial1" [ "%s" ]' %(nodes["Pbrt Mix"].inputs[0].name))
    scene_file.write("\n")
    scene_file.write(r'"string namedmaterial2" [ "%s" ]' %(nodes["Pbrt Mix"].inputs[1].name))
    scene_file.write("\n")

    return ''

def hastexturenewcode(mat, slotname):
    foundTex = False
    print ("checking texture for : ")
    print(mat.name)
    print("checking slot named new code:")
    print(slotname)
    nodes = mat.node_tree.nodes
    #print(mat.[slotname])
    #if mat.slotname == !"":
        #print("Found filepath stored in slot:")
        #foundTex = True
    #print(mat.slotname)
    #print(mat.[slotname])
    print(len(mat.node_tree.links))
    if (len(mat.node_tree.links) > 1):
        socket = nodes[mat.node_tree.nodes[1].name].inputs[slotname]
        print("socket type:")
        print(socket.type)
        print("data stored in slot:")
        print(nodes[mat.node_tree.nodes[1].name].inputs[slotname])
        #links = mat.node_tree.links
        #link = next(l for l in links if l.to_socket == socket)
        #if link.from_node.type == 'TEX_IMAGE':
    return foundTex

def hastextureInSlot (mat,index):
    foundTex = False
    if getTextureInSlotName(index) != "":
        foundTex = True

    return foundTex

def getTextureInSlotName(textureSlotParam):
    srcfile = textureSlotParam
    head, tail = os.path.split(srcfile)
    print("File name is :")
    print(tail)

    return tail

def exportFloatTextureInSlotNew(scene_file,textureSlotParam):
    scene_file.write("\n")
    srcfile = bpy.path.abspath(textureSlotParam)
    texturefilename = getTextureInSlotName(srcfile)
    scene_file.write(r'Texture "%s" "float" "imagemap" "string filename" ["%s"]' % (texturefilename, ("textures/" + texturefilename)))
    scene_file.write("\n")
    dstdir = bpy.path.abspath('//pbrtExport/textures/' + texturefilename)
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
    print(texturefilename)
    print("!!!!! skipping copying for now..")
    #shutil.copyfile(srcfile, dstdir)
#    foundTex = True
    return ''


    ##TODO: write out the path to the file and call function from where we check if texture is in slot.
    ## send the filepath, slot name from there.
def exportTextureInSlot(scene_file,index,mat,slotname):
    nodes = mat.node_tree.nodes
    slot = index
#    foundTex = False
    socket = nodes[mat.node_tree.nodes[1].name].inputs[slot]
    links = mat.node_tree.links
    link = next(l for l in links if l.to_socket == socket)
    if link:
        image = link.from_node.image
        scene_file.write(r'Texture "%s" "color" "imagemap" "string filename" ["%s"]' % (image.name, ("textures/" + image.name))) #.replace("\\","/")
        scene_file.write("\n")
        srcfile = bpy.path.abspath(image.filepath)
        dstdir = bpy.path.abspath('//pbrtExport/textures/' + image.name)
        print("os.path.dirname...")
        print(os.path.dirname(srcfile) + image.name)
        print("srcfile: ")
        print(srcfile)
        print("\n")
        print("dstdir: ")
        print(dstdir)
        print("\n")

        shutil.copyfile(srcfile, dstdir)
#        foundTex = True
    return ''

# Here we should check what material type is being exported.
def export_material(scene_file, material):
    # https://blender.stackexchange.com/questions/51782/get-material-and-color-of-material-on-a-face-of-an-object-in-python
    # https://blender.stackexchange.com/questions/36587/how-to-define-customized-property-in-material

    #context = bpy.context
    #obj = context.object
    #print("Material slots:")
    #print(len(object.material_slots))
    #if len(object.material_slots) == 0:
    if material is None:
        print("no material on object")
        return ''

    #mat = #object.data.materials[slotIndex]
    print ('Exporting material named: ',material.name)
    #nodes = mat.node_tree.nodes
    global hastexture
    hastexture = False
    currentMaterial = None
    #textureName = ""
    # check if this code can be used so get the socket the image is plugged into:
    # https://blender.stackexchange.com/questions/77365/getting-the-image-of-a-texture-node-that-feeds-into-a-node-group

    #   Begin new texture code


    #Later we should loop through all 'slots' to write out all materials applied.

    #mat = object.material_slots[slotIndex].material #Get the material from the material slot you want
    #print ('Fetched material in slot 0 named: ',material.name)
    if material and material.use_nodes: #if it is using nodes
        print('Exporting materal named: ', material.name)

        # this piece of code needs work.
        # we need to restructure how we do this. We should get the 'material output' node (by name for example)
        # material.node_tree.nodes['Material output'].name

        #if material.node_tree.nodes['Material output'] is not None:
            #print("We found the output node!!")

        #Find the surface output node, then export the connected material
        for node in material.node_tree.nodes:
            if node.name == 'Material Output':
                for input in node.inputs:
                    for node_links in input.links:
                        print("going to " + node_links.from_node.name)
                        currentMaterial =  node_links.from_node
                        
                        # We should traverse the node instead of always looping through the material nodes to the find 'input 0'.
                        # this also affects the texture export and so on. all of that needs to be fixed.
                        # Enable the piece below to start doing so.
                        #material = node_links.from_node

        #print ('mat.node_tree.nodes[0].name:', material.node_tree.nodes[0].name)
        #print ('mat.node_tree.nodes[1].name:', material.node_tree.nodes[1].name)

        if currentMaterial.name == 'Mitsuba2 BSDF':
            export_mitsuba_bsdf_material(scene_file,currentMaterial, material.name)

    return''

    # matrix to string
def matrixtostr(matrix):
    return '%f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f '%(matrix[0][0],matrix[0][1],matrix[0][2],matrix[0][3],matrix[1][0],matrix[1][1],matrix[1][2],matrix[1][3],matrix[2][0],matrix[2][1],matrix[2][2],matrix[2][3],matrix[3][0],matrix[3][1],matrix[3][2],matrix[3][3])

def createDefaultExportDirectories(scene_file, scene):
    texturePath = bpy.path.abspath(bpy.data.scenes[0].exportpath + 'textures')
    print("Exporting textures to: ")
    print(texturePath)

    if not os.path.exists(texturePath):
        print('Texture directory did not exist, creating: ')
        print(texturePath)
        os.makedirs(texturePath)

def export_gometry_as_obj(scene_file, scene):
    #bpy.ops.export_scene.obj(filepath=target_file)
    # 
    objects = bpy.data.objects
    #for object in scene.objects:
    for object in objects:
        print("exporting:")
        print(object.name)

        for i in range(len(object.material_slots)):
            material = object.material_slots[i].material
            export_material(scene_file, material)

        if object is not None and object.type != 'CAMERA' and object.type == 'MESH':
            bpy.ops.object.select_all(action="DESELECT")
            object.select_set(True) # 2.8+
            #object.select = True

            objFilePath = bpy.data.scenes[0].exportpath + 'meshes/' + object.name + '.obj'
            objFolderPath = bpy.data.scenes[0].exportpath + 'meshes/'
            if not os.path.exists(objFolderPath):
                print('Meshes directory did not exist, creating: ')
                print(objFolderPath)
                os.makedirs(objFolderPath)
            #exportFilePath = os.path.join(filepath, 'meshes', (object.name + '.obj'))
            bpy.ops.export_scene.obj(filepath=objFilePath, use_selection=True)
            scene_file.write('<shape type="obj">\n')
            scene_file.write('<string name="filename" value="meshes/%s"/>\n' % (object.name + '.obj'))
            scene_file.write('<ref id="%s"/>\n' %(object.material_slots[0].material.name))
            scene_file.write('</shape>\n')
            

def export_geometry(scene_file, scene):
    
    # We now export the mesh as pbrt's triangle meshes.
    # Development documentation :
    # https://docs.blender.org/api/current/bpy.types.MeshLoopTriangle.html
    # https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Mesh_API

    for object in scene.objects:
        print("exporting:")
        print(object.name)

        if object is not None and object.type != 'CAMERA' and object.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
            print('exporting object: ' + object.name)
            bpy.context.view_layer.update()
            object.data.update()
            mesh = object.data

            if not mesh.loop_triangles and mesh.polygons:
                mesh.calc_loop_triangles()

            for i in range(len(object.material_slots)):
                scene_file.write("AttributeBegin\n")
                scene_file.write( "Transform [" + matrixtostr( object.matrix_world.transposed() ) + "]\n" )
                material = object.material_slots[i].material
                export_material(scene_file, material)
                
                scene_file.write( "Shape \"trianglemesh\"\n")

                # TODO: 
                # The current way we loop through triangles is not optimized.
                # This should be fixed by looping through once, then collect all
                # faces\verts etc that belongs to slot X, then export each collection.
                scene_file.write( '\"point P\" [\n' )
                for tri in mesh.loop_triangles:
                    if tri.material_index == i:
                        for vert_index in tri.vertices:
                            scene_file.write("%s %s %s\n" % (mesh.vertices[vert_index].co.x, mesh.vertices[vert_index].co.y, mesh.vertices[vert_index].co.z))
                scene_file.write( "]\n" )
                
                mesh.calc_normals_split()
                scene_file.write( "\"normal N\" [\n" )
                for tri in mesh.loop_triangles:
                    if tri.material_index == i:
                        for vert_index in tri.split_normals:
                            scene_file.write("%s %s %s\n" % (vert_index[0],vert_index[1],vert_index[2]))
                scene_file.write( "]\n" )
                
                scene_file.write( "\"float st\" [\n" )
                for uv_layer in mesh.uv_layers:
                    for tri in mesh.loop_triangles:
                        if tri.material_index == i:
                            for loop_index in tri.loops:
                                scene_file.write("%s %s \n" % (uv_layer.data[loop_index].uv[0], uv_layer.data[loop_index].uv[1]))
                scene_file.write( "]\n" )

                scene_file.write( "\"integer indices\" [\n" )
                faceIndex = 0
                for tri in mesh.loop_triangles:
                    if tri.material_index == i:
                        for vert_index in tri.vertices:
                            scene_file.write("%s " % (faceIndex))
                            faceIndex +=1
                scene_file.write("\n")
                scene_file.write( "]\n" )
                scene_file.write("AttributeEnd\n\n")

    return ''

def export_dummymesh(scene_file):
    scene_file.write(r'AttributeBegin')
    scene_file.write("\n")
    scene_file.write(r'Material "plastic"')
    scene_file.write("\n")
    scene_file.write(r'"color Kd" [.1 .1 .1]')
    scene_file.write("\n")
    scene_file.write(r'"color Ks" [.7 .7 .7] "float roughness" .1')
    scene_file.write("\n")
    scene_file.write(r'Translate 0 0 0')
    scene_file.write("\n")
    scene_file.write(r'Shape "trianglemesh"')
    scene_file.write("\n")
    scene_file.write(r'"point P" [ -1000 -1000 0   1000 -1000 0   1000 1000 0 -1000 1000 0 ]')
    scene_file.write("\n")
    scene_file.write(r'"integer indices" [ 0 1 2 2 3 0]')
    scene_file.write("\n")
    scene_file.write("AttributeEnd")
    scene_file.write("\n\n")
    return ''

def export_Mitsuba(filepath, scene , frameNumber):
    out = os.path.join(filepath, "test" + frameNumber +".xml")
    if not os.path.exists(filepath):
        print('Output directory did not exist, creating: ')
        print(filepath)
        os.makedirs(filepath)

    with open(out, 'w') as scene_file:
        createDefaultExportDirectories(scene_file,scene)
        scene_begin(scene_file)
        #export_film(scene_file, frameNumber)
        #export_sampler(scene_file)
        #export_integrator(scene_file,scene)
        export_camera(scene_file)
        
        #export_EnviromentMap(scene_file)
        #export_environmentLight(scene_file)
        #print('Begin export lights:')
        export_point_lights(scene_file,scene)
        #export_spot_lights(scene_file,scene)
        #print('End export lights.')
        #export_geometry(scene_file,scene)
        export_gometry_as_obj(scene_file,scene)
        #export_dummymesh(scene_file)
        scene_end(scene_file)
        scene_file.close()
