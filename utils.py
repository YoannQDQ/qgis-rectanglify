# -*- coding: utf-8 -*-
"""
Utilities functions for the rectanglify plugin
"""
import math

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


def minimum_bounding_box(feature):
    """Compute the minimum oriented bounding box for the given feature
    Works around a bug in QgsGeometry orientedMinimumBoundingBox
    (https://github.com/qgis/QGIS/pull/34334)

    Args:
        feature (QgsFeature): Input feature

    Returns:
        QgsGeometry: Minimum bounding box
    """

    hull = feature.geometry().convexHull()
    if hull.isEmpty():
        return hull

    min_geom, min_area = oriented_bounding_box(hull)

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
        point_0 = point_1

    return min_geom
