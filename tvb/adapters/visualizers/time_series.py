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
A Javascript displayer for time series, using SVG.

.. moduleauthor:: Marmaduke Woodman <mw@eml.cc>

"""

import json
import tvb.datatypes.time_series as tsdata
from tvb.basic.filters.chain import FilterChain
from tvb.core.adapters.abcdisplayer import ABCDisplayer



class TimeSeries(ABCDisplayer):
    _ui_name = "Time Series Viewer (SVG/d3)"
    _ui_subsection = "timeseries"

    MAX_PREVIEW_DATA_LENGTH = 200


    def get_input_tree(self):
        """
        Inform caller of the data we need as input.
        """
        return [{"name": "time_series",
                 "type": tsdata.TimeSeries,
                 "label": "Time series to be viewed",
                 "required": True,
                 "conditions": FilterChain(fields=[FilterChain.datatype + '.type'],
                                           operations=["!="], values=["TimeSeriesVolume"])
                 }]


    def get_required_memory_size(self, **kwargs):
        """Return required memory."""
        return -1


    def launch(self, time_series, preview=False, figsize=None):
        """Construct data for visualization and launch it."""

        ts = time_series.get_data('time')
        shape = time_series.read_data_shape1()

        if type(time_series) in (tsdata.TimeSeriesRegion,):
            conn = time_series.connectivity
            labels = [l for l in conn.get_data('region_labels')]
        elif hasattr(time_series, 'sensors') and len(time_series.sensors.labels) > 0:
            labels = time_series.sensors.labels.tolist()
        else:
            labels = [str(i) for i in range(shape[-2])]

        ## Assume that the first dimension is the time since that is the case so far 
        ## NOTE: maybe doing a max(shape) and assuming that is the time dimension would be better?
        if preview and shape[0] > self.MAX_PREVIEW_DATA_LENGTH:
            shape[0] = self.MAX_PREVIEW_DATA_LENGTH

        if time_series.labels_ordering and len(time_series.labels_dimensions) >= 1:
            state_variables = time_series.labels_dimensions.get(time_series.labels_ordering[1], [])
            if state_variables <= 1:
                state_variables = []
        else:
            state_variables = []

        pars = {'baseURL': ABCDisplayer.VISUALIZERS_URL_PREFIX + time_series.gid,
                'labels': json.dumps(labels),
                'preview': preview,
                'figsize': figsize,
                'shape': repr(list(shape)),
                't0': ts[0],
                'dt': ts[1] - ts[0] if len(ts) > 1 else 1,
                # The channels component used by the EEG monitor expects a dictionary where
                # the keys are the name of the timeseries, and the values a tuple list 
                'labels_array': {str(time_series.title): [(value, idx) for idx, value in enumerate(labels)]},
                'channelsPage': '../commons/channel_selector.html' if not preview else None,
                'nrOfStateVar': state_variables,
                'nrOfModes': range(shape[3]),
                }

        return self.build_display_result("time_series/view", pars, pages=dict(controlPage="time_series/control"))


    def generate_preview(self, time_series, figure_size):
        return self.launch(time_series, preview=True, figsize=figure_size)

