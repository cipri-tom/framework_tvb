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
.. moduleauthor:: Ionel Ortelecan <ionel.ortelecan@codemart.ro>
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""
import numpy
import pylab
from scipy.optimize import leastsq
from matplotlib.mlab import griddata
from matplotlib import colors
from tvb.core.adapters.abcdisplayer import ABCMPLH5Displayer
from tvb.datatypes.graph import ConnectivityMeasure
from tvb.basic.filters.chain import FilterChain


class BaseTopography():
    """
    Base class for topographic visualizers.
    """
    # the following fields aren't changed from GUI
    plotsensors = False
    plothead = True
    masked = True
    # this field may be modified from the GUI
    plot_contours = False

    # dictionaries that contains processed data
    head_contour = None
    sensor_locations = None
    topography_data = None

    def get_required_memory_size(self, **kwargs):
        """
        Return the required memory to run this algorithm.
        """
        # Don't know how much memory is needed.
        return -1

    def init_topography(self, sensor_locations):
        """
        Initialize entities for topographic computation.
        """
        self.topography_data = self.prepare_sensors(sensor_locations, resolution = 51)
        self.head_contour = self.compute_head_contour(self.topography_data)
        self.sensor_locations = self.compute_sensors(self.topography_data)


    def draw_head_topo(self, figure, topography, color_bar_min = 0, color_bar_max = 0):
        """
        Draw Head top view.
        """
        self._fit_topology(figure, topography, self.topography_data, color_bar_min, color_bar_max)
        if self.plothead:
            # draw head contour
            figure.gca().plot(self.head_contour["x_arr"], self.head_contour["y_arr"], 
                              color= self.head_contour["color"], linewidth = self.head_contour["linewidth"])
        if self.plotsensors:
            # Draw Sensors
            figure.gca().plot(self.sensor_locations["x_arr"], self.sensor_locations["y_arr"], 
                              self.sensor_locations["marker"])


    def _fit_topology(self, figure, topography, topography_data, color_bar_min, color_bar_max):
        """
        Trim data, to make sure everything is inside the head contour.
        """
        x_arr = topography_data["x_arr"]
        y_arr = topography_data["y_arr"]
        circle_x = topography_data["circle_x"]
        circle_y = topography_data["circle_y"]
        rad = topography_data["rad"]

        topo = griddata(topography_data["sproj"][:, 0], topography_data["sproj"][:, 1],
                        numpy.ravel(numpy.array(topography)), x_arr, y_arr)
        if self.plot_contours:
            #draw the contours
            figure.gca().contour(x_arr, y_arr, topo, 10, colors='k', origin="lower", hold='on')

        # mask values outside the head
        if self.masked:
            notinhead = numpy.greater_equal((x_arr - circle_x) ** 2 + (y_arr - circle_y) ** 2, (1.0 * rad) ** 2)
            topo = numpy.ma.masked_where(notinhead, topo)

        # show surface
        map_surf = figure.gca().imshow(topo, origin="lower", extent=(-rad, rad, -rad, rad))

        if not (color_bar_min == 0 and color_bar_max == 0):
            norm = colors.Normalize(vmin=color_bar_min, vmax=color_bar_max)
            map_surf.set_norm(norm)
        figure.colorbar(map_surf)
        figure.gca().set_axis_off()
        return map_surf
        

    @staticmethod
    def prepare_sensors(sensor_locations, resolution =51):
        """
        Common method, to pre-process sensors before display (project them in 2D).
        """
        def sphere_fit(params):
            """Function to fit the sensor locations to a sphere"""
            return ((sensor_locations[:, 0] - params[1]) ** 2 + (sensor_locations[:, 1] - params[2]) ** 2
                    + (sensor_locations[:, 2] - params[3]) ** 2 - params[0] ** 2)

        (radius, circle_x, circle_y, circle_z) = leastsq(sphere_fit, (1, 0, 0, 0))[0]
        # size of each square
        ssh = float(radius) / resolution         # half-size
        # Generate a grid and interpolate using the gridData module
        x_arr = numpy.arange(circle_x - radius, circle_x + radius, ssh * 2.0) + ssh
        y_arr = numpy.arange(circle_y - radius, circle_y + radius, ssh * 2.0) + ssh
        x_arr, y_arr = pylab.meshgrid(x_arr, y_arr)

        # project the sensor locations onto the sphere
        sproj = sensor_locations - numpy.array((circle_x, circle_y, circle_z))
        sproj = radius * sproj / numpy.c_[numpy.sqrt(numpy.sum(sproj ** 2, axis=1))]
        sproj += numpy.array((circle_x, circle_y, circle_z))
        return dict(sproj = sproj, x_arr = x_arr, y_arr = y_arr, 
                    circle_x = circle_x, circle_y = circle_y, rad = radius)


    @staticmethod
    def compute_sensors(topography_data):
        """
        Get locations for the sensors, based on connectivity's projection.
        """
        sproj = topography_data["sproj"]
        circle_x = topography_data["circle_x"]
        circle_y = topography_data["circle_y"]

        zenum = [x[::-1] for x in enumerate(sproj[:, 2].tolist())]
        zenum.sort()
        indx = [x[1] for x in zenum]
        return dict(x_arr=sproj[indx, 0] - circle_x / 2.0, y_arr=sproj[indx, 1] - circle_y / 2.0, marker='wo')


    @staticmethod
    def compute_head_contour(topography_data, color='k', linewidth='5'):
        """
        Plot the main contour (contour of the head).
        """
        scale = topography_data["rad"]
        shift = (topography_data["circle_x"] / 2.0, topography_data["circle_y"] / 2.0)

        rmax = 0.5
        fac = 2 * numpy.pi * 0.01
        # Coordinates for the ears
        ear_x1 = -1 * numpy.array([.497, .510, .518, .5299, .5419, .54, .547,
                                  .532, .510, rmax*numpy.cos(fac * (54 + 42))])
        ear_y1 = numpy.array([.0655, .0775, .0783, .0746, .0555, -.0055, 
                              -.0932, -.1313, -.1384, rmax * numpy.sin(fac * (54 + 42))])
        ear_x2 = numpy.array([rmax * numpy.cos(fac * (54 + 42)), .510, .532,
                            .547, .54, .5419, .5299, .518, .510, .497])
        ear_y2 = numpy.array([rmax *numpy.sin(fac * (54 + 42)), -.1384, -.1313,
                             -.0932, -.0055, .0555, .0746, .0783, .0775, .0655])
        # Coordinates for the Head
        head_x1 = numpy.fromfunction(lambda x: rmax * numpy.cos(fac * (x + 2)), (21,))
        head_y1 = numpy.fromfunction(lambda y: rmax * numpy.sin(fac * (y + 2)), (21,))
        head_x2 = numpy.fromfunction(lambda x: rmax * numpy.cos(fac * (x + 28)), (21,))
        head_y2 = numpy.fromfunction(lambda y: rmax * numpy.sin(fac * (y + 28)), (21,))
        head_x3 = numpy.fromfunction(lambda x: rmax * numpy.cos(fac * (x + 54)), (43,))
        head_y3 = numpy.fromfunction(lambda y: rmax * numpy.sin(fac * (y + 54)), (43,))
        # Coordinates for the Nose
        nose_x = numpy.array([.18 * rmax, 0, -.18 * rmax])
        nose_y = numpy.array([rmax - 0.004, rmax * 1.15, rmax - 0.004])
        # Combine to get the contour
        x_arr = numpy.concatenate((ear_x2, head_x1, nose_x, head_x2, ear_x1, head_x3))
        y_arr = numpy.concatenate((ear_y2, head_y1, nose_y, head_y2, ear_y1, head_y3))
        x_arr *= 2 * scale
        y_arr *= 2 * scale
        x_arr += shift[0]
        y_arr += shift[1]

        return dict(x_arr = x_arr, y_arr = y_arr, color = color, linewidth = linewidth)


    @classmethod
    def _normalize(cls, points_positions):
        """Centers the brain."""
        steps = []
        for column_idx in range(3):
            column = [row[column_idx] for row in points_positions]
            step = (max(column) + min(column)) / 2.0
            steps.append(step)
        step = numpy.array(steps)
        return points_positions - step


