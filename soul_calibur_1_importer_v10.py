import struct
import bpy
import bmesh
import os
from math import radians
import numpy as np
from mathutils import Vector, Matrix, Euler

def read_little_endian_uint32(file):
    return struct.unpack("<I", file.read(4))[0]

def read_little_endian_uint16(file):
    return struct.unpack("<H", file.read(2))[0]

def read_little_endian_uint8(file):
    return struct.unpack("<b", file.read(1))[0]

def read_little_endian_int16(file):
    return struct.unpack("<h", file.read(2))[0]

def read_little_endian_f16_2(file):
    u = struct.unpack("<H", file.read(2))[0]
    v = struct.unpack("<H", file.read(2))[0]
    u = u << 16
    v = v << 16
    uu = struct.unpack("<f", u.to_bytes(4, byteorder='little'))[0]
    vv = struct.unpack("<f", v.to_bytes(4, byteorder='little'))[0]
    return (vv,1-uu)
def read_little_endian_s16_2(file):
    u = struct.unpack("<H", file.read(2))[0] / 65535
    v = struct.unpack("<H", file.read(2))[0] / 65535
    return (u,v)

def read_little_endian_float(file):
    return struct.unpack("<f", file.read(4))[0]

def reset_msb(value, bit_width=16):
    # Create a mask with all bits set except the MSB
    mask = (1 << (bit_width - 1)) - 1
    # Reset the MSB using bitwise AND
    return value & mask

def create_material(mat_name, diffuse_color=(1,1,1,1)):
    mat = bpy.data.materials.new(name=mat_name)
    mat.diffuse_color = diffuse_color
    return mat

def build_bones(table1, chr_index=0, transform_corrections=True):
    """Builds a bone transformation list from table1."""
    bone_trans = []
    
    for bone_data in table1:
        # Unpack rotation and position data
        rot_x, rot_y, rot_z = bone_data["bone_rotation"]
        pos_x, pos_y, pos_z = bone_data["bone_position"]
        
        # Normalize int16 rotations (0–65535) to radians in the range [-π, π]
        angle_x = rot_x / 32767.0 * 3.14159
        angle_y = rot_y / 32767.0 * 3.14159
        angle_z = rot_z / 32767.0 * 3.14159
        
        # Create a rotation matrix from Euler angles (assuming 'XYZ' order)
        euler = Euler((angle_x, angle_y, angle_z), 'XYZ')
        rotation = euler.to_matrix().to_4x4()
        
        # Convert position (assuming the positions need to be scaled by 1/16000)
        translation = Matrix.Translation((pos_x / 16000.0, pos_y / 16000.0, pos_z / 16000.0))
        
        # Combine translation and rotation (order: translation first, then rotation)
        transform = translation @ rotation
        bone_trans.append(transform)
    
    # Apply parent transformations to convert from local to world space
    for i, bone_data in enumerate(table1):
        parent_idx = bone_data["parent_bone_id"]
        if 0 <= parent_idx < len(bone_trans):
            bone_trans[i] = bone_trans[parent_idx] @ bone_trans[i]
    
    return bone_trans

def create_armature(submeshes):
    armature = bpy.data.armatures.new("SoulCaliburArmature")
    armature_obj = bpy.data.objects.new("SoulCaliburArmature", armature)
    bpy.context.collection.objects.link(armature_obj)
    
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    bones = {}
    bone_transforms = build_bones(submeshes)
    
    for bone_index, submesh in enumerate(submeshes):
        bone_name = f"Bone_{bone_index}"
        bone = armature.edit_bones.new(bone_name)
        
        transform = bone_transforms[bone_index]
        position = transform.to_translation()
        
        bone.head = position
        bone.tail = position + Vector((0, 0.1, 0))
        bones[bone_index] = bone
    
    for bone_index, submesh in enumerate(submeshes):
        parent_idx = submesh["parent_bone_id"]
        if parent_idx >= 0 and parent_idx in bones:
            bones[bone_index].parent = bones[parent_idx]
    
    bpy.ops.object.mode_set(mode='OBJECT')
    return armature_obj

