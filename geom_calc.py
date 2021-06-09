# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeomCalculator
                                 A QGIS plugin
 This plugin calcs geometric indicators
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-05-21
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Roman
        email                : philw7321980@gmail.com
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
import qgis
from qgis.core import QgsField, QgsExpression, QgsExpressionContext, QgsExpressionContextUtils, edit, QgsProject, Qgis, \
    QgsProcessingFeatureSourceDefinition, QgsVectorLayer
import processing
# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .geom_calc_dockwidget import GeomCalculatorDockWidget
import os.path


class GeomCalculator:
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
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeomCalculator_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geometric Calculator')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GeomCalculator')
        self.toolbar.setObjectName(u'GeomCalculator')

        # print "** INITIALIZING GeomCalculator"

        self.pluginIsActive = False
        self.dockwidget = None

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
        return QCoreApplication.translate('GeomCalculator', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/geom_calc/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD GeomCalculator"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Geometric Calculator'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING GeomCalculator"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = GeomCalculatorDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            # загрузим все слои в выпадающий список
            def check_layers():
                self.dockwidget.plots.clear()
                self.dockwidget.streets.clear()
                cur_layers = qgis.core.QgsProject.instance().layerTreeRoot().layerOrder()
                layer_names = []
                for cL in cur_layers:
                    layer_names.append(cL.name())
                self.dockwidget.plots.addItems(layer_names)
                self.dockwidget.streets.addItems(layer_names)

            check_layers()

            def do_lines_layer(selected_layer):
                fix_layer = processing.run("native:fixgeometries", {'INPUT': selected_layer, 'OUTPUT': 'memory:'})[
                    'OUTPUT']
                ll = processing.run("native:polygonstolines", {'INPUT': fix_layer, 'OUTPUT': 'memory:'})['OUTPUT']
                e_lines = processing.run("native:explodelines", {'INPUT': ll, 'OUTPUT': 'memory:'})['OUTPUT']
                QgsProject.instance().addMapLayer(e_lines)
                # добавим новый атрибут
                e_lines.dataProvider().addAttributes([QgsField('width', QVariant.Double)])
                e_lines.updateFields()
                # составляем выражения для атрибутов
                context = QgsExpressionContext()
                context.appendScopes(
                    QgsExpressionContextUtils.globalProjectLayerScopes(e_lines))
                length = QgsExpression('$length')
                with edit(e_lines):
                    for f in e_lines.getFeatures():
                        context.setFeature(f)
                        f['width'] = length.evaluate(context)
                        e_lines.updateFeature(f)
                return e_lines

            def calculate():
                # выбранный слой
                cur_layers = qgis.core.QgsProject.instance().layerTreeRoot().layerOrder()
                if not cur_layers:
                    return
                street_index = self.dockwidget.streets.currentIndex()
                streets = cur_layers[street_index]
                plot_index = self.dockwidget.plots.currentIndex()
                plots = cur_layers[plot_index]

                # добавляем атрибуты в таблицу если их нет
                attrs = plots.dataProvider().fields().names()
                if 'Area' not in attrs:
                    plots.dataProvider().addAttributes([QgsField('Area', QVariant.Double)])
                if 'Perimeter' not in attrs:
                    plots.dataProvider().addAttributes([QgsField('Perimeter', QVariant.Double)])
                if 'fCompact' not in attrs:
                    plots.dataProvider().addAttributes([QgsField('fCompact', QVariant.Double)])
                if 'iCompact' not in attrs:
                    plots.dataProvider().addAttributes([QgsField('iCompact', QVariant.Double)])
                plots.updateFields()
                # составляем выражения для атрибутов
                context = QgsExpressionContext()
                context.appendScopes(
                    QgsExpressionContextUtils.globalProjectLayerScopes(plots))
                area = QgsExpression('$area')
                per = QgsExpression('$perimeter')
                f_comp = QgsExpression('$perimeter/(4*sqrt($area))')
                i_comp = QgsExpression('$area / area(bounds( $geometry))')

                # загружаем значения выражений для атрибутов
                with edit(plots):
                    for f in plots.getFeatures():
                        context.setFeature(f)
                        f['Area'] = area.evaluate(context)
                        f['Perimeter'] = per.evaluate(context)
                        f['fCompact'] = f_comp.evaluate(context)
                        f['iCompact'] = i_comp.evaluate(context)
                        plots.updateFeature(f)

                # сделаем новый слой линий и добавим в проект
                exploded = do_lines_layer(plots)
                # буферизируем слой улиц
                buffered = processing.run("native:buffer", {'INPUT': streets,
                                                            'DISTANCE': 30.0,
                                                            'SEGMENTS': 5,
                                                            'DISSOLVE': False,
                                                            'END_CAP_STYLE': 0,
                                                            'JOIN_STYLE': 0,
                                                            'MITER_LIMIT': 2,
                                                            'OUTPUT': 'memory:'})['OUTPUT']
                # выделим объекты и найдем центроиды
                processing.run("native:selectbylocation",
                               {'INPUT': exploded, 'PREDICATE': 6, 'INTERSECT': buffered, 'METHOD': 0})
                centroids = processing.run("native:centroids", {
                    'INPUT': QgsProcessingFeatureSourceDefinition(exploded.id(), selectedFeaturesOnly=True),
                    'ALL_PARTS': False, 'OUTPUT': 'memory:'})['OUTPUT']
                snapped = processing.run("saga:snappointstolines",
                                         {'INPUT': centroids, 'SNAP': streets, 'OUTPUT': 'TEMPORARY_OUTPUT',
                                          'DISTANCE': 30})['OUTPUT']
                snapped_l = QgsVectorLayer(snapped, 'snapped')
                front = processing.run("qgis:distancetonearesthubpoints",
                                       {'INPUT': centroids, 'HUBS': snapped_l, 'OUTPUT': 'memory:', 'FIELD': 'Name',
                                        'UNIT': 0})['OUTPUT']
                front.setName('Front')
                QgsProject.instance().addMapLayer(front)
                QgsProject.instance().removeMapLayer(exploded)

                # удаляем лишние поля для земельных участков, оставляя наименьший HubDistance
                for f in front.getFeatures():
                    front.selectByExpression(" \"Name\" = '{}' ".format(f['Name']))
                    front_side = front.selectedFeatures()[0]
                    for sf in front.selectedFeatures():
                        if sf['HubDist'] < front_side['HubDist']:
                            front_side = sf
                    front.deselect(front_side.id())
                    with edit(front):
                        for fd in front.selectedFeatures():
                            front.deleteFeature(fd.id())

                # посчитаем индекс протяженности фронта
                front.dataProvider().addAttributes([QgsField('iFront', QVariant.Double)])
                front.updateFields()
                with edit(front):
                    for f in front.getFeatures():
                        f['iFront'] = f['HubDist']/f['Perimeter']
                        front.updateFeature(f)

                self.iface.messageBar().pushMessage("Success", "Geometries successfully calculated",
                                                    level=Qgis.Success)

            self.dockwidget.pushButton.clicked.connect(calculate)
            self.dockwidget.check.clicked.connect(check_layers)
