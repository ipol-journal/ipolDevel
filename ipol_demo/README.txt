% IPOL demo web service

# Requirements

This code requires
* python plus some modules, included in the following Debian/Ubuntu
  packages:
  python python-cherrypy3 python-mako python-imaging python-sqlite
* compilation tools and libraries, included in the following
  Debian/Ubuntu packages:
  gcc g++ make cmake libtiff-dev libpng-dev libfftw3-dev

# Usage

To test this service locally,
* copy `demo.conf.example` to `demo.conf`
* run `./demo.py build` to download and build the compiled components
  (only needs to be done once)
* run `./demo.py` to launch the http demo server
* visit http://127.0.0.1:8080 with a graphical web browser

# Development

To create a new demo,

1. in the app folder, copy an example demo ('xxx_something') to a new
   folder name; this folder name will be the demo id
2. in this new folder, customize the class attributes and functions in
   `app.py`
3. in this new folder, customize the default input files in
   `input`, and update the description of these files in
   `input/index.cfg`
4. in this new folder, customize the `params.html` and `result.html`
   templates in the `template` folder
5. debug, test, debug, release
