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
 Change of DB structure to TVB 1.0.3.

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

from sqlalchemy import Table, MetaData


def _prepare_table(meta, table_name):
    """
    Load current DB structure.
    """
    table = Table(table_name, meta, autoload=True)
    for constraint in table._sorted_constraints:
        if not isinstance(constraint.name, (str, unicode)):
            constraint.name = None
    return table


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata.
    """
    meta = MetaData(bind=migrate_engine)
    
    table = _prepare_table(meta, 'USER_PREFERENCES')
    table.c.user_id.alter(name='fk_user')
    
    table = _prepare_table(meta, 'BURST_CONFIGURATIONS')
    table.c.project_id.alter(name='fk_project')
    
    table = _prepare_table(meta, 'MAPPED_DATATYPE_MEASURE')
    table.c.analyzed_datatype.alter(name='_analyzed_datatype')
    
    table = _prepare_table(meta, 'WORKFLOWS',)
    table.c.project_id.alter(name='fk_project')
    table.c.burst_id.alter(name='fk_burst')
    
    table = _prepare_table(meta, 'WORKFLOW_STEPS')
    table.c.workflow_id.alter(name='fk_workflow')
    table.c.algorithm_id.alter(name='fk_algorithm')
    table.c.resulted_op_id.alter(name='fk_operation')



def downgrade(migrate_engine):
    """
    Operations to reverse the above upgrade go in this function.
    """
    meta = MetaData(bind=migrate_engine)
    
    table = _prepare_table(meta, 'USER_PREFERENCES')
    table.c.fk_user.alter(name='user_id')
    
    table = _prepare_table(meta, 'BURST_CONFIGURATIONS')
    table.c.fk_project.alter(name='project_id')
    
    table = _prepare_table(meta, 'MAPPED_DATATYPE_MEASURE')
    table.c._analyzed_datatype.alter(name='analyzed_datatype')
    
    table = _prepare_table(meta, 'WORKFLOWS')
    table.c.fk_project.alter(name='project_id')
    table.c.fk_burst.alter(name='burst_id')
    
    table = _prepare_table(meta, 'WORKFLOW_STEPS')
    table.c.fk_workflow.alter(name='workflow_id')
    table.c.fk_algorithm.alter(name='algorithm_id')
    table.c.fk_operation.alter(name='resulted_op_id')
    
        
        