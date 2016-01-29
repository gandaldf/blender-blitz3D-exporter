#!BPY
# -*- coding: cp1252 -*-

"""
Name: 'B3D Exporter (.b3d)...'
Blender: 248a
Group: 'Export'
Tooltip: 'Export to Blitz3D file format (.b3d)'
"""
__author__ = ["Diego Parisi"]
__url__ = ["www.diegoparisi.com"]
__version__ = "2.06"
__bpydoc__ = """\
"""

# Blender-Blitz3D Exporter 2.06
# Copyright 2009 Diego Parisi  -  www.diegoparisi.com
#
# Lightmap issue fixed by Capricorn 76 Pty. Ltd. - www.capricorn76.com
#
# LICENSE:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

#If you get an error here, it might be
#because you don't have Python installed.
import Blender
import BPyMesh
import sys,os,os.path,struct,math,string
from Blender import Mathutils
from Blender.Mathutils import *
from Blender import Draw,BGL
from Blender.BGL import *

if not hasattr(sys,"argv"): sys.argv = ["???"]

#Events
EVENT_ALL = 1
EVENT_SEL = 2
EVENT_NOR = 3
EVENT_COL = 4
EVENT_CAM = 5
EVENT_LIG = 6
EVENT_EXP = 7
EVENT_QUI = 8

#Global Stacks
flag_stack = []
sets_stack = []
texs_stack = []
brus_stack = []
mesh_stack = []
bone_stack = []
keys_stack = []

#Transformation Matrix
TRANS_MATRIX = Mathutils.Matrix([-1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1])

#Support Functions
def write_int(value):
    return struct.pack("<i",value)

def write_float(value):
    return struct.pack("<f",round(value,4))

def write_string(value):
    binary_format = "<%ds"%(len(value)+1)
    return struct.pack(binary_format,value)

def write_chunk(name,value):
    return name + write_int(len(value)) + value

#Write B3D File
def write_b3d_file(filename):
    file_buf = ""
    temp_buf = ""

    temp_buf += write_int(1) #Version
    temp_buf += write_texs() #TEXS
    temp_buf += write_brus() #BRUS
    temp_buf += write_node() #NODE

    if len(temp_buf) > 0:
        file_buf += write_chunk("BB3D",temp_buf)
        temp_buf = ""

    file = open(filename,'wb')
    file.write(file_buf)
    file.close()

#Write TEXS Chunk
def write_texs():
    texs_buf = ""
    temp_buf = ""
    layer_max = 0
    obj_count = 0
    set_wrote = 0

    if flag_stack[1]:
        exp_obj = Blender.Object.GetSelected()
    else:
        exp_obj = Blender.Object.Get()

    for obj in exp_obj:
        if obj.type == "Mesh":
            set_count = 0
            set_wrote = 0
            data = obj.getData(mesh = True)
            orig_uvlayer = data.activeUVLayer
            layer_set = [[],[],[],[],[],[],[],[]]
            sets_stack.append([[],[],[],[],[],[],[],[]])

            if len(data.getUVLayerNames()) <= 8:
                if len(data.getUVLayerNames()) > layer_max:
                    layer_max = len(data.getUVLayerNames())
            else:
                layer_max = 8

            for face in data.faces:
                for iuvlayer,uvlayer in enumerate(data.getUVLayerNames()):
                    if iuvlayer < 8:
                        data.activeUVLayer = uvlayer
                        layer_set[iuvlayer].append(face.uv)

            for i in xrange(len(data.getUVLayerNames())):
                if set_wrote:
                    set_count += 1
                    set_wrote = 0

                for iuvlayer in xrange(i,len(data.getUVLayerNames())):
                    if layer_set[i] == layer_set[iuvlayer]:
                        if sets_stack[obj_count][iuvlayer] == []:
                            if set_count == 0:
                                tex_flag = 1
                            elif set_count == 1:
                                tex_flag = 65536
                            elif set_count > 1:
                                tex_flag = 1
                            sets_stack[obj_count][iuvlayer] = tex_flag
                            set_wrote = 1

            for face in data.faces:
                for iuvlayer,uvlayer in enumerate(data.getUVLayerNames()):
                    if iuvlayer < 8:
                        data.activeUVLayer = uvlayer
                        if face.image:
                            if not [face.image.name,sets_stack[obj_count][iuvlayer]] in texs_stack:
                                texs_stack.append([face.image.name,sets_stack[obj_count][iuvlayer]])
                                temp_buf += write_string(Blender.sys.basename(face.image.getFilename())) #Texture File Name
                                temp_buf += write_int(sets_stack[obj_count][iuvlayer]) #Flags
                                temp_buf += write_int(2)   #Blend
                                temp_buf += write_float(0) #X_Pos
                                temp_buf += write_float(0) #Y_Pos
                                temp_buf += write_float(1) #X_Scale
                                temp_buf += write_float(1) #Y_Scale
                                temp_buf += write_float(0) #Rotation

            obj_count += 1

            if orig_uvlayer:
                data.activeUVLayer = orig_uvlayer

    texs_stack.append(layer_max)

    if len(temp_buf) > 0:
        texs_buf += write_chunk("TEXS",temp_buf)
        temp_buf = ""

    return texs_buf

