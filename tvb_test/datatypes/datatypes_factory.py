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
'''
    This module contains 
    moduleauthor:: Calin Pavel <calin.pavel@codemart.ro>
'''
import json
from datetime import datetime
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.entities.file.fileshelper import FilesHelper
from tvb.core.entities.transient.structure_entities import DataTypeMetaData
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb_test.adapters.storeadapter import StoreAdapter
from tvb.core.services.projectservice import ProjectService
from tvb.core.services.operationservice import OperationService
from tvb_test.datatypes.datatype1 import Datatype1
from tvb_test.datatypes.datatype2 import Datatype2

class DatatypesFactory():
    """
        This class provides a set of methods that helps user to create 
        different data types for testing.
        These data types will be automatically stored in DB and file system if needed.
    """
    USER_FULL_NAME = "Datatype Factory User"
    DATATYPE_STATE = "RAW_DATA"
    DATATYPE_DATA = ["test", "for", "datatypes", "factory"]
    OPERATION_GROUP_NAME = "OperationsGroup"
    
    user = None
    project = None
    operation = None
    
    def __init__(self):
        now = datetime.now()
        micro_postfix = "_%d"%(now.microsecond) 
        
        # Here create all structures needed later for data types creation
        self.files_helper = FilesHelper()
        
        # First create user 
        user = model.User("datatype_factory_user" + micro_postfix, "test_pass", 
                          "test_mail@tvb.org" + micro_postfix, True, "user")
        self.user = dao.store_entity(user) 
        
        # Now create a project
        project_service = ProjectService()
        data = dict(name='DatatypesFactoryProject' + micro_postfix, description='test_desc', users=[])
        self.project = project_service.store_project(self.user, True, None, **data)
        
        # Create algorithm
        alg_category = model.AlgorithmCategory('one', True)
        dao.store_entity(alg_category)
        alg_group = model.AlgorithmGroup("test_module1", "classname1", alg_category.id)
        dao.store_entity(alg_group)
        algorithm = model.Algorithm(alg_group.id, 'id', name = '', req_data = '', 
                               param_name = '', output = '')
        self.algorithm = dao.store_entity(algorithm)
        
        #Create an operation
        self.meta = {DataTypeMetaData.KEY_SUBJECT : self.USER_FULL_NAME, 
                DataTypeMetaData.KEY_STATE : self.DATATYPE_STATE}
        operation = model.Operation(self.user.id, self.project.id,
                                    self.algorithm.id, 'test parameters', 
                                    meta = json.dumps(self.meta), status="FINISHED",
                                    method_name = ABCAdapter.LAUNCH_METHOD)
        self.operation = dao.store_entity(operation)
        
        
    def get_project(self):
        """
            Return project to which generated data types are assigned
        """
        return self.project
    
    def get_operation(self):
        """
            Return operation to which generated data types are assigned
        """
        return self.operation
    
    def get_user(self):
        """
            Return user to which generated data types are assigned
        """
        return self.user
    
    def _store_datatype(self, data_type, operation_id=None):
        """
            Launch adapter to store a create a persistent DataType.
        """
        operation_id = operation_id or self.operation.id
        data_type.type = data_type.__class__.__name__
        data_type.module = data_type.__class__.__module__
        data_type.subject = self.USER_FULL_NAME
        data_type.state = self.DATATYPE_STATE
        data_type.set_operation_id(operation_id)
        
        adapter_instance = StoreAdapter([data_type])
        operation = dao.get_operation_by_id(operation_id)
        OperationService().initiate_prelaunch(operation, adapter_instance, {})
        
        return data_type
    
    
    def create_simple_datatype(self, subject = USER_FULL_NAME, state = DATATYPE_STATE):
        """
            This method creates a simple data type
        """
        datatype_inst = Datatype1()
        self._fill_datatype(datatype_inst, subject, state)
               
        # Store data type
        return self._store_datatype(datatype_inst)
    
        
    def create_datatype_with_storage(self, subject = USER_FULL_NAME, state = DATATYPE_STATE, 
                                     data = DATATYPE_DATA, operation_id = None):
        """
            This method creates and stores a data type which imply storage on the file system.
        """    
        datatype_inst = Datatype2() 
        self._fill_datatype(datatype_inst, subject, state, operation_id)
        
        datatype_inst.string_data = data
       
        return self._store_datatype(datatype_inst, operation_id)
    
    
    def _fill_datatype(self, datatype, subject, state, operation_id = None):
        """
        This method sets some common attributes on dataType 
        """
        operation_id = operation_id or self.operation.id
        datatype.subject = subject
        datatype.state = state
        # Set_operation_id also sets storage_path attribute
        datatype.set_operation_id(operation_id)
        
        
    def create_datatype_group(self, subject = USER_FULL_NAME, state = DATATYPE_STATE,):
        """ 
            This method creates / stores and returns a DataTypeGroup
        """
        OPERATION_GROUP_RANGE = [json.dumps(["row1", ['a', 'b', 'c']])]
        group = model.OperationGroup(self.project.id, self.OPERATION_GROUP_NAME, 
                                     OPERATION_GROUP_RANGE)
        group = dao.store_entity(group)
            
        datatype_group = model.DataTypeGroup(group.id, subject = subject, 
                                     state=state, operation_id=self.operation.id)
        # Set storage path, before setting data
        datatype_group.storage_path = self.files_helper.get_project_folder(
                            self.project, str(self.operation.id))
        datatype_group = dao.store_entity(datatype_group)
        
        # Now create some data types and add them to group
        for range_val in ['a', 'b', 'c']:
            operation = model.Operation(self.user.id, self.project.id,
                                    self.algorithm.id, 'test parameters', 
                                    meta = json.dumps(self.meta), status="FINISHED",
                                    method_name = ABCAdapter.LAUNCH_METHOD,
                                    range_values = json.dumps({'row1' : range_val}))
            operation.fk_operation_group = group.id
            operation = dao.store_entity(operation)
            datatype = self.create_datatype_with_storage(operation_id = operation.id)
            datatype.row1 = range_val
            datatype.fk_datatype_group = datatype_group.id
            datatype.set_operation_id(operation.id)
            dao.store_entity(datatype)
        
        return datatype_group