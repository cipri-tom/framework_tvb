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

import smtplib
from email.MIMEText import MIMEText



def send(address_from, address_to, email_subject, email_content):
    """
    Sends an Email Message
    """
    email = MIMEText(email_content)
    email['From'] = address_from
    email['To'] = address_to
    email['Subject'] = email_subject

    server = smtplib.SMTP('mail.thevirtualbrain.org', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('tvb_appserver', 'du5rEpratHAc')
    server.sendmail(address_from, address_to, email.as_string())
    server.quit()
    