#Write BRUS Chunk
def write_brus():
    brus_buf = ""
    temp_buf = ""
    mat_count = 0
    obj_count = 0

    if flag_stack[1]:
        exp_obj = Blender.Object.GetSelected()
    else:
        exp_obj = Blender.Object.Get()

    for obj in exp_obj:
        if obj.type == "Mesh":
            data = obj.getData(mesh = True)
            orig_uvlayer = data.activeUVLayer

            for face in data.faces:
                img_found = 0
                face_stack = []
                for iuvlayer,uvlayer in enumerate(data.getUVLayerNames()):
                    if iuvlayer < 8:
                        data.activeUVLayer = uvlayer
                        if data.faceUV and face.image:
                            img_found = 1
                            for i in xrange(len(texs_stack)-1):
                                if texs_stack[i][0] == face.image.name:
                                    if texs_stack[i][1] == sets_stack[obj_count][iuvlayer]:
                                        img_id = i
                        else:
                            img_id = -1

                        face_stack.insert(iuvlayer,img_id)

                for i in xrange(len(face_stack),texs_stack[-1]):
                    face_stack.append(-1)

                if not img_found:
                    if data.materials:
                        if data.materials[face.mat]:
                            mat_data = data.materials[face.mat]
                            mat_colr = mat_data.rgbCol[0]
                            mat_colg = mat_data.rgbCol[1]
                            mat_colb = mat_data.rgbCol[2]
                            mat_alpha = mat_data.getAlpha()
                            mat_name = mat_data.name

                            if not mat_name in brus_stack:
                                brus_stack.append(mat_name)
                                temp_buf += write_string(mat_name) #Brush Name
                                temp_buf += write_float(mat_colr)  #Red
                                temp_buf += write_float(mat_colg)  #Green
                                temp_buf += write_float(mat_colb)  #Blue
                                temp_buf += write_float(mat_alpha) #Alpha
                                temp_buf += write_float(0)         #Shininess
                                temp_buf += write_int(1)           #Blend
                                if flag_stack[3] and data.getColorLayerNames():
                                    temp_buf += write_int(2) #Fx
                                else:
                                    temp_buf += write_int(0) #Fx

                                for i in face_stack:
                                    temp_buf += write_int(i) #Texture ID
                    else:
                        if flag_stack[3] and data.getColorLayerNames():
                            if not face_stack in brus_stack:
                                brus_stack.append(face_stack)
                                mat_count += 1
                                temp_buf += write_string("Brush.%.3i"%mat_count) #Brush Name
                                temp_buf += write_float(1) #Red
                                temp_buf += write_float(1) #Green
                                temp_buf += write_float(1) #Blue
                                temp_buf += write_float(1) #Alpha
                                temp_buf += write_float(0) #Shininess
                                temp_buf += write_int(1)   #Blend
                                temp_buf += write_int(2)   #Fx

                                for i in face_stack:
                                    temp_buf += write_int(i) #Texture ID
                else:
                    if not face_stack in brus_stack:
                        brus_stack.append(face_stack)
                        mat_count += 1
                        temp_buf += write_string("Brush.%.3i"%mat_count) #Brush Name
                        temp_buf += write_float(1) #Red
                        temp_buf += write_float(1) #Green
                        temp_buf += write_float(1) #Blue
                        temp_buf += write_float(1) #Alpha
                        temp_buf += write_float(0) #Shininess
                        temp_buf += write_int(1)   #Blend
                        if flag_stack[3] and data.getColorLayerNames():
                            temp_buf += write_int(2) #Fx
                        else:
                            temp_buf += write_int(0) #Fx

                        for i in face_stack:
                            temp_buf += write_int(i) #Texture ID

            obj_count += 1

            if orig_uvlayer:
                data.activeUVLayer = orig_uvlayer

    if len(temp_buf) > 0:
        brus_buf += write_chunk("BRUS",write_int(texs_stack[-1]) + temp_buf) #N Texs
        temp_buf = ""

    return brus_buf

