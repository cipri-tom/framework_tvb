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
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""

import unittest
import cherrypy
from tvb_test.datatypes.datatypes_factory import DatatypesFactory
from tvb_test.core.base_testcase import TransactionalTestCase
from tvb.adapters.visualizers.pse_discrete import DiscretePSEAdapter
from tvb.adapters.visualizers.pse_isocline import IsoclinePSEAdapter



class PSETest(TransactionalTestCase):
    """
    Unit-tests for BrainViewer.
    """


    def setUp(self):
        self.datatypeFactory = DatatypesFactory()
        self.group = self.datatypeFactory.create_datatype_group()


    def test_launch_discrete(self):
        """
        Check that all required keys are present in output from PSE Discrete Adapter launch.
        """
        viewer = DiscretePSEAdapter()
        result = viewer.launch(self.group)
        expected_keys = ['status', 'size_metric', 'series_array', 'min_shape_size_weight', 'min_color',
                         'max_shape_size_weight', 'max_color', 'mainContent', 'labels_y', 'labels_x',
                         'isAdapter', 'has_started_ops', 'group_id', 'datatypes_dict', 'data', 'color_metric']
        for key in expected_keys:
            self.assertTrue(key in result)


    def test_launch_isocline(self):
        """
        Check that all required keys are present in output from PSE Discrete Adapter launch.
        """
        viewer = IsoclinePSEAdapter()
        try:
            viewer.launch(self.group)
            self.fail("Expected redirect for a group 1D only!")
        except cherrypy.HTTPRedirect:
            pass



def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(PSETest))
    return test_suite



if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)