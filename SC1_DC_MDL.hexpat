#pragma author spaztron64
#pragma description Soul Calibur 1 - Character Model Format (Dreamcast)
#pragma loop_limit 32768

import std.string;

struct vertex_list{
    float       vertex_x [[color("FF0000")]];
    float       vertex_y [[color("00FF00")]];
    float       vertex_z [[color("0000FF")]];;
    u16         vertex_index [[color("00FFFF")]];;
    u16         flags [[color("222222")]];; // It's not clear what these do
};

struct normal_list{
    float       normal_x;
    float       normal_y;
    float       normal_z;
    u16         normal_index;
    u16         flags; // It's not clear what these do
};

struct triangle{
    u16         vertex_index [[color("00FF22")]];   // Reference to a vertex index fetched from a vertex_list_t;
    u16         vertex_color [[color("4391FF")]];   // Influences shading
    u32         uv_coordinates [[color("999900")]]; // UVs  
    
};

struct triangle_strip{
    u8          uv_coordinate [[color("991122")]];  // Why are there three UV coordinates?
    u8          unknown [[color("222222")]];
    u8          unknown3 [[color("222222")]];
    u8          strip_length [[color("FF0000")]];
    triangle    triangles[strip_length];  // Array of triangle_t elements;
};

struct model_submesh{
    u8          bone_id0 [[color("338855")]]; // NULL on weapons?
    u8          bone_id1 [[color("553388")]];
    u8          unk4 [[color("222222")]];
    u8          unk5 [[color("222222")]];     
    u32         vertex_list_pointer [[color("FFAA00")]]; // points to a vertex_list_t
    u32         unknown [[color("222222")]]; // Always 0x00000000?
    u16         vertex_count [[color("2222FF")]];
    u16         normal_count [[color("FF22FF")]];
    s16         bone_rotation_x [[color("00FF99")]];
    s16         bone_rotation_y [[color("00FF99")]];;
    s16         bone_rotation_z [[color("00FF99")]];;
    s16         unknown1 [[color("222222")]];;
    s16         bone_position_x [[color("FFFF99")]];;
    s16         bone_position_y [[color("FFFF99")]];;
    s16         bone_position_z [[color("FFFF99")]];;
    s16         parent_bone_id [[color("88FF44")]];;
    
    vertex_list VLists[vertex_count] @ vertex_list_pointer [[sealed]];
    normal_list NLists[normal_count] @ vertex_list_pointer+(vertex_count*16) [[sealed]];
   
};

struct main_header{
    char           filename[24] [[color("FF0000")]]; // 24 character filename that doesn't really contain anything useful
    u32            triangle_strip_table_pointer [[color("AA55FF")]]; // points to the first triangle_strip_t;
    u8             submesh_count [[color("88121F")]]; // How many model_submesh_t instances exist;
    u8             unk1 [[color("222222")]];
    u16            strip_counter; //To figure how this works.. There is zero trips that eat up this
    model_submesh  model_submesh_table[submesh_count]; // One or more submesh headers. Usually no more than 17
};

main_header Main @ $;

triangle_strip TStrips[while(std::mem::read_unsigned($, 8) != 0)] @ Main.triangle_strip_table_pointer;

// Notes:

// All vertex_lists are in LOCAL space!
// Each of them has an associated bone transform, made up of the properties defined in model_submesh.
// The bones control the default positioning and rotation of all vertices for the given vertex_list.
// When assembled properly, the vertices will form an A-posed human. Without the transforms, the geometry
// will be clumped together at world origin.
// On Arcade, both the bones and vertices were unsigned shorts and mapped directly in 3D space.
// On Dreamcast, vertices were converted to floats, but bone transforms were kept as shorts.
// They are cast as (float)s and divided by 16000.0 each at runtime.

// I'm still not sure how mk64n managed to handle parent_bone_id, bone_id0 and bone_id1
// for forming the armature.
// Refer to the MAXScript for Arcade, since the logic remained the same on Dreamcast.

// If a triangle_strip_t's strip_length is 00, this marks the end of a single strip,
// and the next 32-bit word needs to be read as the beginning of the next triangle_strip_t. 
// If strip_length 00 is read twice in a row, this marks the end of the entire triangle strip table.
// In both cases, usually the entire 32-bit triangle_strip header word is 00000000.
// As such, DON'T rely on the strip_counter variable for counting strips, I'm only using it to tell
// ImHex to highlight stuff.

// uv_coordinate in triangle_strip is most likely a pair of 16-bit S and T coordinates for the given
// vertex in the strip. Byte 1 in triangle_strip also affects texture positioning from observations
// in Flycast during debugging, and it's not 100% clear why that's the case