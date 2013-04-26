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
.. moduleauthor:: Ionel Ortelecan <ionel.ortelecan@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
"""

import json
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.entities.transient.pse import ContextPSE
from tvb.core.adapters.abcdisplayer import ABCDisplayer
from tvb.core.adapters.exceptions import LaunchException
from tvb.datatypes.mapped_values import DatatypeMeasure



class ParameterExplorationAdapter(ABCDisplayer):
    """
    Visualization adapter for Parameter Space Exploration.
    Will be used as a generic visualizer, accessible when input entity is DataTypeGroup.
    Will also be used in Burst as a supplementary navigation layer.
    """
    _ui_name = "Parameter Space Exploration"
    _ui_subsection = "pse"
    MAX_POINTS_PER_DIMENSION = 150
    
    def get_input_tree(self):
        """
        Take as Input a Connectivity Object.
        """
        return [{'name': 'datatype_group',
                 'label': 'Datatype Group',
                 'type': model.DataTypeGroup,
                 'required': True}]


    def __init__(self):
        ABCDisplayer.__init__(self)


    def get_required_memory_size(self, **kwargs):
        """
        Return the required memory to run this algorithm.
        """
        # Don't know how much memory is needed.
        return -1


    def launch(self, datatype_group, color_metric=None, size_metric=None):
        """
        Launch the visualizer.
        """
        pse_context = self.prepare_parameters(datatype_group.id, color_metric, size_metric)
        pse_context.prepare_individual_jsons()

        return self.build_display_result('parameter_exploration/view', pse_context)


    @staticmethod
    def is_compatible(datatype_group_id):
        """
        Check if Isocline adapter makes sense for this datatype group.
        """
        datatype_group = dao.get_datatype_group_by_id(datatype_group_id)
        operation_group = dao.get_operationgroup_by_id(datatype_group.fk_operation_group)
        range1, range2 = ParameterExplorationAdapter._get_range_values(operation_group)
        if len(range1[1]) < ParameterExplorationAdapter.MAX_POINTS_PER_DIMENSION and\
                (range2 is None or len(range2[1]) < ParameterExplorationAdapter.MAX_POINTS_PER_DIMENSION):
            return True
        return False


    @staticmethod
    def prepare_parameters(datatype_group_id, color_metric=None, size_metric=None):
        """
        We suppose that there are max 2 ranges and from each operation results exactly one dataType.
        """
        if not ParameterExplorationAdapter.is_compatible(datatype_group_id):
            raise LaunchException("Range values are too wide to display in discrete manner.")
        datatype_group = dao.get_datatype_group_by_id(datatype_group_id)
        if datatype_group is None:
            raise Exception("Selected DataTypeGroup is no longer present in the database. "
                            "It might have been remove or the specified id is not the correct one.")

        operation_group = dao.get_operationgroup_by_id(datatype_group.fk_operation_group)
        range1, range2 = ParameterExplorationAdapter._get_range_values(operation_group)
        
        range1_labels = range1[1]
        range1_name = range1[0]
        range2_labels = ["_"]
        range2_name = "_"
        if range2 is not None:
            range2_labels = range2[1]
            range2_name = range2[0]

        pse_context = ContextPSE(datatype_group_id, range1_labels, range2_labels, color_metric, size_metric)

        final_dict = dict()
        operations = dao.get_operations_in_group(operation_group.id)
        for operation_ in operations:
            if operation_.status == model.STATUS_STARTED:
                pse_context.has_started_ops = True
            range_values = eval(operation_.range_values)
            key_1 = range_values[range1_name]
            key_2 = "_"
            if range2 is not None:
                key_2 = range_values[range2_name]
            datatype = None
            if operation_.status == model.STATUS_FINISHED:
                datatype = dao.get_results_for_operation(operation_.id)[0]
                measures = dao.get_generic_entity(DatatypeMeasure, datatype.gid, '_analyzed_datatype')
                pse_context.prepare_metrics_datatype(measures, datatype)
            if key_1 not in final_dict:
                final_dict[key_1] = {key_2: pse_context.build_node_info(operation_, datatype)}
            else:
                final_dict[key_1][key_2] = pse_context.build_node_info(operation_, datatype)

        pse_context.fill_object(final_dict)
        ## datatypes_dict is not actually used in the drawing of the PSE and actually
        ## causes problems in case of NaN values, so just remove it before creating the json
        pse_context.datatypes_dict = {}
        return pse_context


    @staticmethod
    def _get_range_values(operation_group):
        if operation_group.range1 is None and operation_group.range2 is None:
            raise Exception("Invalid DataTypeGroup...")

        range1 = json.loads(operation_group.range1)
        range2 = operation_group.range2

        if range2 is not None:
            range2 = json.loads(range2)
        return range1, range2
    
