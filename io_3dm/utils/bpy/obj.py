# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import bmesh
import mathutils

from . import meta

#CREDIT: https://blender.stackexchange.com/a/159540
def apply_transform(ob, loc=False, rot=False, sca=False):
    mb = ob.matrix_basis
    I = Matrix()
    loc, rot, scale = mb.decompose()

    T = Matrix.Translation(loc)
    R = mb.to_3x3().normalized().to_4x4()
    S = Matrix.Diagonal(scale).to_4x4()

    transform = [I, I, I]
    basis = [T, R, S]
    def swap(i):
        transform[i], basis[i] = basis[i], transform[i]
    if loc:
        swap(0)
    if rot:
        swap(1)
    if sca:
        swap(2)
    M = transform[0] @ transform[1] @ transform[2]
    if hasattr(ob.data, "transform"):
        ob.data.transform(M)
    for c in ob.children:
        c.matrix_local = M @ c.matrix_local
    ob.matrix_basis = basis[0] @ basis[1] @ basis[2]
    return None

#CREDIT: https://blenderartists.org/t/joining-objects-in-edit-mode/1158066/2
def join(target, source, remove_doubles=False):
    new = bmesh.new()
    new.from_mesh(target.data)
    temp = bpy.data.meshes.new("temp")
    for blob in source:
        if blob.type == 'MESH':
            _bmesh = bmesh.new()
            _bmesh.from_mesh(blob.data)
            _bmesh.transform(blob.matrix_world)
            _bmesh.to_mesh(temp)
            _bmesh.free()
            mimic_materials(blob, target, temp)
            new.from_mesh(temp)
    bpy.data.meshes.remove(temp)
    if remove_doubles:
        bmesh.ops.remove_doubles(new, verts=new.verts, dist=0.001)
    new.to_mesh(target.data)
    new.free()
    return None

#CREDIT: https://blenderartists.org/t/joining-objects-in-edit-mode/1158066/2
def mimic_materials(source, target, temp):
    s_slots = source.material_slots
    t_slots = target.material_slots

    if not s_slots:
         return None

    matlist = [s_slots[face.material_index].material for face in source.data.polygons]
    # Eliminates namespace lookups == faster loops
    append = target.data.materials.append
    find = target.material_slots.find

    # Add source material to target if it doesn't exist
    for slot in s_slots:
        mat = slot.material
        if mat is not None:
            if mat.name not in t_slots:
                append(mat)

    # assign the correct material index to faces in temp mesh
    for p, mat in zip(temp.polygons, matlist):
        p.material_index = find(mat.name)
    return None

def obt(name, data=None, local=False, force=False, overwrite=None, parent=None, hollow=True):
    scope = None

    if local:
        scope = bpy.context.scene.objects

    if data is None and hollow:
        data = meta.obt(
            bpy.data.meshes,
            name,
            force = force,
            overwrite = overwrite,
        )

    blob = meta.obt(
        bpy.data.objects,
        name,
        data = data,
        scope = scope,
        force = force,
        overwrite = overwrite,
    )

    if parent is not None and blob is not None and blob.name not in parent.objects:
        parent.objects.link(blob)
    return blob

def unlink(blcol, objects=False, recursive=False):
    if recursive:
        collections = [c for c in blcol.children]
        while collections:
            child = collections.pop()
            unlink(child, recursive=True, objects=objects)
            blcol.children.unlink(child)
    if objects:
        objects = [o for o in blcol.objects]
        while objects:
            blcol.objects.unlink(objects.pop())
    return None

def remove(blob, purge_data=True, recursive=True):
    if recursive:
        objects = [o for o in blob.children if o.users <= 1]
        while objects:
            remove(objects.pop(), data=True, recursive=True)
    if purge_data and blob.data.users <= 1:
        match blob.type:
            case 'MESH':
                bpy.data.meshes.remove(blob.data)
            case 'EMPTY':
                pass
            case 'CAMERA':
                bpy.data.cameras.remove(blob.data)
                return None
            case _:
                pass
    if blob is not None:
        bpy.data.objects.remove(blob)
    return None
