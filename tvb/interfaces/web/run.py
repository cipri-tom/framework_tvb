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
Launches the web server and configure the controllers for UI.

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

import os
import sys
import cherrypy
import webbrowser
from copy import copy
from cherrypy import Tool
from sys import platform, argv

### Set running profile from arguments.
from tvb.basic.profile import TvbProfile

TvbProfile.set_profile(argv, True)
from tvb.basic.config.settings import TVBSettings

### For Linux Distribution, correctly set MatplotLib Path, before start.
if TVBSettings().is_linux():
    os.environ['MATPLOTLIBDATA'] = os.path.join(TVBSettings().get_library_folder(), 'mpl-data')

### Import MPLH5 to have the back-end Thread started.
from tvb.interfaces.web.mplh5 import mplh5server
from tvb.basic.logger.builder import get_logger

LOGGER = get_logger('tvb.interfaces.web.mplh5.mplh5server')
mplh5server.start_server(LOGGER)

from tvb.core.adapters.abcdisplayer import ABCDisplayer
from tvb.core.decorators import user_environment_execution
from tvb.core.services.settingsservice import SettingsService
from tvb.core.services.initializer import initialize, reset
from tvb.core.services.exceptions import InvalidSettingsException
from tvb.interfaces.web.request_handler import RequestHandler
from tvb.interfaces.web.controllers.basecontroller import BaseController
from tvb.interfaces.web.controllers.userscontroller import UserController
from tvb.interfaces.web.controllers.help.helpcontroller import HelpController
from tvb.interfaces.web.controllers.project.projectcontroller import ProjectController
from tvb.interfaces.web.controllers.project.figurecontroller import FigureController
from tvb.interfaces.web.controllers.project.dtipipelinecontroller import DTIPipelineController
from tvb.interfaces.web.controllers.flowcontroller import FlowController
from tvb.interfaces.web.controllers.settingscontroller import SettingsController
from tvb.interfaces.web.controllers.burst.burstcontroller import BurstController
from tvb.interfaces.web.controllers.burst.explorationcontroller import ParameterExplorationController
from tvb.interfaces.web.controllers.spatial.base_spatiotemporalcontroller import SpatioTemporalController
from tvb.interfaces.web.controllers.spatial.regionsmodelparameterscontroller import RegionsModelParametersController
from tvb.interfaces.web.controllers.spatial.surfacemodelparameterscontroller import SurfaceModelParametersController
from tvb.interfaces.web.controllers.spatial.regionstimuluscontroller import RegionStimulusController
from tvb.interfaces.web.controllers.spatial.surfacestimuluscontroller import SurfaceStimulusController
from tvb.interfaces.web.controllers.spatial.localconnectivitycontroller import LocalConnectivityController
from tvb.interfaces.web.controllers.spatial.noiseconfigurationcontroller import NoiseConfigurationController


LOGGER = get_logger('tvb.interface.web.run')
CONFIG_EXISTS = not SettingsService.is_first_run()
PARAM_RESET_DB = "reset"

### Ensure Python is using UTF-8 encoding.
### While running distribution/console, default encoding is ASCII
reload(sys)
sys.setdefaultencoding('utf-8')
LOGGER.info("TVB application running using encoding: " + sys.getdefaultencoding())



