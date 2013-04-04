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
import os
import json
import unittest
import cherrypy
import tvb.interfaces.web.controllers.basecontroller as b_c
from tvb.interfaces.web.controllers.spatial.regionsmodelparameterscontroller import RegionsModelParametersController
from tvb.interfaces.web.controllers.burst.burstcontroller import BurstController
from tvb.basic.config.settings import TVBSettings as cfg
from tvb_test.core.base_testcase import BaseControllersTest, TransactionalTestCase
from tvb_test.core.test_factory import TestFactory
from tvb_test.datatypes.datatypes_factory import DatatypesFactory
from tvb_test.adapters.simulator.simulator_adapter_test import SIMULATOR_PARAMETERS
from tvb.core.entities.transient.context_local_connectivity import ContextLocalConnectivity


class RegionsModelParametersContollerTest(TransactionalTestCase, BaseControllersTest):
    """ Unit tests for burstcontroller """
    
    def setUp(self):
        # Add 3 entries so we no longer consider this the first run.
        cfg.add_entries_to_config_file({'test' : 'test',
                                        'test1' : 'test1',
                                        'test2' : 'test2'})
        self.test_user = TestFactory.create_user()
        self.test_project = TestFactory.create_project(self.test_user, "Test")
        self.region_m_p_c =  RegionsModelParametersController()
        cherrypy.session = BaseControllersTest.CherrypySession()
        cherrypy.session[b_c.KEY_USER] = self.test_user
        cherrypy.session[b_c.KEY_PROJECT] = self.test_project
        BurstController().index()
        stored_burst = cherrypy.session[b_c.KEY_BURST_CONFIG]
        _, self.connectivity = DatatypesFactory().create_connectivity()
        new_params = {}
        for key, val in SIMULATOR_PARAMETERS.iteritems():
            new_params[key] = {'value' : val}
        new_params['connectivity'] = {'value' : self.connectivity.gid}
        stored_burst.simulator_configuration = new_params
    
    
    def tearDown(self):
        if os.path.exists(cfg.TVB_CONFIG_FILE):
            os.remove(cfg.TVB_CONFIG_FILE)
    
    
    def test_edit_model_parameters(self):
        result_dict = self.region_m_p_c.edit_model_parameters()
        self.assertEqual(self.connectivity.gid, result_dict['connectivity_entity'].gid)
        self.assertTrue(result_dict['displayDefaultSubmitBtn'])
        self.assertEqual(result_dict['mainContent'], 'spatial/model_param_region_main')
        self.assertEqual(result_dict['submit_parameters_url'], 
                         '/spatial/modelparameters/regions/submit_model_parameters')
        self.assertTrue('paramSlidersData' in result_dict)
        self.assertTrue('parametersNames' in result_dict)
        self.assertTrue('pointsLabels' in result_dict)
        self.assertTrue('positions' in result_dict)
        
        
    def test_load_model_for_connectivity_node(self):
        self.region_m_p_c.edit_model_parameters()
        result_dict = self.region_m_p_c.load_model_for_connectivity_node(1)
        self.assertTrue('paramSlidersData' in result_dict)
        self.assertTrue('parametersNames' in result_dict)
        
        
    def test_update_model_parameter_for_nodes(self):
        self.region_m_p_c.edit_model_parameters()
        result_dict = self.region_m_p_c.load_model_for_connectivity_node(1)
        param_names = result_dict['parametersNames']
        param_values = json.loads(result_dict['paramSlidersData'])
        old_value = param_values[param_names[0]]["default"]
        self.region_m_p_c.update_model_parameter_for_nodes(param_names[0], 
                                                           old_value + 1, json.dumps([1]))
        result_dict = self.region_m_p_c.load_model_for_connectivity_node(1)
        param_names = result_dict['parametersNames']
        param_values = json.loads(result_dict['paramSlidersData'])
        self.assertEqual(param_values[param_names[0]]["default"], old_value + 1)
        
        
    def test_copy_model(self):
        self.region_m_p_c.edit_model_parameters()
        result_dict = self.region_m_p_c.load_model_for_connectivity_node(1)
        param_names = result_dict['parametersNames']
        param_values = json.loads(result_dict['paramSlidersData'])
        old_value = param_values[param_names[0]]["default"]
        self.region_m_p_c.update_model_parameter_for_nodes(param_names[0], 
                                                           old_value + 1, json.dumps([1]))
        self.region_m_p_c.copy_model('1', json.dumps([2]))
        result_dict = self.region_m_p_c.load_model_for_connectivity_node(2)
        param_names = result_dict['parametersNames']
        param_values = json.loads(result_dict['paramSlidersData'])
        self.assertEqual(param_values[param_names[0]]["default"], old_value + 1)
        
        
    def test_reset_model_parameters_for_nodes(self):
        self.region_m_p_c.edit_model_parameters()
        result_dict = self.region_m_p_c.load_model_for_connectivity_node(1)
        param_names = result_dict['parametersNames']
        param_values = json.loads(result_dict['paramSlidersData'])
        old_value = param_values[param_names[0]]["default"]
        self.region_m_p_c.update_model_parameter_for_nodes(param_names[0], 
                                                           old_value + 1, json.dumps([1]))
        self.region_m_p_c.reset_model_parameters_for_nodes(json.dumps([1]))
        result_dict = self.region_m_p_c.load_model_for_connectivity_node(2)
        param_names = result_dict['parametersNames']
        param_values = json.loads(result_dict['paramSlidersData'])
        self.assertEqual(param_values[param_names[0]]["default"], old_value)
        
        
    def test_submit_model_parameters(self):
        self.region_m_p_c.edit_model_parameters()
        self._expect_redirect('/burst/', self.region_m_p_c.submit_model_parameters)
        
            
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(RegionsModelParametersContollerTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)