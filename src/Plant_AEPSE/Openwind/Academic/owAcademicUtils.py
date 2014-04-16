# owAcademicUtils.py
# 2014 02 21
# G Scott (NREL)


# Utility functions for working with OpenWind Academic version
#   - writePositionFile(): write new turbine location file
#   - wait for a new 'results.txt' file
#   - extract locations from file
#   - wait for notify file (IN)
#   - writeNotify(): write notify file (OUT)
#   - convertToLayout(): convert file to fused_wind layout


#   - class WTPosFile(WEFileIO) - read turbine positions from text file
#   - class WTWkbkFile(object)  - read turbine positions from OpenWind workbook


import sys, os, time
import numpy as np
sys.path.append('C:/SystemsEngr/openmdao-0.9.3/Lib/site-packages/pathtools-0.1.2-py2.7.egg')
sys.path.append('C:/SystemsEngr/openmdao-0.9.3/Lib/site-packages/watchdog-0.6.0-py2.7.egg')
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


import getworkbookvals as gwb


# FUSED-Wind imports


from we_file_io import WEFileIO


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
        #print "Detected modification! {:} {:}".format(event.src_path, event.event_type)
        #if event.src_path.endswith('notifyML.txt'):
        #if event.src_path.endswith(self.watchFile):
        if os.path.basename(event.src_path) == os.path.basename(self.watchFile):
            if self.debug:
                sys.stderr.write('Detected modified {:} file'.format(self.watchFile))
                sys.stderr.write('  Modtime {:} '.format(time.asctime(time.localtime(os.path.getmtime(event.src_path)))))
            self.observer.stop()
            
            # read results.txt
            
            if os.path.basename(event.src_path) == 'results.txt':
                try:
                    fh = open(event.src_path, 'r')
                except:
                    sys.stderr.write("MyNotifyMLHandler: Can't open '{:}'\n".format(event.src_path))
                    return None
                    
                line = fh.readline().strip()
                f = line.split()
                nturb = int(f[0])
                netEnergy = float(f[3])
                if self.debug:
                    sys.stderr.write('{:} turbines - {:.1f} kWh\n'.format(nturb,netEnergy))
                fh.close()
                
                if self.callback is not None:
                    self.callback(netEnergy)
                    
                return netEnergy
        
        else:
            sys.stderr.write('Ignoring change to {:}\n'.format(event.src_path))    
        
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
    event_handler = MyNotifyMLHandler(observer, watchFile, callback=callback, debug=True)
    observer.schedule(event_handler, path=path, recursive=False)
    observer.start()


    if debug:
        sys.stderr.write('\nwaitForNotify: waiting for {:}\n  Hit Cntl-C to break\n'.format(watchFile))
    
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
        
    ofname = 'positions.txt'
    if path is not None:
        ofname = '/'.join([path,ofname])
    try:
        ofh = open(ofname,'w')
    except:
        sys.stderr.write('\n*** ERROR in writePositionFile: opening {:} for writing\n'.format(ofname))
        return 0
    
    nt = len(wt_positions)
    if debug:
        sys.stderr.write('writePositionFile: {:} Nturb {:}\n\n'.format(ofname,nt))
    
    for i in range(nt):
        ofh.write('{:9.1f}\t{:10.1f}\n'.format(wt_positions[i][0],wt_positions[i][1]))
        if debug:
            sys.stderr.write('writePositionFile: {:9.1f}\t{:10.1f}\n'.format(wt_positions[i][0],wt_positions[i][1]))
    ofh.close()
    return 1
    
#--------------
    
def writeNotify(path=None, debug=False):
    ''' write 'notifyOW.txt' to let OW know that 'positions.txt' is ready '''


    ofname = 'notifyOW.txt'
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
    
def convertToLayout(fname='results.txt'):
    # read/parse OpenWind optimization output file
      
    try:
        fh = open(fname,'r')
    except:
        sys.stderr.write('\n*** ERROR in convertToLayout: opening {:} for writing\n'.format(fname))
        return 0
    
    fh.close()
    return 1
    
#--------------
    
def parseACresults(fname='results.txt'):
    # read/parse OpenWind optimization output file
    # returns:
    #   netEnergy : scalar value in GWh
    #   netNRGturb[] : net energy by turbine
    #   grossNRGturb[] : gross energy by turbine
      
    try:
        fh = open(fname,'r')
    except:
        sys.stderr.write('\n*** ERROR in parseACresults: opening {:} for writing\n'.format(fname))
        return None, None, None
    
    line = fh.readline()
    f = line.strip().split()
    nturb = int(f[0])
    netEnergy = float(f[3])
    
    netNRG   = [None for i in range(nturb)]
    grossNRG = [None for i in range(nturb)]
    for i in range(nturb):
        f = fh.readline().split()
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
    
    def _read(self, debug=True):
        self.xy = np.loadtxt(self.filename, comments='#')
        if debug:
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
    def __init__(self, wkbk=None, owexe=None):
        self.wkbk = wkbk
        self.owexe = owexe
        
    def _read(self, debug=True):
        self.xy = np.array(gwb.getTurbPos(self.wkbk, self.owexe, delFiles=True))
        
        if debug:
            sys.stderr.write('WTWkbkFile: read array {:} from {:}\n'.format(self.xy.shape, self.wkbk))
            for i in range(self.xy.shape[0]):
                for j in range(self.xy.shape[1]):
                    sys.stderr.write('{:.1f} '.format(self.xy[i][j]))
                sys.stderr.write('\n')
            
#---------------------------------------------


def main():
    # test
    
    wtp = WTPosFile(filename='positions.txt')
    wt = wtp.read()
    
    exit()
    
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
    
    waitForNotify(debug=True)
    
    pass


    
#---------------------------------------------------


if __name__ == "__main__":


    main()

