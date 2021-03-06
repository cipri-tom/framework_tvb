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
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Base DAO behavior.

.. moduleauthor:: bogdan.neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

from sqlalchemy.orm.exc import NoResultFound
from tvb.basic.logger.builder import get_logger
from tvb.core.entities import model
from tvb.core.entities.storage.sessionmaker import SESSION_META_CLASS
from tvb.config import SIMULATION_DATATYPE_CLASS



class RootDAO(object):
    """
    GLOBAL OPERATIONS
    """

    __metaclass__ = SESSION_META_CLASS
    session = None
    logger = get_logger(__name__)

    EXCEPTION_DATATYPE_GROUP = "DataTypeGroup"
    EXCEPTION_DATATYPE_SIMULATION = SIMULATION_DATATYPE_CLASS


    def store_entity(self, entity):
        """Store in DB one generic entity."""
        self.session.add(entity)
        self.session.commit()
        saved_entity = self.session.query(entity.__class__).filter_by(id=entity.id).one()
        return saved_entity


    def store_entities(self, entities_list):
        """Store in DB a list of generic entities."""
        self.session.add_all(entities_list)
        self.session.commit()
        stored_entities = []
        for entity in entities_list:
            stored_entities.append(self.session.query(entity.__class__).filter_by(id=entity.id).one())
        return stored_entities


    def get_generic_entity(self, entity_type, filter_value, select_field="id"):
        """Retrieve an entity from a generic table,filtered by a generic field."""
        if isinstance(entity_type, (str, unicode)):
            classname = entity_type[entity_type.rfind(".") + 1:]
            entity_class = __import__(entity_type[0: entity_type.rfind(".")], globals(), locals(), classname)
            entity_class = eval("entity_class." + classname)
            result = self.session.query(entity_class).filter(entity_class.__dict__[select_field] == filter_value).all()
        else:
            result = self.session.query(entity_type).filter(entity_type.__dict__[select_field] == filter_value).all()

        # Need this since entity has attributes loaded automatically on DB load from 
        # traited DB events. This causes the session to see the entity as dirty and issues
        # an invalid commit() which leaves the entity unattached to any sessions later on.
        self.session.expunge_all()
        return result


    def remove_entity(self, entity_class, entity_id):
        """ 
        Find entity by Id and Type, end then remove it.
        Return True, when entity was removed successfully, of False when exception.
        """
        result = False
        try:
            entity = self.session.query(entity_class).filter_by(id=entity_id).one()
            self.session.delete(entity)
            self.session.commit()
            result = True
        except NoResultFound, ex:
            self.logger.info("Entity from class %s with id %s no longer exists."%(entity_class, entity_id))
        except Exception, excep:
            self.logger.exception(excep)
        return result


    #
    # DATA_TYPE RELATED METHODS
    #

    def remove_datatype(self, gid):
        """When removing dataType, remove from all tables referenced."""
        data = self.session.query(model.DataType).filter(model.DataType.gid == gid).all()
        for entity in data:
            extended_ent = self.get_generic_entity(entity.module + "." + entity.type, entity.id)
            self.session.delete(extended_ent[0])
        self.session.commit()


    def get_datatype_by_id(self, data_id):
        """Retrieve DataType entity by ID."""
        result = self.session.query(model.DataType).filter_by(id=data_id).one()
        result.parent_operation.project
        return result
    
  
