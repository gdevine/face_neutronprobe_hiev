#!/usr/bin/env python3
"""
Upload Neutron Probe data from EucFACE using the HievPy library. The upload will happen in two steps:

1. Raw data in the Data folder will be renamed to match naming conventions and copied to a folder called 'Renamed'.
   A copy of the file will also be made in the backups folder
2. Data will be uploaded to HIEv from the 'Renamed' folder and upon completion will be removed from both the 'Data'
   folder and the 'Renamed' folder

* Data to upload should be in a folder called 'Data' at the same level as this script

"""

__author__ = "Gerard Devine"
__version__ = "0.1.0"
__license__ = "MIT"


import os
import shutil
import hievpy as hp
from datetime import datetime


# Set the API token for HIEv access
api_token = os.environ['HIEV_API_KEY']

# Get the current path
cwd = os.getcwd()

# Check if necessary folders are in place and create if not
if not os.path.exists(os.path.join(cwd, 'Data')):
    os.mkdir(os.path.join(cwd, 'Data'))
if not os.path.exists(os.path.join(cwd, 'Renamed')):
    os.mkdir(os.path.join(cwd, 'Renamed'))
if not os.path.exists(os.path.join(cwd, 'Backups')):
    os.mkdir(os.path.join(cwd, 'Backups'))

data_dir = os.path.join(cwd, 'data')
renamed_dir = os.path.join(cwd, 'Renamed')
backups_dir = os.path.join(cwd, 'Backups')


# -- Open log file for writing and append date/time stamp into file for a new entry
logfile = 'log.txt'
log = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), logfile), 'a')
log.write('\n------------  Begin: '+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'  ------------ \n')

# Set metadata for all uploads
metadata = {"experiment_id": 77,
            "type": "RAW",
            "description": "Neutron Probe soil moisture data measured every three weeks (where each file is one day \
             of data). Measurements are taken across all rings at the EucFACE experiment. ",
            "creator_email": "g.devine@westernsydney.edu.au",
            "contributor_names": ['Tom Smith, t.smith@google.com',
                                  'Jane White, J.White@aol.com',
                                  'Frank Blank, f.black@yahoo.com'],
            "label_names": '"Rainfall","Environment","TOA5"',
            "grant_numbers": '"ZXY7654","PRQ53422"',
            "related_websites": '"http://www.bom.org.au","http://www.westernsydney.edu.au"',
            "start_time": '2014-01-01 12:11:10',
            "end_time": '2014-12-30 14:09:08'
            }


def rename_file(file):
    """ Returns the renamed filename matching the human-friendly FACE convention

    This function assumes input file is of format FADDMMYY, e.g FA150518
    """

    day = str(file)[2:4]
    month = str(file)[4:6]
    year = '20'+str(file)[6:]

    return 'FACE_AUTO_RA_NEUTRON_R_'+year+month+day+'.txt'


def main():
    file_counter = 0
    for file in data_dir:
        if file.startswith('FA') and len(file) == 8:
            log.write('\n*Info: Match found: ' + file)
            toupload_file_path = os.path.join(data_dir, file)
            backups_file_path = os.path.join(backups_dir, file)

            # 1. Make a backup copy of the file in the Backups directory
            shutil.copy(toupload_file_path, backups_file_path)
            log.write('\n*Info: Initial backup made of file ' + file + ' to Backups folder')
            
            # 2. Copy the file to Renamed folder and rename it to match naming convention
            renamed_file = rename_file(file)
            renamed_file_path = os.path.join(renamed_dir, renamed_file)
            # Check if file already exists in the Renamed folder
            if os.path.exists(renamed_file_path):
                log.write('\n*Warning: File ' + renamed_file + ' already exists in Renamed folder')
                continue
            shutil.copy(toupload_file_path, renamed_file_path)
            log.write('\n*Info: File ' + file + ' moved to Renamed folder and renamed to ' + renamed_file)

            # 3. Upload the file to HIEv
            try:
                hp.upload(api_token, renamed_file_path, metadata)
                log.write('\n*Info: File ' + file + ' successfully uploaded to HIEv')
            except Exception as e:
                log.write('\n*Error: Could not upload file ' + file + ' to HIEv. Error: ' + str(e))
                continue

            # 4. Remove the file from both the ToUpload and Renamed folders
            os.remove(toupload_file_path)
            os.remove(renamed_file_path)
            log.write('\n*Info: File ' + file + ' cleaned out of ToUpload and Renamed folders')
            # Increment counter
            file_counter += 1

        else:
            # This file does not match the FA naming convention
            log.write('\n*WARNING: The file named ' + file + ' does not match upload naming convention - ignoring\n')

    log.write('\n*Info: Run Complete. ' + file_counter + '(s) successfully files uploaded to HIEv')
    log.write('\n------------  End: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '  ------------ \n')


if __name__ == "__main__":
    main()
