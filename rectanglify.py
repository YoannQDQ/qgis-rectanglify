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
import traceback

from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QDialog

from qgis.core import (
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsWkbTypes,
    QgsProject,
    QgsMapLayer,
    QgsGeometry,
    QgsTask,
    QgsApplication,
    Qgis,
)

from qgis.utils import QgsMessageLog

# Initialize Qt resources from file resources.py
from .resources import *
from .utils import BeginCommand, rectanglify_geometry

from .settingsdialog import Ui_SettingsDialog


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

        # Init settings
        self.settings = QSettings()
        self.settings.beginGroup("plugins/rectanglify")
        self.settings.setValue(
            "constantArea", self.settings.value("constantArea", True, bool)
        )
        self.settings.setValue(
            "keepRings", self.settings.value("keepRings", True, bool)
        )
        self.settings.setValue(
            "ringsShareAxes", self.settings.value("ringsShareAxes", True, bool)
        )

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

        self.settings_action = QAction(
            QIcon(""), self.tr("Rectanglify Settings"), parent=self.iface.mainWindow(),
        )
        self.settings_action.triggered.connect(self.open_settings)

        self.iface.advancedDigitizeToolBar().addAction(self.rectanglify_action)
        self.iface.editMenu().addAction(self.rectanglify_action)

        self.plugin_menu = self.iface.pluginMenu().addMenu(
            QIcon(":/plugins/rectanglify/actionRectanglify.svg"), "Rectanglify"
        )
        self.plugin_menu.addAction(self.rectanglify_action)
        self.plugin_menu.addAction(self.settings_action)
        self.iface.editMenu().addAction(self.rectanglify_action)

        self.iface.currentLayerChanged.connect(self.update_action_state)
        self.attach_to_project()
        self.update_action_state()

        self.task_rectanglify: QgsTask = None

        self.dialog = QDialog(self.iface.mainWindow())
        self.dialog.ui = Ui_SettingsDialog()
        self.dialog.ui.setupUi(self.dialog)

    def attach_to_project(self):
        """Connect newly added layers to monitor their selection and editing state"""
        QgsProject.instance().layerWasAdded[QgsMapLayer].connect(self.connect_layer)
        for layer in QgsProject.instance().mapLayers().values():
            self.connect_layer(layer)

    def detach_from_project(self):
        """Disconnect all layers"""
        QgsProject.instance().layerWasAdded[QgsMapLayer].disconnect(self.connect_layer)
        for layer in QgsProject.instance().mapLayers().values():
            self.disconnect_layer(layer)

    def connect_layer(self, layer):
        """Connect layer to monitor their selection and editing state"""
        if (
            isinstance(layer, QgsVectorLayer)
            and layer.geometryType() == QgsWkbTypes.PolygonGeometry
        ):
            layer.editingStarted.connect(self.update_action_state)
            layer.editingStopped.connect(self.update_action_state)
            layer.selectionChanged.connect(self.update_action_state)

    def disconnect_layer(self, layer):
        """Diconnect from layer signals"""
        if (
            isinstance(layer, QgsVectorLayer)
            and layer.geometryType() == QgsWkbTypes.PolygonGeometry
        ):
            layer.editingStarted.disconnect(self.update_action_state)
            layer.editingStopped.disconnect(self.update_action_state)
            layer.selectionChanged.disconnect(self.update_action_state)

    def update_action_state(self):
        """Enable/Disable action"""
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
        self.iface.pluginMenu().removeAction(self.plugin_menu.menuAction())
        self.rectanglify_action.deleteLater()
        self.detach_from_project()

    def rectanglify(self):
        """Create a QgsTask that will perform the actual rectanglification"""

        # On finished will be called when the tasks ends, whether it failed
        # or succeeded
        self.task_rectanglify = QgsTask.fromFunction(
            "Rectanglify", self._rectanglify, on_finished=self.on_finished,
        )
        QgsApplication.taskManager().addTask(self.task_rectanglify)

    def _rectanglify(self, task: QgsTask):
        """Rectanglify active layer's features"""

        layer: QgsVectorLayer = self.iface.activeLayer()
        only_selected = layer.selectedFeatureCount() > 0
        constant_area = self.settings.value("constantArea", True, bool)
        keep_rings = self.settings.value("keepRings", True, bool)
        rings_share_axes = self.settings.value("ringsShareAxes", True, bool)

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
                total = layer.selectedFeatureCount()
            else:
                features = layer.getFeatures(
                    QgsFeatureRequest().setSubsetOfAttributes([])
                )
                total = layer.featureCount()

            for i, feat in enumerate(features, 1):

                # Check if task is canceled. Raising an exception will revert any
                # change made up to this point, thanks to the BeginCommand __exit__
                # method
                if task.isCanceled():
                    raise Exception("Canceled")

                if feat.geometry().isMultipart():
                    multi = [
                        rectanglify_geometry(
                            QgsGeometry.fromPolygonXY(polygon),
                            constant_area,
                            keep_rings,
                            rings_share_axes,
                        )
                        for polygon in feat.geometry().asMultiPolygon()
                    ]
                    new_geom = QgsGeometry.collectGeometry(multi)
                else:
                    new_geom = rectanglify_geometry(
                        feat.geometry(), constant_area, keep_rings, rings_share_axes
                    )
                layer.changeGeometry(feat.id(), new_geom)

                # Report task progress
                task.setProgress(i * 100 / total)

    def on_finished(self, exception, result=None):
        """Task completion handler"""

        # Task is either canceled or another exception occured
        if exception:

            # If task is canceled, simply display a temporary info message
            if self.task_rectanglify.isCanceled():
                self.iface.messageBar().pushMessage(self.tr("Rectanglify canceled"))

            # Else, display a warning message, and log exception in the Message log
            else:
                trace = "\n".join(
                    traceback.format_exception(
                        type(exception), exception, exception.__traceback__
                    )
                )
                QgsMessageLog.logMessage(
                    f"Exception during Rectanglify: {trace}",
                    "Rectanglify",
                    Qgis.Warning,
                )
                self.iface.messageBar().pushMessage(
                    self.tr("Rectanglify failed. See message log for details."),
                    level=Qgis.Warning,
                )

        self.task_rectanglify = None

    def open_settings(self):
        """Open the settings dialog"""

        # Update Checkboxes from plugin settings
        self.dialog.ui.constantAreaCheckBox.setChecked(
            self.settings.value("constantArea", True, bool)
        )
        self.dialog.ui.keepRingsCheckBox.setChecked(
            self.settings.value("keepRings", True, bool)
        )
        self.dialog.ui.sharedAxesCheckBox.setChecked(
            self.settings.value("ringsShareAxes", True, bool)
        )

        # If dialog is accepted (click on Ok button), update plugin settings
        if self.dialog.exec() == QDialog.Accepted:
            self.settings.setValue(
                "constantArea", self.dialog.ui.constantAreaCheckBox.isChecked()
            )
            self.settings.setValue(
                "keepRings", self.dialog.ui.keepRingsCheckBox.isChecked()
            )
            self.settings.setValue(
                "ringsShareAxes", self.dialog.ui.sharedAxesCheckBox.isChecked()
            )
