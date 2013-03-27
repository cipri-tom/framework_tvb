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
"""
import datetime
import tvb.core.services.eventhandler as eventhandler
from tvb.core.entities.model import ROLE_ADMINISTRATOR
from tvb.core.entities.modelmanager import initialize_startup
from tvb.core.entities.modelmanager import reset_database
from tvb.core.code_versions.code_update_manager import CodeUpdateManager
from tvb.core.services.projectservice import initialize_storage
from tvb.core.services.userservice import UserService
from tvb.core.services.settingsservice import SettingsService
from tvb.core.adapters.introspector import Introspector
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.traits import db_events


def reset():
    """
    Service Layer for Database reset.
    """
    reset_database()


def initialize(introspected_modules, load_xml_events=True):
    """
    Initialize when Application is starting.
    Check for new algorithms or new DataTypes.
    """
    SettingsService().check_db_url(cfg.DB_URL)
    
    ## Initialize DB
    is_db_empty = initialize_startup()
    
    ## Create Projects storage root in case it does not exist.
    initialize_storage()
    
    ## Populate DB algorithms, by introspection
    event_folders = []
    start_introspection_time = datetime.datetime.now()
    for module in introspected_modules:
        introspector = Introspector(module)
        # Introspection is always done, even if DB was not empty.
        introspector.introspect(True)
        event_path = introspector.get_events_path()
        if event_path:
            event_folders.append(event_path)
    # Now remove any unverified Algo-Groups, categories or Portlets
    invalid_stored_entities = dao.get_non_validated_entities(start_introspection_time)
    for entity in invalid_stored_entities:
        dao.remove_entity(entity.__class__, entity.id)
   
    ## Populate events
    if load_xml_events:
        eventhandler.read_events(event_folders)
    
    ## Make sure DB events are linked.
    db_events.attach_db_events()
    
    ## Create default users.
    if is_db_empty:
        dao.store_entity(model.User(cfg.SYSTEM_USER_NAME, None, None, True, None))
        UserService().create_user(username=cfg.ADMINISTRATOR_NAME, password=cfg.ADMINISTRATOR_PASSWORD,
                                  email=cfg.ADMINISTRATOR_EMAIL, role=ROLE_ADMINISTRATOR)
        
    ## In case actions related to latest code-changes are needed, make sure they are executed.
    CodeUpdateManager().update_all()
   
   
            