#Write NODE Chunk
def write_node():
    global bone_stack
    global keys_stack
    root_buf = ""
    node_buf = ""
    main_buf = ""
    temp_buf = ""
    obj_count = 0
    amb_light = 0

    num_mesh = 0
    num_ligs = 0
    num_cams = 0
    num_lorc = 0
    exp_scn = Blender.Scene.GetCurrent()
    exp_con = exp_scn.getRenderingContext()

    first_frame = Blender.Draw.Create(exp_con.startFrame())
    last_frame = Blender.Draw.Create(exp_con.endFrame())
    num_frames = last_frame.val - first_frame.val

    if flag_stack[1]:
        exp_obj = Blender.Object.GetSelected()
    else:
        exp_obj = Blender.Object.Get()

    for obj in exp_obj:
        if obj.type == "Mesh":
            num_mesh += 1
        if obj.type == "Camera":
            num_cams += 1
        if obj.type == "Lamp":
            num_ligs += 1

    if flag_stack[4] == 1:
        num_lorc += num_cams

    if flag_stack[5] == 1:
        num_lorc += 1
        num_lorc += num_ligs

    if num_mesh + num_lorc > 1:
        exp_root = 1
    else:
        exp_root = 0

    if exp_root:
        root_buf += write_string("ROOT") #Node Name

        root_buf += write_float(0) #Position X
        root_buf += write_float(0) #Position Y
        root_buf += write_float(0) #Position Z

        root_buf += write_float(1) #Scale X
        root_buf += write_float(1) #Scale Y
        root_buf += write_float(1) #Scale Z

        root_buf += write_float(1) #Rotation W
        root_buf += write_float(0) #Rotation X
        root_buf += write_float(0) #Rotation Y
        root_buf += write_float(0) #Rotation Z

    for obj in exp_obj:
        if obj.type == "Mesh":
            bone_stack = []
            keys_stack = []
            data = obj.getData(mesh = True)

            arm_action = None
            if obj.getParent():
                if obj.getParent().type == "Armature":
                    arm = obj.getParent()
                    if arm.getAction():
                        arm_action = arm.getAction()

            if arm_action:
                matrix = Matrix()

                temp_buf += write_string(obj.name) #Node Name

                position = matrix.translationPart()
                temp_buf += write_float(-position[0]) #Position X
                temp_buf += write_float(position[1])  #Position Y
                temp_buf += write_float(position[2])  #Position Z

                scale = matrix.scalePart()
                temp_buf += write_float(scale[0]) #Scale X
                temp_buf += write_float(scale[2]) #Scale Y
                temp_buf += write_float(scale[1]) #Scale Z

                quat = matrix.toQuat()
                quat.normalize()

                temp_buf += write_float(quat.w) #Rotation W
                temp_buf += write_float(quat.x) #Rotation X
                temp_buf += write_float(quat.z) #Rotation Y
                temp_buf += write_float(quat.y) #Rotation Z
            else:
                matrix = obj.getMatrix("worldspace")
                matrix *= TRANS_MATRIX

                temp_buf += write_string(obj.name) #Node Name

                position = matrix.translationPart()
                temp_buf += write_float(-position[0]) #Position X
                temp_buf += write_float(position[1])  #Position Y
                temp_buf += write_float(position[2])  #Position Z

                scale = matrix.scalePart()
                temp_buf += write_float(scale[0]) #Scale X
                temp_buf += write_float(scale[2]) #Scale Y
                temp_buf += write_float(scale[1]) #Scale Z

                matrix *= RotationMatrix(180,4,"y")
                matrix *= RotationMatrix(90,4,"x")
                quat = matrix.toQuat()
                quat.normalize()

                temp_buf += write_float(quat.w) #Rotation W
                temp_buf += write_float(quat.x) #Rotation X
                temp_buf += write_float(quat.z) #Rotation Y
                temp_buf += write_float(quat.y) #Rotation Z

            if arm_action:
                Blender.Set("curframe",0)
                Blender.Window.Redraw()

                data = arm.getData()
                arm_matrix = arm.getMatrix("worldspace")
                arm_matrix *= TRANS_MATRIX.invert()

                def read_armature(arm_matrix,bone,parent = None):
                    if (parent and not bone.parent.name == parent.name):
                        return

                    matrix = Blender.Mathutils.Matrix(bone.matrix["ARMATURESPACE"])

                    if parent:
                        par_matrix = matrix * Blender.Mathutils.Matrix(parent.matrix["ARMATURESPACE"]).invert()
                    else:
                        par_matrix = matrix * arm_matrix

                    bone_stack.append([par_matrix,parent,bone])

                    if bone.children:
                        for child in bone.children: read_armature(arm_matrix,child,bone)

                for bone in data.bones.values():
                    if not bone.parent:
                        read_armature(arm_matrix,bone)

                arm_action.setActive(arm)
                frame_count = first_frame.val

                while frame_count <= last_frame.val:
                    Blender.Set("curframe",int(frame_count))
                    Blender.Window.Redraw()
                    arm_pose = arm.getPose()
                    arm_matrix = arm.getMatrix("worldspace")
                    arm_matrix *= TRANS_MATRIX

                    for bone_name in data.bones.keys():
                        bone_matrix = Blender.Mathutils.Matrix(arm_pose.bones[bone_name].poseMatrix)

                        for ibone in xrange(len(bone_stack)):
                            if bone_stack[ibone][2].name == bone_name:
                                if bone_stack[ibone][1]:
                                    par_matrix = Blender.Mathutils.Matrix(arm_pose.bones[bone_stack[ibone][1].name].poseMatrix)
                                    bone_matrix *= par_matrix.invert()
                                else:
                                    bone_matrix *= arm_matrix

                                bone_loc = bone_matrix.translationPart()
                                bone_rot = bone_matrix.rotationPart().toQuat()
                                bone_rot.normalize()
                                bone_sca = bone_matrix.scalePart()
                                keys_stack.append([frame_count - first_frame.val,bone_name,bone_loc,bone_sca,bone_rot])

                    frame_count += 1

                Blender.Set("curframe",0)
                Blender.Window.Redraw()

            temp_buf += write_node_mesh(obj,obj_count,arm_action,exp_root) #NODE MESH

            if arm_action:
                temp_buf += write_node_anim(num_frames) #NODE ANIM

                for ibone in xrange(len(bone_stack)):
                    if not bone_stack[ibone][1]:
                        temp_buf += write_node_node(ibone) #NODE NODE

            obj_count += 1

            if len(temp_buf) > 0:
                node_buf += write_chunk("NODE",temp_buf)
                temp_buf = ""

        if flag_stack[4]:
            if obj.type == "Camera":
                data = obj.getData()
                matrix = obj.getMatrix("worldspace")
                matrix *= TRANS_MATRIX

                if data.type == "ortho":
                    cam_type = 2
                    cam_zoom = round(data.scale,4)
                else:
                    cam_type = 1
                    cam_zoom = round(data.lens,4)

                cam_near = round(data.clipStart,4)
                cam_far = round(data.clipEnd,4)

                node_name = ("CAMS"+"\n%s"%obj.name+"\n%s"%cam_type+\
                             "\n%s"%cam_zoom+"\n%s"%cam_near+"\n%s"%cam_far)
                temp_buf += write_string(node_name) #Node Name

                position = matrix.translationPart()
                temp_buf += write_float(-position[0]) #Position X
                temp_buf += write_float(position[1])  #Position Y
                temp_buf += write_float(position[2])  #Position Z

                scale = matrix.scalePart()
                temp_buf += write_float(scale[0]) #Scale X
                temp_buf += write_float(scale[1]) #Scale Y
                temp_buf += write_float(scale[2]) #Scale Z

                matrix *= RotationMatrix(180,4,"y")
                quat = matrix.toQuat()
                quat.normalize()

                temp_buf += write_float(quat.w)  #Rotation W
                temp_buf += write_float(quat.x)  #Rotation X
                temp_buf += write_float(quat.y)  #Rotation Y
                temp_buf += write_float(-quat.z) #Rotation Z

                if len(temp_buf) > 0:
                    node_buf += write_chunk("NODE",temp_buf)
                    temp_buf = ""

        if flag_stack[5]:
            if amb_light == 0:
                data = Blender.World.GetCurrent()

                amb_light = 1
                amb_color = (int(data.amb[2]*255) |(int(data.amb[1]*255) << 8) | (int(data.amb[0]*255) << 16))

                node_name = ("AMBI"+"\n%s"%amb_color)
                temp_buf += write_string(node_name) #Node Name

                temp_buf += write_float(0) #Position X
                temp_buf += write_float(0) #Position Y
                temp_buf += write_float(0) #Position Z

                temp_buf += write_float(1) #Scale X
                temp_buf += write_float(1) #Scale Y
                temp_buf += write_float(1) #Scale Z

                temp_buf += write_float(1) #Rotation W
                temp_buf += write_float(0) #Rotation X
                temp_buf += write_float(0) #Rotation Y
                temp_buf += write_float(0) #Rotation Z

                if len(temp_buf) > 0:
                    node_buf += write_chunk("NODE",temp_buf)
                    temp_buf = ""

            if obj.type == "Lamp":
                data = obj.getData()
                matrix = obj.getMatrix("worldspace")
                matrix *= TRANS_MATRIX

                if data.type == 0:
                    lig_type = 2
                elif data.type == 2:
                    lig_type = 3
                else:
                    lig_type = 1

                lig_angle = round(data.spotSize,4)
                lig_color = (int(data.b*255) |(int(data.g*255) << 8) | (int(data.r*255) << 16))
                lig_range = round(data.dist,4)

                node_name = ("LIGS"+"\n%s"%obj.name+"\n%s"%lig_type+\
                             "\n%s"%lig_angle+"\n%s"%lig_color+"\n%s"%lig_range)
                temp_buf += write_string(node_name) #Node Name

                position = matrix.translationPart()
                temp_buf += write_float(-position[0]) #Position X
                temp_buf += write_float(position[1])  #Position Y
                temp_buf += write_float(position[2])  #Position Z

                scale = matrix.scalePart()
                temp_buf += write_float(scale[0]) #Scale X
                temp_buf += write_float(scale[1]) #Scale Y
                temp_buf += write_float(scale[2]) #Scale Z

                matrix *= RotationMatrix(180,4,"y")
                quat = matrix.toQuat()
                quat.normalize()

                temp_buf += write_float(quat.w)  #Rotation W
                temp_buf += write_float(quat.x)  #Rotation X
                temp_buf += write_float(quat.y)  #Rotation Y
                temp_buf += write_float(-quat.z) #Rotation Z

                if len(temp_buf) > 0:
                    node_buf += write_chunk("NODE",temp_buf)
                    temp_buf = ""

    if len(node_buf) > 0:
        if exp_root:
            main_buf += write_chunk("NODE",root_buf + node_buf)
        else:
            main_buf += node_buf

        node_buf = ""
        root_buf = ""

    return main_buf

