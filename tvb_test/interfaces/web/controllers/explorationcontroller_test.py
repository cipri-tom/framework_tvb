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
import json
import unittest
from tvb.interfaces.web.controllers.burst.explorationcontroller import ParameterExplorationController
from tvb_test.core.base_testcase import TransactionalTestCase
from tvb_test.interfaces.web.controllers.basecontroller_test import BaseControllersTest
from tvb_test.datatypes.datatypes_factory import DatatypesFactory


class ExplorationContollerTest(TransactionalTestCase, BaseControllersTest):
    """ Unit tests for burstcontroller """
    
    def setUp(self):
        BaseControllersTest.init(self)
        self.datatype_group = DatatypesFactory().create_datatype_group()
        self.param_c =  ParameterExplorationController()
    
    
    def tearDown(self):
        BaseControllersTest.cleanup(self)
            
            
    def test_draw_parameter_exploration(self):
        result = json.loads(self.param_c.draw_parameter_exploration(self.datatype_group.id, 
                                                                    None, None))
        self.assertTrue(result['available_metrics'] == [])
        self.assertEqual(result['color_metric'], None)
        self.assertEqual(result['size_metric'], None)
        # TODO: This latter checks are strictly tied to data generated
        # in the datatypes_factory. Try and move them here?
        self.assertEqual(result['labels_x'], ['a', 'b', 'c'])
        self.assertEqual(result['labels_y'], ['_'])
        self.assertEqual(len(result['data']), 3)
        for entry in result['data']:
            self.assertEqual(entry[0]['dataType'], 'Datatype2')
            for key in ['Gid', 'color_weight', 'operationId', 'tooltip']:
                self.assertTrue(key in entry[0])
            
def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(ExplorationContollerTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)