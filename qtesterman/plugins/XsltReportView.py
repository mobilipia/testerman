# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009 QTesterman contributors
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
##

##
# A plugin to display logs through an XSLT transformation.
#
##

from PyQt4.Qt import *
from PyQt4.QtXml import *

from Base import *
from CommonWidgets import *

import Plugin
import PluginManager

import os.path

# Plugin ID, as generated by uuidgen
PLUGIN_ID = "4bd1dbc8-7bbc-4bf7-821d-286af583b369"
VERSION = "1.0.1"
DESCRIPTION = """
This reporter is applies an XSLT transformation to the raw XML execution logs <br />
to extract interesting things according to your needs. <br />
The XSLT files should be named with the ".xslt" extension and located in <br />
the configured directory to make them appear from the report view."""

try:
	import libxslt
	import libxml2
	DependenciesAvailable = True
except ImportError:
	DependenciesAvailable = False
	log("Unable to import libxslt and libxml2 modules : XSLT report plugin cannot be loaded")

class WXsltLogView(Plugin.WReportView):
	def __init__(self, parent = None):
		Plugin.WReportView.__init__(self, parent)

		settings = QSettings()
		self.xsltPath = settings.value('plugins/%s/xsltpath' % PLUGIN_ID, QVariant(".")).toString()

		# The log		
		self.xml = QString()

		self.__createWidgets()
	
	def __createWidgets(self):
		layout = QVBoxLayout()
		
		# A button bar with selectable XSLT and save option ?
		buttonLayout = QHBoxLayout()
		buttonLayout.addWidget(QLabel("XSLT transformation:"))
		self.transformationComboBox = QComboBox()
		buttonLayout.addWidget(self.transformationComboBox)
		self.applyTransformationButton = QPushButton("Apply")
		buttonLayout.addWidget(self.applyTransformationButton)
		self.refreshTransformationButton = QPushButton("Refresh available transformations")
		buttonLayout.addWidget(self.refreshTransformationButton)
		buttonLayout.addStretch()
		self.connect(self.applyTransformationButton, SIGNAL('clicked()'), self.applyTransformation)
		self.connect(self.refreshTransformationButton, SIGNAL('clicked()'), self.refreshTransformationsList)

		# We display XSLT transformation options only if we have the required librairies
		if DependenciesAvailable:
			layout.addLayout(buttonLayout)
		else:
			layout.addWidget(QLabel("Unable to import libxslt and libxml2 modules : XSLT report plugin cannot be loaded"))
			layout.addWidget(QLabel("Please install libxml2 (and libxslt1 under unixes) python package(s) for your python/OS versions."))

		# The text view
		self.textView = QTextEdit()
		self.textView.setReadOnly(1)
		font = QFont("courier", 8)
		font.setFixedPitch(True)
		self.textView.setFont(font)
		self.textView.setLineWrapMode(QTextEdit.NoWrap)
		
		layout.addWidget(self.textView)
		
		self.setLayout(layout)
		
		self.refreshTransformationsList()

	def refreshTransformationsList(self):
		"""
		Reload available transformations and repopulate the combo box.
		"""
		self.transformationComboBox.clear()

		settings = QSettings()
		self.xsltPath = settings.value('plugins/%s/xsltpath' % PLUGIN_ID, QVariant(".")).toString()
		
		d = QDir(self.xsltPath)
		d.setNameFilters([ "*.xsl", "*.xslt" ])
		d.setSorting(QDir.Name)
		for transfo in d.entryList():
			self.transformationComboBox.addItem(transfo)

	def applyTransformation(self):
		if self.transformationComboBox.currentText().isEmpty():
			return

		try:
			f = open(self.xsltPath.toAscii() + '/' + self.transformationComboBox.currentText().toAscii())
			xslt = f.read()
			f.close()
		except Exception, e:
			log("Unable to read XSLT file: " + str(e))
			return

		transient = WTransientWindow("Log Viewer", self)
		transient.showTextLabel("Applying XSLT...")
		xml = '<?xml version="1.0" encoding="utf-8"?><root>' + str(self.xml.toUtf8()) + '</root>'
		try:
			xmlDoc = libxml2.parseDoc(xml)
			xsltDoc = libxml2.parseDoc(xslt)
			style = libxslt.parseStylesheetDoc(xsltDoc)
			transformedDoc = style.applyStylesheet(xmlDoc, None)
			transformedXml = style.saveResultToString(transformedDoc)
			style.freeStylesheet()
			#xsltDoc.freeDoc() -- freeStylesheet does it ???
			transformedDoc.freeDoc()
			xmlDoc.freeDoc()
		except Exception, e:
			log("Unable to apply XSLT to log: " + str(e))
			transient.hide()
			transient.setParent(None) # enable garbage collecting of the transient window
			return
			
		transient.hide()
		transient.setParent(None) # enable garbage collecting of the transient window
		if transformedXml.find("<html", 0, 50) == -1: #should be enhanced...
			self.textView.setPlainText(transformedXml)
		else:
			self.textView.setHtml(transformedXml)

	def onEvent(self, domElement):
		if DependenciesAvailable:
			# Accumulate the events into pure txt form.
			domElement.save(QTextStream(self.xml), 0)
	
	def displayLog(self):
		pass
	
	def clearLog(self):
		self.xml = QString()
		self.textView.clear()


class WXsltLogViewConfiguration(Plugin.WPluginConfiguration):
	def __init__(self, parent = None):
		Plugin.WPluginConfiguration.__init__(self, parent)
		self.__createWidgets()

	def __createWidgets(self):
		"""
		The model is in the saved settings.
		"""
		self.xlstPathLineEdit = QLineEdit()
		self.xlstPathLineEdit.setMinimumWidth(150)
		self.browseDirectoryButton = QPushButton("...")
		self.connect(self.browseDirectoryButton, SIGNAL('clicked()'), self.browseDirectory)
		layout = QVBoxLayout()
		layout.addWidget(QLabel("Search XSLT files (.xslt) in directory:"))
		optionLayout = QHBoxLayout()
		optionLayout.addWidget(self.xlstPathLineEdit)
		optionLayout.addWidget(self.browseDirectoryButton)
		layout.addLayout(optionLayout)

		self.setLayout(layout)

	def browseDirectory(self):
		xsltPath = QFileDialog.getExistingDirectory(self, "XSLT files directory", self.xlstPathLineEdit.text())
		if not xsltPath.isEmpty():
			self.xlstPathLineEdit.setText(os.path.normpath(unicode(xsltPath)))

	def displayConfiguration(self):
		path = "plugins/%s" % PLUGIN_ID
		# Read the settings
		settings = QSettings()
		xsltPath = settings.value(path + '/xsltpath', QVariant(QString(QApplication.instance().get('qtestermanpath')))).toString()
		self.xlstPathLineEdit.setText(xsltPath)

	def saveConfiguration(self):
		"""
		Update the data model.
		"""
		settings = QSettings()
		path = "plugins/%s" % PLUGIN_ID
		settings.setValue(path + '/xsltpath', QVariant(self.xlstPathLineEdit.text()))
		return True

	def checkConfiguration(self):
		"""
		Check the data model, return 1 if OK, 0 if not.
		"""
		return True


PluginManager.registerPluginClass("XSLT", PLUGIN_ID, WXsltLogView, WXsltLogViewConfiguration, version = VERSION, description = DESCRIPTION)