#Write NODE MESH Chunk
def write_node_mesh(obj,obj_count,arm_action,exp_root):
    global mesh_stack
    mesh_stack = []
    mesh_buf = ""
    temp_buf = ""

    temp_buf += write_int(-1) #Brush ID
    temp_buf += write_node_mesh_vrts(obj,obj_count,arm_action,exp_root) #NODE MESH VRTS
    temp_buf += write_node_mesh_tris(obj,obj_count,arm_action,exp_root) #NODE MESH TRIS

    if len(temp_buf) > 0:
        mesh_buf += write_chunk("MESH",temp_buf)
        temp_buf = ""

    return mesh_buf

#Write NODE MESH VRTS Chunk
def write_node_mesh_vrts(obj,obj_count,arm_action,exp_root):
    vrts_buf = ""
    temp_buf = ""
    obj_flags = 0
    ids_count = 0

    data = obj.getData(mesh = True)
    orig_uvlayer = data.activeUVLayer

    if flag_stack[2]:
        obj_flags += 1

    if flag_stack[3] and data.getColorLayerNames():
        obj_flags += 2

    temp_buf += write_int(obj_flags) #Flags
    temp_buf += write_int(len(data.getUVLayerNames())) #UV Set
    temp_buf += write_int(2) #UV Set Size

    for i in data.verts:
        mesh_stack.append([-1,-1,-1,[],[[],[],[],[],[],[],[],[]],[]])

    for face in data.faces:
        for ivert,vert in enumerate(face.verts):
            if mesh_stack[vert.index][0] == -1:
                link_matrix = obj.getMatrix("worldspace")
                mesh_matrix = Matrix(link_matrix[0],link_matrix[1],link_matrix[2],link_matrix[3])
                vert_matrix = TranslationMatrix(vert.co)

                if arm_action:
                    vert_matrix *= mesh_matrix

                vert_matrix *= TRANS_MATRIX
                vert_matrix = vert_matrix.translationPart()

                mesh_stack[vert.index][0] = vert.index
                mesh_stack[vert.index][1] = vert_matrix

                if flag_stack[2]:
                    link_matrix = obj.getMatrix("worldspace")
                    mesh_matrix = Matrix(link_matrix[0],link_matrix[1],link_matrix[2],link_matrix[3])
                    norm_matrix = TranslationMatrix(vert.no)

                    if arm_action:
                        norm_matrix *= mesh_matrix

                    norm_matrix *= TRANS_MATRIX
                    norm_matrix = norm_matrix.translationPart()

                    mesh_stack[vert.index][2] = norm_matrix

                if flag_stack[3] and data.getColorLayerNames():
                    mesh_stack[vert.index][3] = face.col[ivert]

                if data.vertexUV and not data.faceUV:
		    mesh_stack[vert.index][4][0].append([face.index,vert.uvco[0]])
                if not data.vertexUV and not data.faceUV:
		    mesh_stack[vert.index][4][0].append([face.index,[0.0,0.0]])

                for vert_influ in data.getVertexInfluences(vert.index):
                    mesh_stack[vert.index][5].append(vert_influ)

    if data.faceUV:
        if not 65536 in sets_stack[obj_count]:
            vert_opti = 1
        else:
            vert_opti = 0

        for iuvlayer,uvlayer in enumerate(data.getUVLayerNames()):
            if iuvlayer < 8:
                data.activeUVLayer = uvlayer
                for face in data.faces:
                    for ivert,vert in enumerate(face.verts):
                        if vert_opti:
                            if not face.uv[ivert] in mesh_stack[vert.index][4][iuvlayer]:
				mesh_stack[vert.index][4][iuvlayer].append([face.index,face.uv[ivert]])
                        else:
			    mesh_stack[vert.index][4][iuvlayer].append([face.index,face.uv[ivert]])

    if orig_uvlayer:
        data.activeUVLayer = orig_uvlayer

    for ivert in xrange(len(mesh_stack)):
	mesh_stack[ivert][0] = ids_count
	for iuv in xrange(len(mesh_stack[ivert][4][0])):
	    ids_count += 1

            temp_buf += write_float(-mesh_stack[ivert][1].x) #X
            temp_buf += write_float(mesh_stack[ivert][1].y)  #Y
            temp_buf += write_float(mesh_stack[ivert][1].z)  #Z

            if flag_stack[2]:
                temp_buf += write_float(-mesh_stack[ivert][2].x) #NX
                temp_buf += write_float(mesh_stack[ivert][2].y)  #NY
                temp_buf += write_float(mesh_stack[ivert][2].z)  #NZ

            if flag_stack[3] and data.getColorLayerNames():
                temp_buf += write_float(mesh_stack[ivert][3].r/255.0) #R
                temp_buf += write_float(mesh_stack[ivert][3].g/255.0) #G
                temp_buf += write_float(mesh_stack[ivert][3].b/255.0) #B
                temp_buf += write_float(mesh_stack[ivert][3].a/255.0) #A

            for iuvlayer in xrange(len(data.getUVLayerNames())):
                temp_buf += write_float(mesh_stack[ivert][4][iuvlayer][iuv][1][0])  #U
                temp_buf += write_float(-mesh_stack[ivert][4][iuvlayer][iuv][1][1]) #V

    if len(temp_buf) > 0:
        vrts_buf += write_chunk("VRTS",temp_buf)
        temp_buf = ""

    return vrts_buf