class TopographicViewer(ABCMPLH5Displayer, BaseTopography):
    """
    Interface between TVB Framework and web display of a topography viewer.
    """
    
    _ui_name = "Topographic View"
    _ui_subsection = "topography"

    def get_input_tree(self):
        return [{'name':'data_0', 'label':'Connectivity Measures 1',
                 'type': ConnectivityMeasure, 'required': True,
                 'conditions': FilterChain(fields = [FilterChain.datatype + '._nr_dimensions'], operations = ["=="], values = [1]),
                 'description': 'Punctual values for each node in the connectivity matrix. '
                                'This will give the colors of the resulting topographic image.'},
                {'name':'data_1', 'label':'Connectivity Measures 2','type': ConnectivityMeasure,
                 'conditions': FilterChain(fields = [FilterChain.datatype + '._nr_dimensions'], operations = ["=="], values = [1]),
                 'description': 'Comparative values'},
                {'name':'data_2', 'label':'Connectivity Measures 3','type': ConnectivityMeasure,
                 'conditions': FilterChain(fields = [FilterChain.datatype + '._nr_dimensions'], operations = ["=="], values = [1]),
                 'description': 'Comparative values'},
                {'name': 'display_contours', 'label': 'Display Contours', 'type': 'bool'}]


    def plot(self, figure, data_0, data_1 = None, data_2 = None, display_contours=True):
        """
        Actual drawing method.
        """
        connectivity = data_0.connectivity
        sensor_locations = BaseTopography._normalize(connectivity.centres)
        self.plot_contours = display_contours
        sensor_number = len(sensor_locations)
        
        arrays = []
        titles = []
        for measure in [data_0, data_1, data_2]:
            if measure is not None:
                if len(measure.connectivity.centres) != sensor_number:
                    raise Exception("Use the same connectivity!!!")
                arrays.append(measure.array_data.tolist())
                titles.append(measure.title)

        self.init_topography(sensor_locations)

        for i, array_data in enumerate(arrays):
            figure.add_subplot(1, len(arrays), i + 1)
            self.draw_head_topo(figure, array_data)
            figure.gca().set_title(titles[i])


