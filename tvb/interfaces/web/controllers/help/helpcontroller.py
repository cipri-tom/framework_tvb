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
Basic Help functionality.

.. moduleauthor:: Calin Pavel
"""

import cherrypy
from tvb.interfaces.web.controllers.basecontroller import using_template, BaseController
from tvb.interfaces.web.controllers.help.help_config import HelpConfig



class HelpController(BaseController):
    """
    This class takes care of all requester related to HELP system.
    """


    def __init__(self):
        BaseController.__init__(self)
        self.config = HelpConfig()


    @cherrypy.expose
    @using_template('overlay')
    def showOnlineHelp(self, section=None, subsection=None, **data):
        """
        This method generates the content of the overlay presenting Online-Help.
        In case both section and subsection are missing, we'll open main OnlineHelp page.
        
        :param section: section for which to open help
        :param subsection: subsection for which to open help
        """
        template_specification = self.fill_overlay_attributes(None, "TVB", "Online-Help", "help/online_help", "help")

        # Add URL of the help page
        template_specification["helpURL"] = self.config.get_help_url(section, subsection)

        return self.fill_default_attributes(template_specification)
    
    