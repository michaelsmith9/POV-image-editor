#Imports used for this code
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
import upload_thread
from upload_thread import WorkThread

#added for stuff
import bitmaps
from bitmaps import *

#author: Michael Smith

"""
The Model class.
"""
class Model(object):
    """
    A class to perform tha processing required for the MVC pattern:
    1. Loading and parsing files and generating the required
        QPixmap from these files.
    2. Uploading data to the chip though the use of a WorkThread
    """
    
    def __init__(self, parent):
        """
        Model.__init__(self, parent) -> None
        Initialises the model

        Keyword arguments:
        parent -- the parent object for this class instance

        Returns nothing.
        """
        # set parent to be the given parent
        self.parent = parent
        # set width and height to be 0 
        self.width = 0
        self.height = 0
        # he image to return, when requested to the controller
        self.image = None
        #list of names of bitmaps
        self.bitmaps = ['zero', 'one', 'two', 'three', 'four', 'five',
                        'six', 'seven', 'eight', 'nine',
                        'metre', 'dash', 'seconds']
                        
    def isAscii(self, path):
        """
        isAscii(self, path) -> bool
        Parses the file located at path to determine if it is an ascii
        file.

        Keyword arguments:
        path -- the absolute path to the chosen file

        Returns a boolean to indicated if the given file at path is an
        ascii file. True if the file header is P1, P2 or P3.
        """
        try:
            given_file = open(path, 'r')
            first_line = given_file.readline()
            first_line = first_line.strip() #strip the newline char
            given_file.close()
            if first_line == 'P1' or first_line == 'P2' or first_line == 'P3':
                return True
            else:
                return  False
        except Exception:
            return False

    def getPixmap(self, path):
        """
        getPixmap(self, path) -> QPixmap
        Attempts to parse the file at path and generate a QPixmap from it.

        Key arguments:
        path -- the absolute path to the chosen file

        Returns the QPixmap located at path. 
        """
        # test if it is an ascii file
        if self.isAscii(path) == False:
            
            try:
                # will fail if not image
                im = Image.open(str(path))
                im.close()
                #attempt to open it as a binary file
                pixmap = QtGui.QPixmap(str(path))
                self.image = pixmap.toImage()
                self.width = pixmap.width()
                self.height = pixmap.height()
                return pixmap
            
            except IOError as e:
                #binary file failed, throw error
                message_box = QtGui.QMessageBox()
                message_box.setText('Bad image!')
                message_box.exec_()
                return None
            
        else:
            #it is an ascii file, so open it has one 
            pixmap = self.openAsciiFile(path)
            
            if pixmap == None:
                message_box = QtGui.QMessageBox()
                message_box.setText('Bad image!')
                message_box.exec_()
                return None
            
            else:
                #return the pixmap
                return pixmap
        
    def openAsciiFile(self, path):
        """
        openFile(self, path) -> QPixmap
        Determines the type of ascii file at the location given by path and
        calls the appropriate parser method.

        Keyword arguments:
        path -- the absolute path to the chosen file

        Returns the pixmap generated from the given file or None if file
        parsing fails
        """
        #attempt to open the file
        try:
            given_file = open(path, 'r')
        except Exception:
            return None
        # read first line in to determine file type
        file_type = given_file.readline()
        type_test = file_type.strip()

        #P1 file parser
        if type_test == 'P1':
            pixmap = self.p1Parser(given_file)
            return pixmap

        #P2 file parser
        if type_test == 'P2':
            pixmap = self.p2Parser(given_file)
            return pixmap

        #P3 file parser
        if type_test == 'P3':
            pixmap = self.p3Parser(given_file)
            return pixmap
        given_file.close()

    def p1Parser(self, f):
        """
        p1Parser(self, f) -> QPixmap
        Parses the given file (f) as if it was a p1 type.

        Keyword arguments:
        f -- a file that is already opened and assumed to have had its first
        line read

        Returns the QPixmap generated by parsing the file.
        """
        #get dimensions
        dimensionsNotSplit = f.readline()
        #split line to get width and height
        dimensions = dimensionsNotSplit.split()
        width = int(dimensions[0])
        height = int(dimensions[1])
        
        #pixmap now has dimensions of image
        pixmap = QtGui.QPixmap(width, height)
        #use painter to put pixels on pixmap
        painter = QtGui.QPainter(pixmap)
        
        #loop over all values in file
        j = 0
        nextLine = f.readline()
        a = 0
        while nextLine != '':
            array = list(nextLine.strip())
            i = 0
            
            #take value in text file and set corresponding pixel
            while i < len(array):
                
                #if it's zero, then its black
                if array[i] == '0':
                    painter.setPen(QtGui.QColor(255,255,255,255))
                    painter.drawPoint(i+a, j)
                else:
                    painter.setPen(QtGui.QColor(0,0,0,255))
                    painter.drawPoint(i+a,j)
                i += 1
                
            #increment a (offset) by length of array
            a += len(array)
            #if a == width (we've added a row's worth of pixels), reset a
            # and increment j
            if a == width:
                a = 0
                j += 1
            nextLine = f.readline()
            #global width and height re-assignment
            
        self.width = width
        self.height = height
        
        return pixmap
        
    def p2Parser(self, f):
        """
        p2Parser(self, f) -> QPixmap
        Parses the file (f) assuming it is a P2 type file.

        Keyword arguments:
        f -- the file to be parsed (assumes that the first line as already
            been read [the header line])

        Returns the QPixmap generated
        """
        dimensionsNotSplit = f.readline()
        #split line to get width and height
        dimensions = dimensionsNotSplit.split()
        width = int(dimensions[0])
        height = int(dimensions[1])
        
        #maxval is white, 0 is black
        maxval = int(f.readline().strip())
        multiplier = 255./maxval
        
        pixmap = QtGui.QPixmap(width, height)
        
        painter = QtGui.QPainter(pixmap)
        j=0
        nextLine = f.readline()
        a = 0
        while nextLine != '':
            array = list(nextLine.split())
            i=0
            
            while i < len(array):
                #get the p2 (pgm) color
                color = self.getColorP2(int(array[i]), multiplier)
                painter.setPen(color)
                painter.drawPoint(i+a, j)
                i += 1
                
            a += len(array)
            if a == width:
                a = 0
                j += 1
                
            nextLine = f.readline()
            
        self.width = width
        self.height = height
        
        return pixmap
        
    def p3Parser(self, f):
        """
        (p3Parser(self, f) -> QPixmap
        Parses the file (f) assuming it is a P3 type.

        Keyword aguments:
        f -- the file to be parsed (assumes first line already read)

        Returns the QPixmap generated by parsing the file
        """
        dimensionsNotSplit = f.readline()
        #split line to get width and height
        dimensions = dimensionsNotSplit.split()
        width = int(dimensions[0])
        height = int(dimensions[1])
        
        #maxval is white, 0 is black
        maxval = int(f.readline().strip())
        multiplier = 255./maxval
        pixmap = QtGui.QPixmap(width, height)
        pixmap.fill(QtGui.QColor(0,0,0))
        
        painter = QtGui.QPainter(pixmap)
        j=0
        nextLine = f.readline()

        #throw away all commented lines
        while nextLine.startswith('#') == True:
            nextLine = f.readline()
            
        a = 0
        while nextLine != '':
            array = nextLine.split()
            i=0
            while i < (len(array)-2):
                #get the color, from 3 values
                color = self.getColorP3(array[i:i+3], multiplier)
                painter.setPen(color)
                painter.drawPoint(i/3+a, j)
                painter.drawPoint
                i += 3
            #/3 as colors in triplets
            a += len(array)/3
            if a == width:
                a = 0
                j += 1
            nextLine = f.readline()
        
        self.width = width
        self.height = height
        return pixmap

    def getColorP2(self, number, mult):
        """
        getColorP2(self, number, mult) -> QColor
        Returns a QColor suitable for a P2 (grayscale image) (i.e. R G B
        values are the same)

        Keyword arguments:
        number -- the number to determine the colour from
        mult -- the multiplier to set the max colour to

        Returns a QColor generated using the number and mult
        """
        value = int(number * int(mult))
        #set alpha to 255, and R,G,B to same as grayscale
        return QtGui.QColor(value, value, value, 255)

    def getColorP3(self, arr, mult):
        """
        getColorP3(self, arr, mult) -> QColor
        Returns a QColor suitable for a P3 (R G B) image.

        Keyword arguments:
        arr -- a list of three numbers indicating the R G B values to be set
            according to the mult
        mult -- the given mult to set the max R G B value to

        Returns a QColor generated using the arr and mult.
        """
        red = int(arr[0])*int(mult)
        green = int(arr[1])*int(mult)
        blue = int(arr[2])*int(mult)

        #return the QColor, set alpha to 255
        return QtGui.QColor(red, green, blue, 255)

    def getWidth(self):
        """
        getWidth(self) -> int
        Returns the width of the current loaded pixmap.
        """
        return self.width
    
    def getHeight(self):
        """
        getHeight(self) -> int
        Returns the height of the current loaded pixmap.
        """
        return self.height

    def getImage(self):
        """
        getImage(self) -> QImage
        Returns the QImage held by this instance of model.
        """
        return self.image

    def uploadData(self, data):
        """
        uploadData(self, data) -> WorkThread
        uploads the given data list using a WorkThread

        Keyword arguments:
        data -- a list of chars (value between 0 and 255). List length must
            be 11520. 

        Returns the WorkThread generated or None if error thrown (list length
        not 11520)
        """
        if len(data) != 11776:
            return None
        else:
            self.upload_thread = upload_thread.WorkThread(self, data)
            return self.upload_thread
        
    def generateData(self, image):
        """
        generateData(self, image)
        Generates a list of length 11520 containing chars (size one byte)
        each witha value between 0 and 255 representing the 8 bit colour
        value for the given pixel in image. Colours put into the list per
        column, first column first, second column next, and so on. For a given
        column, the pixel at the 'base' of the column (bottom side) is
        loaded first.

        Key arguments:
        image -- the QImage to generate data from.
        
        Returns a list of data guaranteed to be of length 11520 containing
        the 8 bit colour value for each pixel (in order) for the given image.
        Each entry is a char.
        """
        #the list in which to store the data
        data = []
        qsize = image.size()
        width = qsize.width()
        height = qsize.height()

        #go from 32 to 0 (not 0 to 32)
        i = 0
        j = height
        numAdded = 0

        #add in padding before and after rather than just after
        #the image
        space = 360 - width
        padleft = space/2
        if width%2 != 0:
            padright = space/2 + 1
        else:
            padright = space/2

        plcnt = 0
        while plcnt < padleft*32:
            data.append(chr(0))
            plcnt += 1
        
        # i increments each time until we reach the width
        # of the image
        while i < width:

            # j begins at height - 1 (in a 32 pixel image,
            # this is pixel 31) or the pixel furthest
            # away from the top left corner for a given
            # column
            j = height-1
            
            while j >= 0:
                #get the pixel at location (i, j)
                px = image.pixel(i, j)
                #get it's rgb tuple (r, g, b, alpha)
                value = QtGui.QColor(px).getRgb()
                #get the 8 bit colour (convert down)
                total = self.to255Colour(value)
                data.append(chr(total))
                j -= 1
                numAdded += 1
            i += 1
        #add padding on right if the
        #image is < 11520 pixels - padding is black

        prcnt = 0
        while prcnt < padright*32:
            data.append(chr(0))
            prcnt += 1
            
        #un comment the below code to add in numbers
        numberData = self.generateNumberList()
        for i in numberData:
            data.append(i)
            
        return data

    def to255Colour(self, value):
        """
        to255Colour(self, value) -> int
        Converts a tuple of the form (r, g, b, alpha) to a number
        between 0 and 255 representing a single 8 bit colour.

        Key arguments:
        value -- a typle of the form (r, g, b, alpha) where r, g, b are
            integers between 0 and 255 each in RGB form RRRGGGBB
        
        Returns a number between 0 and 255 representing the value of the
        tuple converted to 8 bit RGB.
        """
        # take the value (between 0 and 255) and divide by 36 to
        # get a value between 0 and 7 (bit pattern 000 to 111)
        # (conversion for RED and GREEN)
        red = value[0]/36
        green = value[1]/36
        # take the value (between 0 and 255) and divide by 85
        # to get a value between 0 and 3 (bit battern 00 to 11)
        # (conversion for BLUE)
        blue = value[2]/85

        # get total colour (between 0 and 255) by then converting
        # the individual red, green, and blue values and pushing
        # them up to the appropriate bits (i.e. blue takes bits
        # 3, 4, 5 in an 8 bit number so multiply by 2 to shift it
        # into the range
        redBit = red*2**5
        greenBit = green*2**2
        blueBit = blue
        total = redBit + greenBit + blueBit

        return total

    def generateNumberList(self):
        """
        generateNumberList(self) -> list
        Generates a list of chars (either 255 or 0) indicating a byte
        value.

        Returns a list of size 1144 bytes with values being chars
        of 0 or 255.
        """
        numberList = []
        #move through each bitmap to get right one
        #for each number/symbol
        for i in self.bitmaps:
            #go through all grid names
            value = eval(i)
            #add in reverse order
            #so add from bottom left of map to start with
            #going up each row and then across columns
            row = 10
            while row > -1:
                col = 0
                byte = 0
                while col < 8:
                    byte += int(value[row*8 + col])*2**(7-col)
                    col += 1
                numberList.append(chr(byte))
                row -= 1
            # pad with a 0b0000000 so that each bitmap is
            # represented by 12 bytes for easy flash storage
            numberList.append(chr(0))
            

        # pad numberList so even number of pages sent
        # one page is 128 bytes so we have added 13 chars of
        # size 12 bytes each (13 * 12 = 156 bytes) so we need
        # 100 more bytes to bring the bytes sent to an even
        # number of pages (2 pages)

        j = 0
        while j < 100:
            numberList.append(chr(0))
            j += 1
                    
        return numberList
        
        
