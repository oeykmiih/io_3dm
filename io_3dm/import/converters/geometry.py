# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import bmesh
import mathutils
import math
import rhino3dm

def vector(rhvector):
    match type(rhvector):
        case rhino3dm.Vector3d:
            blvector = mathutils.Vector((rhvector.X, rhvector.Y, rhvector.Z))
        case rhino3dm.Vector2d:
            blvector = mathutils.Vector((rhvector.X, rhvector.Y, rhvector.Z))
        case rhino3dm.Point4d:
            blvector = mathutils.Vector((rhvector.X, rhvector.Y, rhvector.Z, rhvector.W))
        case rhino3dm.Point3d:
            blvector = mathutils.Vector((rhvector.X, rhvector.Y, rhvector.Z))
        case rhino3dm.Point2d:
            blvector = mathutils.Vector((rhvector.X, rhvector.Y))
    return blvector

def mesh(rhob, scale, options):
    # Get meshes
    match rhob.Geometry.ObjectType:
        case rhino3dm.ObjectType.Extrusion:
            rhmesh = [rhob.Geometry.GetMesh(rhino3dm.MeshType.Any)]
        case rhino3dm.ObjectType.Mesh:
            rhmesh = [rhob.Geometry]
        case rhino3dm.ObjectType.SubD:
            rhmesh = [rhino3dm.Mesh.CreateFromSubDControlNet(rhob.Geometry)]
        case rhino3dm.ObjectType.Brep:
            rhmesh = [rhob.Geometry.Faces[f].GetMesh(rhino3dm.MeshType.Any) for f in range(len(rhob.Geometry.Faces)) if type(rhob.Geometry.Faces[f])!=list]

    findex = 0
    faces = []
    vertices = []

    # Add faces and vertices to lists
    for mesh in rhmesh:
        if mesh:
            rhmesh_join(mesh)
            mesh.Faces.CullDegenerateFaces()
            mesh.Faces.ConvertTrianglesToQuads(math.pi / 90.0, 0.875)

            faces.extend([list(map(lambda x: x + findex, mesh.Faces[f])) for f in range(len(mesh.Faces))])

            # Rhino always uses 4 values to describe faces, which can lead to
            ## invalid faces in Blender. Tris will have a duplicate index for the 4th
            ## value.
            for f in faces:
                if f[-1] == f[-2]:
                    del f[-1]

            findex = findex + len(mesh.Vertices)
            vertices.extend([(mesh.Vertices[v].X * scale, mesh.Vertices[v].Y * scale, mesh.Vertices[v].Z * scale) for v in range(len(mesh.Vertices))])

    blmesh = bpy.data.meshes.new(name=str(rhob.Attributes.Id)) # Create empty mesh
    blmesh.from_pydata(vertices, [], faces)
    return blmesh

def rhmesh_join(mesh):
    return None

def rhmesh_remove_doubles(mesh):
    mesh.Vertices.CombineIdentical(True, True)
    return mesh

def curve(rhob, scale, options):
    blcurve = bpy.data.curves.new(name=str(rhob.Attributes.Id), type='CURVE') # Create empty curve
    _IMPORT_CURVE[type(rhob.Geometry)](rhob.Geometry, blcurve, scale)
    return blcurve

def curve_line(rcurve, bcurve, scale):
    fr = rcurve.Line.From
    to = rcurve.Line.To
    line = bcurve.splines.new('POLY')
    line.points.add(1)
    line.points[0].co = (fr.X * scale, fr.Y * scale, fr.Z * scale, 1)
    line.points[1].co = (to.X * scale, to.Y * scale, to.Z * scale, 1)
    return line

def curve_polyline(rcurve, bcurve, scale):
    N = rcurve.PointCount
    polyline = bcurve.splines.new('POLY')

    polyline.use_cyclic_u = rcurve.IsClosed
    if rcurve.IsClosed:
        N -= 1

    polyline.points.add(N - 1)
    for i in range(0, N):
        rpt = rcurve.Point(i)
        polyline.points[i].co = (rpt.X * scale, rpt.Y * scale, rpt.Z * scale, 1)
    return polyline

def curve_nurbs(rcurve, bcurve, scale):
    N = len(rcurve.Points)

    nurbs = bcurve.splines.new('NURBS')
    nurbs.use_cyclic_u = rcurve.IsClosed

    nurbs.points.add(N - 1)
    for i in range(0, N):
        rpt = rcurve.Points[i]
        nurbs.points[i].co = (rpt.X * scale, rpt.Y * scale, rpt.Z * scale, rpt.W * scale)

    nurbs.use_endpoint_u = True
    nurbs.order_u = rcurve.Order
    return nurbs

def curve_arc(rcurve, bcurve, scale):
    spt = mathutils.Vector((rcurve.Arc.StartPoint.X, rcurve.Arc.StartPoint.Y, rcurve.Arc.StartPoint.Z)) * scale
    ept = mathutils.Vector((rcurve.Arc.EndPoint.X, rcurve.Arc.EndPoint.Y, rcurve.Arc.EndPoint.Z)) * scale
    cpt = mathutils.Vector((rcurve.Arc.Center.X, rcurve.Arc.Center.Y, rcurve.Arc.Center.Z)) * scale

    r1 = spt - cpt
    r2 = ept - cpt

    r1.normalize()
    r2.normalize()

    d = rcurve.Arc.Length * scale

    normal = r1.cross(r2)

    t1 = normal.cross(r1)
    t2 = normal.cross(r2)

    arc = bcurve.splines.new('NURBS')

    arc.use_cyclic_u = False

    arc.points.add(3)

    arc.points[0].co = (spt.x, spt.y, spt.z, 1)

    sspt = spt + t1 * d * 0.33
    arc.points[1].co = (sspt.x, sspt.y, sspt.z, 1)

    eept = ept - t2 * d * 0.33
    arc.points[2].co = (eept.x, eept.y, eept.z, 1)

    arc.points[3].co = (ept.x, ept.y, ept.z, 1)

    arc.use_endpoint_u = True
    arc.order_u = 3
    return arc

def curve_polycurve(rcurve, bcurve, scale):
    for seg in range(rcurve.SegmentCount):
        segcurve = rcurve.SegmentCurve(seg)
        if type(segcurve) in _IMPORT_CURVE.keys():
            _IMPORT_CURVE[type(segcurve)](segcurve, bcurve, scale)
    return None

_IMPORT_CURVE = {
    rhino3dm.ArcCurve : curve_arc,
    rhino3dm.LineCurve : curve_line,
    rhino3dm.NurbsCurve : curve_nurbs,
    rhino3dm.PolylineCurve : curve_polyline,
    rhino3dm.PolyCurve : curve_polycurve,
}

RHINO_IMPORT_DEFAULT = {
    rhino3dm.ObjectType.Brep : mesh,
    rhino3dm.ObjectType.Extrusion : mesh,
    rhino3dm.ObjectType.Mesh : mesh,
    rhino3dm.ObjectType.SubD : mesh,
    rhino3dm.ObjectType.Curve : curve,
    rhino3dm.ObjectType.InstanceReference : None,
}

RHINO_IMPORT = RHINO_IMPORT_DEFAULT.copy()
