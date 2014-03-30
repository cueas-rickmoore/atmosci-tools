""" STATION working directory cleaner
"""

import os
import commands

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

FILENAME_TEMPLATE = '*_stations_%s.h5'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def deleteFile(filepath, debug):
    if not debug:
        os.remove(filepath)
        print 'deleted', filepath
    else: print 'delete', filepath

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class StationDirectoryCleaner(object):

    def __init__(self, working_dir):
        self.working_dir = working_dir

    def __call__(self, dates, region=None, debug=False):
        working_dir = self.working_dir
        if os.path.isdir(working_dir):
            if region is not None:
                region = region.upper()
                for date in dates:
                    date_str = date.strftime('%Y%m%d')
                    filename = '%s_stations_%s.h5' % (region,date_str)
                    filepath = os.path.join(working_dir,filename)
                    if os.path.isfile(filepath):
                        deleteFile(filepath, debug) 
            else:
                for date in dates:
                    filename = FILENAME_TEMPLATE % date.strftime('%Y%m%d')
                    command = 'ls ' + os.path.join(working_dir, filename)
                    for filepath in commands.getoutput(command).split('\n'):
                        if os.path.isfile(filepath): # file exists
                            deleteFile(filepath, debug)
                        else: # must be an error message
                            print filepath
        else:
            print 'working directory does not exist :', working_dir

        # always dump the MAC OS .DS_Store file
        filepath = os.path.join(working_dir,'.DS_Store')
        if os.path.isfile(filepath):
            deleteFile(filepath, debug)

        # delete log files
        command = 'ls %s%s*.log' % (working_dir, os.sep)
        for filepath in commands.getoutput(command).split('\n'):
            if os.path.isfile(filepath):
                deleteFile(filepath, debug)

