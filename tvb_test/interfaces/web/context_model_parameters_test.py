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
"""
import unittest
import numpy
from tvb.core.services.flowservice import FlowService
from tvb.datatypes.connectivity import Connectivity
from tvb.core.adapters.abcadapter import ABCAdapter
import tvb.simulator.models as models_module
from tvb.interfaces.web.entities.context_model_parameters import ContextModelParameters
from tvb_test.core.test_factory import TestFactory
from tvb_test.core.base_testcase import TransactionalTestCase

class ContextModelParametersTest(TransactionalTestCase):
    """
    Test class for the context_model_parameters module.
    """
    START = 100.55
    INCREMENT = 122.32

    def setUp(self):
        """
        Reset the database before each test.
        """
        self.flow_service = FlowService()

        self.test_user = TestFactory.create_user()
        self.test_project = TestFactory.create_project(self.test_user)
        TestFactory.import_cff(test_user=self.test_user, test_project=self.test_project)
        self.default_model = models_module.Generic2dOscillator()

        all_connectivities = self.flow_service.get_available_datatypes(self.test_project.id, Connectivity)
        self.connectivity = ABCAdapter.load_entity_by_gid(all_connectivities[0][2])
        self.connectivity.number_of_regions = 74
        self.context_model_param = ContextModelParameters(self.connectivity, self.default_model)


    def tearDown(self):
        """
        Reset the database when test is done.
        """
        self.delete_project_folders()


    def test_load_model_for_connectivity_node(self):
        self.context_model_param.load_model_for_connectivity_node(0)
        model_0 = self.context_model_param._get_model_for_region(0)
        self._check_model_params_for_default_values(model_0)
        self._check_model_params_for_default_values(self.context_model_param._phase_plane.model)

        self.context_model_param.load_model_for_connectivity_node(1)
        model_1 = self.context_model_param._get_model_for_region(1)
        self._check_model_params_for_default_values(model_1)
        self._check_model_params_for_default_values(self.context_model_param._phase_plane.model)

        self._update_all_model_params(1)
        model_1 = self.context_model_param._get_model_for_region(1)
        self._check_model_params_for_updated_values(model_1)
        self._check_model_params_for_updated_values(self.context_model_param._phase_plane.model)

        self.context_model_param.load_model_for_connectivity_node(0)
        model_0 = self.context_model_param._get_model_for_region(0)
        self._check_model_params_for_default_values(model_0)
        self._check_model_params_for_default_values(self.context_model_param._phase_plane.model)


    def test_update_model_parameter(self):
        self.context_model_param.load_model_for_connectivity_node(0)
        model_0 = self.context_model_param._get_model_for_region(0)
        self._check_model_params_for_default_values(model_0)
        self._check_model_params_for_default_values(self.context_model_param._phase_plane.model)

        self._update_all_model_params(0)
        model_0 = self.context_model_param._get_model_for_region(0)
        self._check_model_params_for_updated_values(model_0)
        self._check_model_params_for_updated_values(self.context_model_param._phase_plane.model)


    def test_reset_model_parameters_for_node(self):
        self.context_model_param.load_model_for_connectivity_node(0)
        model_0 = self.context_model_param._get_model_for_region(0)
        self._check_model_params_for_default_values(model_0)
        self._check_model_params_for_default_values(self.context_model_param._phase_plane.model)

        self._update_all_model_params(0)
        model_0 = self.context_model_param._get_model_for_region(0)
        self._check_model_params_for_updated_values(model_0)
        self._check_model_params_for_updated_values(self.context_model_param._phase_plane.model)

        self.context_model_param.reset_model_parameters_for_nodes([0])
        model_0 = self.context_model_param._get_model_for_region(0)
        self._check_model_params_for_default_values(model_0)
        #because we reset a list of nodes we do not update the phase plane
        self._check_model_params_for_updated_values(self.context_model_param._phase_plane.model)


    def test_get_values_for_parameter(self):
        model_params = self.context_model_param.model_parameter_names
        for param in model_params:
            self.assertEqual(str(getattr(self.default_model, param).tolist()),
                             self.context_model_param.get_values_for_parameter(param))

        self._update_all_model_params(0)
        for param in model_params:
            value = self.START + self.INCREMENT
            expected_list = [float(getattr(self.default_model, param)[0]) for i in range(self.connectivity.number_of_regions)]
            expected_list[0] = value
            self.assertEqual(str(expected_list), self.context_model_param.get_values_for_parameter(param))


    def _update_all_model_params(self, connectivity_node_index):
        self.context_model_param.load_model_for_connectivity_node(connectivity_node_index)
        model_params = self.context_model_param.model_parameter_names
        for param in model_params:
            value = self.START + self.INCREMENT
            self.context_model_param.update_model_parameter(connectivity_node_index, param, value)


    def _check_model_params_for_default_values(self, model_to_check):
        model_params = self.context_model_param.model_parameter_names
        for param in model_params:
            self.assertEqual(getattr(self.default_model, param), getattr(model_to_check, param), "The parameters should be equal.")


    def _check_model_params_for_updated_values(self, model_to_check):
        model_params = self.context_model_param.model_parameter_names
        for param in model_params:
            value = self.START + self.INCREMENT
            self.assertEqual(numpy.array([value]), getattr(model_to_check, param), "The parameters should be equal.")



def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(ContextModelParametersTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)
    
    