def init_cherrypy(arguments=None):
    #### Mount static folders from modules marked for introspection
    arguments = arguments or []
    CONFIGUER = TVBSettings.CHERRYPY_CONFIGURATION
    for module in arguments:
        module_inst = __import__(str(module), globals(), locals(), ["__init__"])
        module_path = os.path.dirname(os.path.abspath(module_inst.__file__))
        CONFIGUER["/static_" + str(module)] = {'tools.staticdir.on': True,
                                               'tools.staticdir.dir': '.',
                                               'tools.staticdir.root': module_path}

    #### Mount controllers, and specify the root URL for them.
    cherrypy.tree.mount(BaseController(), "/", config=CONFIGUER)
    cherrypy.tree.mount(UserController(), "/user/", config=CONFIGUER)
    cherrypy.tree.mount(ProjectController(), "/project/", config=CONFIGUER)
    cherrypy.tree.mount(FigureController(), "/project/figure/", config=CONFIGUER)
    cherrypy.tree.mount(FlowController(), "/flow/", config=CONFIGUER)
    cherrypy.tree.mount(SettingsController(), "/settings/", config=CONFIGUER)
    cherrypy.tree.mount(DTIPipelineController(), "/pipeline/", config=CONFIGUER)
    cherrypy.tree.mount(HelpController(), "/help/", config=CONFIGUER)
    cherrypy.tree.mount(BurstController(), "/burst/", config=CONFIGUER)
    cherrypy.tree.mount(ParameterExplorationController(), "/burst/explore/", config=CONFIGUER)
    cherrypy.tree.mount(SpatioTemporalController(), "/spatial/", config=CONFIGUER)
    cherrypy.tree.mount(RegionsModelParametersController(), "/spatial/modelparameters/regions/", config=CONFIGUER)
    cherrypy.tree.mount(SurfaceModelParametersController(), "/spatial/modelparameters/surface/", config=CONFIGUER)
    cherrypy.tree.mount(RegionStimulusController(), "/spatial/stimulus/region/", config=CONFIGUER)
    cherrypy.tree.mount(SurfaceStimulusController(), "/spatial/stimulus/surface/", config=CONFIGUER)
    cherrypy.tree.mount(LocalConnectivityController(), "/spatial/localconnectivity/", config=CONFIGUER)
    cherrypy.tree.mount(NoiseConfigurationController(), "/spatial/noiseconfiguration/", config=CONFIGUER)
    cherrypy.config.update(CONFIGUER)

    #----------------- Register additional request handlers -----------------
    # This tool checks for MAX upload size
    cherrypy.tools.upload = Tool('on_start_resource', RequestHandler.check_upload_size)
    # This tools clean up files on disk (mainly after export)
    cherrypy.tools.cleanup = Tool('on_end_request', RequestHandler.clean_files_on_disk)
    #----------------- End register additional request handlers ----------------

    #### HTTP Server is fired now ######  
    cherrypy.engine.start()



def start_tvb(arguments):
    """
    Fire CherryPy server and listen on a free port
    """

    if PARAM_RESET_DB in arguments:
    ##### When specified, clean everything in DB
        reset()
        arguments.remove(PARAM_RESET_DB)

    if not os.path.exists(TVBSettings.TVB_STORAGE):
        try:
            os.makedirs(TVBSettings.TVB_STORAGE)
        except Exception:
            sys.exit("You do not have enough rights to use TVB storage folder:" + str(TVBSettings.TVB_STORAGE))

    try:
        initialize(arguments)
    except InvalidSettingsException, excep:
        LOGGER.exception(excep)
        sys.exit()

    #### Mark that the interface is Web
    ABCDisplayer.VISUALIZERS_ROOT = TVBSettings.WEB_VISUALIZERS_ROOT
    ABCDisplayer.VISUALIZERS_URL_PREFIX = TVBSettings.WEB_VISUALIZERS_URL_PREFIX

    init_cherrypy(arguments)

    run_browser()

    ## Launch CherryPy loop forever.
    LOGGER.info("Finished starting TVB version:" + str(TVBSettings.CURRENT_VERSION))
    cherrypy.engine.block()
    cherrypy.log.error_log


@user_environment_execution
def run_browser():
    try:
    ################ Fire a browser page at the end. 
        if platform.startswith('win'):
            browser_app = webbrowser.get('windows-default')
        elif platform == 'darwin':
            browser_app = webbrowser.get('macosx')
        else:
            browser_app = webbrowser

        ## Actual browser fire.
        if CONFIG_EXISTS:
            browser_app.open(TVBSettings.BASE_URL)
        else:
            browser_app.open(TVBSettings.BASE_URL + 'settings/settings')

    except Exception, excep:
        LOGGER.error("Browser could not be fired!  Please manually type in your preferred browser: "
                     "http://127.0.0.1:8080/")
        LOGGER.exception(excep)


if __name__ == '__main__':
    #### Prepare parameters and fire CherryPy
    #### Remove not-relevant parameter, 0 should point towards this "run.py" file
    DUPLICATE_ARGV = copy(argv)
    DUPLICATE_ARGV.remove(DUPLICATE_ARGV[0])

    start_tvb(DUPLICATE_ARGV)



