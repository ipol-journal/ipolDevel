from ipol_webapp.settings import ALLAUTH_GESTS

__author__ = 'jak'

import logging

logger = logging.getLogger(__name__)



class NavbarReusableMixinMF(object):


    def allauth_guests(self):
        try:
            a = ALLAUTH_GESTS
        except Exception as e:
            msg = "NavbarReusableMixinMF %s" % e
            logger.error(msg)
        return a