#Write NODE MESH TRIS Chunk
def write_node_mesh_tris(obj,obj_count,arm_action,exp_root):
    tris_buf = ""
    temp_buf = ""
    last_brus = None
    brus_written = 0

    data = obj.getData(mesh = True)
    orig_uvlayer = data.activeUVLayer

    for face in data.faces:
        img_found = 0
        face_stack = []
        for iuvlayer,uvlayer in enumerate(data.getUVLayerNames()):
            if iuvlayer < 8:
                data.activeUVLayer = uvlayer
                if data.faceUV and face.image:
                    img_found = 1
                    for i in xrange(len(texs_stack)-1):
                        if texs_stack[i][0] == face.image.name:
                            if texs_stack[i][1] == sets_stack[obj_count][iuvlayer]:
                                img_id = i
                else:
                    img_id = -1

                face_stack.insert(iuvlayer,img_id)

        for i in xrange(len(face_stack),texs_stack[-1]):
            face_stack.append(-1)

        if img_found == 0:
            brus_id = -1
            if data.materials:
                if data.materials[face.mat]:
                    mat_name = data.materials[face.mat].name
                    for i in xrange(len(brus_stack)):
                        if brus_stack[i] == mat_name:
                            brus_id = i
            else:
                for i in xrange(len(brus_stack)):
                    if brus_stack[i] == face_stack:
                        brus_id = i
        else:
            brus_id = -1
            for i in xrange(len(brus_stack)):
                if brus_stack[i] == face_stack:
                    brus_id = i

        if last_brus <> brus_id:
            if brus_written == 0:
                brus_written = 1
            else:
                if len(temp_buf) > 0:
                    tris_buf += write_chunk("TRIS",temp_buf)
                    temp_buf = ""

            temp_buf += write_int(brus_id) #Brush ID
            last_brus = brus_id

        face_id = [0,0,0,0]

        if data.faceUV:
            for i in xrange(len(face.verts)):
                for iuv in xrange(len(mesh_stack[face.v[i].index][4][0])):
                    if mesh_stack[face.v[i].index][4][0][iuv][0] == face.index:
                        face_id[i] = mesh_stack[face.v[i].index][0] + iuv
        else:
            for i in xrange(len(face.verts)):
                face_id[i] = mesh_stack[face.v[i].index][0]

        temp_buf += write_int(face_id[2]) #A
        temp_buf += write_int(face_id[1]) #B
        temp_buf += write_int(face_id[0]) #C

        if len(face.v) == 4:
            temp_buf += write_int(face_id[3]) #A
            temp_buf += write_int(face_id[2]) #B
            temp_buf += write_int(face_id[0]) #C

    if orig_uvlayer:
        data.activeUVLayer = orig_uvlayer

    if len(temp_buf) > 0:
        tris_buf += write_chunk("TRIS",temp_buf)
        temp_buf = ""

    return tris_buf

