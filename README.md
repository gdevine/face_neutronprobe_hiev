### FACE Neutron Probe data to HIEv

Python script to convert Raw Neutron Probe data to level 1 CSV format and upload to HIEv. This script calls out to an R script provided by Teresa Gimeno (teresa.gimeno@bc3research.org). 

__Implementation__

Data (that should be named FADDMMYY.txt or FADDMMYY.TXT by default) to be uploaded into HIEv should be placed in a folder named 'Data' - the path of which can be set in the main script, **upload_np.py**.
The script needs to be able to access a HIEv API key stored in a credentials.py file at the top level.

__Prerequisites__

This routine needs the HIEvPy library installed, e.g through pip. This library can be found at https://test.pypi.org/project/hievpy/
     
