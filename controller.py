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
import model
from model import Model
import view
from view import View

"""
The controller class.
"""
class Controller(QtGui.QMainWindow):
    """
    A class to link the sub classes (View, Model) together and to control
    the overall logic of the program.
    """

    def __init__(self):
        """
        Controller.__init__(self) -> None.
        Initialises the controller.
        
        Does not return.
        """
        super(Controller, self).__init__()
        #the name for the file to load
        self.name = ''
        #the PIL image object
        self.im = ''
        #a pixmap, initially 360x32 and all white
        self.pixmap = QtGui.QPixmap(360, 32)

        #make pixmap initially black
        self.pixmap.fill(QtGui.QColor(0,0,0))
        
        #reset map is given by the pixmap, make a deep copy
        self.reset_map = self.pixmap.copy(QtCore.QRect(0,0,360,32))
        #image object is formed by pixmap
        self.image = self.pixmap.toImage()
        #data array to store pixmap pixel information for transmission
        self.data = []
        #width and height
        self.width = 360
        self.height = 32
        #initialise the GUI
        self.initGui()
        #initialise the model
        #self.model = Model(self)
        #we have not loaded an image
        self.loaded_image = False
        #the copy of the pixmap held by the controller map as a deep copy
        #never to be given to another class (as pixmaps are passed
        #by reference)
        self.controller_map = QtGui.QPixmap(self.pixmap)
        #initially not in POV mode
        self.in_POV = False
        self.thread_created = False

        #pos for moving
        self.current_pos = 0
        #text size
        self.text_size = 20

        #the model
        self.model = model.Model(self)

        self.text_font = 'Trebuchet MS'
        #self.text_font = 'WingDings'

    def initGui(self):
        """
        initGui(self) -> None.
        Initialises the GUI.
        
        Does not return.
        """
        #Create a status bar
        self.statusBar()
        
        #Set up QAction for each menuBar action
        new_image = QtGui.QAction('New', self)
        new_image.setShortcut('Ctrl+N')
        new_image.setStatusTip('Create a new Image')
        new_image.triggered.connect(self.newImage)
        
        open_image = QtGui.QAction('Load', self)
        open_image.setShortcut('Ctrl+O')
        open_image.setStatusTip('Open an Image')
        open_image.triggered.connect(self.openDialog)

        save_image = QtGui.QAction('Save', self)
        save_image.setShortcut('Ctrl+S')
        save_image.setStatusTip('Save an Image')
        save_image.triggered.connect(self.saveDialog)

        exit_program = QtGui.QAction('Exit', self)
        exit_program.setShortcut('Ctrl+Q')
        exit_program.setStatusTip('Quit the program')
        exit_program.triggered.connect(self.exitProgram)

        #set up QAction for each view action
        preview = QtGui.QAction('Preview', self)
        preview.setShortcut('Ctrl+P')
        preview.setStatusTip('Preview on Wheel')
        preview.triggered.connect(self.preview)

        image_view = QtGui.QAction('Image Mode', self)
        image_view.setShortcut('Ctrl+I')
        image_view.setStatusTip('Change to image mode')
        image_view.triggered.connect(self.imageView)

        #set up QAction for action menu
        upload = QtGui.QAction('Upload to chip', self)
        upload.setShortcut('Ctrl+U')
        upload.setStatusTip('Upload to chip')
        upload.triggered.connect(self.upload)
        
        menubar = self.menuBar()
        #add file_menu
        file_menu = menubar.addMenu('File')
        file_menu.addAction(new_image)
        file_menu.addAction(open_image)
        file_menu.addAction(save_image)
        file_menu.addAction(exit_program)
        #add edit_menu
        edit_menu =menubar.addMenu('View')
        edit_menu.addAction(preview)
        edit_menu.addAction(image_view)
        #add actionMenu
        action_menu = menubar.addMenu('Action')
        action_menu.addAction(upload)

        #initialise the mainwidget
        self.view = View(self, self.pixmap, self.width, self.height)

        self.setCentralWidget(self.view)
        self.setGeometry(100, 100, 600, 600)
        self.setWindowTitle('POV')
        self.show()

    def closeEvent(self, e):
        """
        cloaseEvent(self, e) -> None.
        Handles the close event. If the upload thread is running,
        this shuts it down.
        
        Does not return.
        """
        if self.thread_created == True:
            self.upload_thread.quit()
        sys.exit()

    def changeEvent(self, e):
        """
        changeEvent(self, e) -> None
        Captures a change event (i.e. WindowStateChange) and if
        not maximised, then does nothing, if maximised then it
        signals the view that the screen has been maximised.

        Key arguments:
        e -- the trigger event.

        Does not return.
        """
        if e.type() == QtCore.QEvent.WindowStateChange:
            if self.windowState()& QtCore.Qt.WindowMaximized:
                self.view.maximised()

    def exitProgram(self):
        """
        exitProgram(self) -> None
        Exits the program. Checks if the upload thread is running and
        kills it if it is.

        Does not return.
        """
        
        if self.thread_created == True:
            self.upload_thread.quit()
        sys.exit()

    def openDialog(self):
        """
        openDialog(self) -> None
        The user has requested to open a file, runs the open dialog process.

        Does not return.
        """
        self.view.nukeWidgets()
        # get path to file
        path = QtGui.QFileDialog.getOpenFileName(self, 'Load Image')
        self.view.removeImageInput()
        # no file selected
        if path == '':
            pass
        else:
            self.name = open(path, 'r')

            if self.name == '':
                pass
            else:
                #get the pixmap located at path
                self.pixmap = self.model.getPixmap(path)
                
                if self.pixmap != None:
                    # if it is not none then it is a valid pixmap
                    self.image = self.model.getImage()
                    self.width = self.model.getWidth()
                    self.height = self.model.getHeight()
                    self.reset_map = self.pixmap

                    #tell main_widget to update its pixmap
                    self.view.newPixmap(self.pixmap, self.width,
                                                    self.height)
                    self.loaded_image = True
                    #keep reset map to reset changes
                    self.reset_map = self.pixmap.copy(
                        QtCore.QRect(0,0,360,32))
                    #keep controller map
                    #controller map is a deep copy of the pixmap to
                    #prevent corruption of the map in the View
                    self.controller_map = QtGui.QPixmap(self.pixmap)
                    self.controller_map = self.pixmap.copy(
                        QtCore.QRect(0,0,360,32))
         
    def preview(self):
        """
        preview(self) -> None.
        Enters preview mode.
        
        Does not return.
        """
        self.in_POV = True
        self.image = self.controller_map.toImage()
        self.pixmap = QtGui.QPixmap(self.controller_map)
        self.view.generatePov(self.controller_map)
    
    def imageView(self):
        """
        imageView(self) -> None.
        Enters image mode.
        
        Does not return.
        """
        self.in_POV = False
        self.view.newPixmap(self.controller_map, self.width, self.height)

    def newImage(self):
        """
        newImage(self) -> None
        Handles the new_image QAction being triggered.

        Does not return.
        """
        self.view.setNewPixmap()
        
    def createNewImage(self, width):
        """
        createNewImage(self, width) -> None
        Creates a new image (pixmap on the view) using the given
        width and height.

        Key arguments:
        width -- the width of the map (between 0 and 361)

        Does not return
        """
        #create a new pixmap using the given dimension
        self.pixmap = QtGui.QPixmap(width, 32)
        #fill it with black
        self.pixmap.fill(QtGui.QColor(0,0,0))
        #set the reset map to a copy of this map
        self.reset_map = self.pixmap.copy(QtCore.QRect(0,0,width,32))
        #generate our image
        self.image = self.pixmap.toImage()
        #set the controller map to a deep copy of this pixmap
        self.controller_map = self.pixmap.copy(
            QtCore.QRect(0,0,width,32))
        self.width = width
        #request a new pixmap to be displayed in the view
        self.view.newPixmap(self.pixmap, self.width,
                                    self.height)
        #remove the input for a new image
        self.view.removeImageInput()

    def saveDialog(self):
        """
        saveDialog(self) -> None.
        Handles a click on the save_dialog QAction by saving the image.

        Does not return.
        """
        self.view.nukeWidgets()
        path = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        if path == '':
            pass
        else:
            #save file as PPM
            self.image = self.controller_map.toImage()
            self.image.save(path, "PPM")
        
    def pixelChange(self, x, y, clr):
        """
        pixelChange(self, x, y, clr) -> None
        Change the colour of a pixel at (x, y) in the controller pixmap to
        colour.

        Key parameters:
        x -- the x position of the pixel (0 to 359).
        y -- the y position of the pixel (0 to 31).
        clr -- the QColor of the pixel.

        Does not return.
        """
        painter = QtGui.QPainter(self.controller_map)
        painter.setPen(clr)
        painter.drawPoint(x,y)
        self.redraw()

    def updatePixel(self, y, x, colour):
        """
        pixelChange(self, y, x, clr) -> None
        Updates the colour of a pixel at the given (x, y) in the controller
        image using the given colour.

        Key parameters:
        x -- the x position of the pixel (0 to 359).
        y -- the y position of the pixel (0 to 31).
        clr -- the QColor of the pixel.

        Does not return.
        """
        self.image = self.controller_map.toImage()
        self.image.setPixel(x, y,colour.rgb())
        self.controller_map = QtGui.QPixmap.fromImage(self.image)

    def addLine(self, sx, sy, ex, ey, clr):
        """
        addLine(self, sx, sy, ex, ey, clr) -> None.
        Draws a line between the two sets of points (sx, sy)
        and (ex, ey) using clr.

        Key arguments:
        sx -- the starting x coordinate (0 to 359).
        sy -- the starting y coordinate (0 to 31).
        ex -- the ending x coordinate (0 to 359).
        ey -- the ending y coordinate (0 to 31).
        clr -- the QColour to draw the line.
        
        Does not return.
        """
        painter = QtGui.QPainter(self.controller_map)
        painter.setPen(clr)
        painter.drawLine(sx, sy, ex, ey)
        self.redraw()


    def povLineDraw(self, sr, stheta, er, etheta, clr):
        """
        povLineDraw(self, sr, stheta, er, etheta, clr) -> None
        Draws a line in POV mode between thet points given by (sr, stheta)
        and (er, etheta) using the QColour clr.

        Key arguments:
        sr -- the starting radius (between 22 and 54).
        stheta -- the starting angle (between -180 and 180).
        er -- the ending radius (between 22 and 54).
        etheta -- the ending angle (between -180 and 180).
        
        Does not return.
        """
        sr = sr - 22
        er = er  - 22
        stheta = stheta 
        etheta = etheta
        
        painter = QtGui.QPainter(self.controller_map)
        painter.setPen(clr)

        # check if bounds mean we wrapped around the 0 degree line
        if stheta < 180 and stheta > 90:
            stheta -= 90
        else:
            stheta += 270
        if etheta < 180 and etheta > 90:
            etheta -= 90
        else:
            etheta += 270
        
        if ((stheta >= 0 and stheta < 90) or
            (etheta >= 0 and etheta < 90)
            ) and ((etheta <= 360 and etheta > 270) or
                 (stheta <= 360 and stheta > 270)):
                painter.drawLine(math.floor(stheta), 31 - math.floor(sr),
                        math.floor(0), 31 - math.floor(er))
                painter.drawLine(math.floor(etheta), 31 - math.floor(sr),
                                 math.floor(360), 31 - math.floor(er))

        else:
            painter.drawLine(math.floor(stheta), 31 - math.floor(sr),
                             math.floor(etheta), 31 - math.floor(er))
        self.preview()

    def areaAdd(self, sx, sy, ex, ey, clr):
        """
        areaAdd(self, sx, ey, ex, ey, clr) -> None.
        Adds an area (or block draw) between the coordinates given
        by (sx, sy) and (ex, ey) using the QColor clr.

        Key arguments:
        sx -- the starting x coordinate (0 to 359).
        sy -- the starting y coordinate (0 to 31).
        ex -- the ending x coordinate (0 to 359).
        ey -- the ending y coordinate (0 to 31).
        clr -- the QColour to draw the line.
        
        Does not return.
        """
        painter = QtGui.QPainter(self.controller_map)
        painter.fillRect(sx, sy, (ex-sx), (ey-sy), QtGui.QBrush(clr))
        self.redraw()
        
    def newPixmap(self):
        """
        newPixmap(self) -> None.
        Resets the map to the reset_map (held by the controller) and
        sends this map to the view to be displayed.

        Does not return.
        """
        self.pixmap = self.reset_map.copy(QtCore.QRect(0,0,360,32))
        self.view.newPixmap(self.pixmap, self.width, self.height)
        self.controller_map = self.reset_map.copy(QtCore.QRect(0,0,360,32))

    def textSizeChange(self, value):
        """
        textSizeChange(self, value) -> None.
        Alters the size of the displayed text in the GUI.

        Key arguments:
        value -- the value to change the text too (between 0 and 99)
        
        Does not return.
        """
        clr = self.stringclr
        string = self.string
        self.controller_map = self.before_text.copy(
            QtCore.QRect(0, 0, self.width, self.height))
        
        #set the text size according to value
        if value < 15:
            size = 8
        elif value < 30:
            size = 10
        elif value < 40:
            size = 12
        elif value < 50:
            size = 14
        elif value < 70:
            size = 16
        elif value < 90:
            size = 18
        else:
            size = 20
        self.text_size = size
        self.current_pos = 0

        font = QtGui.QFont(self.text_font, size)
        font.setBold(True)
        
        if self.in_POV == False:
            #draw Text
            # set our painter 
            painter = QtGui.QPainter(self.controller_map)
            painter.setPen(clr)
            painter.setFont(font)

            # draw the text
            rect = painter.drawText(QtCore.QRect(0, 0, self.width,
                                                 self.height), 0, string)
            painter.drawText(0, 0, self.width, self.height, 0, string)
            
            # set the text width to the rect width
            self.text_width = rect.width()
            
            self.redraw()
            
        else:
            #if in POV then draw text and generate POV
            painter = QtGui.QPainter(self.controller_map)
            painter.setPen(clr)
            painter.setFont(font)
            rect = painter.drawText(QtCore.QRect(0, 0,
                                                 self.width, self.height),
                                    0, string)
            painter.drawText(0, 0, self.width, self.height, 0, string)
            self.text_width = rect.width()
            self.preview()

    def requestResize(self):
        """
        requestResize(self) -> None
        Receives a resize request, resizes window to trigger
        resizeEvent.

        Does not return.
        """
        size = self.size()
        self.resize(size.width() + 10, size.height() + 10)
        self.resize(size.width(), size.height())

    def textMoveRight(self):
        """
        textMoveRight(self) -> None.
        Attempts to move the text string right, if successful it
        updates the pixmap and tells the view.

        Does not return.
        """
        clr = self.stringclr
        string = self.string
        
        size = self.text_size
        self.controller_map = self.before_text.copy(
            QtCore.QRect(0,0,self.width, self.height))

        #take the current size
        #move right
        self.current_pos += 10
        #max shift
        limit = 30

        font = QtGui.QFont(self.text_font, size)
        font.setBold(True)

        #self.text_width set
        if self.current_pos > (self.width - self.text_width):
            self.current_pos -= 10
        
        #if self.current_pos > (360 - len(string))
        if self.in_POV == False:
            #draw Text
            painter = QtGui.QPainter(self.controller_map)
            painter.setPen(clr)
            #painter.setFont(QtGui.QFont(self.text_font, size))
            painter.setFont(font)
            painter.drawText(QtCore.QRectF(self.current_pos,
                                            0, self.width, self.height), string)
            self.redraw()
        else:
            #if in POV then draw text and generate POV
            painter = QtGui.QPainter(self.controller_map)
            painter.setPen(clr)
            #painter.setFont(QtGui.QFont(self.text_font, size))
            painter.setFont(font)
            painter.drawText(QtCore.QRectF(self.current_pos,
                                            0, self.width, self.height), string)
            self.preview()

    def textMoveLeft(self):
        """
        textMoveLeft(self) -> None.
        Attempts to move the text string left, if successful,
        it updates the pixmap and tells the view.

        Does not return.
        """
        clr = self.stringclr
        string = self.string
        self.controller_map = self.before_text.copy(
            QtCore.QRect(0,0,self.width, self.height))
        
        size = self.text_size
        #take the current size
        #move right
        self.current_pos -= 10

        font = QtGui.QFont(self.text_font, size)
        font.setBold(True)
        
        #max shift
        limit = 30
        if self.current_pos < (0):
            self.current_pos += 10
    
        if self.in_POV == False:
            #draw Text
            painter = QtGui.QPainter(self.controller_map)
            painter.setPen(clr)
            #painter.setFont(QtGui.QFont(self.text_font, size))
            painter.setFont(font)
            painter.drawText(QtCore.QRectF(self.current_pos,
                                            0, self.width, self.height), string)
            self.redraw()
        else:
            #if in POV then draw text and generate POV
            painter = QtGui.QPainter(self.controller_map)
            painter.setPen(clr)
            #painter.setFont(QtGui.QFont(self.text_font, size))
            painter.setFont(font)
            painter.drawText(QtCore.QRectF(self.current_pos,
                                            0, self.width, self.height), string)
            
            self.preview()
  
    def addText(self, clr, string):
        """
        addText(self, clr, string) -> None.
        Adds the text given in string using the QColor clr
        to the pixmap and sends an update request to the View.

        Key arguments:
        clr -- the QColor to draw the text in.
        string -- the text string to add.

        Does not return.
        """
        self.stringclr = clr
        self.string = string
        #add way to resize text
        #make slider appear
        self.view.addTextSlider()

        self.before_text = self.controller_map.copy(
            QtCore.QRect(0,0,self.width, self.height))

        font = QtGui.QFont(self.text_font, 20)
        font.setBold(True)

        if self.in_POV == False:
            painter = QtGui.QPainter(self.controller_map)
            painter.setPen(clr)
            
            painter.setFont(font)

            #get width
            rect = painter.drawText(0, 0, 360, 32, 0, string)
            self.text_width = rect.width()
            self.redraw()
        else:
            #we are in POV mode
            painter = QtGui.QPainter(self.controller_map)
            painter.setPen(clr)
            #painter.setFont(QtGui.QFont(self.text_font, 20))
            painter.setFont(font)
            rect = painter.drawText(0, 0, 360, 32, 0, string)
            self.text_width = rect.width()
            self.preview()

        #make copy after added text
        
        
    def redraw(self):
        """
        redraw(self) -> None.
        Sends a redraw request to the View.

        Does not return.
        """
        self.view.redraw(self.controller_map)

    def upload(self):
        """
        upload(self) -> None.
        Uploads the current image data to the chip.

        Does not return.
        """
        self.view.nukeWidgets()
        #get the image of the controller map
        self.image = self.controller_map.toImage()
        data = []
        #generate the data
        data = self.model.generateData(self.image)
        #print len(data)
        self.view.addLoadingBar()

        self.upload_thread = self.model.uploadData(data)
        #create a thread to upload the data
        if self.upload_thread != None:
            self.thread_created = True
            self.connect(self.upload_thread, self.upload_thread.signal,
                         self.updateProgress)
            self.upload_thread.start()

    def updateProgress(self, value):
        """
        updateProgress(self, value) -> None
        Sets the loading bar in the view according to the reeived
        update value.

        Key arguments:
        value -- the value to be updated to.

        Does not return.
        """
        if value < 100:
            self.view.setLoadingBar(value)
        if value > 99:
            self.view.removeLoadingBar()
            self.thread_created = False
        if value == -1:
            self.thread_created = False
            msgBox = QtGui.QMessageBox()
            msgBox.setText('Cannot find USB!')
            msgBox.exec_()
            self.view.removeLoadingBar()


  

