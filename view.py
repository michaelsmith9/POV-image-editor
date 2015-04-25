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
import canvas
from canvas import Canvas

"""
The visible part of the program
"""
class View(QtGui.QWidget):
    """
    A class to contain all the buttons and the canvas for dispaying
    a pixmap. It is the graphical user interface. 
    """

    def __init__(self, parent, pixmap, width, height):
        """
        View.__init__(self, parent, pixmap, width, height) -> None
        Initialises the view with the given parameters.

        Keyword arguments:
        parent -- the parent class
        pixmap -- the given QPixmap to display
        width -- the width of the pixmap
        height -- the height of the pixmap.

        Does not return.
        """
        super(View, self).__init__()
        self.parent = parent
        self.width = width
        self.height = height

        self.set_colour = QtGui.QColor(255,255,255)
        
        #draw type is initially PIX (pixel)
        self.draw_type = 'PIX'
        
        #initialse the widget
        self.init_widget(pixmap, width, height)

        self.save_pixmap_level = 10
        #set pov mode colour
        self.setPovColour(self.set_colour)

    def init_widget(self, pixmap, width, height):
        """
        initWidget(self, pixmap, width, height) -> None
        Initialises the widget using the given pixmap, width and height
        parameters.

        Key arguments:
        pixmap -- the QPixmap to display
        width -- the width of said pixmap
        height -- the height of the pixmap

        Does not return
        """
        #colour indicator
        self.colour_indicator = QtGui.QPixmap(50,10)
        self.colour_indicator.fill(self.set_colour)
        self.col_label = QtGui.QLabel()
        self.col_label.setPixmap(self.colour_indicator)
        self.col_label.setScaledContents(True)
        #tie col_label's mousePressEvent to a method to allow colour selection
        self.col_label.mousePressEvent = self.colourRequest
        
        #Set up grid layout
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        
        #Create buttons
        self.line_button = QtGui.QPushButton('Line Draw')
        self.free_button = QtGui.QPushButton('Free Draw')
        self.area_button = QtGui.QPushButton('Area Draw')
        self.pixel_button = QtGui.QPushButton('Pixel Draw')
        self.colour_button = QtGui.QPushButton('Select Colour')
        self.text_button = QtGui.QPushButton('Add Text')
        self.zoom_in = QtGui.QPushButton('Zoom In')
        self.zoom_out = QtGui.QPushButton('Zoom Out')
        self.reset_button = QtGui.QPushButton('Reset')

        #self.setSizePolicy ( QSizePolicy.Expanding, QSizePolicy.Expanding)
        #Connect buttons with functions (NOTE: not draw_line() i.e. no brackets)
        self.line_button.clicked.connect(self.lineDraw)
        self.free_button.clicked.connect(self.freeDraw)
        self.area_button.clicked.connect(self.areaDraw)
        self.pixel_button.clicked.connect(self.pixelDraw)
        self.colour_button.clicked.connect(self.colourSelect)
        self.text_button.clicked.connect(self.textDraw)
        self.zoom_in.clicked.connect(self.zoomIntoImage)
        self.zoom_out.clicked.connect(self.zoomOutImage)
        self.reset_button.clicked.connect(self.reset)
        
        #Add button widgets to each position
        self.grid.addWidget(self.line_button, 0, 0, 1, 1)
        self.grid.addWidget(self.free_button, 0, 1,1,1)
        self.grid.addWidget(self.area_button, 0, 2,1,1)
        self.grid.addWidget(self.pixel_button, 0, 3,1,1)
        self.grid.addWidget(self.colour_button, 0, 4,1,1)
        self.grid.addWidget(self.text_button, 0, 5,1,1)
        self.grid.addWidget(self.zoom_in, 0, 6,1,1)
        self.grid.addWidget(self.zoom_out, 0, 7,1,1)
        self.grid.addWidget(self.reset_button, 0, 8,1,1)
        self.grid.addWidget(self.col_label,0,9,1,1)

        #set column stretch parameters
        a = [0, 1, 2, 3, 4, 5, 6, 7]
        for i in a:
            self.grid.setColumnStretch(i,10)

        #Create canvas widget for pixmap
        self.canvas = Canvas(self)
        #Place in row 1, col 0, stretch across 4 columns
        self.grid.addWidget(self.canvas, 1, 0, 1, 10)
        #Pass view the pixmap that we were passed in constructor
        self.canvas.displayImage(pixmap, width, height)

        #self.fitInView(self.canvas)
        
        self.show()

    def maximised(self):
        """
        maximised(self) -> None
        Signals the Canvas that the MainWindow has been maximised.

        Does not return.
        """
        self.canvas.maximised()
        
    def addTextSlider(self):
        """
        addTextSlider(self) -> None
        Adds a text slider and buttons to alter the size of text on the canvas.

        Does not return.
        """
        #finish text resizing (clear any text that has already been added)
        self.finishedTextResizing()
        
        #add a QSlider to select text size
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setValue(99)
        self.slider.valueChanged[int].connect(self.changeValue)

        #add a label to allow text size
        self.slider_label = QtGui.QLabel('CHANGE TEXT SIZE: ')
        self.remove_label = QtGui.QPushButton('THAT\'S GOOD')
        self.remove_label.clicked.connect(self.finishedTextResizing)

        #add buttons for changing text position
        self.pos_button_right = QtGui.QPushButton('MOVE RIGHT')
        self.pos_button_right.clicked.connect(self.moveTextRight)
        self.grid.addWidget(self.pos_button_right, 2, 9, 1, 1)
        self.pos_button_left = QtGui.QPushButton('MOVE LEFT')
        self.pos_button_left.clicked.connect(self.moveTextLeft)
        self.grid.addWidget(self.pos_button_left, 2, 8, 1, 1)
        
        self.grid.addWidget(self.slider_label, 2, 5,1,1)
        self.grid.addWidget(self.slider, 2,6,1,1)
        self.grid.addWidget(self.remove_label, 2,7,1,1)

        self.grid.setColumnStretch(6,9)

    def addLoadingBar(self):
        """
        addLoadingBar(self) -> None
        Adds a loading bar to the View.

        Does not return
        """
        self.progress_bar = QtGui.QProgressBar()

        self.grid.addWidget(self.progress_bar, 2,3,1,2)
        
        self.progress_bar.show()
        
    def setLoadingBar(self, value):
        """
        setLoadingBar(self, value) -> None
        Sets the value of the loading bar.

        Keyword arguments:
        value -- the value to set the loading bar to
            
        Does not return.
        """
        self.progress_bar.setValue(value)

    def removeLoadingBar(self):
        """
        removeLoadingBar(self) -> None
        Removes the loading bar from the view.

        Does not return.
        """
        item = self.grid.itemAtPosition(2,3)
        widget = item.widget()
        self.grid.removeWidget(widget)
        widget.deleteLater()

    def changeValue(self, value):
        """
        changeValue(self, value) -> None
        Signals the parent the value of the text to be displayed.

        Does not return
        """
        self.parent.textSizeChange(value)

    def moveTextRight(self):
        """
        moveTextRight(self) -> None
        Signals the parent that the text should be moved right.

        Does not return.
        """
        self.parent.textMoveRight()

    def triggerResize(self):
        """
        triggerResize(self) ->
        Triggers a resizeEvent in the controller.

        Does not return.
        """
        self.parent.requestResize()

    def moveTextLeft(self):
        """
        moveTextLeft(self) -> None
        Signals the parent that the text should be moved left.

        Does not return.
        """
        self.parent.textMoveLeft()
    
    def finishedTextResizing(self):
        """
        finishedTextResizing(self) -> None
        Attemps to remove the added slider and buttons used
        for resizing text.

        Does not return. 
        """
        try:
            # try to remove the items, if not there
            # then they weren't there in the first place
            # so ignore exception
            i = 5
            while i < 10:
                item = self.grid.itemAtPosition(2, i)
                widget = item.widget()
                self.grid.removeWidget(widget)
                widget.deleteLater()
                i += 1
        except Exception:
            pass

    def setNewPixmap(self):
        """
        setNewPixmap(self) -> None
        Adds the buttons and input to the GUI to allow the user to
        add a new pixmap.

        Does not return.
        """
        self.width_label = QtGui.QLabel('ENTER WIDTH: ')
        self.width_field = QtGui.QLineEdit()
        self.generate = QtGui.QPushButton('GENERATE')
        self.generate.clicked.connect(self.createNewImage)
        
        self.grid.addWidget(self.width_label, 2,0)
        self.grid.addWidget(self.width_field,2,1)
        self.grid.addWidget(self.generate,2,2)
        
    def createNewImage(self):
        """
        createNewImage(self) -> None
        Connected to the new pixmap button, signals the parent
        that a new image is to be created.

        Does not return
        """
        givenWidth = self.width_field.text()
        #check bounds
        width = 360
        
        try:
            #more than 3 chars were entered, ignore the input
            if len(givenWidth) > 3:
                raise Exception
            width = int(givenWidth)
            
            if width < 1 or width > 360:
                
                msgBox = QtGui.QMessageBox()
                msgBox.setText('Please enter a valid width')
                msgBox.exec_()

            #signal the parent to create a new image
            self.parent.createNewImage(width)
                
        except Exception:
            msgBox = QtGui.QMessageBox()
            msgBox.setText('Please enter a valid width')
            msgBox.exec_()

    def removeImageInput(self):
        """
        removeImageInput(self) -> None
        Removes the input buttons and fields for generating an image.

        Does not return.
        """
        i = 0
        try:
            while i < 3:
                item = self.grid.itemAtPosition(2, i)
                widget = item.widget()
                self.grid.removeWidget(widget)
                widget.deleteLater()
                i += 1
        except Exception:
            pass

    def nukeWidgets(self):
        """
        nukeWidgets(self) -> None
        Removes any widgets in 2nd row of view.

        Does not return.
        """
        i = 0;
        while i < 10:
            try:
                item = self.grid.itemAtPosition(2, i)
                if item != None:
                    widget = item.widget()
                    self.grid.removeWidget(widget)
                    widget.deleteLater()
            except Exception:
                pass
            i += 1

    def newPixmap(self, pixmap, width, height):
        """
        newPixmap(self, pixmap, widget, height) -> None
        Discards the pixmap currently being displayed by the view
        and disaplys the new pixmap given by pixmap.

        Does not return.
        """
        # reset zoom level
        # add the new pixmap
        self.width = width
        self.height = height
        self.canvas.displayImage(pixmap, width, height)

    def reset(self):
        """
        reset(self) -> None
        Signals the parent to reset the view and resets the zoom level.
        """
        # reset the zoom level
        # request a new pixmap
        self.parent.newPixmap()
        self.canvas.resetZoom()

    def redraw(self, pixmap):
        """
        redraw(self, pixmap) -> None
        Clears the view and redraws the pixmap with the given pixmap
        assumes that pixmap has the same width and height as the original
        pixmap.

        Key arguments:
        pixmap -- a QPixmap with identical dimensions to the currently
            laoded pixmap.

        Does not return.
        """
        self.canvas.clear()
        self.canvas.editImage(pixmap)

    def zoomIntoImage(self):
        """ 
        zoomIntoImage(self) -> None
        Zooms in one increment to the canvas.

        Does not return.
        """
        """self.zoom_level -= 1
        if self.zoom_level > 6:
            self.canvas.setScale(2, 2)
        else:
            self.zoom_level = 6
        """
        self.canvas.zoomIn()
    
    def zoomOutImage(self):
        """
        zoomOutImage(self) -> None
        Zooms out of the image.

        Does not return.
        """
        """
        self.zoom_level += 1
        if self.zoom_level < 12:
            self.canvas.setScale(0.5, 0.5)
        else:
            self.zoom_level = 12
        """
        self.canvas.zoomOut()

    def lineDraw(self):
        """
        lineDraw(self) -> None
        Selects line draw as the current drawing tool.

        Does not return.
        """
        self.canvas.lineDrawSelect()
    
    def freeDraw(self):
        """
        freeDraw(self) -> None
        Selects free draw as the current drawing tool.

        Does not return
        """
        self.canvas.freeDrawSelect()

    def textDraw(self):
        """
        textDraw(self) -> None
        Gets user input for text and adds it to the canvas.

        Does not return.
        """
        string, ok = QtGui.QInputDialog.getText(self, 'Get text',
                                   'Enter your text:')
        #assume chars are 16 in size
        cut = self.width/12
        if self.width > 350:
            cut = 25
        #problem is text of all small letters will be too short,
        if len(string) > cut:
            msgBox = QtGui.QMessageBox()
            msgBox.setText('Your string was too long, '
                           + 'we used: ' + string[0:cut])
            msgBox.exec_()
        #set string size according to size of grid
        if ok:
            self.parent.addText(self.set_colour, string[0:cut])
        
    def areaDraw(self):
        """
        areaDraw(self) -> None
        Selects areaDraw as the current drawing tool.
        
        Does not return.
        """
        self.canvas.areaSelect()

    def pixelDraw(self):
        """
        pixelDraw(self) -> None
        Selects pixel draw as the current drawing tool.
        
        Does not return.
        """
        self.canvas.pixelSelect()

    def doPixelDraw(self, x, y):
        """ 
        doPixelDraw(self, x, y) -> None
        Signals the parent that a pixel draw must be performed
        at the given x and y co-ordinate.

        Key arguments:
        x -- the x coordinate of the point (between 0 and 360)
        y -- the y coordinate of the point (between 0 and 32)

        Does not return.
        """
        self.parent.pixelChange(x, y, self.set_colour)

    def doLineDraw(self, sx, sy, ex, ey):
        """
        doLineDraw(self, sx, sy, ex, ey) -> None
        Signals the parent that a line draw should be performed between
        the given coordinates: (sx, sy) and (ex, ey).

        Key arguments:
        sx -- the starting x coordinate (between 0 and 360)
        sy -- the starting y coordinate (between 0 and 32)
        ex -- the ending x coordinate (between 0 and 360)
        ey -- the ending y coordinate (between 0 and 32)

        Does not return.
        """
        self.parent.addLine(sx, sy, ex, ey, self.set_colour)

    def doLineDrawPov(self, sr, stheta, er, etheta):
        """
        doLineDrawPov(self, sr, stheta, er, etheta) -> None
        Signals the parent to perform a line draw (in POV mode) between
        the given points.

        Key arguments:
        sr -- the starting radial distance (between 22 and 54)
        stheta -- the starting angle (between -180 and +180)
        er -- the ending radial distance (between 22 and 54)
        etheta -- the ending angle (between -180 and +180)

        Does not return.
        """
        
        self.parent.povLineDraw(sr, stheta, er, etheta, self.set_colour)

    def doAreaDraw(self, sx, sy, ex, ey):
        """
        doAreaDraw(self, sx, sy, ex, ey) -> None
        Signals the parent to perform a block (area) draw using the coordinates
        as the bound for the rectangle.

        Key arguments:
        sx -- the top left corner of the rectangle (0 to 360) x coordinate
        sy -- the top left corner of the rectanlge (0 to 32) y coordinate
        ex -- the bottom right corner of the rectangle (0 to 360) x coordinate
        ey -- the bottom right corner of the rectangle (0 to 32) y coordinate

        Does not return.
        """
        self.parent.areaAdd(sx, sy, ex, ey, self.set_colour)

    def colourSelect(self):
        """
        colourSelect(self) -> None
        Triggers the colour selection dialog.

        Does not return.
        """
        self.set_colour = QtGui.QColorDialog.getColor()
        self.colour_indicator.fill(self.set_colour)
        self.col_label.setPixmap(self.colour_indicator)
        self.setPovColour(self.set_colour)

    def colourRequest(self, event):
        """
        colourRequest(self, event) -> None
        Handles the event and triggers colourSelect().

        Does not return.
        """
        self.colourSelect()

    def generatePov(self, pixmap):
        """
        generatePov(self, pixmap) -> None
        Signals the canvas to generate the pov given the pixmap.

        Key arguments:
        pixmap -- the QPixmap with which to generate POV mode.

        Does not return.
        """
        self.canvas.generatePov(pixmap)

    def setPovColour(self, colour):
        """
        setPovColour(self, colour) -> None
        Sets the Pov draw colour to colour.

        Key arguments:
        colour -- the QColor to set.

        Does not return.
        """
        self.canvas.setPovColour(colour)

    def sendUpdate(self, r, theta, colour):
        """
        sendUpdate(self, r, theta, colour) -> None
        Send an update to the controller as to the colour of a pixel.

        Key arguments:
        r -- the radial position (y coordinate) of the pixel to be updated.
        theta -- the angle (x coordinate) of the pixel to be updated.
        colour -- the colour to update the pixel to.

        Does not return.
        """
        self.parent.updatePixel(r,theta,colour)
        
