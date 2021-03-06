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
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Ionel Ortelecan <ionel.ortelecan@codemart.ro>
"""

import cherrypy
import json
from copy import deepcopy

import tvb.interfaces.web.controllers.basecontroller as base
import tvb.basic.traits.traited_interface as traited_interface
from tvb.interfaces.web.controllers.basecontroller import using_template, settings
from tvb.interfaces.web.controllers.userscontroller import logged
from tvb.interfaces.web.controllers.flowcontroller import SelectedAdapterContext
from tvb.basic.traits.parameters_factory import get_traited_instance_for_name
from tvb.basic.logger.builder import get_logger
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.core.services.flowservice import FlowService
from tvb.adapters.visualizers.connectivity import ConnectivityViewer
from tvb.simulator.models import Model
from tvb.simulator.integrators import Integrator
from tvb.config import SIMULATOR_CLASS, SIMULATOR_MODULE
from tvb.datatypes import noise_framework


PARAM_CONNECTIVITY = 'connectivity'
PARAM_SURFACE = 'surface'
PARAM_MODEL = 'model'
PARAM_INTEGRATOR = 'integrator'
MODEL_PARAMETERS = 'model_parameters'
INTEGRATOR_PARAMETERS = 'integrator_parameters'
PARAMS_MODEL_PATTERN = 'model_parameters_option_%s_%s'



class SpatioTemporalController(base.BaseController):
    """
    Base class which contains methods related to spatio-temporal actions.
    """


    def __init__(self):
        base.BaseController.__init__(self)
        self.flow_service = FlowService()
        self.logger = get_logger(__name__)
        editable_entities = [dict(link='/spatial/stimulus/region/step_1_submit/1/1', title='Region Stimulus',
                                  subsection='regionstim', description='Create a new Stimulus on Region level'),
                             dict(link='/spatial/stimulus/surface/step_1_submit/1/1', title='Surface Stimulus',
                                  subsection='surfacestim', description='Create a new Stimulus on Surface level')]
        self.submenu_list = editable_entities


    @cherrypy.expose
    @using_template('base_template')
    @logged()
    @settings()
    def index(self, **data):
        """
        Displays the main page for the spatio temporal section.
        """
        template_specification = dict(title="Spatio temporal", data=data)
        template_specification['mainContent'] = 'header_menu'
        return self.fill_default_attributes(template_specification)


    @staticmethod
    def get_connectivity_parameters(input_connectivity, surface_data=None):
        """
        Returns a dictionary which contains all the needed data for drawing a connectivity.
        """
        viewer = ConnectivityViewer()
        global_params, global_pages = viewer.compute_connectivity_global_params(input_connectivity, surface_data)
        global_params.update(global_pages)
        global_params['selectedConnectivityGid'] = input_connectivity.gid
        return global_params


    def get_data_from_burst_configuration(self):
        """
        Returns the model, integrator, connectivity and surface instances from the burst configuration.
        """
        ### Read from session current burst-configuration
        burst_configuration = base.get_from_session(base.KEY_BURST_CONFIG)
        if burst_configuration is None:
            return None, None, None
        first_range = burst_configuration.get_simulation_parameter_value('range_1')
        second_range = burst_configuration.get_simulation_parameter_value('range_2')
        if ((first_range is not None and str(first_range).startswith(MODEL_PARAMETERS)) or
                (second_range is not None and str(second_range).startswith(MODEL_PARAMETERS))):
            base.set_error_message("When configuring model parameters you are not allowed to specify range values.")
            raise cherrypy.HTTPRedirect("/burst/")
        group = self.flow_service.get_algorithm_by_module_and_class(SIMULATOR_MODULE, SIMULATOR_CLASS)[1]
        simulator_adapter = self.flow_service.build_adapter_instance(group)
        try:
            params_dict = simulator_adapter.convert_ui_inputs(burst_configuration.get_all_simulator_values()[0], False)
        except Exception, excep:
            self.logger.exception(excep)
            base.set_error_message("Some of the provided parameters have an invalid value.")
            raise cherrypy.HTTPRedirect("/burst/")
        ### Prepare Model instance
        model = burst_configuration.get_simulation_parameter_value(PARAM_MODEL)
        model_parameters = params_dict[MODEL_PARAMETERS]
        noise_framework.build_noise(model_parameters)
        try:
            model = get_traited_instance_for_name(model, Model, model_parameters)
        except Exception, ex:
            self.logger.exception(ex)
            self.logger.info("Could not create the model instance with the given parameters. "
                             "A new model instance will be created with the default values.")
            model = get_traited_instance_for_name(model, Model, {})
        ### Prepare Integrator instance
        integrator = burst_configuration.get_simulation_parameter_value(PARAM_INTEGRATOR)
        integrator_parameters = params_dict[INTEGRATOR_PARAMETERS]
        noise_framework.build_noise(integrator_parameters)
        try:
            integrator = get_traited_instance_for_name(integrator, Integrator, integrator_parameters)
        except Exception, ex:
            self.logger.exception(ex)
            self.logger.info("Could not create the integrator instance with the given parameters. "
                             "A new integrator instance will be created with the default values.")
            integrator = get_traited_instance_for_name(integrator, Integrator, {})
        ### Prepare Connectivity
        connectivity_gid = burst_configuration.get_simulation_parameter_value(PARAM_CONNECTIVITY)
        connectivity = ABCAdapter.load_entity_by_gid(connectivity_gid)
        ### Prepare Surface
        surface_gid = burst_configuration.get_simulation_parameter_value(PARAM_SURFACE)
        surface = None
        if surface_gid is not None and len(surface_gid):
            surface = ABCAdapter.load_entity_by_gid(surface_gid)
        return model, integrator, connectivity, surface


    @staticmethod
    def display_surface(surface_gid):
        """
        Generates the HTML for displaying the surface with the given ID.
        """
        surface = ABCAdapter.load_entity_by_gid(surface_gid)
        base.add2session(PARAM_SURFACE, surface_gid)
        url_vertices_pick, url_normals_pick, url_triangles_pick = surface.get_urls_for_pick_rendering()
        url_vertices, url_normals, _, url_triangles, alphas, alphas_indices = surface.get_urls_for_rendering(True, None)

        template_specification = dict()
        template_specification['urlVerticesPick'] = json.dumps(url_vertices_pick)
        template_specification['urlTrianglesPick'] = json.dumps(url_triangles_pick)
        template_specification['urlNormalsPick'] = json.dumps(url_normals_pick)
        template_specification['urlVertices'] = json.dumps(url_vertices)
        template_specification['urlTriangles'] = json.dumps(url_triangles)
        template_specification['urlNormals'] = json.dumps(url_normals)
        template_specification['alphas'] = json.dumps(alphas)
        template_specification['alphas_indices'] = json.dumps(alphas_indices)
        template_specification['brainCenter'] = json.dumps(surface.center())
        return template_specification


    @staticmethod
    def prepare_entity_interface(input_list):
        """
        Prepares the input tree obtained from a creator.
        """
        return {'inputList': input_list,
                base.KEY_PARAMETERS_CONFIG: False}


    def get_creator_and_interface(self, creator_module, creator_class, datatype_instance, lock_midpoint_for_eq=None):
        """
        Returns a Tuple: a creator instance and a dictionary for the creator interface.
        The interface is prepared for rendering, it is populated with existent data, in case of a
        parameter of type DataType. The name of the attributes are also prefixed to identify groups.
        """
        algo_group = self.flow_service.get_algorithm_by_module_and_class(creator_module, creator_class)[1]
        group, _ = self.flow_service.prepare_adapter(base.get_current_project().id, algo_group)

        #I didn't use the interface(from the above line) returned by the method 'prepare_adapter' from flow service
        # because the selects that display dataTypes will also have the 'All' entry.
        datatype_instance.trait.bound = traited_interface.INTERFACE_ATTRIBUTES_ONLY
        input_list = datatype_instance.interface[traited_interface.INTERFACE_ATTRIBUTES]
        if lock_midpoint_for_eq is not None:
            for idx in lock_midpoint_for_eq:
                input_list[idx] = self._lock_midpoints(input_list[idx])
        category = self.flow_service.get_visualisers_category()
        input_list = self.flow_service.prepare_parameters(input_list, base.get_current_project().id, category.id)
        input_list = ABCAdapter.prepare_param_names(input_list)

        return self.flow_service.build_adapter_instance(group), input_list


    @staticmethod
    def get_series_json(data, label):
        """ For each data point entry, build the FLOT specific JSON. """
        series = "{\"data\": " + json.dumps(data) + ","
        series += "\"label\": \"" + label + "\""
        series += "}"
        return series


    @staticmethod
    def build_final_json(list_of_series):
        """ Given a list with all the data points, build the final FLOT json. """
        final_json = "["
        for i, value in enumerate(list_of_series):
            if i:
                final_json += ","
            final_json += value
        final_json += "]"
        return final_json


    @staticmethod
    def get_ui_message(list_of_equation_names):
        """
        The message returned by this method should be displayed if
        the equation with the given name couldn't be evaluated in all points.
        """
        if len(list_of_equation_names):
            return ("Could not evaluate the " + ", ".join(list_of_equation_names) + " equation(s) "
                    "in all the points. Some of the values were changed.")
        else:
            return ""


    def get_select_existent_entities(self, label, entity_type, entity_gid=None):
        """
        Returns the dictionary needed for drawing the select which display all
        the created entities of the specified type.
        """
        project_id = base.get_current_project().id
        category = self.flow_service.get_visualisers_category()

        interface = [{'name': 'existentEntitiesSelect', 'label': label, 'type': entity_type}]
        if entity_gid is not None:
            interface[0]['default'] = entity_gid
        interface = self.flow_service.prepare_parameters(interface, project_id, category.id)
        interface = ABCAdapter.prepare_param_names(interface)

        return interface


    @staticmethod
    def add_interface_to_session(left_input_tree, right_input_tree):
        """
        left_input_tree and right_input_tree are expected to be lists of dictionaries.

        Those 2 given lists will be concatenated and added to session.
        In order to work the filters, the interface should be added to session.
        """
        entire_tree = deepcopy(left_input_tree)
        entire_tree.extend(right_input_tree)
        SelectedAdapterContext().add_adapter_to_session(None, entire_tree)


    def fill_default_attributes(self, template_dictionary, subsection='stimulus'):
        """
        Overwrite base controller to add required parameters for adapter templates.
        """
        template_dictionary[base.KEY_SECTION] = 'stimulus'
        template_dictionary[base.KEY_SUB_SECTION] = subsection
        template_dictionary[base.KEY_SUBMENU_LIST] = self.submenu_list
        template_dictionary[base.KEY_INCLUDE_RESOURCES] = 'spatial/included_resources'
        base.BaseController.fill_default_attributes(self, template_dictionary)
        return template_dictionary


    def get_x_axis_range(self, min_x_str, max_x_str):
        """
        Fill range for the X-axis displayed in 2D graph.
        """
        min_x = 0
        max_x = 100
        error_msg = ''
        if self.is_int(min_x_str):
            min_x = int(min_x_str)

            if self.is_int(max_x_str):
                max_x = int(max_x_str)
            else:
                min_x = 0
                error_msg = "The max value for the x-axis should be an integer value."

            if min_x >= max_x:
                error_msg = "The min value for the x-axis should be smaller then the max value of the x-axis."
                min_x = 0
                max_x = 100
        else:
            error_msg = "The min value for the x-axis should be an integer value."

        return min_x, max_x, error_msg


    @staticmethod
    def _lock_midpoints(equations_dict):
        """
        Set mid-points for gaussian / double gausians as locked to 0.0 in case of spatial equations.
        """
        for equation in equations_dict[ABCAdapter.KEY_OPTIONS]:
            if equation[ABCAdapter.KEY_NAME] == 'Gaussian':
                for entry in equation[ABCAdapter.KEY_ATTRIBUTES][1][ABCAdapter.KEY_ATTRIBUTES]:
                    if entry[ABCAdapter.KEY_NAME] == 'midpoint':
                        entry['locked'] = True
            if equation[ABCAdapter.KEY_NAME] == 'DoubleGaussian':
                for entry in equation[ABCAdapter.KEY_ATTRIBUTES][1][ABCAdapter.KEY_ATTRIBUTES]:
                    if entry[ABCAdapter.KEY_NAME] == 'midpoint1':
                        entry['locked'] = True
        return equations_dict


    @staticmethod
    def is_int(str_value):
        """
        Checks if the given string may be converted to an int value.
        """
        try:
            int(str_value)
            return True
        except Exception:
            return False
        
        
    def get_data_for_param_sliders(self, connectivity_node_index, context_model_parameters):
        """
        Method used only for handling the exception.
        """
        try:
            return context_model_parameters.get_data_for_param_sliders(connectivity_node_index)
        except ValueError, excep:
            self.logger.info("All the model parameters that are configurable should be valid arrays or numbers.")
            self.logger.exception(excep)
            base.set_error_message("All the model parameters that are configurable should be valid arrays or numbers.")
            raise cherrypy.HTTPRedirect("/burst/")
        
        
        