def import_soul_calibur_model(filepath):
    with open(filepath, "rb") as file:
        # Read the main header
        filename = file.read(24)
        triangle_strip_table_pointer = read_little_endian_uint32(file)
        submesh_count = read_little_endian_uint16(file)
        strip_counter = read_little_endian_uint16(file)

        print(f"Filename: {filename}")
        print(f"Triangle Strip Table Pointer: {triangle_strip_table_pointer}")
        print(f"Header Length: {submesh_count}")
        
        submesh_id = 0

        # Read submesh headers
        submeshes = []
        for x in range(submesh_count):
            vertex_count = read_little_endian_uint16(file)
            corrective_count = read_little_endian_uint16(file)
            vertex_list_pointer = read_little_endian_uint32(file)
            unknown = read_little_endian_uint32(file)
            unk1 = read_little_endian_uint16(file)
            unk2 = read_little_endian_uint16(file)
            bone_rotation_x = read_little_endian_int16(file)
            bone_rotation_y = read_little_endian_int16(file)
            bone_rotation_z = read_little_endian_int16(file)
            unknown2 = read_little_endian_int16(file)
            bone_position_x = read_little_endian_int16(file)
            bone_position_y = read_little_endian_int16(file)
            bone_position_z = read_little_endian_int16(file)
            parent_bone_id = read_little_endian_int16(file)

            submeshes.append({
                "vertex_count": vertex_count,
                "corrective_count": corrective_count,
                "vertex_list_pointer": vertex_list_pointer,
                "bone_rotation": (bone_rotation_x, bone_rotation_y, bone_rotation_z),
                "bone_position": (bone_position_x, bone_position_y, bone_position_z),
                "parent_bone_id": parent_bone_id,
            })
        
        bone_transforms = build_bones(submeshes)
        
        # Create the armature first
        armature_obj = create_armature(submeshes)
        
        # Create a new Blender object for the model
        mesh = bpy.data.meshes.new("SoulCaliburModel")
        obj = bpy.data.objects.new("SoulCaliburModel", mesh)
        bpy.context.collection.objects.link(obj)
        currMats = []
        # Add vertex groups for each bone
        for bone_index in range(len(submeshes)):
            obj.vertex_groups.new(name=f"Bone_{bone_index}")

        bm = bmesh.new()
        uvlayers = []
        uvids = []
        altUV = bm.loops.layers.uv.new()
        
        # Create all possible vertices (4096 due to 12-bit indexing)
        base_vertices = [bm.verts.new((0, 0, 0)) for _ in range(4096)]
        bm.verts.ensure_lookup_table()

        # Track which vertices are actually used by each bone
        bone_vertex_indices = {bone_index: set() for bone_index in range(len(submeshes))}

        # Process all vertices
        for bone_index, submesh in enumerate(submeshes):
            file.seek(submesh["vertex_list_pointer"])
            bone_matrix = bone_transforms[bone_index]
            
            for vertex_idx in range(submesh["vertex_count"]+submesh["corrective_count"]):
                vertex_x = read_little_endian_float(file)
                vertex_y = read_little_endian_float(file)
                vertex_z = read_little_endian_float(file)
                w_component = read_little_endian_float(file)
                
                # Extract vertex index from w component's upper bits
                w_bytes = struct.pack('f', w_component)
                vertex_index = (w_bytes[1] << 8) | w_bytes[0]  # First two bytes contain the index
                
                # Get target vertex index (12 bits)
                target_index = vertex_index & 0xFFF
                
                vertex = Vector((vertex_x, vertex_y, vertex_z, w_component))
                transformed_vertex = bone_matrix @ vertex
                
                if vertex_index < 32768:
                    print(f"Vertex: {vertex_index}")
                    base_vertices[target_index].co = transformed_vertex.xyz
                    bone_vertex_indices[bone_index].add(target_index)
                else:
                    print(f"Corrective: {vertex_index}")
                    base_vertices[target_index].co += transformed_vertex.xyz
                    bone_vertex_indices[bone_index].add(target_index)
            
        
                    

        # Read triangle strips
        file.seek(triangle_strip_table_pointer)
        strip_inc = 0
    
        while(1):
            # Read the strip header
            mat_idx = read_little_endian_uint8(file)
            if(not mat_idx in currMats):
                currMats.append(mat_idx)
                obj.data.materials.append(create_material(str("Mat_%04i"%mat_idx)))
            
            unk_uv = read_little_endian_uint16(file)
            if(not unk_uv in uvids):
                uv_layer = bm.loops.layers.uv.new()
                uvlayers.append(uv_layer)
                uvids.append(unk_uv)
                
            else:
                uv_layer = uvlayers[uvids.index(unk_uv)]
                
            
            strip_length = read_little_endian_uint8(file)
            strip_inc += 1
        
            #print(f'Strip No.: {strip_inc}')
            print(hex(strip_length))
        
            # Check for the end of triangle strips
            if strip_length == 0:
                # Peek ahead to confirm end of strips
                next_unk_uv = read_little_endian_uint16(file)
                next_unk_uv = read_little_endian_uint8(file)
                next_strip_length = read_little_endian_uint8(file)
        
                if next_strip_length == 0:
                    # Double-zero terminator detected, end of strips
                    break
                else:
                    # Not the end, rewind to process the next strip
                    file.seek(-4, os.SEEK_CUR)
                    continue
        
            # Process the current triangle strip
            triangles = []
            uvtri = []
            for _ in range(strip_length):
                vertex_index = read_little_endian_uint16(file)
                vertex_color = read_little_endian_uint16(file)
                print(f"vertex_index: {vertex_index}")
                uv_coordinates = read_little_endian_f16_2(file)
                triangles.append(vertex_index)
                uvtri.append(uv_coordinates)
        
        
            # Create faces from the current triangle strip
            
            for i in range(len(triangles) - 2):
                try:
                    v1 = bm.verts[triangles[i]]
                    v2 = bm.verts[triangles[i + 1]]
                    v3 = bm.verts[triangles[i + 2]]
        
                    # Handle winding order
                    if i % 2 == 0:  # Even winding
                        face_verts = [v1, v2, v3]
                    else:           # Odd winding (reverse)
                        face_verts = [v1, v3, v2]
        

                    if not bm.faces.get(face_verts):
                        bm.faces.new(face_verts)
                        bm.faces.get(face_verts).loops[0][uv_layer].uv = uvtri[i+0]
                        if i % 2 == 0:
                            bm.faces.get(face_verts).loops[2][uv_layer].uv = uvtri[i+1]
                            bm.faces.get(face_verts).loops[1][uv_layer].uv = uvtri[i+2]
                        else:
                            bm.faces.get(face_verts).loops[2][uv_layer].uv = uvtri[i+1]
                            bm.faces.get(face_verts).loops[1][uv_layer].uv = uvtri[i+2]
                    else:
                        bm.faces.get(face_verts).loops[0][altUV].uv = uvtri[i+2]
                        if i % 2 == 0:
                            bm.faces.get(face_verts).loops[1][altUV].uv = uvtri[i+1]
                            bm.faces.get(face_verts).loops[2][altUV].uv = uvtri[i+0]
                        else:
                            bm.faces.get(face_verts).loops[1][altUV].uv = uvtri[i+0]
                            bm.faces.get(face_verts).loops[2][altUV].uv = uvtri[i+1]
                    bm.faces.get(face_verts).material_index = currMats.index(mat_idx)
                    
                    print(f'Drawing face: {triangles[i]}, {triangles[i + 1]}, {triangles[i + 2]}')
        
                except IndexError as e:
                    print(f"Invalid triangle indices: {triangles[i]}, {triangles[i + 1]}, {triangles[i + 2]} (Error: {e})")
                except ValueError as e:
                    print(f"Face creation error: {e}")
            
            bm.faces.ensure_lookup_table()
        
        # Apply the mesh to the object
        bm.to_mesh(mesh)
        bm.free()
        
        # Apply vertex weights - each vertex is weighted to bones that influenced it
        for bone_index, vertex_indices in bone_vertex_indices.items():
            if vertex_indices:  # Only add if there are vertices
                vertex_group = obj.vertex_groups[f"Bone_{bone_index}"]
                vertex_group.add(list(vertex_indices), 1.0, 'REPLACE')

        # Add armature modifier
        armature_mod = obj.modifiers.new(name="Armature", type='ARMATURE')
        armature_mod.object = armature_obj
        obj.parent = armature_obj
        
        print("Model imported successfully with armature!")

# Usage
os.chdir(r'C:\Users\smb12\Desktop\SC2\SC1\Dreamcast\USA\Human\191.bin_Extract\0000.bin_Extract')
os.system("cls")
import_soul_calibur_model("0000.bin.dec")