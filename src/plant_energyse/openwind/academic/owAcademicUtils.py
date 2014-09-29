# owAcademicUtils.py
# 2014 02 21
# G Scott (NREL)

# Utility functions for working with OpenWind Academic version
#   - writePositionFile(): write new turbine location file
#   - waitForNotify(watchFile='results.txt'): wait for a new 'results.txt' file
#   - writeNotify(): write notify file (OUT)
#   - parseACresults(): read/parse OpenWind optimization output file

#   - class MyNotifyMLHandler(FileSystemEventHandler) - watch for changes in file
#   - class WTPosFile(WEFileIO) - read turbine positions from text file
#   - class WTWkbkFile(object)  - read turbine positions from OpenWind workbook

import sys, os, time
import numpy as np
sys.path.append('D:/SystemsEngr/openmdao-0.9.3/Lib/site-packages/pathtools-0.1.2-py2.7.egg')
sys.path.append('D:/SystemsEngr/openmdao-0.9.3/Lib/site-packages/watchdog-0.6.0-py2.7.egg')
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import openwind.getworkbookvals as gwb

# FUSED-Wind imports

from fusedwind.plant_flow.py4we.we_file_io import WEFileIO

#---------------------------------------------

# Use watchdog to detect new 'notifyML.txt' file because
#   openMDAO uses watchdog for various things and it's installed already

# code based on:
#   http://stackoverflow.com/questions/18599339/python-watchdog-monitoring-file-for-changes

# OpenWind sometimes writes 'result.txt' but no 'notifyML.txt', so we need to be able to watch for that too

class MyNotifyMLHandler(FileSystemEventHandler):
    # watch for changes in watchFile
    #   (on_creation not needed, since modification includes creation)
    
    def __init__(self, observer, watchFile, callback=None, debug=False):
        self.observer = observer
        self.watchFile = watchFile
        self.debug = debug
        self.callback = callback
        
    def on_modified(self, event):
        print event.src_path
        if os.path.basename(event.src_path) == os.path.basename(self.watchFile):
            if self.debug:
                sys.stderr.write('on_modified: Detected modified {:} file\n'.format(self.watchFile))
                sys.stderr.write('  Modtime {:} \n'.format(time.asctime(time.localtime(os.path.getmtime(event.src_path)))))
            self.observer.stop()
            
            # read results.txt (if that's what we're waiting for) and return netEnergy
            # 2014 07 16 : file name is not always 'results.txt', so let's open the file and see if it makes sense
            
            try:
                fh = open(event.src_path, 'r')
            except:
                sys.stderr.write("MyNotifyMLHandler: Can't open '{:}'\n".format(event.src_path))
                return None
            
            try:    
                line = fh.readline().strip()
                f = line.split()
                nturb = int(f[0])
                netEnergy = float(f[3])
                if self.debug:
                    sys.stderr.write('{:} : {:} turbines - {:.1f} kWh\n'.format(os.path.basename(event.src_path),nturb,netEnergy))
                fh.close()
                
                if self.callback is not None:
                    self.callback(netEnergy)
                    
                return netEnergy
            except:
                sys.stderr.write('\n*** File {:} does not appear to be an OpenWind results file\n'.format(event.src_path))
                return None
        else:
            if self.debug:
                #sys.stderr.write('Ignoring change to {:}\n'.format(event.src_path))
                pass    
        
        return None     
            
    #def on_created(self, event):
    #    print "Detected creation! {:} {:}".format(event.src_path, event.event_type)
    #    if event.src_path.endswith('notifyML.txt'):
    #        print 'Found new notifyML.txt file!'
    #
    #def on_deleted(self, event):
    #    print "Detected deletion! {:} {:}".format(event.src_path, event.event_type)
    #    if event.src_path.endswith('notifyML.txt'):
    #        print 'Deleted notifyML.txt file!'