#Write NODE ANIM Chunk
def write_node_anim(num_frames):
    anim_buf = ""
    temp_buf = ""

    temp_buf += write_int(0) #Flags
    temp_buf += write_int(num_frames) #Frames
    temp_buf += write_float(60) #FPS

    if len(temp_buf) > 0:
        anim_buf += write_chunk("ANIM",temp_buf)
        temp_buf = ""

    return anim_buf

#Write NODE NODE Chunk
def write_node_node(ibone):
    node_buf = ""
    temp_buf = ""

    matrix = bone_stack[ibone][0]
    temp_buf += write_string(bone_stack[ibone][2].name) #Node Name

    position = matrix.translationPart()
    temp_buf += write_float(-position[0]) #Position X
    temp_buf += write_float(position[1])  #Position Y
    temp_buf += write_float(position[2])  #Position Z

    scale = matrix.scalePart()
    temp_buf += write_float(scale[0]) #Scale X
    temp_buf += write_float(scale[1]) #Scale Y
    temp_buf += write_float(scale[2]) #Scale Z

    quat = matrix.toQuat()
    quat.normalize()

    temp_buf += write_float(quat.w)  #Rotation W
    temp_buf += write_float(-quat.x) #Rotation X
    temp_buf += write_float(quat.y)  #Rotation Y
    temp_buf += write_float(quat.z)  #Rotation Z

    temp_buf += write_node_bone(ibone)
    temp_buf += write_node_keys(ibone)

    for iibone in xrange(len(bone_stack)):
        if bone_stack[iibone][1] == bone_stack[ibone][2]:
            temp_buf += write_node_node(iibone)

    if len(temp_buf) > 0:
        node_buf += write_chunk("NODE",temp_buf)
        temp_buf = ""

    return node_buf

