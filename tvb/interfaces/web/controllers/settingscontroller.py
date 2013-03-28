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

import os
import json
import subprocess
import cherrypy
import formencode
import threading
from time import sleep
from formencode import validators
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.core.utils import check_matlab_version
from tvb.core.services.settingsservice import SettingsService
from tvb.interfaces.web.controllers.basecontroller import using_template
from tvb.interfaces.web.controllers.userscontroller import admin, UserController
from tvb.core.services.exceptions import InvalidSettingsException
import tvb.interfaces.web.controllers.basecontroller as bc 



class SettingsController(UserController):
    """
    Controller for TVB-Settings web page.
    Inherit from UserController, to have the same fill_default_attributes method (with versionInfo).
    """
    
    def __init__(self):
        UserController.__init__(self)  
        self.settingsservice = SettingsService()      
           

    @cherrypy.expose
    @using_template('user/base_user')
    @admin()
    def settings(self, save_settings=False, **data):
        """Main settings page submit and get"""
        template_specification = dict(mainContent="../settings/system_settings", title="System Settings")
        if save_settings:
            try:
                form = SettingsForm()
                data = form.to_python(data)
                isrestart, isreset = self.settingsservice.save_settings(**data)
                if isrestart:
                    thread = threading.Thread(target=self._restart_services, kwargs={'should_reset' : isreset})
                    thread.start()
                    bc.add2session(bc.KEY_IS_RESTART, True)
                    bc.set_info_message('Please wait until TVB is restarted properly!')
                    raise cherrypy.HTTPRedirect('/tvb')
                # Here we will leave the same settings page to be displayed.
                # It will continue reloading when CherryPy restarts.
            except formencode.Invalid, excep:
                template_specification[bc.KEY_ERRORS] = excep.unpack_errors()
            except InvalidSettingsException, excep:
                self.logger.error('Invalid settings!  Exception %s was raised' %(str(excep)))
                bc.set_error_message(excep.message)
        template_specification.update({'keys_order': self.settingsservice.KEYS_DISPLAY_ORDER,
                                       'config_data': self.settingsservice.configurable_keys,
                                       bc.KEY_FIRST_RUN: self.settingsservice.is_first_run()})
        return self.fill_default_attributes(template_specification)
 
 
    def _restart_services(self, should_reset):
        """
        Restart CherryPy and Backend.
        """
        if cfg.MPLH5_Server_Thread is not None:
            cfg.MPLH5_Server_Thread.shutdown()
            cfg.MPLH5_Server_Thread.server_close()
        else:
            self.logger.warning('For some reason the mplh5 never started.')
        cherrypy.engine.exit()
        self.logger.debug("Waiting for Cherrypy to terminate.")
        sleep(2)
        python_path = cfg().get_python_path()
        proc_params = [python_path, '-m', 'bin.app', 'start', 'web']
        if should_reset:
            proc_params.append('reset')
        subprocess.Popen(proc_params, shell=False) 
 
 
    @cherrypy.expose
    def check_db_url(self, **data): 
        """
        Action on DB-URL validate button.
        """
        try:
            storage_path = data[self.settingsservice.KEY_STORAGE]
            if os.path.isfile(storage_path):
                raise InvalidSettingsException('TVB Storage should be set to a folder and not a file.')
            if not os.path.isdir(storage_path):
                try:
                    os.mkdir(storage_path)
                except OSError:
                    return json.dumps({'status' : 'not ok', 
                                       'message' : 'Could not create root storage for TVB. Are you sure you have permissions there?'})
            self.settingsservice.check_db_url(data[self.settingsservice.KEY_DB_URL])
            return json.dumps({'status' : 'ok', 'message' : 'The database URL is valid.'})
        except InvalidSettingsException, excep:
            self.logger.error(excep)
            return json.dumps({'status' : 'not ok', 'message' : 'The database URL is not valid.'})
            
            
    @cherrypy.expose
    def validate_matlab_path(self, **data):
        """
        Check if the set path from the ui actually corresponds to a matlab executable.
        """
        submitted_path = data[self.settingsservice.KEY_MATLAB_EXECUTABLE]
        if len(submitted_path) == 0:
            return json.dumps({'status' : 'ok', 
                               'message' : 'No Matlab/Ocatve path was given. Some analyzers will not be available.'})
        if os.path.isfile(submitted_path):
            version = check_matlab_version(submitted_path)
            return json.dumps({'status' : 'ok', 
                               'message' : 'Valid Matlab/Octave. Found version: %s.'%(version,)})
        else:
            return json.dumps({'status' : 'not ok', 
                               'message' : 'Invalid Matlab/Octave path.'})
    

