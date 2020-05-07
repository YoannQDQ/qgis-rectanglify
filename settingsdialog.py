# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settingsdialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        SettingsDialog.resize(232, 134)
        self.verticalLayout = QtWidgets.QVBoxLayout(SettingsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.constantAreaCheckBox = QtWidgets.QCheckBox(SettingsDialog)
        self.constantAreaCheckBox.setObjectName("constantAreaCheckBox")
        self.verticalLayout.addWidget(self.constantAreaCheckBox)
        self.keepRingsCheckBox = QtWidgets.QCheckBox(SettingsDialog)
        self.keepRingsCheckBox.setObjectName("keepRingsCheckBox")
        self.verticalLayout.addWidget(self.keepRingsCheckBox)
        self.sharedAxesCheckBox = QtWidgets.QCheckBox(SettingsDialog)
        self.sharedAxesCheckBox.setEnabled(False)
        self.sharedAxesCheckBox.setObjectName("sharedAxesCheckBox")
        self.verticalLayout.addWidget(self.sharedAxesCheckBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.okButton = QtWidgets.QPushButton(SettingsDialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtWidgets.QPushButton(SettingsDialog)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(SettingsDialog)
        self.okButton.clicked.connect(SettingsDialog.accept)
        self.cancelButton.clicked.connect(SettingsDialog.reject)
        self.keepRingsCheckBox.toggled['bool'].connect(self.sharedAxesCheckBox.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        _translate = QtCore.QCoreApplication.translate
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "Rectanglify Settings"))
        self.constantAreaCheckBox.setToolTip(_translate("SettingsDialog", "If enabled, rectanglify will scale down the mimimum oriented bounding box as to keep the same area as the original feature"))
        self.constantAreaCheckBox.setText(_translate("SettingsDialog", "Constant area"))
        self.keepRingsCheckBox.setToolTip(_translate("SettingsDialog", "If enabled, rectanglify will try to rectanglify rings in feature geometries"))
        self.keepRingsCheckBox.setText(_translate("SettingsDialog", "Keep rings"))
        self.sharedAxesCheckBox.setToolTip(_translate("SettingsDialog", "If enabled, the rings will have the same orientation as the outer polygon"))
        self.sharedAxesCheckBox.setText(_translate("SettingsDialog", "Rings share axes"))
        self.okButton.setText(_translate("SettingsDialog", "Ok"))
        self.cancelButton.setText(_translate("SettingsDialog", "Cancel"))

