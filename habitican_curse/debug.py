""" Module "DEBUG" : Wrapper for displaying messages

"""

# Custom module imports
import screen as Screen
import global_objects as G
import config as C
import logging

#Initialize the logging facility
dbg_level=C.getConfig("debug_lvl")
dbg_file=C.getConfig("debug_file")

if(dbg_file is not None):
    logging.basicConfig(filename=dbg_file,level=int(dbg_level))
else:
    logging.basicConfig(level=int(dbg_level))

#Send a message to the logging facility
# This existis so we don't depend everything on the python
# logging module
def Log(level, string):
    logging.log(level, string)
