# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
"""
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""
import sys
import numpy
import json
from scipy import interpolate
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.adapters.abcdisplayer import ABCMPLH5Displayer
from tvb.core.adapters.exceptions import LaunchException
from tvb.datatypes.mapped_values import DatatypeMeasure
from tvb.basic.config.settings import TVBSettings as config
from tvb.basic.filters.chain import FilterChain


# The resolution for computing dots inside the displayed isocline.
# This is not the sae as display size.
RESOLUTION = (600, 600)



class IsoclinePseAdapter(ABCMPLH5Displayer):
    """
    Visualization adapter for Parameter Space Exploration.
    Will be used as a generic visualizer, accessible when input entity is DataTypeGroup.
    Will also be used in Burst as a supplementary navigation layer.
    """

    _ui_name = "Isocline PSE"
    _ui_subsection = "pse"


    def __init__(self):
        ABCMPLH5Displayer.__init__(self)
        self.figures = {}
        self.interp_models = {}


    def get_input_tree(self):
        """
        Take as Input a Connectivity Object.
        """
        return [{'name': 'datatype_group',
                 'label': 'Datatype Group',
                 'type': model.DataTypeGroup,
                 'required': True,
                 'conditions': FilterChain(fields=[FilterChain.datatype + ".no_of_ranges"],
                                           operations=["=="], values=[2])}]


    def get_required_memory_size(self, **kwargs):
        """
        Return the required memory to run this algorithm.
        """
        # Don't know how much memory is needed.
        return -1


    def burst_preview(self, datatype_group_id, width, height):
        """
        Generate the preview for the burst page.
        """
        if not width:
            width = height
        figure_size = (700, 700)
        if width and height:
            figure_size = (width, height)
        datatype_group = dao.get_datatype_group_by_id(datatype_group_id)
        result_dict = self.launch(datatype_group=datatype_group, figure_size=figure_size)
        result_dict['isPreview'] = True
        return result_dict


    def is_compatible(self, datatype_group_id):
        """
        Check if Isocline adapter makes sense for this datatype group.
        """
        datatype_group = dao.get_datatype_group_by_id(datatype_group_id)
        operation_group = dao.get_operationgroup_by_id(datatype_group.fk_operation_group)
        try:
            self._get_range_values(operation_group)
            return True
        except LaunchException:
            return False


    def launch(self, datatype_group, **kwargs):
        """
        Also overwrite launch from ABCDisplayer since we want to hanlde a list of figures instead of 
        only one figure.
        """
        show_full_toolbar = True
        if self.PARAM_FIGURE_SIZE in kwargs:
            figsize = kwargs[self.PARAM_FIGURE_SIZE]
            figsize = ((figsize[0]) / 80, (figsize[1]) / 80)
            del kwargs[self.PARAM_FIGURE_SIZE]
        else:
            figsize = (15, 7)

        operation_group = dao.get_operationgroup_by_id(datatype_group.fk_operation_group)

        range1_name, range2_name, self.range1, self.range2 = self._get_range_values(operation_group)

        # Get the computed measures on this datatype
        first_op = dao.get_operations_in_group(operation_group.id)[0]
        if first_op.status != model.STATUS_FINISHED:
            raise LaunchException("Not all operations from this range are finished. "
                                      "Cannot generate data until then.")
        datatype = dao.get_results_for_operation(first_op.id)[0]
        dt_measure = dao.get_generic_entity(DatatypeMeasure, datatype.gid, '_analyzed_datatype')[0]
        figure_nrs = {}
        metrics = dt_measure.metrics
        for metric in metrics:
            # Separate plot for each metric.
            self._create_plot(metric, figsize, operation_group, range1_name, range2_name, figure_nrs)

        parameters = dict(title=self._ui_name, figureNumbers=figure_nrs, showFullToolbar=show_full_toolbar,
                          serverIp=config.SERVER_IP, serverPort=config.MPLH5_SERVER_PORT, metrics=metrics,
                          figuresJSON=json.dumps(figure_nrs))
        if self.EXPORTABLE_FIGURE not in parameters:
            parameters[self.EXPORTABLE_FIGURE] = True
        return self.build_display_result("isocline_pse/view", parameters)


    def plot(self, figure, operation_group, metric, range1_name, range2_name):
        """
        Do the plot for the given figure. Also need operation group, metric and ranges
        in order to compute the data to be plotted.
        """
        operations = dao.get_operations_in_group(operation_group.id)
        # Data from which to interpolate larger 2-D space
        apriori_x = numpy.array(self.range1)
        apriori_y = numpy.array(self.range2)
        apriori_data = numpy.zeros((apriori_x.size, apriori_y.size))
        # An 2D array of gids which is used later to launch overlay for a datatype
        datatypes_gids = [[None for _ in self.range2] for _ in self.range1]
        for operation_ in operations:
            range_values = eval(operation_.range_values)
            key_1 = range_values[range1_name]
            index_x = self.range1.index(key_1)
            key_2 = range_values[range2_name]
            index_y = self.range2.index(key_2)
            if operation_.status != model.STATUS_FINISHED:
                raise LaunchException("Not all operations from this range are finished. "
                                      "Cannot generate data until then.")
            datatype = dao.get_results_for_operation(operation_.id)[0]
            datatypes_gids[index_x][index_y] = datatype.gid
            measures = dao.get_generic_entity(DatatypeMeasure, datatype.gid, '_analyzed_datatype')
            if measures:
                apriori_data[index_x][index_y] = measures[0].metrics[metric]
            else:
                apriori_data[index_x][index_y] = 0
        # Attempt order-3 interpolation.
        kx = ky = 3
        if len(self.range1) <= 3 or len(self.range2) <= 3:
            # Number of points is too small, just do linear interpolation
            kx = ky = 1
        s = interpolate.RectBivariateSpline(apriori_x, apriori_y, apriori_data, kx=kx, ky=ky)
        # Get data of higher resolution that we'll plot later on
        posteriori_x = numpy.arange(self.range1[0], self.range1[-1],
                                    (self.range1[-1] - self.range1[0]) / RESOLUTION[0])
        posteriori_y = numpy.arange(self.range2[0], self.range2[-1],
                                    (self.range2[-1] - self.range2[0]) / RESOLUTION[1])
        posteriori_data = numpy.rot90(s(posteriori_x, posteriori_y))

        self.interp_models[figure.number] = s
        # Do actual plot.        
        axes = figure.gca()
        img = axes.imshow(posteriori_data, extent=(min(self.range1), max(self.range1),
                                                   min(self.range2), max(self.range2)),
                          aspect='auto', interpolation='nearest')
        axes.set_title("Interpolated values for metric %s" % (metric,))
        figure.colorbar(img)

        axes.set_xlabel(range1_name)
        axes.set_ylabel(range2_name)


        def format_coord(x, y):
            return 'x=%1.4f, y=%1.4f' % (x, y)


        axes.format_coord = format_coord
        return datatypes_gids


    def _create_plot(self, metric, figsize, operation_group, range1_name, range2_name, figure_nrs):
        """
        Create a plot for each metric, with a given figsize:. We need also operation group,
        ranges for data computations. figure_nrs iw a mapping between metric : figure_number
        """
        figure = self._create_new_figure(figsize)

        # Create events for each figure.
        def _click_event(event, figure=figure):
            if event.inaxes is figure.gca():
                x, y = event.xdata, event.ydata
                x_idx = -1
                x_dist = sys.maxint
                for idx, val in enumerate(self.range1):
                    if x_dist > abs(val - x):
                        x_dist = abs(val - x)
                        x_idx = idx
                y_idx = -1
                y_dist = sys.maxint
                for idx, val in enumerate(self.range2):
                    if y_dist > abs(val - y):
                        y_dist = abs(val - y)
                        y_idx = idx
                figure.command = "clickedDatatype('%s')" % (self.datatype_gids[x_idx][y_idx])


        def _hover_event(event, figure=figure):
            if event.inaxes is figure.gca():
                x, y = event.xdata, event.ydata
                figure.command = "hoverPlot(%s, %s, %s, %s)" % (figure.number, x, y,
                                                                self.interp_models[figure.number]([x], [y]))


        dt_gids = self.plot(figure, operation_group, metric, range1_name, range2_name)
        # Save the array of gids so we can later look op for the on_click events
        self.datatype_gids = dt_gids
        self.figures[figure.number] = figure
        figure_nrs[metric] = figure.number
        figure.canvas.mpl_connect('button_press_event', _click_event)
        figure.canvas.mpl_connect('motion_notify_event', _hover_event)
        figure.canvas.draw()


    def _get_range_values(self, operation_group):
        """
        Parse the range values for a given operation group.
        """
        range1 = json.loads(operation_group.range1)
        range1_labels = range1[1]
        can_interpolate_range1 = True  # Assume this is a float range that we can interpolate
        for idx, entry in enumerate(range1_labels):
            try:
                range1_labels[idx] = float(entry)
            except ValueError:
                # It's a DataType range, in which case interpolation makes no sense ?
                can_interpolate_range1 = False
        range1_name = range1[0]

        range2 = operation_group.range2
        can_interpolate_range2 = False
        range2_labels = ["_"]
        range2_name = "_"
        if range2 is not None:
            can_interpolate_range2 = True
            range2 = json.loads(range2)
            range2_labels = range2[1]
            for idx, entry in enumerate(range2_labels):
                try:
                    range2_labels[idx] = float(entry)
                except ValueError:
                    # It's a DataType range, in which case interpolation makes no sense ?
                    can_interpolate_range2 = False
            range2_name = range2[0]

        if not (can_interpolate_range1 and can_interpolate_range2):
            raise LaunchException("Need 2-D range with float values in order to interpolate data.")
        return range1_name, range2_name, range1_labels, range2_labels
    
        
