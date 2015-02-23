"""
HTTP tools
"""

import cherrypy

# HTTP 201 handling is poor
# Browsers act like with HTTP 200, without redirection
def success_201(url):
    """
    HTTP "201 Created"
    """
    cherrypy.response.status = "201 Created"
    cherrypy.response.headers['Location'] = "%s" % url

# HTTP 301-303 are fairly well supported
# These codes can't be used for a web page because the document is not
# displayed.
def redir_301(url):
    """
    HTTP "301 Moved Permanently" redirection
    """
    cherrypy.response.status = "301 Moved Permanently"
    cherrypy.response.headers['Location'] = "%s" % url

def redir_302(url):
    """
    HTTP "302 Found" redirection
    """
    cherrypy.response.status = "302 Found"
    cherrypy.response.headers['Location'] = "%s" % url

def redir_303(url):
    """
    HTTP "303 See Other" redirection
    """
    cherrypy.response.status = "303 See Other"
    cherrypy.response.headers['Location'] = "%s" % url

# HTTP 307 implementation is not reliable
# It would be better for a POST->POST wait->run redirection.
# http://www.alanflavell.org.uk/www/post-redirect.html
# http://stackoverflow.com/questions/46582/redirect-post
def redir_307(url):
    """
    HTTP "307 Temporary Redirect" redirection
    """
    cherrypy.response.status = "307 Temporary Redirect"
    cherrypy.response.headers['Location'] = "%s" % url

# HTTP Refresh is non-standard but supposedly well supported
# It has the advantage of displaying the page content before requesting
# the next page.
# It appears that while html meta refresh is well supported,
# HTTP Refresh is not and triggers loops in IE and Opera
def refresh(url, delay=1):
    """
    HTTP "Refresh" header
    """
    cherrypy.response.headers['Refresh'] = "%i;url=%s" % (delay, url)
