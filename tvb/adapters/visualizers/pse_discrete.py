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

from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.entities.transient.pse import ContextDiscretePSE
from tvb.core.adapters.abcdisplayer import ABCDisplayer
from tvb.datatypes.mapped_values import DatatypeMeasure
from tvb.basic.filters.chain import FilterChain


MAX_NUMBER_OF_POINT_TO_SUPPORT = 200



class DiscretePSEAdapter(ABCDisplayer):
    """
    Visualization adapter for Parameter Space Exploration.
    Will be used as a generic visualizer, accessible when input entity is DataTypeGroup.
    Will also be used in Burst as a supplementary navigation layer.
    """
    _ui_name = "Discrete Parameter Space Exploration"
    _ui_subsection = "pse"


    def get_input_tree(self):
        """
        Take as Input a Connectivity Object.
        """
        return [{'name': 'datatype_group',
                 'label': 'Datatype Group',
                 'type': model.DataTypeGroup,
                 'required': True,
                 'conditions': FilterChain(fields=[FilterChain.datatype + ".no_of_ranges",
                                                   FilterChain.datatype + ".count_results"],
                                           operations=["<=", "<="], values=[2, MAX_NUMBER_OF_POINT_TO_SUPPORT])}]


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
        pse_context = self.prepare_parameters(datatype_group.gid, color_metric, size_metric)
        pse_context.prepare_individual_jsons()

        return self.build_display_result('pse_discrete/view', pse_context)


    @staticmethod
    def prepare_parameters(datatype_group_gid, color_metric=None, size_metric=None):
        """
        We suppose that there are max 2 ranges and from each operation results exactly one dataType.
        """
        datatype_group = dao.get_datatype_group_by_gid(datatype_group_gid)
        if datatype_group is None:
            raise Exception("Selected DataTypeGroup is no longer present in the database. "
                            "It might have been remove or the specified id is not the correct one.")

        operation_group = dao.get_operationgroup_by_id(datatype_group.fk_operation_group)
        _, range1_name, range1_labels = operation_group.load_range_numbers(operation_group.range1)
        has_range2, range2_name, range2_labels = operation_group.load_range_numbers(operation_group.range2)

        pse_context = ContextDiscretePSE(datatype_group_gid, range1_labels, range2_labels, color_metric, size_metric)

        final_dict = dict()
        operations = dao.get_operations_in_group(operation_group.id)
        for operation_ in operations:
            if operation_.status == model.STATUS_STARTED:
                pse_context.has_started_ops = True
            range_values = eval(operation_.range_values)
            key_1 = range_values[range1_name]
            key_2 = "-"
            if has_range2 is not None:
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

