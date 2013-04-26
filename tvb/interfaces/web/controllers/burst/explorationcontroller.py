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
from tvb.core.adapters.exceptions import LaunchException
"""
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""
import json
import urllib
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
    def get_default_pse_viewer(self, datatype_group_id):
        """
        For a given datatype group, check first the discrete PSE is compatible.
        If this is not the case fallback to the continous one. If none are available
        return None.
        """
        algo_group = self.flow_service.get_algorithm_by_module_and_class(PSE_ADAPTER_MODULE, PSE_ADAPTER_CLASS)[1]
        param_explore_discrete = self.flow_service.build_adapter_instance(algo_group)
        if param_explore_discrete.is_compatible(datatype_group_id):
            return "FLOT"
        algo_group = self.flow_service.get_algorithm_by_module_and_class(ISO_PSE_ADAPTER_MODULE, ISO_PSE_ADAPTER_CLASS)[1]
        param_explore_continous = self.flow_service.build_adapter_instance(algo_group)
        if param_explore_continous.is_compatible(datatype_group_id):
            return "ISO"
        return None
    

    @cherrypy.expose
    @ajax_call(False)
    def draw_parameter_exploration(self, datatype_group_id, color_metric=None, size_metric=None):
        """
        Create new data for when the user chooses to refresh from the UI.
        """
        if color_metric == 'None': color_metric = None
        if size_metric == 'None': size_metric = None
        algo_group = self.flow_service.get_algorithm_by_module_and_class(PSE_ADAPTER_MODULE, PSE_ADAPTER_CLASS)[1]
        param_explore_adapter = self.flow_service.build_adapter_instance(algo_group)
        if param_explore_adapter.is_compatible(datatype_group_id):
            return self._get_flot_html_result(param_explore_adapter, datatype_group_id, color_metric, size_metric)
        else:
            return self._display_error_page('Discrete Explorer', 
                                            "Discrete explorer can only handle a max of %i values per dimension."%(
                                                                    param_explore_adapter.MAX_POINTS_PER_DIMENSION,))
        
    @bc.using_template('visualizers/parameter_exploration/burst_preview')
    def _get_flot_html_result(self, adapter, datatype_group_id, color_metric, size_metric):
        try:
            params = adapter.prepare_parameters(datatype_group_id, color_metric, size_metric)
            for key in ['labels_x', 'labels_y', 'data']:
                params[key] = json.dumps(params[key])
            return params
        except LaunchException, ex:
            error_msg = urllib.quote(ex.message)
            raise cherrypy.HTTPRedirect('/burst/explore/_display_error_page?adapter_name="Discrete+viewer"&message="%s"'%(error_msg,))
    
    @cherrypy.expose
    @ajax_call(False)
    def draw_isocline_explorer(self, datatype_group_id, width=None, height=None):
        if width is not None: width = int(width)
        if height is not None: height = int(height)
        algo_group = self.flow_service.get_algorithm_by_module_and_class(ISO_PSE_ADAPTER_MODULE, ISO_PSE_ADAPTER_CLASS)[1]
        iso_param_expore = self.flow_service.build_adapter_instance(algo_group)
        if iso_param_expore.is_compatible(datatype_group_id):
            return self._get_iso_pse_html(iso_param_expore, datatype_group_id, width, height)
        else:
            return self._display_error_page('Continous Explorer', "Continous PSE requires a 2D range of floating point values.")
    
    
    @bc.using_template('visualizers/isocline_pse/view')
    def _get_iso_pse_html(self, adapter, datatype_group_id, width, height):
        """
        Generate the HTML for the isocline visualizers.
        """
        try:
            return adapter.burst_preview(datatype_group_id, width, height)
        except LaunchException, ex:
            error_msg = urllib.quote(ex.message)
            raise cherrypy.HTTPRedirect('/burst/explore/_display_error_page?adapter_name="Isocline+viewer"&message="%s"'%(error_msg,))
    
    @cherrypy.expose
    @bc.using_template('burst/burst_pse_error')
    def _display_error_page(self, adapter_name, message):
        return {'adapter_name' : adapter_name, 'message' : message}
                