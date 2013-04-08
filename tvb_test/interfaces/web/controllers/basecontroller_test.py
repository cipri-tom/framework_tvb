import os
import cherrypy
from tvb.basic.config.settings import TVBSettings as cfg
from tvb.basic.config.utils import EnhancedDictionary
from tvb_test.core.base_testcase import BaseTestCase
from tvb_test.core.test_factory import TestFactory
import tvb.interfaces.web.controllers.basecontroller as b_c

class BaseControllersTest(BaseTestCase):    
    
    class CherrypySession(EnhancedDictionary):
    
        data = {}
        
        def acquire_lock(self):
            pass
        
        def release_lock(self):
            pass
        
    def _expect_redirect(self, page, method, *args, **kwargs):
        """
        A generic mechanism that calls a method with some arguments and expects a redirect
        to a given page.
        """
        try:
            method(*args, **kwargs)
            self.fail("Should be redirect to %s."%(page,))
        except cherrypy.HTTPRedirect, redirect:
            self.assertTrue(redirect.urls[0].endswith(page), "Should be redirect to %s"%(page,))
    
    
    def init(self):
        '''
        Have a different name than setUp so we can use it safely in transactions and it will
        not be called before running actual test.
        '''
        # Add 3 entries so we no longer consider this the first run.
        cfg.add_entries_to_config_file({'test' : 'test',
                                        'test1' : 'test1',
                                        'test2' : 'test2'})
        self.test_user = TestFactory.create_user(username="CtrlTstUsr")
        self.test_project = TestFactory.create_project(self.test_user, "Test")
        cherrypy.session = BaseControllersTest.CherrypySession()
        cherrypy.session[b_c.KEY_USER] = self.test_user
        cherrypy.session[b_c.KEY_PROJECT] = self.test_project
    
    
    def cleanup(self):
        '''
        ve a different name than tearDown so we can use it safely in transactions and it will
        not be called after running actual test.
        '''
        if os.path.exists(cfg.TVB_CONFIG_FILE):
            os.remove(cfg.TVB_CONFIG_FILE)
            