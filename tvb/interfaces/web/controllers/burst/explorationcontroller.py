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

import json
import urllib
import cherrypy
from tvb.config import DISCRETE_PSE_ADAPTER_MODULE, DISCRETE_PSE_ADAPTER_CLASS, ISOCLINE_PSE_ADAPTER_CLASS, ISOCLINE_PSE_ADAPTER_MODULE
from tvb.core.services import projectservice
from tvb.core.adapters.exceptions import LaunchException
from tvb.interfaces.web.controllers.basecontroller import BaseController, ajax_call, using_template


PSE_FLOT = "FLOT"
PSE_ISO = "ISO"

REDIRECT_MSG = '/burst/explore/pse_error?adapter_name=%s&message=%s'


class ParameterExplorationController(BaseController):
    """
    Controller to handle PSE actions.
    """


    def __init__(self):
        BaseController.__init__(self)
        self.project_service = projectservice.ProjectService()


    @cherrypy.expose
    @ajax_call(False)
    def get_default_pse_viewer(self, datatype_group_id):
        """
        For a given DataTypeGroup, check first if the discrete PSE is compatible.
        If this is not the case fallback to the continos PSE viewer.
        If none are available return: None.
        """
        group = self.flow_service.get_algorithm_by_module_and_class(DISCRETE_PSE_ADAPTER_MODULE,
                                                                    DISCRETE_PSE_ADAPTER_CLASS)[1]
        adapter = self.flow_service.build_adapter_instance(group)
        if adapter.is_compatible(datatype_group_id):
            return PSE_FLOT

        group = self.flow_service.get_algorithm_by_module_and_class(ISOCLINE_PSE_ADAPTER_MODULE,
                                                                    ISOCLINE_PSE_ADAPTER_CLASS)[1]
        adapter = self.flow_service.build_adapter_instance(group)
        if adapter.is_compatible(datatype_group_id):
            return PSE_ISO

        return None


    @cherrypy.expose
    @using_template('visualizers/pse_discrete/burst_preview')
    def draw_discrete_exploration(self, datatype_group_id, color_metric=None, size_metric=None):
        """
        Create new data for when the user chooses to refresh from the UI.
        """
        if color_metric == 'None':
            color_metric = None
        if size_metric == 'None':
            size_metric = None

        group = self.flow_service.get_algorithm_by_module_and_class(DISCRETE_PSE_ADAPTER_MODULE,
                                                                    DISCRETE_PSE_ADAPTER_CLASS)[1]
        adapter = self.flow_service.build_adapter_instance(group)
        if adapter.is_compatible(datatype_group_id):
            try:
                params = adapter.prepare_parameters(datatype_group_id, color_metric, size_metric)
                for key in ['labels_x', 'labels_y', 'data']:
                    params[key] = json.dumps(params[key])
                return params
            except LaunchException, ex:
                error_msg = urllib.quote(ex.message)
        else:
            error_msg = urllib.quote("Discrete explorer can only handle a max of %i values per "
                                     "dimension." % adapter.MAX_POINTS_PER_DIMENSION)

        name = urllib.quote(adapter._ui_name)
        raise cherrypy.HTTPRedirect(REDIRECT_MSG % (name, error_msg))


    @cherrypy.expose
    @using_template('visualizers/pse_isocline/burst_preview')
    def draw_isocline_exploration(self, datatype_group_id, width=None, height=None):

        if width is not None:
            width = int(width)
        if height is not None:
            height = int(height)

        group = self.flow_service.get_algorithm_by_module_and_class(ISOCLINE_PSE_ADAPTER_MODULE,
                                                                    ISOCLINE_PSE_ADAPTER_CLASS)[1]
        adapter = self.flow_service.build_adapter_instance(group)

        if adapter.is_compatible(datatype_group_id):
            try:
                return adapter.burst_preview(datatype_group_id, width, height)
            except LaunchException, ex:
                error_msg = urllib.quote(ex.message)
        else:
            error_msg = urllib.quote("Isocline PSE requires a 2D range of floating point values.")

        name = urllib.quote(adapter._ui_name)
        raise cherrypy.HTTPRedirect(REDIRECT_MSG % (name, error_msg))


    @cherrypy.expose
    @using_template('burst/burst_pse_error')
    def pse_error(self, adapter_name, message):
        return {'adapter_name': adapter_name, 'message': message}
                