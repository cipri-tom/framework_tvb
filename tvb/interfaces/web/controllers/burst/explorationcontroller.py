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
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""

import cherrypy
from tvb.config import PSE_ADAPTER_MODULE, PSE_ADAPTER_CLASS, ISO_PSE_ADAPTER_CLASS, ISO_PSE_ADAPTER_MODULE
from tvb.core.services import projectservice
from tvb.interfaces.web.controllers.basecontroller import ajax_call
from tvb.interfaces.web.controllers import basecontroller as bc


class ParameterExplorationController(bc.BaseController):
    """
    Controller to handle PSE actions.
    """


    def __init__(self):
        bc.BaseController.__init__(self)
        self.project_service = projectservice.ProjectService()


    @cherrypy.expose
    @ajax_call(False)
    def draw_parameter_exploration(self, datatype_group_id, color_metric, size_metric):
        """
        Create new data for when the user chooses to refresh from the UI.
        """
        if color_metric == 'None':
            color_metric = None
        if size_metric == 'None':
            size_metric = None

        algo_group = self.flow_service.get_algorithm_by_module_and_class(PSE_ADAPTER_MODULE, PSE_ADAPTER_CLASS)[1]
        param_explore_adapter = self.flow_service.build_adapter_instance(algo_group)

        params = param_explore_adapter.prepare_parameters(datatype_group_id, color_metric, size_metric)
        return params.prepare_full_json()
    
    
    @cherrypy.expose
    def draw_isocline_explorer(self, datatype_group_id):
        try:
            html_result = self._get_iso_pse_html(datatype_group_id)
        except cherrypy.HTTPRedirect:
            html_result = "Continous PSE requires a 2D range of floating point values."
        return html_result
    
    
    @bc.using_template('visualizers/mplh5/figure')
    def _get_iso_pse_html(self, datatype_group_id):
        """
        Generate the HTML for the isocline visualizers.
        """
        algo_group = self.flow_service.get_algorithm_by_module_and_class(ISO_PSE_ADAPTER_MODULE, ISO_PSE_ADAPTER_CLASS)[1]
        iso_param_expore = self.flow_service.build_adapter_instance(algo_group)
        return iso_param_expore.burst_preview(datatype_group_id)
    
    
                