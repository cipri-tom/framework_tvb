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
from tvb.interfaces.web.structure import WebStructure
from tvb.interfaces.web.controllers.help.helpcontroller import HelpController
from tvb.basic.config.settings import TVBSettings as cfg
from tvb_test.core.base_testcase import BaseControllersTest, TransactionalTestCase


class HelpControllerTest(TransactionalTestCase, BaseControllersTest):
    """ Unit tests for helpcontroller """
    
    def setUp(self):
        # Add 3 entries so we no longer consider this the first run.
        cfg.add_entries_to_config_file({'test' : 'test',
                                        'test1' : 'test1',
                                        'test2' : 'test2'})
        self.help_c =  HelpController()
        cherrypy.session = BaseControllersTest.CherrypySession()
    
    
    def tearDown(self):
        if os.path.exists(cfg.TVB_CONFIG_FILE):
            os.remove(cfg.TVB_CONFIG_FILE)
            
            
    def test_show_online_help(self):
        result_dict = self.help_c.showOnlineHelp(WebStructure.SECTION_PROJECT, WebStructure.SUB_SECTION_OPERATIONS)
        self.assertTrue('helpURL' in result_dict)
        self.assertEqual(result_dict['helpURL'], '/static/help/UserGuide-UI_Project.html#operations')
        self.assertEqual(result_dict['overlay_class'], 'help')
        self.assertEqual(result_dict['overlay_content_template'], 'help/online_help')
        self.assertEqual(result_dict['overlay_description'], 'Online-Help')
        
            
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(HelpControllerTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)