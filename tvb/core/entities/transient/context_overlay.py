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
Entities to be used with an overlay on Operation or DataType, are defined here.

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

import numpy
from tvb.basic.config.settings import EnhancedDictionary
from tvb.core.entities import model
from tvb.core.utils import date2string


class CommonDetails(EnhancedDictionary):
    """
    Enhanced dictionary holding details about an entity.
    It also contains metadata on how this details will be displayed in UI (disabled/readonly/hidden input field).
    """
    
    CODE_GID = "gid"
    CODE_OPERATION_TAG = "operation_label"
    CODE_OPERATION_GROUP_ID = 'operation_group_id'
    CODE_OPERATION_GROUP_NAME = 'operation_group_name'
    
    def __init__(self):
        
        super(CommonDetails, self).__init__()
        self.metadata = dict()
        self.scientific_details = dict()
        
        self.gid = None
        self.metadata[self.CODE_GID] = {"name": "Unique Global Identifier", "readonly": "True"}
        
        self.author = None
        self.metadata['author'] = {"name": "Author", "disabled": "True"}
        
        self.operation_type = None
        self.metadata['operation_type'] = {"name": "Operation Algorithm", "disabled": "True"}
        
        self.operation_label = None
        self.metadata[self.CODE_OPERATION_TAG] = {"name": "Operation Label"}
        
        self.count = 1
        self.metadata['count'] = {"name": "No. of entities in group", "disabled": "True"}
        
        self.operation_group_id = None
        self.metadata[self.CODE_OPERATION_GROUP_ID] = {"name": "groupId", "hidden": "True"}
        
        self.operation_group_name = None
        self.metadata[self.CODE_OPERATION_GROUP_NAME] = {"name": "operationGroupName", "hidden":"True"}
        
        self.burst_name = None
        self.metadata['burst_name'] = {"name": "Simulation", "disabled": "True"}
        
        
    def add_scientific_fields(self, extra_fields_dict):
        """
        :param extra_fields_dict a dictionary of fields to be added in a distinct category.
        """
        for key, value in extra_fields_dict.iteritems():
            if (value is not None and isinstance(value, numpy.ndarray)):
                # Make sure arrays are displayed in a compatible form: [1, 2, 3]
                value = str(value.tolist())
            elif (value is not None and isinstance(value, list) and len(value) > 0 and isinstance(value[0], unicode)):
                value = [str(v) for v in value]
            self.scientific_details[key] = {"name": key, "value": str(value), "disabled": "True"}


    @property
    def meta_attributes_list(self):
        """
        A list with all attributes for a DataType which are expected to be submitted from UI.
        """
        result = self.keys()
        result.remove('metadata')
        result.remove('scientific_details')
        return result
    
    
    @staticmethod
    def compute_operation_name(category_name, group_name, algorithm_name):
        """
        Compute Operation display name, based on Operation Category, AlgoGroup and Algorithm.
        """
        display_name = ''
        if category_name:
            display_name = category_name
        if group_name:
            display_name = display_name + "->" + group_name
        if algorithm_name and (group_name is None or group_name.lstrip().rstrip() != algorithm_name.lstrip().rstrip()):
            display_name = display_name + "->" + algorithm_name
        return display_name
    

    def get_ui_fields(self):
        """
        :returns: list of dictionaries to be used for UI display.
        Each entry in the list will be displayed as a UI group of fields.
        """
        framework_metadata = self.metadata
        for key in self.meta_attributes_list:
            framework_metadata[key]['value'] = getattr(self, key)
        if len(self.scientific_details) > 0:
            return [self.scientific_details, framework_metadata]    
        return [framework_metadata]
        


class OperationOverlayDetails(CommonDetails):
    """
    Entity used for displaying in an overlay details about an operation.
    """


    def __init__(self, operation, username, count_inputs, count_results, burst, no_of_op_in_group):
        super(OperationOverlayDetails, self).__init__()
        
        self.operation_id = operation.id
        self.metadata['operation_id'] = {"name": "Entity id", "disabled": "True"}
        
        self.operation_status = operation.status
        self.metadata['operation_status'] = {"name": "Status", "disabled": "True"}
        
        self.start_date = date2string(operation.start_date)
        self.metadata['start_date'] = {"name": "Start date", "disabled": "True"}
        
        self.end_date = "None" if operation.completion_date is None else date2string(operation.completion_date)
        self.metadata['end_date'] = {"name": "End date", "disabled":"True"}
        
        self.result_datatypes = count_results
        self.metadata['result_datatypes'] = {"name": "No. of resulted DataTypes", "disabled": "True"}
        
        self.input_datatypes = count_inputs
        self.metadata['input_datatypes'] =  {"name": "No. of input DataTypes", "disabled": "True"}
        
        ### Now set/update generic fields
        self.gid = operation.gid
        self.author = username
        self.count = no_of_op_in_group
        self.burst_name = burst.name if burst is not None else ""
        self.operation_type = self.compute_operation_name(operation.algorithm.algo_group.group_category.displayname,
                                                operation.algorithm.algo_group.displayname, operation.algorithm.name)
        
        group_id = operation.operation_group.id if operation.operation_group is not None else None
        self.operation_group_id = group_id
        
        self.operation_label = (operation.operation_group.name if operation.operation_group is not None 
                                else operation.user_group)
        self.metadata[self.CODE_OPERATION_TAG]["disabled"] = 'True'
        
        group_value = operation.operation_group.name if operation.operation_group is not None else None
        self.operation_group_name = group_value
        self.metadata[self.CODE_OPERATION_GROUP_NAME]["disabled"] = 'True'
        


