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
A displayer for the principal components analysis.

.. moduleauthor:: Marmaduke Woodman <mw@eml.cc>

"""

from tvb.datatypes.mode_decompositions import PrincipalComponents
from tvb.core.adapters.abcdisplayer import ABCDisplayer



class PCA(ABCDisplayer):
    _ui_name = "Principal Components Analysis"


    def get_input_tree(self):
        """Inform caller of the data we need"""

        return [{"name": "pca",
                 "type": PrincipalComponents,
                 "label": "Principal component analysis:",
                 "required": True
                 }]


    def get_required_memory_size(self, **kwargs):
        """Return required memory. Here, it's unknown/insignificant."""
        return -1


    def launch(self, pca):
        """Construct data for visualization and launch it."""

        # get data from pca datatype, convert to json
        u = self.dump_prec(pca.get_data('fractions').flat)
        vt = self.dump_prec(pca.get_data('weights').flat)

        return self.build_display_result("pca/view", dict(u=u, vt=vt))


    def generate_preview(self, pca, figure_size):
        return self.launch(pca)


    def dump_prec(self, xs, prec=3):
        """
        Dump a list of numbers into a string, each at the specified precision. 
        """

        return "[" + ",".join(map(lambda x: ("%0." + str(prec) + "g") % (x,), xs)) + "]"

