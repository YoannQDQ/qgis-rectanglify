# -*- coding: utf-8 -*-
"""
Utilities functions for the rectanglify plugin
"""
import math

from PyQt5.QtGui import QTransform

from qgis.core import (
    QgsVectorLayer,
    QgsGeometry,
    QgsPointXY,
    QgsGeometryUtils,
)


class BeginCommand:
    """
    Context Manager that starts an edit command and ensure it is not kept hanging.
    """

    def __init__(self, layer, command_name):
        self.layer: QgsVectorLayer = layer
        self.command_name = command_name

    def __enter__(self):
        if not self.layer.isEditable():
            self.layer.startEditing()
        self.layer.beginEditCommand(self.command_name)

    def __exit__(self, exception_type, value, traceback):
        if exception_type is not None:
            self.layer.destroyEditCommand()
        else:
            self.layer.endEditCommand()
        self.layer.triggerRepaint()


def oriented_bounding_box(geometry, angle=0):
    """Compute the oriented bounding box of the geometry at a given angle

    Args:
        geometry (QgsGeometry): Input geometry
        angle (int, optional): Angle. Defaults to 0.

    Returns:
        (QgsGemetry, double): Computed oriented bounding box and its area
    """
    hull = geometry.convexHull()
    if hull.isEmpty():
        return hull
    point_0 = hull.vertexAt(0)
    hull.rotate(angle, QgsPointXY(point_0.x(), point_0.y()))
    oob = hull.boundingBox()
    res = QgsGeometry.fromRect(oob)
    res.rotate(-angle, QgsPointXY(point_0.x(), point_0.y()))
    return res, oob.area()


def minimum_bounding_box(geometry):
    """Compute the minimum oriented bounding box for the given geometry
    Works around a bug in QgsGeometry orientedMinimumBoundingBox
    (https://github.com/qgis/QGIS/pull/34334)

    Args:
        geometry (QgsGeometry): Input feature

    Returns:
        QgsGeometry: Minimum bounding box
    """

    hull = geometry.convexHull()
    if hull.isEmpty():
        return hull

    min_geom, min_area = None, math.inf
    min_angle = None

    point_0 = None
    for vertex in hull.vertices():
        if point_0 is None:
            point_0 = vertex
            continue
        point_1 = vertex
        angle = -math.degrees(
            QgsGeometryUtils.lineAngle(
                point_0.x(), point_0.y(), point_1.x(), point_1.y()
            )
        )
        geom, area = oriented_bounding_box(hull, angle)
        if area < min_area:
            min_geom, min_area = geom, area
            min_angle = angle
        point_0 = point_1

    return min_geom, min_angle


def scale_geometry(geometry, area_ratio):
    """Scale the geometry so that its new area is area_ratio * old_area

    Args:
        geometry (QgsGeometry): Input geometry
        area_ratio (double): Ratio

    Returns:
        QgsGeometry: Output Geometry. Note that the input geometry is modified in-place
    """

    centroid = geometry.centroid().asPoint()
    transform = QTransform()
    transform.translate(centroid.x(), centroid.y())
    transform.scale(area_ratio ** 0.5, area_ratio ** 0.5)
    transform.translate(-centroid.x(), -centroid.y())
    geometry.transform(transform)
    return geometry


def rectanglify_geometry(
    geometry, constant_area=True, keep_rings=True, rings_share_axes=True, angle=None
):
    """Rectanglifies the geometry. Optionally keep constannt area and rings

    Args:
        geometry (QgsGeometry): Input geometry
        constant_area (bool, optional): If True, the rectanglified geometry is scaled to
            be the same area as the old one
        keep_rings (bool, optional): If True, rectanglify will try to keep the rings.
            Note that in some cases, the rings cannot be kept. Rings are always scaled
            to keep a constant area. Defaults to True.
        rings_share_axes (bool, optional): If True, the rings orientation will match the
            outer polygon orientation. Else, Rectanglify computes a minimum oriented
            bounding box . Defaults to True.
        angle (double, optional): If specified, use it to generate an oriented bounding
            box instead of computing a minimal one. Defaults to None.

    Returns:
        QgsGeometry: Output rectanglified geometry
    """
    # If an angle is define use it. Else, compute miminum bounding box
    if angle is None:
        new_geom, angle = minimum_bounding_box(geometry)
    else:
        new_geom, _ = oriented_bounding_box(geometry, angle)

    # Try to keep rings
    if keep_rings:

        # We just care about the rings here, not the outer polygon
        _, *rings = geometry.asPolygon()

        # Recursively call rectanglify_geometry on the rings
        for ring in rings:
            ring = rectanglify_geometry(
                QgsGeometry.fromPolygonXY([ring]),
                angle=angle if rings_share_axes else None,
            ).asPolygon()[0]
            new_geom.addRing(ring)

    # Scale geometry
    if constant_area:
        old_area = geometry.area()
        new_area = new_geom.area()
        scale_geometry(new_geom, old_area / new_area)
    return new_geom
