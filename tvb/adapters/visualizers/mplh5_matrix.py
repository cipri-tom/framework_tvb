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
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>
"""

import numpy
from tvb.core.adapters.abcdisplayer import ABCMPLH5Displayer
from tvb.datatypes.arrays import FloatArray
from tvb.basic.filters.chain import FilterChain



class MatrixViewer(ABCMPLH5Displayer):
    """
    For an input of an 2d Square Matrix, plot using a MPLH5 canvas.
    """
    _ui_name = "Matrix Viewer"
    _ui_subsection = "matrix"
    
    def get_input_tree(self):
        """Accept analyzers results. """
        
        
        return [{"name" : "input_array", "label": "Square Matrix", 
                 "type" : FloatArray, "required": True}]
    
    def get_required_memory_size(self, figure, input_array, order_by=None):
        """
        Return the required memory to run this algorithm.
        """
        # Don't know how much memory is needed.
        return numpy.prod(input_array.shape) * 8
    
    def plot(self, figure, input_array, order_by=None):
            
        labels = None
        matrix = input_array.data
        matrix_size = input_array.shape[0]
        plot_title = input_array.display_name
        
        if (order_by is None) or (order_by.data is None):
            order = numpy.arange(matrix_size)
#        else:
#            order = numpy.argsort(order_by.data)
#            if (order.shape[0] != matrix_size):
#                raise LaunchException("Invalid order array")
        
        # Assumes order is shape (number_of_regions, )
        order_rows = order[:, numpy.newaxis]
        order_columns = order_rows.T

        axes = figure.gca()
        img = axes.matshow(matrix[order_rows, order_columns])
        axes.set_title(plot_title) 
        figure.colorbar(img)
        
        if (labels is None):
            return
        axes.set_yticks(numpy.arange(matrix_size))
        axes.set_yticklabels(list(labels[order]), fontsize=8)
        
        axes.set_xticks(numpy.arange(matrix_size))
        axes.set_xticklabels(list(labels[order]), fontsize=8, rotation=90)

