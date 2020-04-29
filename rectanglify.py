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
import os.path

from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

from qgis.core import (
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsWkbTypes,
    QgsProject,
    QgsMapLayer,
)

# Initialize Qt resources from file resources.py
from .resources import *
from .utils import BeginCommand, minimum_bounding_box


class Rectanglify:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "Rectanglify_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u"&Rectanglify")

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("Rectanglify", message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.rectanglify_action = QAction(
            QIcon(":/plugins/rectanglify/actionRectanglify.svg"),
            self.tr("Rectanglify Selected Features"),
            parent=self.iface.mainWindow(),
        )

        self.rectanglify_action.triggered.connect(self.rectanglify)

        self.iface.advancedDigitizeToolBar().addAction(self.rectanglify_action)
        self.iface.editMenu().addAction(self.rectanglify_action)

        self.iface.currentLayerChanged.connect(self.update_action_state)
        self.attach_to_project()
        self.update_action_state()

    def attach_to_project(self):
        QgsProject.instance().layerWasAdded[QgsMapLayer].connect(self.connect_layer)
        self.connect_layers()

    def detach_from_project(self):
        QgsProject.instance().layerWasAdded[QgsMapLayer].disconnect(self.connect_layer)
        self.disconnect_layers()

    def connect_layers(self):
        for layer in QgsProject.instance().mapLayers().values():
            self.connect_layer(layer)

    def disconnect_layers(self):
        for layer in QgsProject.instance().mapLayers().values():
            self.disconnect_layer(layer)

    def connect_layer(self, layer):
        if (
            isinstance(layer, QgsVectorLayer)
            and layer.geometryType() == QgsWkbTypes.PolygonGeometry
        ):
            layer.editingStarted.connect(self.update_action_state)
            layer.editingStopped.connect(self.update_action_state)
            layer.selectionChanged.connect(self.update_action_state)

    def disconnect_layer(self, layer):
        if (
            isinstance(layer, QgsVectorLayer)
            and layer.geometryType() == QgsWkbTypes.PolygonGeometry
        ):
            layer.editingStarted.disconnect(self.update_action_state)
            layer.editingStopped.disconnect(self.update_action_state)
            layer.selectionChanged.disconnect(self.update_action_state)

    def update_action_state(self):

        layer: QgsVectorLayer = self.iface.activeLayer()
        enabled = (
            isinstance(layer, QgsVectorLayer)
            and layer.geometryType() == QgsWkbTypes.PolygonGeometry
            and layer.isEditable()
        )

        self.rectanglify_action.setEnabled(enabled)

        if enabled:
            if layer.selectedFeatureCount() in (0, layer.featureCount()):
                self.rectanglify_action.setText(self.tr("Rectanglify All Features"))
            else:
                self.rectanglify_action.setText(
                    self.tr("Rectanglify Selected Features")
                )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.iface.advancedDigitizeToolBar().removeAction(self.rectanglify_action)
        self.iface.editMenu().removeAction(self.rectanglify_action)
        self.rectanglify_action.deleteLater()
        self.detach_from_project()

    def rectanglify(self):

        layer: QgsVectorLayer = self.iface.activeLayer()

        only_selected = layer.selectedFeatureCount() > 0

        with BeginCommand(
            layer,
            self.tr("Rectanglify selected features")
            if only_selected
            else self.tr("Rectanglify all features"),
        ):

            if only_selected:
                features = layer.getSelectedFeatures(
                    QgsFeatureRequest().setSubsetOfAttributes([])
                )
            else:
                features = layer.getFeatures(
                    QgsFeatureRequest().setSubsetOfAttributes([])
                )

            for feat in features:
                new_geom = minimum_bounding_box(feat)
                layer.changeGeometry(feat.id(), new_geom)
