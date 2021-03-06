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
"""
import copy
import json
import numpy

import unittest
import cherrypy
from time import sleep
from tvb.config import SIMULATOR_MODULE, SIMULATOR_CLASS
import tvb.interfaces.web.controllers.basecontroller as b_c
from tvb.interfaces.web.controllers.burst.burstcontroller import BurstController
from tvb.core.entities import model
from tvb.datatypes.connectivity import Connectivity
from tvb.core.entities.file.fileshelper import FilesHelper
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.core.entities.transient.structure_entities import DataTypeMetaData
from tvb.core.services.burstservice import BurstService
from tvb.core.services.operationservice import OperationService
from tvb.core.services.flowservice import FlowService
from tvb.core.entities.storage import dao
from tvb.core.entities.model.model_burst import BurstConfiguration, NUMBER_OF_PORTLETS_PER_TAB
from tvb.core.entities.transient.burst_configuration_entities import AdapterConfiguration
from tvb_test.adapters.storeadapter import StoreAdapter
from tvb_test.interfaces.web.controllers.basecontroller_test import BaseControllersTest
from tvb_test.adapters.simulator.simulator_adapter_test import SIMULATOR_PARAMETERS



class BurstContollerTest(BaseControllersTest):
    """ Unit tests for burstcontroller """


    def setUp(self):
        """
        Sets up the environment for testing;
        creates a `BurstController`
        """
        BaseControllersTest.init(self)
        self.burst_c = BurstController()


    def tearDown(self):
        """
        Cleans up the environment after testing is done;
        resets the database
        """
        BaseControllersTest.cleanup(self)
        self.reset_database()


    def test_index(self):
        """
        Test that index returns a dict with all required keys. Also check
        that the default portlets are populated, with only the first being
        the TimeSeries portlet and the rest are empty.
        """
        result_dict = self.burst_c.index()
        self.assertTrue('burst_list' in result_dict and result_dict['burst_list'] == [])
        self.assertTrue('available_metrics' in result_dict and isinstance(result_dict['available_metrics'], list))
        self.assertTrue('portletList' in result_dict and isinstance(result_dict['portletList'], list))
        self.assertEqual(result_dict[b_c.KEY_SECTION], "burst")
        self.assertTrue('burstConfig' in result_dict and isinstance(result_dict['burstConfig'], BurstConfiguration))
        portlets = json.loads(result_dict['selectedPortlets'])
        portlet_id = dao.get_portlet_by_identifier("TimeSeries").id
        for tab_idx, tab in enumerate(portlets):
            for index_in_tab, value in enumerate(tab):
                if tab_idx == 0 and index_in_tab == 0:
                    self.assertEqual(value, [portlet_id, "TimeSeries"])
                else:
                    self.assertEqual(value, [-1, "None"])
        self.assertTrue(result_dict['draw_hidden_ranges'])


    def test_load_burst_history(self):
        """
        Create two burst, load the burst and check that we get back
        the same stored bursts.
        """
        self._store_burst(self.test_project.id, 'started', {'test': 'test'}, 'burst1')
        burst = self._store_burst(self.test_project.id, 'started', {'test': 'test'}, 'burst2')
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst
        result_dict = self.burst_c.load_burst_history()
        burst_history = result_dict['burst_list']
        self.assertEqual(len(burst_history), 2)
        for burst in burst_history:
            self.assertTrue(burst.name in ('burst1', 'burst2'))


    def test_get_selected_burst(self):
        """
        Create burst, add it to session, then check that get_selected_burst
        return the same burst. Also check that for an unstored entity we get
        back 'None'
        """
        burst_entity = BurstConfiguration(self.test_project.id, 'started', {}, 'burst1')
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst_entity
        stored_id = self.burst_c.get_selected_burst()
        self.assertEqual(stored_id, 'None')
        burst_entity = dao.store_entity(burst_entity)
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst_entity
        stored_id = self.burst_c.get_selected_burst()
        self.assertEqual(str(stored_id), str(burst_entity.id))


    def test_get_portlet_configurable_interface(self):
        """
        Look up that an AdapterConfiguration is returned for the default
        portlet configuration, if we look at index (0, 0) where TimeSeries portlet
        should be default.
        """
        self.burst_c.index()
        result = self.burst_c.get_portlet_configurable_interface(0)
        self.assertTrue(b_c.KEY_PARAMETERS_CONFIG in result)
        self.assertFalse(result[b_c.KEY_PARAMETERS_CONFIG])
        adapter_config = result['adapters_list']
        # Default TimeSeries portlet should be available, so we expect
        # adapter_config to be a list of AdapterConfiguration with one element
        self.assertEqual(len(adapter_config), 1)
        self.assertTrue(isinstance(adapter_config[0], AdapterConfiguration))


    def test_portlet_tab_display(self):
        """
        Update the default portlet configuration, by storing a TimeSeries
        portlet for all postions. Then check that we get the same configuration.
        """
        self.burst_c.index()
        portlet_id = dao.get_portlet_by_identifier("TimeSeries").id
        one_tab = [[portlet_id, "TimeSeries"] for _ in range(NUMBER_OF_PORTLETS_PER_TAB)]
        full_tabs = [one_tab for _ in range(BurstConfiguration.nr_of_tabs)]
        data = {'tab_portlets_list': json.dumps(full_tabs)}
        result = self.burst_c.portlet_tab_display(**data)
        selected_portlets = result['portlet_tab_list']
        for entry in selected_portlets:
            self.assertEqual(entry.id, portlet_id)


    def test_get_configured_portlets_no_session(self):
        """
        Test that if we have no burst stored in session, an empty
        portlet list is reduced.
        """
        result = self.burst_c.get_configured_portlets()
        self.assertTrue('portlet_tab_list' in result)
        self.assertTrue(result['portlet_tab_list'] == [])


    def test_get_configured_portlets_default(self):
        """
        Check that the default configuration holds one portlet
        and it's identifier is 'TimeSeries'.
        """
        self.burst_c.index()
        result = self.burst_c.get_configured_portlets()
        self.assertTrue('portlet_tab_list' in result)
        portlets_list = result['portlet_tab_list']
        self.assertEqual(len(portlets_list), 1)
        self.assertTrue(portlets_list[0].algorithm_identifier == 'TimeSeries')


    def test_get_portlet_session_configuration(self):
        """
        Test that the default portlet session sonciguration is generated
        as expected, with a default TimeSeries portlet and rest empty.
        """
        self.burst_c.index()
        result = json.loads(self.burst_c.get_portlet_session_configuration())
        portlet_id = dao.get_portlet_by_identifier("TimeSeries").id
        for tab_idx, tab in enumerate(result):
            for index_in_tab, value in enumerate(tab):
                if tab_idx == 0 and index_in_tab == 0:
                    self.assertEqual(value, [portlet_id, "TimeSeries"])
                else:
                    self.assertEqual(value, [-1, "None"])


    def test_save_parameters_no_relaunch(self):
        """
        Test the save parameters for the default TimeSeries portlet and
        pass an empty dictionary as the 'new' data. In this case a relaunch
        should not be required.
        """
        self.burst_c.index()
        self.assertEqual('noRelaunch', self.burst_c.save_parameters(0))


    def test_rename_burst(self):
        """
        Create and store a burst, then rename it and check that it
        works as expected.
        """
        burst = self._store_burst(self.test_project.id, 'started', {'test': 'test'}, 'burst1')
        self.burst_c.rename_burst(burst.id, "test_new_burst_name")
        renamed_burst = dao.get_burst_by_id(burst.id)
        self.assertEqual(renamed_burst.name, "test_new_burst_name")


    def test_launch_burst(self):
        """
        Launch a burst and check that it finishes correctly and before timeout (100)
        """
        self.burst_c.index()
        _, connectivity = self._burst_create_connectivity()
        launch_params = copy.deepcopy(SIMULATOR_PARAMETERS)
        launch_params['connectivity'] = dao.get_datatype_by_id(connectivity.id).gid
        launch_params['simulation_length'] = '100'
        burst_id, _ = json.loads(self.burst_c.launch_burst("new", "test_burst", **launch_params))
        waited = 1
        timeout = 100
        burst_config = dao.get_burst_by_id(burst_id)
        while burst_config.status == BurstConfiguration.BURST_RUNNING and waited <= timeout:
            sleep(1)
            waited += 1
            burst_config = dao.get_burst_by_id(burst_config.id)
        if waited > timeout:
            self.fail("Timed out waiting for simulations to finish.")
        if burst_config.status != BurstConfiguration.BURST_FINISHED:
            BurstService().stop_burst(burst_config)
            self.fail("Burst should have finished succesfully.")


    def test_load_burst(self):
        """
        Test loading and burst and checking you get expected dictionary.
        """
        self.burst_c.index()
        burst = self._store_burst(self.test_project.id, 'started', {'test': 'test'}, 'burst1')
        result = json.loads(self.burst_c.load_burst(burst.id))
        self.assertEqual(result["status"], "started")
        self.assertEqual(result['group_gid'], None)
        self.assertEqual(result['selected_tab'], 0)


    def test_load_burst_removed(self):
        """
        Add burst to session, then remove burst from database. Try to load
        burst and check that it will raise exception and remove it from session.
        """
        burst = self._store_burst(self.test_project.id, 'started', {'test': 'test'}, 'burst1')
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst
        burst_id = burst.id
        BurstService().remove_burst(burst_id)
        self.assertRaises(Exception, self.burst_c.load_burst, burst_id)
        self.assertTrue(b_c.KEY_BURST_CONFIG not in cherrypy.session)


    def test_remove_burst_not_session(self):
        """
        Test removing a burst that is not the one currently stored in 
        session. SHould just remove and return a 'done' string.
        """
        burst = self._store_burst(self.test_project.id, 'finished', {'test': 'test'}, 'burst1')
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst
        another_burst = self._store_burst(self.test_project.id, 'finished', {'test': 'test'}, 'burst1')
        result = self.burst_c.remove_burst_entity(another_burst.id)
        self.assertEqual(result, 'done')


    def test_remove_burst_in_session(self):
        """
        Test that if we remove the burst that is the current one from the
        session, we get a 'reset-new' string as result.
        """
        burst = self._store_burst(self.test_project.id, 'finished', {'test': 'test'}, 'burst1')
        cherrypy.session[b_c.KEY_BURST_CONFIG] = burst
        result = self.burst_c.remove_burst_entity(burst.id)
        self.assertEqual(result, 'reset-new')


    def _store_burst(self, proj_id, status, sim_config, name):
        """
        Create and store a burst entity, for the project given project_id, having the
        given status and simulator parames config, under the given name.
        """
        burst = BurstConfiguration(proj_id, status, sim_config, name)
        burst.prepare_before_save()
        return dao.store_entity(burst)


    def _burst_create_connectivity(self):
        """
        Create a connectivity that will be used in "non-dummy" burst launches (with the actual simulator).
        TODO: This is duplicate code from burstservice_test. Should go into the 'generic' DataType factory
        once that is done.
        """
        meta = {DataTypeMetaData.KEY_SUBJECT: "John Doe", DataTypeMetaData.KEY_STATE: "RAW"}
        algorithm, algo_group = FlowService().get_algorithm_by_module_and_class(SIMULATOR_MODULE, SIMULATOR_CLASS)
        self.operation = model.Operation(self.test_user.id, self.test_project.id, algo_group.id,
                                         json.dumps(''),
                                         meta=json.dumps(meta), status=model.STATUS_STARTED,
                                         method_name=ABCAdapter.LAUNCH_METHOD)
        self.operation = dao.store_entity(self.operation)
        storage_path = FilesHelper().get_project_folder(self.test_project, str(self.operation.id))
        connectivity = Connectivity(storage_path=storage_path)
        connectivity.weights = numpy.ones((74, 74))
        connectivity.centres = numpy.ones((74, 3))
        adapter_instance = StoreAdapter([connectivity])
        OperationService().initiate_prelaunch(self.operation, adapter_instance, {})
        return algorithm.id, connectivity



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
    
    