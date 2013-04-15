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
import unittest
from tvb.core.entities.file.fileshelper import FilesHelper
from tvb_test.datatypes.datatypes_factory import DatatypesFactory
from tvb_test.core.base_testcase import TransactionalTestCase
from tvb.adapters.visualizers.covariance import CovarianceVisualizer
from tvb.core.services.flowservice import FlowService
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.datatypes.surfaces import CorticalSurface
from tvb.datatypes.connectivity import Connectivity
from tvb_test.core.test_factory import TestFactory


class CovarianceViewerTest(TransactionalTestCase):
    """
    Unit-tests for BrainViewer.
    """
    def setUp(self):
        self.datatypeFactory = DatatypesFactory()
        self.test_project = self.datatypeFactory.get_project()
        self.test_user = self.datatypeFactory.get_user()
        
        TestFactory.import_cff(test_user = self.test_user, test_project=self.test_project)
        self.connectivity = self._get_entity(Connectivity())
        self.assertTrue(self.connectivity is not None)
        self.surface = self._get_entity(CorticalSurface())
        self.assertTrue(self.surface is not None)
                
    def tearDown(self):
        """
        Clean-up tests data
        """
        FilesHelper().remove_project_structure(self.test_project.name)
    
    def _get_entity(self, expected_data, filters = None):
        data_types = FlowService().get_available_datatypes(self.test_project.id,
                                expected_data.module + "." + expected_data.type, filters)
        self.assertEqual(1, len(data_types), "Project should contain only one data type:" + str(expected_data.type))
        entity = ABCAdapter.load_entity_by_gid(data_types[0][2])
        self.assertTrue(entity is not None, "Instance should not be none")
        return entity
    
    
    def test_launch(self):
        """
        Check that all required keys are present in output from BrainViewer launch.
        """
        time_series = self.datatypeFactory.create_timeseries(self.connectivity)
        covariance = self.datatypeFactory.create_covaraince(time_series)
        viewer = CovarianceVisualizer()
        result = viewer.launch(covariance)
        expected_keys = ['matrix_strides', 'matrix_shape', 'matrix_data', 'mainContent', 'isAdapter',
                         'figure_exportable']
        for key in expected_keys:
            self.assertTrue(key in result)
    
    
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(CovarianceViewerTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)