#Write NODE BONE Chunk
def write_node_bone(ibone):
    bone_buf = ""
    temp_buf = ""

    for ivert in xrange(len(mesh_stack)):
        for iuv in xrange(len(mesh_stack[ivert][4][0])):
            for vert_influ in mesh_stack[ivert][5]:
                if bone_stack[ibone][2].name == vert_influ[0]:
                    temp_buf += write_int(mesh_stack[ivert][0] + iuv) # Face Vertex ID
                    temp_buf += write_float(vert_influ[1]) #Weight

    bone_buf += write_chunk("BONE",temp_buf)
    temp_buf = ""

    return bone_buf

#Write NODE KEYS Chunk
def write_node_keys(ibone):
    keys_buf = ""
    temp_buf = ""

    temp_buf += write_int(7) #Flags

    for ikeys in xrange(len(keys_stack)):
        if keys_stack[ikeys][1] == bone_stack[ibone][2].name:
            temp_buf += write_int(keys_stack[ikeys][0]) #Frame

            position = keys_stack[ikeys][2]
            temp_buf += write_float(-position[0]) #Position X
            temp_buf += write_float(position[1])  #Position Y
            temp_buf += write_float(position[2])  #Position Z

            scale = keys_stack[ikeys][3]
            temp_buf += write_float(scale[0]) #Scale X
            temp_buf += write_float(scale[1]) #Scale Y
            temp_buf += write_float(scale[2]) #Scale Z

            quat = keys_stack[ikeys][4]
            quat.normalize()

            temp_buf += write_float(quat.w)  #Rotation W
            temp_buf += write_float(-quat.x) #Rotation X
            temp_buf += write_float(quat.y)  #Rotation Y
            temp_buf += write_float(quat.z)  #Rotation Z

    keys_buf += write_chunk("KEYS",temp_buf)
    temp_buf = ""

    return keys_buf

