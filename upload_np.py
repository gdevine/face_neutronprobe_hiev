#!/usr/bin/env python3
"""
Upload Neutron Probe data from EucFACE using the HievPy library. The upload will happen in two steps:

1. Raw data in the Data folder will be copied to a folder called 'Renamed' and renamed to match naming conventions,
   and restructured to be in a clean CSV format. A copy of the file will also be made in the backups folder
2. Data will be uploaded to HIEv (both the Raw txt file and the L1 csv file) from the 'Renamed' folder and upon
   completion will be removed from both the 'Data' folder and the 'Renamed' folder

* Data to upload should be in a folder called 'Data' at the same level as this script

"""

__author__ = "Gerard Devine"
__version__ = "0.1.0"
__license__ = "MIT"


import os
import shutil
import hievpy as hp
from datetime import datetime
import subprocess


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

data_dir = os.path.join(cwd, 'Data')
renamed_dir = os.path.join(cwd, 'Renamed')
backups_dir = os.path.join(cwd, 'Backups')


# -- Open log file for writing and append date/time stamp into file for a new entry
logfile = 'log.txt'
log = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), logfile), 'a')
log.write('\n\n------------  Begin: '+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'  ------------ \n')

# Set metadata for all uploads (raw text format and level 1 CSV)
metadata_r = {"experiment_id": 31,
            "type": "RAW",
            "description": "Raw Neutron Probe soil moisture data (in Text format) measured approximately every three \
                           weeks, where each file represents the reading taken on the date identified in the \
                           filename (or in the metadata). Measurements are taken across all rings at the EucFACE \
                           experiment. Converted Level 1 CSV versions of this data can also be found in HIEv (See "
                           "associated data)",
            "creator_email": "vinod.kumar@uws.edu.au",
            "label_names": '"Neutron Probe","Soil Moisture"',
            "related_websites": '"https://www.westernsydney.edu.au/hie"',
            }
metadata_l1 = {"experiment_id": 31,
            "type": "PROCESSED",
            "description": "Level 1 Neutron Probe soil moisture data (in CSV format) from the EucFACE site. This file \
                           has been generated from the associated R script file (created by Teresa Gimeno) that \
                           converts the raw text format (see associated raw .txt file) to a more readable CSV format.",
            "creator_email": "g.devine@uws.edu.au",
            "label_names": '"Neutron Probe","Soil Moisture"',
            "contributor_names[]": ['Teresa Gimeno, teresa.gimeno@bc3research.org'],
            "related_websites": '"https://www.westernsydney.edu.au/hie"',
            }


def rename_file(infile):
    """ Returns the renamed filename matching the human-friendly FACE convention

    This function assumes input file is of format FADDMMYY.TXT, e.g FA150518.TXT
    """

    day = str(infile)[2:4]
    month = str(infile)[4:6]
    year = '20'+str(infile)[6:8]

    return 'FACE_AUTO_RA_NEUTRON_R_'+year+month+day+'.txt'


def rename_csv_file(infile):
    """ Renames a raw converted CSV file to L1 naming convention

    This function assumes input file is of format FACE_AUTO_RA_NEUTRON_R_'+year+month+day+'.txt,
    e.g. FACE_AUTO_RA_NEUTRON_R_20180205.txt, with resulting output file FACE_AUTO_RA_NEUTRON_L1_20180205.csv
    """

    l1 = infile.replace("_R_", "_L1_")

    return l1.replace(".txt", ".csv")


def get_datetimes(infile):
    """ Returns a start and end date/time as extracted from the infile filename

    """

    day = str(infile)[2:4]
    month = str(infile)[4:6]
    year = '20'+str(infile)[6:8]

    return year+'-'+month+'-'+day+' 00:00:00', year+'-'+month+'-'+day+' 23:59:59'


def txt2csv(infile):
    """ Convert raw text-formatted neutron probe file to CSV

    """

    command = 'Rscript'
    path2script = os.path.join(cwd, 'FACE_SCRIPT_NEUTRON_TXT-2-CSV.r')
    args = [infile]

    cmd = [command, path2script] + args
    subprocess.check_output(cmd, universal_newlines=True)


file_counter = 0
log.write('\n*Info: Looping over files in Data folder....')
for file in os.listdir(data_dir):
    if file.startswith('FA') and file.split('.')[1] == 'TXT':
        log.write('\n*Info: Match found: ' + file)
        data_file_path = os.path.join(data_dir, file)
        backups_file_path = os.path.join(backups_dir, file)

        # 1. Make a backup copy of the file in the Backups directory
        shutil.copyfile(data_file_path, backups_file_path)
        log.write('\n*Info: Initial backup made of file ' + file + ' to Backups folder')

        # 2. Copy the file to Renamed folder and rename it to match naming convention
        renamed_file = rename_file(file)
        renamed_file_path = os.path.join(renamed_dir, renamed_file)
        # Check if file already exists in the Renamed folder
        if os.path.exists(renamed_file_path):
            log.write('\n*Warning: File ' + renamed_file + ' already exists in Renamed folder - skipping this file')
        else:
            shutil.copyfile(data_file_path, renamed_file_path)
            log.write('\n*Info: File ' + file + ' moved to Renamed folder and renamed to ' + renamed_file)

            # 3. Convert the renamed file to L1 CSV format and rename accordingly
            l1_file = rename_csv_file(renamed_file)
            l1_file_path = os.path.join(renamed_dir, l1_file)
            if os.path.exists(l1_file_path):
                log.write('\n*Warning: File ' + l1_file + ' already exists in Renamed folder')
                continue
            shutil.copyfile(renamed_file_path, l1_file_path)
            try:
                with open(l1_file_path, 'r') as f1:
                    txt2csv(f1.name)
                log.write('\n*Info: Converted ' + file + ' to CSV file and renamed accordingly')
            except Exception as e:
                log.write('\n*Error: Could not convert text file to CSV file. Error: ' + str(e))
                continue

            # 4. Grab the start date/end date from the file name and then upload both the Raw and L1 files to HIEv
            try:
                start_datetime, end_datetime = get_datetimes(file)
                metadata_r["start_time"] = start_datetime
                metadata_r["end_time"] = end_datetime
                metadata_l1["start_time"] = start_datetime
                metadata_l1["end_time"] = end_datetime
                metadata_l1["parent_filenames[]"] = [renamed_file, 'FACE_SCRIPT_NEUTRON_TXT-TO-CSV.zip']
                upload = hp.upload(api_token, renamed_file_path, metadata_r)
                log.write('\n*Info: File ' + renamed_file + ' successfully uploaded to HIEv')
                upload = hp.upload(api_token, l1_file_path, metadata_l1)
                log.write('\n*Info: File ' + l1_file + ' successfully uploaded to HIEv')
            except Exception as e:
                log.write('\n*Error: Could not upload file ' + file + ' to HIEv. Error: ' + str(e))
                continue

            # 5. Remove the file from both the data and Renamed folders
            os.remove(data_file_path)
            os.remove(renamed_file_path)
            os.remove(l1_file_path)
            log.write('\n*Info: File ' + file + ' cleaned out of Data and Renamed folders')
            # Increment counter
            file_counter += 1
            log.write('')

    else:
        # This file does not match the FA naming convention
        log.write('\n*Warning: The file named ' + file + ' does not match FA naming convention - ignoring')
        log.write('')


log.write('\n*Info: Run Complete. ' + str(file_counter) + ' successful file pairs (Raw and L1) uploaded to HIEv')
log.write('\n------------  End: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '  ------------ \n')
