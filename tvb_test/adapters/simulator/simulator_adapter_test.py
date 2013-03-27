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
"""

import json
import unittest
import numpy
from copy import copy
from tvb.config import SIMULATOR_CLASS, SIMULATOR_MODULE
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.entities.file.fileshelper import FilesHelper
from tvb.core.services.projectservice import ProjectService, initialize_storage
from tvb.core.services.flowservice import FlowService
from tvb.core.services.operationservice import OperationService
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.time_series import TimeSeriesRegion
from tvb_test.adapters.storeadapter import StoreAdapter
from tvb.core.entities.transient.structure_entities import DataTypeMetaData
from tvb_test.core.base_testcase import TransactionalTestCase

# Default values for simulator's input. These values can be replace with adapter.get_flatten_interface...
SIMULATOR_PARAMETERS = {
        "model": "Generic2dOscillator",
        "model_parameters_option_Generic2dOscillator_state_variable_range_parameters_parameters_V": "[-2.0  4.0]",
        "model_parameters_option_Generic2dOscillator_state_variable_range_parameters_parameters_W": "[-6.0  6.0]",
        "model_parameters_option_Generic2dOscillator_tau": "[1.0]",  
        "model_parameters_option_Generic2dOscillator_I": "[0.0]",
        "model_parameters_option_Generic2dOscillator_a": "[-2.0]",
        "model_parameters_option_Generic2dOscillator_b": "[-10.0]", 
        "model_parameters_option_Generic2dOscillator_c": "[0.0]", 
        "model_parameters_option_Generic2dOscillator_d": "[0.1]", 
        "model_parameters_option_Generic2dOscillator_e": "[3.0]",  
        "model_parameters_option_Generic2dOscillator_f": "[1.0]",
        "model_parameters_option_Generic2dOscillator_alpha": "[1.0]", 
        "model_parameters_option_Generic2dOscillator_beta": "[1.0]", 
        "model_parameters_option_Generic2dOscillator_noise": "Noise", 
        "model_parameters_option_Generic2dOscillator_noise_parameters_option_Noise_nsig": "[1.0]", 
        "model_parameters_option_Generic2dOscillator_noise_parameters_option_Noise_ntau": "0.0", 
        "model_parameters_option_Generic2dOscillator_noise_parameters_option_Noise_random_stream": "RandomStream", 
        "model_parameters_option_Generic2dOscillator_noise_parameters_option_Noise_random_stream_parameters_option_RandomStream_init_seed": "42", 
        "connectivity": "7eadbaeb-afdc-11e1-ab21-68a86d1bd4fa", 
        "surface": "", 
        "stimulus": "", 
        "initial_conditions": "",
        "currentAlgoId": "10",
        "first_range": "0",   
        "second_range": "0",
        "integrator": "HeunDeterministic",
        "integrator_parameters_option_HeunDeterministic_dt": "0.015625", 
        "monitors": "TemporalAverage",
        "monitors_parameters_option_TemporalAverage_period": "0.9765625", 
        "coupling": "Linear",
        "coupling_parameters_option_Linear_a": "[0.00390625]",
        "coupling_parameters_option_Linear_b": "[0.0]",
        "simulation_length": "32"}
    
    
class SimulatorAdapterTest(TransactionalTestCase):
    """
    Basic testing that SImulator is still working from UI.
    """
    CONNECTIVITY_NODES = 74
    
    def setUp(self):
        """
        Reset the database before each test.
        """
        initialize_storage()
        user = model.User("test_user", "test_pass", "test_mail@tvb.org", True, "user")
        self.test_user = dao.store_entity(user) 
        data = dict(name='test_proj', description='desc', users=[])
        self.test_project = ProjectService().store_project(self.test_user, True, None, **data)
        meta = {DataTypeMetaData.KEY_SUBJECT : "John Doe", 
                DataTypeMetaData.KEY_STATE : "RAW"}
        algo_group = dao.find_group(SIMULATOR_MODULE, SIMULATOR_CLASS)
        self.simulator_adapter = FlowService().build_adapter_instance(algo_group)
                                            
        self.operation = model.Operation(self.test_user.id, self.test_project.id, algo_group.id, 
                                         json.dumps(SIMULATOR_PARAMETERS), 
                                         meta = json.dumps(meta), status="STARTED",
                                         method_name = ABCAdapter.LAUNCH_METHOD)
        self.operation = dao.store_entity(self.operation)
        
        SIMULATOR_PARAMETERS['connectivity'] = self._create_connectivity(self.CONNECTIVITY_NODES)
     
     
    def _create_connectivity(self, nodes_number):
        """
        Create a connectivity entity and return its GID
        """
        storage_path = FilesHelper().get_project_folder(self.test_project, str(self.operation.id))
        connectivity = Connectivity(storage_path=storage_path)
        connectivity.weights = numpy.ones((nodes_number, nodes_number))
        connectivity.centres = numpy.ones((nodes_number, 3))
        adapter_instance = StoreAdapter([connectivity])
        OperationService().initiate_prelaunch(self.operation, adapter_instance, {})
        
        return dao.get_datatype_by_id(connectivity.id).gid
            
            
    def test_happy_flow_launch(self):
        """
        Test that launching a simulation from UI works.
        """
        OperationService().initiate_prelaunch(self.operation, self.simulator_adapter, {}, **SIMULATOR_PARAMETERS)
        sim_result = dao.get_generic_entity(TimeSeriesRegion, 'TimeSeriesRegion', 'type')[0]
        self.assertEquals(sim_result.read_data_shape(), (32, 1, self.CONNECTIVITY_NODES, 1))
    
    
    def _estimate_hdd(self, new_parameters_dict):
        """ Private method, to return HDD estimation for a given set of input parameters"""
        filtered_params = self.simulator_adapter.prepare_ui_inputs(new_parameters_dict)
        self.simulator_adapter.configure(**filtered_params)
        return self.simulator_adapter.get_required_disk_size(**filtered_params)   


    def test_estimate_hdd(self):
        """
        Test that occupied HDD estimation for simulation results considers simulation length.
        """
        factor = 5
        simulation_parameters = copy(SIMULATOR_PARAMETERS)
        ## Estimate HDD with default simulation parameters
        estimate1 = self._estimate_hdd(simulation_parameters)
        self.assertTrue(estimate1 > 1)
        
        ## Change simulation length and monitor period, we expect a direct proportial increase in estimated HDD
        simulation_parameters['simulation_length'] = float(simulation_parameters['simulation_length']) * factor
        period = float(simulation_parameters['monitors_parameters_option_TemporalAverage_period'])
        simulation_parameters['monitors_parameters_option_TemporalAverage_period'] = period / factor
        estimate2 = self._estimate_hdd(simulation_parameters)
        self.assertEqual(estimate1,  estimate2 / factor / factor)
        
        ## Change number of nodes in connectivity. Expect HDD estimation increase.
        simulation_parameters['connectivity'] = self._create_connectivity(self.CONNECTIVITY_NODES * factor)
        estimate3 = self._estimate_hdd(simulation_parameters)
        self.assertEqual(estimate2, estimate3 / factor)
        
        
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(SimulatorAdapterTest))
    return test_suite

if __name__ == "__main__":
    #So you can run tests from this package individually.
    unittest.main() 
    
    
    
    
    