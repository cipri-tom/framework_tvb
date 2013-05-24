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
#   Frontiers in Neuroinformatics (in press)
#
#

"""
.. moduleauthor:: bogdan.neacsa <bogdan.neacsa@codemart.ro>
"""

import os
import unittest
import tvb_test
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.entities.storage import dao
from tvb.core.entities.file.fileshelper import FilesHelper
from tvb.core.entities.transient.structure_entities import DataTypeMetaData
from tvb.core.entities.transient.burst_configuration_entities import WorkflowStepConfiguration as wf_cfg
from tvb.core.services.flowservice import FlowService
from tvb.core.services.workflowservice import WorkflowService
from tvb.core.services.burstservice import BurstService
from tvb.core.services.operationservice import OperationService
from tvb_test.datatypes.datatype1 import Datatype1
from tvb_test.datatypes import datatypes_factory
from tvb_test.core.base_testcase import TransactionalTestCase
from tvb_test.core.test_factory import TestFactory



class WorkflowTest(TransactionalTestCase):
    """
    Test that workflow conversion methods are valid.
    """


    def setUp(self):
    #        self.clean_database()
        self.test_user = TestFactory.create_user()
        self.test_project = TestFactory.create_project(self.test_user)
        self.old_config_file = cfg.CURRENT_DIR
        cfg.CURRENT_DIR = os.path.dirname(tvb_test.__file__)
        self.workflow_service = WorkflowService()
        self.burst_service = BurstService()
        self.operation_service = OperationService()
        self.flow_service = FlowService()


    def tearDown(self):
        """
        Remove project folders and clean up database.
        """
        FilesHelper().remove_project_structure(self.test_project.name)
        self.delete_project_folders()
        cfg.CURRENT_DIR = self.old_config_file


    def __create_complex_workflow(self, workflow_step_list):
        """
        Creates a burst with a complex workflow with a given list of workflow steps.
        @param workflow_step_list: a lsit of workflow steps that will be used in the
            creation of a new workflow for a new burst
        """
        burst_config = TestFactory.store_burst(self.test_project.id)

        stored_dt = datatypes_factory.DatatypesFactory()._store_datatype(Datatype1())

        first_step_algorithm = self.flow_service.get_algorithm_by_module_and_class("tvb_test.adapters.testadapter1",
                                                                                   "TestAdapterDatatypeInput")[0]
        metadata = {DataTypeMetaData.KEY_BURST: burst_config.id}
        kwargs = {"test_dt_input": stored_dt.gid, 'test_non_dt_input': '0'}
        operations, group = self.operation_service.prepare_operations(self.test_user.id, self.test_project.id,
                                                                      first_step_algorithm,
                                                                      first_step_algorithm.algo_group.group_category,
                                                                      metadata, **kwargs)

        workflows = self.workflow_service.create_and_store_workflow(project_id=self.test_project.id,
                                                                    burst_id=burst_config.id,
                                                                    simulator_index=0,
                                                                    simulator_id=first_step_algorithm.id,
                                                                    operations=operations)
        self.operation_service.prepare_operations_for_workflowsteps(workflow_step_list, workflows, self.test_user.id,
                                                                    burst_config.id, self.test_project.id, group,
                                                                    operations)
        #fire the first op
        if len(operations) > 0:
            self.operation_service.launch_operation(operations[0].id, False)
        return burst_config.id


    def test_workflow_generation(self):
        """
        A simple test just for the fact that a workflow is created an ran, 
        no dynamic parameters are passed. In this case we create a two steps
        workflow: step1 - tvb_test.adapters.testadapter2.TestAdapter2
                  step2 - tvb_test.adapters.testadapter1.TestAdapter1
        The first adapter doesn't return anything and the second returns one
        tvb.datatypes.datatype1.Datatype1 instance. We check that the steps
        are actually ran by checking that two operations are created and that
        one dataType is stored.
        """
        workflow_step_list = [TestFactory.create_workflow_step("tvb_test.adapters.testadapter2", "TestAdapter2",
                                                               static_kwargs={"test2": 2}, step_index=1),
                              TestFactory.create_workflow_step("tvb_test.adapters.testadapter1", "TestAdapter1",
                                                               static_kwargs={"test1_val1": 1, "test1_val2": 1},
                                                               step_index=2)]
        self.__create_complex_workflow(workflow_step_list)
        stored_datatypes = dao.get_datatypes_info_for_project(self.test_project.id)
        self.assertTrue(len(stored_datatypes) == 2, "DataType from second step was not stored.")
        self.assertTrue(stored_datatypes[0][0] == 'Datatype1', "Wrong type was stored.")
        self.assertTrue(stored_datatypes[1][0] == 'Datatype1', "Wrong type was stored.")

        finished, started, error, _ = dao.get_operation_numbers(self.test_project.id)
        self.assertEqual(finished, 3, "Didnt start operations for both adapters in workflow.")
        self.assertEqual(started, 0, "Some operations from workflow didnt finish.")
        self.assertEqual(error, 0, "Some operations finished with error status.")


    def test_workflow_dynamic_params(self):
        """
        A simple test just for the fact that dynamic parameters are passed properly
        between two workflow steps: 
                  step1 - tvb_test.adapters.testadapter1.TestAdapter1
                  step2 - tvb_test.adapters.testadapter3.TestAdapter3
        The first adapter returns a tvb.datatypes.datatype1.Datatype1 instance. 
        The second adapter has this passed as a dynamic workflow parameter.
        We check that the steps are actually ran by checking that two operations 
        are created and that two dataTypes are stored.
        """
        workflow_step_list = [TestFactory.create_workflow_step("tvb_test.adapters.testadapter1", "TestAdapter1",
                                                               static_kwargs={"test1_val1": 1, "test1_val2": 1},
                                                               step_index=1),
                              TestFactory.create_workflow_step("tvb_test.adapters.testadapter3", "TestAdapter3",
                                                               dynamic_kwargs={
                                                                   "test": {wf_cfg.DATATYPE_INDEX_KEY: 0,
                                                                            wf_cfg.STEP_INDEX_KEY: 1}}, step_index=2)]

        self.__create_complex_workflow(workflow_step_list)
        stored_datatypes = dao.get_datatypes_info_for_project(self.test_project.id)
        self.assertTrue(len(stored_datatypes) == 3, "DataType from all step were not stored.")
        for result_row in stored_datatypes:
            self.assertTrue(result_row[0] in ['Datatype1', 'Datatype2'], "Wrong type was stored.")

        finished, started, error, _ = dao.get_operation_numbers(self.test_project.id)
        self.assertEqual(finished, 3, "Didn't start operations for both adapters in workflow.")
        self.assertEqual(started, 0, "Some operations from workflow didn't finish.")
        self.assertEqual(error, 0, "Some operations finished with error status.")


    def test_configuration2workflow(self):
        """
        Test that building a WorflowStep from a WorkflowStepConfiguration. Make sure all the data is 
        correctly passed. Also check that any base_wf_step is incremented to dynamic parameters step index.
        """
        workflow_step = TestFactory.create_workflow_step("tvb_test.adapters.testadapter1", "TestAdapter1",
                                                         static_kwargs={"static_param": "test"},
                                                         dynamic_kwargs={"dynamic_param": {wf_cfg.STEP_INDEX_KEY: 0,
                                                                                           wf_cfg.DATATYPE_INDEX_KEY: 0}},
                                                         step_index=1, base_step=5)
        self.assertEqual(workflow_step.step_index, 1, "Wrong step index in created workflow step.")
        self.assertEqual(workflow_step.static_param, {'static_param': 'test'}, 'Different static parameters on step.')
        self.assertEqual(workflow_step.dynamic_param, {'dynamic_param': {wf_cfg.STEP_INDEX_KEY: 5,
                                                                         wf_cfg.DATATYPE_INDEX_KEY: 0}},
                         "Dynamic parameters not saved properly, or base workflow index not added to step index.")


    def test_create_workflow(self):
        """
        Test that a workflow with all the associated workflow steps is actually created.
        """
        workflow_step_list = [TestFactory.create_workflow_step("tvb_test.adapters.testadapter2", "TestAdapter2",
                                                               static_kwargs={"test2": 2}, step_index=1),
                              TestFactory.create_workflow_step("tvb_test.adapters.testadapter1", "TestAdapter1",
                                                               static_kwargs={"test1_val1": 1, "test1_val2": 1},
                                                               step_index=2)]
        burst_id = self.__create_complex_workflow(workflow_step_list)
        workflow_entities = dao.get_workflows_for_burst(burst_id)
        self.assertTrue(len(workflow_entities) == 1, "For some reason workflow was not stored in database.")
        workflow_steps = dao.get_workflow_steps(workflow_entities[0].id)
        self.assertEqual(len(workflow_steps), len(workflow_step_list) + 1, "Wrong number of workflow steps created.")



def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(WorkflowTest))
    return test_suite



if __name__ == "__main__":
    #So you can run tests from this package individually.
    unittest.main() 
    
    
    