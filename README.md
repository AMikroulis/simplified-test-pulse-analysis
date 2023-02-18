If you are running this for the first time, run the <i>check packages.py</i> first, to check if any packages are missing.

The <i>analysis.py</i> will open the main script to process the HEKA/abf files.

<br/><br/>
Requirements
<br/>
<i>Needs the voltage command trace as well as the current trace to be saved in the files.</i>
<br/>
For ABF files:<br/>
            A folder with .abf files.

For HEKA files:<br/>
            A folder with .dat files, and their corresponding .inf files
                        (you get the .inf file from PatchMaster Replay menu)

<br/><br/>
Operation <br/>

0. select the file type (HEKA/Axon)
1. click Scan
2. select the folder with the recordings
3. switch to the 2nd tab (test pulse)
4. select the protocol name for the test pulse and the channel <u>for the current trace</u>
5. check the box for TP on the top right
6. add a log note or custom name for the results folder if needed (boxes on the right side)
7. click run and confirm the folder with the data files
8. wait (it will say “finished” when it’s done).

Results are placed in the same folder with the recordings, as:
a HTML overview file,
a CSV file with the tabulated results,
a folder with results and intermediate processing step files for each recording.


Copyright 2018-2022 Apostolos Mikroulis, Eliška Waloschková.

This software is provided under the zlib license.
