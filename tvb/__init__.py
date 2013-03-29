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
We want tvb package to extend over at least 3 folders:
web and desktop interfaces, and scientific-library packages.
"""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

if 'tvb' in __path__:
    # We want the order in PYTHONPATH to have an influence in case we have both scientific_library and TVB Framework present.
    # So just remove tvb from __path__ since this will only influence relative imports.
    __path__.remove('tvb')