class DataTypeOverlayDetails(CommonDetails):
    """
    Entity used for displaying in an overlay details about a DataType.
    """
    
    DATA_SUBJECT = "subject"
    DATA_STATE = "data_state"
    DATA_TITLE = "datatype_title"
    DATA_TAG_1 = "datatype_tag_1"
    DATA_TAG_2 = "datatype_tag_2"
    DATA_TAG_3 = "datatype_tag_3"
    DATA_TAG_4 = "datatype_tag_4"
    DATA_TAG_5 = "datatype_tag_5"
    
    
    def __init__(self):
        
        super(DataTypeOverlayDetails, self).__init__()
        
        self.data_state = None
        self.metadata[self.DATA_STATE] = {"name": "State"}
        
        self.datatype_title = None
        self.metadata[self.DATA_TITLE] = {"name": "Title", "disabled": "True"}
        
        self.subject = None
        self.metadata[self.DATA_SUBJECT] = {"name": "Subject"}
        
        self.data_type = None
        self.metadata['data_type'] = {"name": "Data Type", "disabled": "True"}
        
        self.data_type_id = None
        self.metadata['data_type_id'] = {"name": "Entity id", "disabled": "True"}
        
        self.create_date = None
        self.metadata['create_date'] = {"name": "Creation Date", "disabled": "True"}
        
        self.datatype_tag_1 = None
        self.metadata[self.DATA_TAG_1] = {"name": "DataType Tag 1"}
        
        self.datatype_tag_2 = None
        self.metadata[self.DATA_TAG_2] = {"name": "DataType Tag 2"}
        
        self.datatype_tag_3 = None
        self.metadata[self.DATA_TAG_3] = {"name": "DataType Tag 3"}
        
        self.datatype_tag_4 = None
        self.metadata[self.DATA_TAG_4] = {"name": "DataType Tag 4"}
        
        self.datatype_tag_5 = None
        self.metadata[self.DATA_TAG_5] = {"name": "DataType Tag 5"}
        
        self.datatype_size = None
        self.metadata['datatype_size'] = {"name": "Size on Disk (KB)", "disabled": "True"}
    
    
    
    def fill_from_datatype(self, datatype_result, parent_burst):
        """
        Fill current dictionary with information from a loaded DB DataType.
        :param datatype_result DB loaded DataType
        :param parent_burst Burst entity in which current dataType was generated
        """
        
        self.gid = datatype_result.gid
        self.data_type_id  = datatype_result.id
        self.data_state = datatype_result.state
        self.datatype_title = datatype_result.display_name
        self.subject = datatype_result.subject
        self.data_type = datatype_result.type
        self.datatype_tag_1 = datatype_result.user_tag_1
        self.datatype_tag_2 = datatype_result.user_tag_2
        self.datatype_tag_3 = datatype_result.user_tag_3
        self.datatype_tag_4 = datatype_result.user_tag_4
        self.datatype_tag_5 = datatype_result.user_tag_5
        self.datatype_size = datatype_result.disk_size
        self.author = datatype_result.parent_operation.user.username
        
        parent_algorithm = datatype_result.parent_operation.algorithm
        operation_name = self.compute_operation_name(parent_algorithm.algo_group.group_category.displayname,
                                                     parent_algorithm.algo_group.displayname, parent_algorithm.name)
        self.operation_type = operation_name
        
        create_date_str = ''
        if datatype_result.parent_operation.completion_date is not None:
            create_date_str = date2string(datatype_result.parent_operation.completion_date)
        self.create_date = create_date_str
        
        if parent_burst is not None:
            self.burst_name = parent_burst.name
        else:
            self.burst_name = ''
            
        ### Populate Group attributes
        if isinstance(datatype_result, model.DataTypeGroup):
            self.count = datatype_result.count_results
            self.operation_group_name  = datatype_result.parent_operation.operation_group.name
            self.operation_label = datatype_result.parent_operation.operation_group.name
            self.operation_group_id = datatype_result.parent_operation.operation_group.id
        else:
            self.operation_label = datatype_result.parent_operation.user_group
            
        ### Populate Scientific attributes
        if hasattr(datatype_result, 'summary_info') and datatype_result.summary_info is not None:
            self.add_scientific_fields(datatype_result.summary_info)
    
    
    
    