def waitForNotify(watchFile='notifyML.txt', path='.', callback=None, debug=False):
    ''' wait for Openwind to write 'notifyML.txt' (or other watchFile)
    
        2014 04 10: OW doesn't write notifyML.txt, so usually we watch for 'results.txt'
                  : added path argument so we can watch folder that contains workbook
    '''
    
    observer = Observer()
    event_handler = MyNotifyMLHandler(observer, watchFile, callback=callback, debug=debug)
    observer.schedule(event_handler, path=path, recursive=False)
    observer.start()

    if debug:
        sys.stderr.write('\nwaitForNotify: waiting for {:} in {:}\n  Hit Cntl-C to break\n'.format(watchFile, path))
    
    # What was the purpose of this loop in example code? Works fine without it
    #try:
    #    while True:
    #        time.sleep(1)
    #except KeyboardInterrupt:
    #    observer.stop()
    observer.join()

#--------------
    
def writePositionFile(wt_positions, debug=False, path=None):
    ''' write tab-delimited turbine location file 'positions.txt'
        wt_positions[n][2] is a 2-D array of X and Y coordinates
          (could be the wt_positions array from a GenericWindFarmTurbineLayout object
        coordinates should be in UTM meters '''
        
    ofname = 'positions.txt' # OpenWind looks for this exact name
    if path is not None:
        ofname = '/'.join([path,ofname])
    try:
        ofh = open(ofname,'w')
    except:
        sys.stderr.write('\n*** ERROR in writePositionFile: opening {:} for writing\n'.format(ofname))
        return 0
    
    nt = len(wt_positions)
    if nt == 0:
        sys.stderr.write('\n*** WARNING: calling writePositionFile() with zero-length wt_positions\n\n')
    if debug:
        sys.stderr.write('writePositionFile: {:} Nturb {:}\n'.format(ofname,nt))
    
    for i in range(nt):
        ofh.write('{:9.1f}\t{:10.1f}\n'.format(wt_positions[i][0],wt_positions[i][1]))
        if debug:
            sys.stderr.write('  wPF: {:} {:9.1f}\t{:10.1f}\n'.format(i+1,wt_positions[i][0],wt_positions[i][1]))
    ofh.close()
    return 1
    
#--------------
    
def logPositions(wt_positions, ofname=None):
    ''' append a line containing x-y coordinate pairs for all turbines to file named in 'ofname'
        similar to writePositionFile(), but keeps a permanent record of positions
        wt_positions[n][2] is a 2-D array of X and Y coordinates
          (could be the wt_positions array from a GenericWindFarmTurbineLayout object
        coordinates should be in UTM meters '''
        
    if ofname is None:
        sys.stderr.write('\n*** ERROR in logPositions: ofname not specified\n')
        return 0
    try:
        ofh = open(ofname,'a')
    except:
        sys.stderr.write('\n*** ERROR in logPositions: opening {:} for appending\n'.format(ofname))
        return 0
    
    nt = len(wt_positions)
    if nt == 0:
        sys.stderr.write('\n*** WARNING: calling logPositions() with zero-length wt_positions\n\n')
    
    for i in range(nt):
        ofh.write('{:9.1f}\t{:10.1f}\t'.format(wt_positions[i][0],wt_positions[i][1]))
    ofh.write('\n')
    ofh.close()
    return 1
    
#--------------
    
def writeNotify(path=None, debug=False):
    ''' write 'notifyOW.txt' to let OW know that 'positions.txt' is ready '''

    ofname = 'notifyOW.txt' # OpenWind looks for this exact name
    if path is not None:
        ofname = '/'.join([path,ofname])
    try:
        # opening a file with 'w' empties any existing file or creates a new empty file
        ofh = open(ofname,'w')
        ofh.close()
    except:
        sys.stderr.write('\n*** ERROR in writeNotify: opening or writing {:}\n'.format(ofname))
        return 0
    if debug:
        sys.stderr.write('writeNotify: {:}\n'.format(ofname))
    return 1
    
#--------------
    
