# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Rectanglify
 A QGIS plugin
 Add a digitizing tool which "rectanglifies" selected features of a polygon vector layer

                              -------------------
        begin                : 2020-04-28
        git sha              : $Format:%H$
        copyright            : (C) 2020 Yoann Quenach de Quivillic
        email                : yoann.quenach@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import math

from qgis.core import (
    QgsVectorLayer,
    QgsGeometry,
    QgsPointXY,
    QgsGeometryUtils,
)


class BeginCommand:
    def __init__(self, layer, command_name):
        self.layer: QgsVectorLayer = layer
        self.command_name = command_name

    def __enter__(self):
        if not self.layer.isEditable():
            self.layer.startEditing()
        self.layer.beginEditCommand(self.command_name)

    def __exit__(self, type, value, traceback):
        if type:
            self.layer.destroyEditCommand()
        else:
            self.layer.endEditCommand()
        self.layer.triggerRepaint()


def oriented_bounding_box(geometry, angle=0):
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
