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
import unittest
import cherrypy
import tvb.interfaces.web.controllers.basecontroller as b_c
from tvb.interfaces.web.controllers.spatial.regionstimuluscontroller import RegionStimulusController
from tvb.basic.config.settings import TVBSettings as cfg
from tvb_test.core.base_testcase import BaseControllersTest, TransactionalTestCase
from tvb_test.core.test_factory import TestFactory


class RegionsStimulusContollerTest(TransactionalTestCase, BaseControllersTest):
    """ Unit tests for burstcontroller """
    
    def setUp(self):
        # Add 3 entries so we no longer consider this the first run.
        cfg.add_entries_to_config_file({'test' : 'test',
                                        'test1' : 'test1',
                                        'test2' : 'test2'})
        self.test_user = TestFactory.create_user()
        self.test_project = TestFactory.create_project(self.test_user, "Test")
        self.region_s_c =  RegionStimulusController()
        cherrypy.session = BaseControllersTest.CherrypySession()
        cherrypy.session[b_c.KEY_USER] = self.test_user
        cherrypy.session[b_c.KEY_PROJECT] = self.test_project
    
    
    def tearDown(self):
        if os.path.exists(cfg.TVB_CONFIG_FILE):
            os.remove(cfg.TVB_CONFIG_FILE)
    
    def test_step_1(self):
        self.region_s_c.step_1_submit(1, 1)
        result_dict = self.region_s_c.step_1()
        self.assertEqual(result_dict['equationViewerUrl'], '/spatial/stimulus/region/get_equation_chart')
        self.assertTrue('fieldsPrefixes' in result_dict)
        self.assertEqual(result_dict['loadExistentEntityUrl'], '/spatial/stimulus/region/load_region_stimulus')
        self.assertEqual(result_dict['mainContent'], 'spatial/stimulus_region_step1_main')
        self.assertEqual(result_dict['next_step_url'], '/spatial/stimulus/region/step_1_submit')

            
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(RegionsStimulusContollerTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)