def parseACresults(fname='results.txt', debug=False):
    # read/parse OpenWind optimization output file
    # returns:
    #   netEnergy : scalar value in kWh
    #   netNRGturb[] : net energy by turbine
    #   grossNRGturb[] : gross energy by turbine
    # debug=True : dumps contents of fname to STDOUT
      
    try:
        fh = open(fname,'r')
    except:
        sys.stderr.write('\n*** ERROR in parseACresults: opening {:} for writing\n'.format(fname))
        return None, None, None
    
    line = fh.readline().strip()
    if debug:
        print 'pACr :', line
        
    f = line.split()
    nturb = int(f[0])
    netEnergy = float(f[3])
    
    netNRG   = [None for i in range(nturb)]
    grossNRG = [None for i in range(nturb)]
    for i in range(nturb):
        line = fh.readline().strip()
        if debug:
            print 'pACr :', line
        f = line.split()
        netNRG[i] = float(f[0])
        grossNRG[i] = float(f[1])
    
    fh.close()
    return netEnergy, netNRG, grossNRG

# Typical contents of results.txt:    
#2	turbines	NetEnergy=	45486517.625150	currentNet	currentGross	bestNet
#22726427.094659425000	24604810.142472614000	22726427.094659425000
#22760090.530491002000	24633894.805187557000	22760090.530491002000

#---------------------------------------------

class WTPosFile(WEFileIO):
    ''' Read turbine positions from 'positions.txt' or other text file 
          - positions are saved in self.xy (a NumPy ndarray)
        WEFileIO calls _read on creation, but can be called when file changes
    '''
    
    def __init__(self, filename=None, debug=False):
        super(WTPosFile, self).__init__()
        self.debug = debug
        self.filename = filename
        
        self._read()
        
    def _read(self):
        self.xy = np.loadtxt(self.filename, comments='#')
        if self.debug:
            sys.stderr.write('WTPosFile: read array {:} from {:}\n'.format(self.xy.shape, self.filename))
            for i in range(self.xy.shape[0]):
                for j in range(self.xy.shape[1]):
                    sys.stderr.write('{:.1f} '.format(self.xy[i][j]))
                sys.stderr.write('\n')
            
#---------------------------------------------

class WTWkbkFile(object):
    ''' Read turbine positions from OpenWind workbook 
          - positions are saved in self.xy (a NumPy ndarray)
          - uses getworkbookvals::getTurbPos() which calls OpenWind
    '''
    def __init__(self, wkbk=None, owexe=None, debug=False):
        self.wkbk = wkbk
        self.owexe = owexe
        self.debug = debug
        
        self._read()
        
    def _read(self):
        self.xy = np.array(gwb.getTurbPos(self.wkbk, self.owexe, delFiles=True))
        
        if self.debug:
            sys.stderr.write('WTWkbkFile: read array {:} from {:}\n'.format(self.xy.shape, self.wkbk))
            for i in range(self.xy.shape[0]):
                for j in range(self.xy.shape[1]):
                    sys.stderr.write('{:.1f} '.format(self.xy[i][j]))
                sys.stderr.write('\n')
            
#---------------------------------------------

def main():
    # test
    
    # delete notifyML.txt
    # start watchdog Observer
    # tell user to write notifyML.txt manually
    # see if watchdog finds it
    
    # (example uses approx coords of VOWTAP project - UTM 18N)
    nturb = 20
    x = np.random.random_integers( 457300,  high=470600, size=nturb)
    y = np.random.random_integers(4077719, high=4090719, size=nturb)
    wt_positions = np.transpose(np.array([x,y]))
    writePositionFile(wt_positions)
    sys.stderr.write('Should have written positions.txt\n')
    
    writeNotify()
    sys.stderr.write('Should have created empty owNotify.txt\n')
    
    sys.stderr.write('\nTesting waitForNotify\n')
    sys.stderr.write("*** When 'Enter Cntl-C to break' message appears,\n enter 'touch notifyML.txt' from another command shell\n")
    waitForNotify(debug=True)
    
    wtp = WTPosFile(filename='positions.txt')
    wt = wtp.read()
    
#---------------------------------------------------

if __name__ == "__main__":

    main()