class DiskSpaceValidator(formencode.FancyValidator):
    """
    Custom validator for TVB disk space / user.
    """
    
    def _to_python(self, value, _):
        """ 
        Validation required method.
        :param value is user-specified value, in MB
        """
        try:
            value = long(value)
        except Exception, _:
            raise formencode.Invalid('Invalid disk space %s. Should be number'%value, value, None)
        
        available_mem_kb = SettingsService.get_disk_free_space()
        kb_value = value * (2 ** 10)
        if kb_value > 0 and kb_value < available_mem_kb:
            return kb_value
        else:
            available_mem_mb = available_mem_kb / (2 ** 10)
            raise formencode.Invalid('Invalid disk space %s. Should be number between 0 and %s MB (total '
                                     'available space on your disk)!'%(value, available_mem_mb), value, None)
     
     
class PortValidator(formencode.FancyValidator):
    """
    Custom validator for OS Port number.
    """
    
    def _to_python(self, value, _):
        """ 
        Validation required method.
        """
        try:
            value = int(value)
        except Exception, _:
            raise formencode.Invalid('Invalid port %s. Should be number between 0 and 65535.'%value, value, None)
        if value > 0 and value < 65535:
            return value
        else:
            raise formencode.Invalid('Invalid port number %s. Should be in interval [0, 65535]'%value, value, None)
   
   
class ThreadNrValidator(formencode.FancyValidator):
    """
    Custom validator number of threads.
    """
    
    def _to_python(self, value, _):
        """ 
        Validation required method.
        """
        try:
            value = int(value)
        except Exception, _:
            raise formencode.Invalid('Invalid number %d. Should be number between 1 and 16.'%value, value, None)
        if value > 0 and value < 17:
            return value
        else:
            raise formencode.Invalid('Invalid number %d. Should be in interval [1, 16]'%value, value, None)
        

class SurfaceVerticesNrValidator(formencode.FancyValidator):
    """
    Custom validator for the number of vertices allowed for a surface
    """
    MAX_VALUE = 256 * 256 * 256 + 1 # Max number of colors 
    
    def _to_python(self, value, _):
        """ 
        Validation required method.
        """
        try:
            value = int(value)
            if value > 0 and value < self.MAX_VALUE:
                return value
            else:
                raise formencode.Invalid('Invalid value: %d. Should be a number between 1 and %d.'% (value, 
                                                                            self.MAX_VALUE), value, None)
        except Exception, _:
            raise formencode.Invalid('Invalid value: %d. Should be a number between 1 and %d.'% (value, 
                                                                            self.MAX_VALUE), value, None)
            
class MatlabValidator(formencode.FancyValidator):
    """
    Custom validator for the number of vertices allowed for a surface
    """
    
    def _to_python(self, value, _):
        """ 
        Validation required method.
        """
        try:
            version = check_matlab_version(value)
            if len(version) > 0:
                return value
            else:
                formencode.Invalid('No valid matlab installation was found at the path you provided.', '', None)
        except Exception, _:
            raise formencode.Invalid('No valid matlab installation was found at the path you provided.', '', None)
           
   
class SettingsForm(formencode.Schema):
    """
    Validate Settings Page inputs.
    """
    
    ADMINISTRATOR_NAME = formencode.All(validators.UnicodeString(not_empty=True), validators.PlainText())
    ADMINISTRATOR_PASSWORD = validators.UnicodeString(not_empty=True)
    ADMINISTRATOR_EMAIL = validators.Email(not_empty=True)
    TVB_STORAGE = validators.UnicodeString(not_empty=True)
    USR_DISK_SPACE = DiskSpaceValidator()
    MATLAB_EXECUTABLE = MatlabValidator()
    SELECTED_DB = validators.UnicodeString(not_empty=True)
    URL_VALUE = validators.UnicodeString(not_empty=True)
    SERVER_IP = validators.UnicodeString(not_empty=True)
    WEB_SERVER_PORT = PortValidator()
    MPLH5_SERVER_PORT = PortValidator()
    MAXIMUM_NR_OF_THREADS = ThreadNrValidator()
    MAXIMUM_NR_OF_VERTICES_ON_SURFACE = SurfaceVerticesNrValidator()
    MAXIMUM_NR_OF_OPS_IN_RANGE = validators.Int(min= 5, max= 5000, not_empty= True)
    DEPLOY_CLUSTER = validators.Bool()



