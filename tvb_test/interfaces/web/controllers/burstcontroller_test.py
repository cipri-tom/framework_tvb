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

from tvb.basic.profile import TvbProfile as tvb_profile
#set the current environment to the test setup
tvb_profile.set_profile(["-profile", "TEST_POSTGRES_PROFILE"])

import unittest
import cherrypy
import tvb.interfaces.web.controllers.basecontroller as b_c
from tvb.interfaces.web.controllers.burst.burstcontroller import BurstController
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.entities.storage import dao
from tvb.core.entities.model.model_burst import BurstConfiguration, NUMBER_OF_PORTLETS_PER_TAB
from tvb_test.adapters.testadapter1 import TestAdapter1
from tvb_test.datatypes.datatypes_factory import DatatypesFactory
from tvb_test.core.base_testcase import BaseControllersTest
from tvb_test.core.test_factory import TestFactory


class BurstContollerTest(BaseControllersTest):
    """ Unit tests for burstcontroller """
    
    def setUp(self):
        # Add 3 entries so we no longer consider this the first run.
        cfg.add_entries_to_config_file({'test' : 'test',
                                        'test1' : 'test1',
                                        'test2' : 'test2'})
        self.test_user = TestFactory.create_user()
        self.test_project = TestFactory.create_project(self.test_user, "Test")
        self.burst_c =  BurstController()
        cherrypy.session = BaseControllersTest.CherrypySession()
        cherrypy.session[b_c.KEY_USER] = self.test_user
        cherrypy.session[b_c.KEY_PROJECT] = self.test_project
    
    
    def tearDown(self):
        if os.path.exists(cfg.TVB_CONFIG_FILE):
            os.remove(cfg.TVB_CONFIG_FILE)
            
            
    def test_index(self):
        """
        """
        result_dict = self.burst_c.index()
        self.assertTrue('burst_list' in result_dict and result_dict['burst_list'] == [])
        self.assertTrue('available_metrics' in result_dict and isinstance(result_dict['available_metrics'], list))
        self.assertTrue('portletList' in result_dict and isinstance(result_dict['portletList'], list))
        self.assertEqual(result_dict[b_c.KEY_SECTION], "burst")
        self.assertTrue('burstConfig' in result_dict and isinstance(result_dict['burstConfig'], BurstConfiguration))
        portlets = json.loads(result_dict['selectedPortlets'])
        portlet_id = dao.get_portlet_by_identifier("TimeSeries").id
        for tab_idx in range(len(portlets)):
            for index_in_tab in range(len(portlets[0])):
                if tab_idx == 0 and index_in_tab == 0:
                    self.assertEqual(portlets[tab_idx][index_in_tab], [portlet_id, "TimeSeries"])
                else:
                    self.assertEqual(portlets[tab_idx][index_in_tab], [-1, "None"])
        self.assertTrue(result_dict['draw_hidden_ranges'])
        
        
    def test_load_burst_history(self):
        """
        """
        burst = BurstConfiguration(self.test_project.id, 'started', {'test' : 'test'}, 'burst1')
        burst.prepare_before_save()
        dao.store_entity(burst)
        burst = BurstConfiguration(self.test_project.id, 'started', {'test' : 'test'}, 'burst2')
        burst.prepare_before_save()
        burst = dao.store_entity(burst)
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst
        result_dict = self.burst_c.load_burst_history()
        burst_history = result_dict['burst_list']
        self.assertEqual(len(burst_history), 2)
        for burst in burst_history:
            self.assertTrue(burst.name in ('burst1', 'burst2'))
            
            
    def test_get_selected_burst(self):
        """
        """
        burst_entity = BurstConfiguration(self.test_project.id, 'started', {}, 'burst1')
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst_entity
        stored_id = self.burst_c.get_selected_burst()
        self.assertEqual(stored_id, 'None')
        burst_entity = dao.store_entity(burst_entity)  
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst_entity  
        stored_id = self.burst_c.get_selected_burst()
        self.assertEqual(str(stored_id), str(burst_entity.id))
            
            
    def test_portlet_tab_display(self):
        self.burst_c.index()
        portlet_id = dao.get_portlet_by_identifier("TimeSeries").id
        one_tab = [[portlet_id, "TimeSeries"] for _ in range(NUMBER_OF_PORTLETS_PER_TAB)]
        full_tabs = [one_tab for _ in range(BurstConfiguration.nr_of_tabs)]
        data = {'tab_portlets_list' : json.dumps(full_tabs)}
        result = self.burst_c.portlet_tab_display(**data)
        selected_portlets = result['portlet_tab_list']
        for entry in selected_portlets:
            self.assertEqual(entry.id, portlet_id)
        
            
            
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(BurstContollerTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)
    
    