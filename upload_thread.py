import sys
import glob
from PyQt4 import QtGui, QtCore
import random
import PIL
from PIL import Image, ImageQt
from PyQt4.QtCore import QString
import serial
import math
import os
import time
import threading

"""
Thread to perform upload of data via USB to the chip.
"""
class WorkThread(QtCore.QThread):
    """
    A Thread which scans through the available COM ports
    until it locates the required USB and then
    uploads the data to the chip.
    """
    
    def __init__(self, parent, data):
        """
        __init__(self, parent, data) -> None
        Initialises this thread.

        Key arguments:
        parent -- the parent of this thread
        data -- the data to upload assumed to be a list with parameters:
               - length: 11520
               - containing: chars only

        Returns nothing.
        """
        QtCore.QThread.__init__(self)
        #set the signal to be string uploading
        self.signal = QtCore.SIGNAL("uploading")
        #initialise the data for this array
        self.data = data

    def run(self):
        """
        run(self) -> None
        Runs the given thread. Searches through available COM ports
        to find those that are active and then attempts a handshake with
        each open port to find our device.

        Does not return.
        """
        #Look at all USB ports, find our port with a handshake
        #our_device string
        our_device = '' 
        com_string = 'COM'
        #list of ports to test
        to_test = []

        #create the list of ports to test
        for i in range(256):
            #append to_test with all combinations of COM + number,
            #i.e. COM1,COM2
            to_test.append(com_string+str(i))

        #we are 2% done, send a signal
        self.emit(QtCore.SIGNAL("uploading"), 2)
            
        #a list of available ports
        available_ports = []

        to_test = []
        for i in range(255, -1, -1):
            to_test.append(com_string + str(i))

        for test_port in to_test:
            try:
                #just test if we can open it
                port = serial.Serial(test_port)
                port.close()
                #if we are here, it could be opened
                available_ports.append(test_port)
            except Exception:
                #not an available port, so pass
                pass
        #we are 5% done, send a signal
        self.emit(QtCore.SIGNAL("uploading"), 4)

        
        #look at all the available ports to see if it is the usb port
        for port in available_ports:
            #test each port in available_ports to see if it's our device
            #changed timeout to 0.25
            port_test = serial.Serial(port, 19200, timeout = 0.2)

            # perform handshake (send a 'b' and see if the response
            # is also a 'b')
            port_test.write('b')

            #read call blocks for timeout (0.2 seconds), so if
            # no response in that time, move onto next port
            val = port_test.read(1)
            #if we read back a 'b', then it is the POV chip
            if val == 'b':
                #close the port we were using
                port_test.close()
                #set our_device to said port
                our_device = port
                break
            else:
                #it was not our port, close
                port_test.close()
                
        self.emit(QtCore.SIGNAL("uploading"), 8)

        #our_device is now the comPort we want

        #try to write data to device
        try:
            mark = 0
            ser = serial.Serial(our_device, 19200,
                                        timeout=1)

            #loop through all data and send out page by page
            j = 0
            num_sent = 0
            while j < len(self.data)/128:
                i = 0
                while i < 128:
                    ser.write(self.data[i+j*128])
                    
                    i += 1
                #read back byte to indicate success
                read = ser.read(1)
                #sleep to allow buffer to clear
                time.sleep(0.05)
                j += 1
                self.emit(QtCore.SIGNAL("uploading"), j+8)

            final = ser.read(1)
            ser.close()
            
        except Exception as e:
            #emit -1 on error
            self.emit(QtCore.SIGNAL("uploading"), -1)
        #kill the thread (whether successful or not)
        self.terminate()
        
