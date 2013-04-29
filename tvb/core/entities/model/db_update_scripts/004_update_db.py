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
 Change of DB structure after TVB 1.0.4

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

from sqlalchemy import Column, Integer, Boolean
from migrate.changeset.schema import create_column, drop_column
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.basic.logger.builder import get_logger

meta = model.Base.metadata
COL_RANGES_1 = Column('no_of_ranges', Integer, default=0)
COL_RANGES_2 = Column('only_numeric_ranges', Boolean, default=False)



def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata.
    """
    meta.bind = migrate_engine

    table = meta.tables['DATA_TYPES_GROUPS']
    create_column(COL_RANGES_1, table)
    create_column(COL_RANGES_2, table)

    try:
        ## Iterate DataTypeGroups from previous code-versions and try to update value for the new column.
        previous_groups = dao.get_generic_entity(model.DataTypeGroup, "0", "no_of_ranges")

        for group in previous_groups:

            operation_group = dao.get_operationgroup_by_id(group.fk_operation_group)
            group.only_numeric_ranges = operation_group.has_only_numeric_ranges

            if operation_group.range3 is not None:
                group.no_of_ranges = 3
            elif operation_group.range2 is not None:
                group.no_of_ranges = 2
            elif operation_group.range1 is not None:
                group.no_of_ranges = 1
            else:
                group.no_of_ranges = 0

            dao.store_entity(group)

    except Exception, excep:
        ## we can live with a column only having default value. We will not stop the startup.
        logger = get_logger(__name__)
        logger.exception(excep)



def downgrade(migrate_engine):
    """Operations to reverse the above upgrade go here."""
    meta.bind = migrate_engine

    table = meta.tables['DATA_TYPES_GROUPS']
    drop_column(COL_RANGES_1, table)
    drop_column(COL_RANGES_2, table)