#Handle Event
def handle_button(event):
    global EVENT_ALL,EVENT_SEL
    global EVENT_NOR,EVENT_COL,EVENT_CAM,EVENT_LIG
    global EVENT_EXP,EVENT_QUI

    if event == EVENT_ALL:
        flag_stack[0] = 1-flag_stack[0] #All Objects
        flag_stack[1] = 1-flag_stack[1] #Selected Only
        Blender.Draw.Redraw(1)

    if event == EVENT_SEL:
        flag_stack[1] = 1-flag_stack[1] #Selected Only
        flag_stack[0] = 1-flag_stack[0] #All Objects
        Blender.Draw.Redraw(1)

    if event == EVENT_NOR:
        flag_stack[2] = 1-flag_stack[2] #Vertex Normals
        Blender.Draw.Redraw(1)

    if event == EVENT_COL:
        flag_stack[3] = 1-flag_stack[3] #Vertex Colors
        Blender.Draw.Redraw(1)

    if event == EVENT_CAM:
        flag_stack[4] = 1-flag_stack[4] #Cameras
        Blender.Draw.Redraw(1)

    if event == EVENT_LIG:
        flag_stack[5] = 1-flag_stack[5] #Lights
        Blender.Draw.Redraw(1)

    if event == EVENT_EXP:
        tmp_filename = Blender.sys.makename(ext = ".b3d")
        Blender.Window.FileSelector(savefile_callback,"Export B3D",tmp_filename)

    if event == EVENT_QUI:
        Blender.Draw.Exit()

#Handle GUI
def handle_event(event,value):
    if event == Blender.Draw.ESCKEY:
        Blender.Draw.Exit()
        return

#Draw GUI
def draw_gui():
    global EVENT_ALL,EVENT_SEL
    global EVENT_NOR,EVENT_COL,EVENT_CAM,EVENT_LIG
    global EVENT_EXP,EVENT_QUI
    button_width = 222
    button_height = 20

    def draw_rect(x,y,width,height):
        glBegin(GL_LINE_LOOP)
        glVertex2i(x,y)
        glVertex2i(x+width,y)
        glVertex2i(x+width,y-height)
        glVertex2i(x,y-height)
        glEnd()

    Blender.BGL.glClearColor(34.0/255.0,85.0/255.0,136.0/255.0,1.0)
    Blender.BGL.glClear(Blender.BGL.GL_COLOR_BUFFER_BIT)

    glColor3f(170.0/255.0,255.0/255.0,255.0/255.0)
    draw_rect(20,330,262,310)
    draw_rect(22,328,258,306)

    glColor3f(255.0/255.0,238.0/255.0,0.0/255.0)
    glRasterPos2i(70,300)
    Draw.Text("Blitz3D Exporter 2.06",'large')

    Blender.Draw.Toggle("All Objects",EVENT_ALL,40,13*button_height,button_width,button_height,flag_stack[0],"Export All Scene Objects")
    Blender.Draw.Toggle("Selected Only",EVENT_SEL,40,12*button_height,button_width,button_height,flag_stack[1],"Export Only Selected Objects")

    Blender.Draw.Toggle("Normals",EVENT_NOR,40,10*button_height,button_width,button_height,flag_stack[2],"Export Vertex Normals")
    Blender.Draw.Toggle("Vertex Colors",EVENT_COL,40,9*button_height,button_width,button_height,flag_stack[3],"Export Vertex Colors")
    Blender.Draw.Toggle("Cameras",EVENT_CAM,40,8*button_height,button_width,button_height,flag_stack[4],"Export Cameras")
    Blender.Draw.Toggle("Lights",EVENT_LIG,40,7*button_height,button_width,button_height,flag_stack[5],"Export Lights")

    Blender.Draw.Button("Export",EVENT_EXP,40,5*button_height,button_width,button_height,"Export to B3D")
    Blender.Draw.Button("Quit",EVENT_QUI,40,4*button_height,button_width,button_height,"Quit this script")

    glRasterPos2i(36,55)
    Draw.Text("Copyright 2009 Diego Parisi",'small')
    glRasterPos2i(105,37)
    Draw.Text("www.diegoparisi.com",'small')

Blender.Draw.Register(draw_gui,handle_event,handle_button)

#Callback Functions
def savefile_callback(filename):
    if filename == "":
        return

    if not filename.endswith(".b3d"):
	filename += ".b3d"

    if Blender.sys.exists(filename):
	result = Draw.PupMenu("File Already Exists, Overwrite?%t|Yes%x1|No%x0")
	if result != 1:
	    return

    start = Blender.sys.time()
    write_b3d_file(filename)
    end = Blender.sys.time()
    print "%s"%Blender.sys.basename(filename)+" successfully exported in %.4f seconds"%(end-start)
    Blender.Draw.Exit()
    return

#Export B3D
def export_b3d():
    flag_stack.append(1) #All Objects
    flag_stack.append(0) #Selected Only
    flag_stack.append(0) #Vertex Normals
    flag_stack.append(0) #Vertex Colors
    flag_stack.append(0) #Cameras
    flag_stack.append(0) #Lights

    draw_gui()

#Main
def main():

    export_b3d()

if __name__ == "__main__":
    main()
