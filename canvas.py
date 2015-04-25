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

#1. fix resize initiailly
#2. re-implement for POV resizing
#3. won't nexessary be 360 wide
#4. handle maximise and minimise

"""
The class to display the pixmap to the user.
"""
class Canvas(QtGui.QGraphicsView):
    """
    This class extends the QGraphicsView to add
    extra functionaility with regards to warping an image
    so that it can be shown in a POV mode.
    """
    
    def __init__(self, parent):
        """
        Canvas.__init__(self, parent) -> None
        Initialise the Canvas with the given parent.

        Key arguments:
        parent -- the parent class (usually a QWidget).

        Does not return
        """
        QtGui.QGraphicsView.__init__(self)
        #Create a scene that takes our view
        self.scene = QtGui.QGraphicsScene(self)
        self.zoom_level = 10
        
        #intialise coordinates to handle where the user has clickewd
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        
        self.parent = parent
        #set draw type and pov mode to default
        self.draw_type = 'PIX'
        self.pov_mode = False
        self.pov_colour = QtGui.QColor(0,0,0,255)

        self.grid_colour = QtGui.QColor(140,140,140,255)

        #size for comparison
        self.new_size = None
        self.old_size = None

        self.zoom_flag = False

        self.is_max = False
        self.is_min = False


    def freeDrawSelect(self):
        """
        freeDrawSelect(self) -> None
        Selects free draw as the current drawing method.
        
        Does not return.
        """
        self.draw_type = 'FREE'

    def lineDrawSelect(self):
        """
        lineDrawSelect(self) -> None
        Selects line draw as the current drawing method.

        Does not return.
        """
        self.draw_type = 'LINE'

    def areaSelect(self):
        """
        areaSelect(self) -> None
        Selects are draw as the current drawing method.
        
        Does not return.
        """
        self.draw_type = 'AREA'

    def pixelSelect(self):
        """
        pixelSelect(self) -> None
        Selects pixel draw as the current drawing method.

        Does not return.
        """
        self.draw_type = 'PIX'
        
    def clear(self):
        """
        clear(self) -> None
        Clears the scene.

        Does not return.
        """
        self.scene.clear()

    def zoomIn(self):
        """
        zoomIn(self) -> None
        Zoomz in to pixmap, only to set level.

        Does not return.
        """
        self.zoom_flag = True
        if self.zoom_level < 14:
            self.scale(1.3, 1.3)
            self.zoom_level += 1

    def zoomOut(self):
        """
        zoomOut(self) -> None
        Zooms out of pixmap, only to set level.

        Does not return.
        """
        self.zoom_flag = True
        if self.zoom_level > 8:
            self.scale(0.7, 0.7)
            self.zoom_level -= 1

    def resetZoom(self):
        """
        resetZoom(self) -> None
        Resets the zoom level of the canvas.

        Does not return.
        """
        if self.zoom_level < 10:
            while self.zoom_level < 10:
                self.scale(0.7, 0.7)
                self.zoom_level += 1
        elif self.zoom_level > 10:
            while self.zoom_level > 10:
                self.scale(1.3, 1.3)
                self.zoom_level -= 1
        self.fitToScale(QtCore.QPoint(0,0))
    
    def setScale(self, x, y):
        """
        setScale(self, x, y) -> None
        Sets the scale of the view given the x and y.

        Key arguments:
        x -- the x multiplier (int).
        y -- the y multiplier (int).
        
        Does not return.
        """
        self.scale(x,y)

    def editImage(self, pixmap):
        """
        editImage(self, pixmap) -> None
        Updates the pixmap being displayed to the given pixmap.

        Key arguments:
        pixmap -- the pixmap to display.
        
        Does not return.
        """
        if pixmap == '':
            pass
        else:
            # set our save_pixmap
            self.save_pixmap = pixmap

            # clear the scene
            self.scene.clear()
            item = QtGui.QGraphicsPixmapItem(pixmap)

            # add the item and draw the grid
            self.scene.addItem(item)
        
            self.pov_mode = False
            
            self.drawBorderAndGrid(self.scene, pixmap.width(),
                                   pixmap.height(),False)

    def displayImage(self, pixmap, width, height):
        """
        displayImage(self, pixmap, width, height) -> None
        Displays a pixmap with the given width and height.

        Key arguments:
        pixmap -- the QPixmap to display.
        width -- the width (int) of said pixmap.
        height -- the height(int) of the pixmap.
        
        Does not return.
        """
        if pixmap == '':
            pass
        else:
            self.save_pixmap = pixmap.copy(0, 0, pixmap.width(),
                                           pixmap.height())
            
            self.scene.clear()
        
            self.scene = QtGui.QGraphicsScene(0, 0, width, height, None)
          
            self.setScene(self.scene)
        
            item = QtGui.QGraphicsPixmapItem(pixmap)
            
            # check if we are maximised
            if self.is_max == True:

                # below scales the window to fit
                         
                map_edge = self.mapFromScene(
                    QtCore.QPoint(0, 0))
                map_far = self.mapFromScene(
                    QtCore.QPoint(width, height))
                
                while (map_edge.x() > 0 and map_edge.y() < self.height()):
                    self.scale(1.01, 1.01)
                    map_edge = self.mapFromScene(QtCore.QPoint(0, 0))
                    
                map_edge = self.mapFromScene(width, 0)
                
                
                while (map_edge.x() < self.width() and
                       map_edge.y() < self.height()):
                    self.scale(1.01, 1.01)
                    map_edge = self.mapFromScene(QtCore.QPointF(width,0))

            
                map_far = self.mapFromScene(
                    QtCore.QPoint(width, height))

                if map_far.x() > self.width():
                    
                    # zoom in if too far to left
                    while map_far.x() > self.width():
                        self.scale(0.99, 0.99)
                        map_far = self.mapFromScene(QtCore.QPoint(width,0))

                    map_far = self.mapFromScene(QtCore.QPoint(width, 0))
                    map_near = self.mapFromScene(QtCore.QPoint(0, 0))

                    # zoom in if too far to right
                    while map_near.x() > 0:
                        self.scale(1.01, 1.01)
                        map_far = self.mapFromScene(QtCore.QPoint(width,0))
                        map_near = self.mapFromScene(QtCore.QPoint(0,0))

                    map_far = self.mapFromScene(QtCore.QPoint(0,
                                                              height))

                    # while height greater than height of GUI, zoom in
                    while map_far.y() > self.height():
                        self.scale(0.99, 0.99)
                        map_far = self.mapFromScene(QtCore.QPoint(0,
                                                                  height))

                    # while height is less than height of GUI, zoom out
                    while map_far.y() < 0:
                        self.scale(0.99, 0.99)
                        map_far = self.mapFromScene(QtCore.QPoint(0,
                                                                  height))
                
                
            self.scene.addItem(item)

            self.zoom_level = 10

            self.pov_mode = False
            
            if pixmap.width() == 108 and pixmap.height() == 108:
                self.pov_mode = True
                self.drawBorderAndGrid(self.scene, width, height, True)
            else:
                self.pov_mode = False
                self.drawBorderAndGrid(self.scene, width, height, False)

            self.parent.triggerResize()

    def focusPov(self):
        """
        focusPov(self) -> None
        Focuses in on POV mode representation.

        Does not return.
        """
        # map the top left coordinate 
        map_bottom = self.mapFromScene(QtCore.QPoint(0, 0))
        
        # if it is not at zero and is less than the width, then
        # zoom in
        while map_bottom.y() > 0 and map_bottom.x() < self.width():
            self.scale(1.01, 1.01)
            map_bottom = self.mapFromScene(QtCore.QPoint(108, 0))

        # map the edge
        map_bottom = self.mapFromScene(QtCore.QPoint(0, 108))

        #zoom out if appopriate
        while map_bottom.y() > self.height():
            self.scale(0.99, 0.99)
            map_bottom = self.mapFromScene(QtCore.QPoint(0, 108))
            
    def generatePov(self, controller_map):
        """
        generatePov(self, controller_map) -> None
        Generates POV mode using the QPixmap controller_map.

        Key arguments:
        controller_map -- the QPixmap to generate POV mode from.
        
        Does not return.
        """
        #we are in pov mode
        self.pov_mode = True

        #clear the scene
        self.scene.clear()
        chosen_width = 108
        
        self.scene = QtGui.QGraphicsScene(0,0, chosen_width,
                                          chosen_width, None)

        edge_scene = self.mapFromScene(QtCore.QPoint(108, 0))
        
        #increase scale until the edge hits the edge of the view
        while (edge_scene.x() < self.width()):
            self.scale(1.01, 1.01)
            edge_scene = self.mapFromScene(QtCore.QPoint(108, 0))

        edge_scene = self.mapFromScene(QtCore.QPoint(108, 0))
        while (edge_scene.x() > self.width()):
            self.scale(0.99, 0.99)
            edge_scene = self.mapFromScene(QtCore.QPoint(108, 0))

        self.setScene(self.scene)
        cmap_width = 108
        
        self.parent.triggerResize()
        
        #convert the pixmap to an image to get pixel colours
        image = controller_map.toImage()
        grid_pen = QtGui.QPen(QtGui.QColor(0,0,0,255))

        #get thetashift (to centre image on top of wheel)

        #get pad theta in degrees
        padtheta = (360 - controller_map.width())/2
        #convert to radians
        padtheta = padtheta * math.pi / 180
        #thetashift is a shift of pi/2 radians (90 degrees)
        #and then whatever the theta padding was
        thetashift = padtheta + math.pi/2
        

        #starting radius is 53
        r = 53.0
        angle = 0.0
        #a list of points to draw a polygon between
        points = []
        #the shift to centre the annulus (pov image)
        shift = 54
        #draw the POV
        last_angle = 0
        
        #loop through all radii until we hit the lower limit
        while r > 21.0:
            angle = 0
            #loop through all angles for a given radius
            while angle < float(controller_map.width())-0.5:
                
                points = []
                # add on amount with respect to width of image
                theta = angle*math.pi/180 + thetashift
                #first time: 0.0, second: 1.0, third: 1.0, fourth: 1.0

                #get the radius in
                rin = math.floor(53.0-r)
                px = image.pixel(round(angle), rin)

                #get the value of the pixel to set the colour on the pov 
                value = QtGui.QColor(px)
                grid_pen.setColor(value)
                grid_pen = QtGui.QPen(value)

                #append points with foure QPointF (floating point QPoints)
                #each point being one corner of the rectangle to be drawn
                points.append(QtCore.QPointF(r*math.cos(theta) + shift,
                                              r*math.sin(theta) + shift))
                points.append(
                    QtCore.QPointF((r + 1)*math.cos(theta) + shift,
                                   (r + 1)*math.sin(theta) + shift))
                points.append(
                    QtCore.QPointF((r + 1)*math.cos(
                        theta+math.pi/180)+ shift,
                                   (r + 1)*math.sin(theta+math.pi/180)
                                   + shift))
                points.append(
                    QtCore.QPointF(r*math.cos(theta + math.pi/180)+ shift,
                                   r*math.sin(theta+math.pi/180) + shift))
                
                polygon = QtGui.QPolygonF(points)
                self.scene.addPolygon(polygon, grid_pen, QtGui.QBrush(value))

                angle += 1.
            # set the last_angle to this angle (for drawing the rest in black)
            last_angle = angle
            r -= 1.
        r = 53.0
        
        #if the width was less than 360, then draw the remaining pixels black
        if float(controller_map.width()) < 360.:
            #make angle start at wherever we were
            while r > 21.0:
                angle = last_angle

                while angle < float(360)-0.5:
                    points = []
                    # add on amount with respect to width of image
                    theta = angle*math.pi/180+thetashift
                    #first time: 0.0, second: 1.0, third: 1.0, fourth: 1.0
                    #we want 0,0,1,1
                    rin = math.floor(53.0-r)
         
                    value = QtGui.QColor((0,0,0))
                    grid_pen.setColor(value)
                    grid_pen = QtGui.QPen(value)
                    
                    # add the appropriate four points to a list
                    # to construct the POV mode from
                    points.append(
                        QtCore.QPointF(r*math.cos(theta) + shift,
                                                  r*math.sin(theta) + shift))
                    points.append(
                        QtCore.QPointF((r+1)*math.cos(theta) + shift,
                                                  (r+1)*math.sin(theta) + shift))
                    points.append(
                        QtCore.QPointF((r+1)*math.cos(theta+math.pi/180) + shift,
                                          (r+1)*math.sin(theta+math.pi/180)
                                       + shift))
                    points.append(
                        QtCore.QPointF(r*math.cos(theta+math.pi/180) + shift,
                                          r*math.sin(theta+math.pi/180) + shift))
                    
                    polygon = QtGui.QPolygonF(points)
                    self.scene.addPolygon(polygon, grid_pen, QtGui.QBrush(value))

                    angle += 1.
                r -= 1.

        self.drawBorderAndGrid(self.scene, controller_map.width(),
                               controller_map.height(), True)

    def drawBorderAndGrid(self, scene, width, height, val):
        """
        drawBorderAndGrid(self, scene, width, height, val) -> None
        Draws the border and grid using the given parameters.

        Key arguments:
        scene -- the QGraphicsScene on which to draw the grid.
        width -- the width of the grid.
        height -- the height of the grid.
        val -- identifies as POV mode, true or false.
        
        Does not return.
        """
        grid_pen = QtGui.QPen(self.grid_colour)

        # if False, draw a 2D x,y grid
        if val == False:
            scene.addRect(QtCore.QRectF(0,0,width, height),
                      grid_pen)
            i = 0
            while i < width:
                scene.addLine(i,0,i,32,grid_pen)
                i += 1
            i = 0
            while i < height:
                scene.addLine(0,i,width,i,grid_pen)
                i += 1
        else:
            # if true, draw ellipses and lines
            shift = 54
            grid_pen.setColor(self.grid_colour)
            i = 0
            #add rings of ellipses
            while i < 33:
                w = 44+2*i
                h = 44+2*i
                x = shift-(w/2)
                y = shift-(h/2)
                self.scene.addEllipse(x,y,w,h,grid_pen)
                i += 1
            #add in lines
            i = 0

            #inner ellipse has a radius of 15
            #outer ellipse has a radius of 37
            while i < 360:
                x1 = 22*math.cos(float(i*math.pi/180.))+shift
                y1 = 22*math.sin(float(i*math.pi/180.))+shift
                x2 = 54*math.cos(float(i*math.pi/180.))+shift
                y2 = 54*math.sin(float(i*math.pi/180.))+shift
                self.scene.addLine(x1,y1,x2,y2,grid_pen)
                i += 1

    def setPovColour(self, colour):
        """
        setPovColour(self, colour) -> None.
        Sets POV mode drawing colour according to colour.

        Key arguments:
        colour -- the QColor to set.
        
        Does not return.
        """
        self.pov_colour = colour

    def drawInPov(self, x, y):
        """
        drawInPov(self, x, y) -> None.
        Changes the value of a signle pixel in POV mode.

        Key arguments:
        x -- the x coordinate.
        y -- the y coordinate.

        Does not return.
        """
        # set the QPen
        grid_pen = QtGui.QPen(self.pov_colour)
        value = self.pov_colour
        
        shift = 54
        a = x
        b = y

        #need to check if in bounds of POV wheel
            
        theta = math.atan2(b-shift, a-shift)

        r = math.sqrt((a-shift)**2 + (b-shift)**2)

        if r > 22 and r < 54:
            #get individual sqaure for r
            r = math.floor(r)
            #get indivudal square for theta
            theta = math.floor(theta*180/math.pi)*math.pi/180
            points = []

            points.append(QtCore.QPointF(r*math.cos(theta) + shift,
                                            r*math.sin(theta) + shift))
            points.append(QtCore.QPointF((r+1)*math.cos(theta) + shift,
                                            (r+1)*math.sin(theta) + shift))
            points.append(
                QtCore.QPointF((r+1)*math.cos(theta+math.pi/180) + shift,
                                        (r+1)*math.sin(theta+math.pi/180)
                               + shift))
            points.append(
                QtCore.QPointF(r*math.cos(theta+math.pi/180) + shift,
                                    r*math.sin(theta+math.pi/180) + shift))
                    
            polygon = QtGui.QPolygonF(points)
            self.scene.addPolygon(polygon, grid_pen, QtGui.QBrush(value))
            #update pixmap
            self.updatePixmap(r, theta,self.pov_colour)

    def doLineDrawPov(self, sx, sy, ex, ey):
        """
        doLineDrawPov(self, sx, sy, ex, ey) -> None.
        Performs a line draw (in POV mode) between (sx, sy) and (ex, ey)
        assuming a POV sized grid.

        Key parameters:
        sx -- the stating x position of the line.
        sy -- the starting y coordinate of the line.
        ex -- the ending x coordinate of the line.
        ey -- the ending y coordinate of the line.
            
        Does not return.
        """
        shift = 54
        grid_pen = QtGui.QPen(self.pov_colour)
        value = self.pov_colour
        
        #need to check if in bounds of POV wheel
        #stheta = math.atan(((b-shift)/(a-shift)))
        stheta = math.atan2(sy-shift, sx-shift)

        sr = math.sqrt((sx-shift)**2 + (sy-shift)**2)

        etheta = math.atan2(ey-shift, ex-shift)
        er = math.sqrt((ex-shift)**2 + (ey-shift)**2)
      
        etheta = etheta*180/math.pi
        stheta = stheta*180/math.pi

        #check if in bounds of POV annulus
        if sr > 22 and sr < 54 and er > 22 and er < 54:
            self.parent.doLineDrawPov(sr, stheta, er, etheta)
            
    def updatePixmap(self, r, theta, colour):
        """
        updatePixmap(self, r, theta, colour) -> None
        Sends an update to the parent (signaled from POV) given from
        the radius and theta of an event.

        Key parameters:
        r -- the POV radial location of the pixel (between 22 and 54).
        theta -- the POV angle of the pixel (between 0 and 360).
        colour -- the colour of the pixel to be changed to.
            
        Does not return.
        """
        #update the pixmap at r, theta
        self.parent.sendUpdate(r-22,theta*180/math.pi+180,colour)


    def resizeEvent(self, event):
        """
        resizeEvent(self, event) -> None
        Reimplementation of the QResizeEvent. Calls a QGraphicsView's
        ResizeEvent and then additional code resizes the pixmap.
        
        Does not return.
        """
        #take oldsize and compare to new size
        self.new_size = event.size()
        # bool to indicate if rescaling is necessary
        should_change = False

        small_range = 1
        
        if self.old_size != None:
            # check if it's a decent change (i.e. 1 pixel)
            # as opposed to being triggered automatically by
            # Qt
            
            #if new widths and heights are much more than old
            if ((self.new_size.width() >
                 (self.old_size.width() + small_range))and
                (self.zoom_flag == False)):
                
                should_change = True
            if ((self.new_size.height() >
                 (self.old_size.height() + small_range))and
                (self.zoom_flag == False)):
                should_change = True
                
            #if new widths and heights are much less than the old
            if ((self.new_size.width() <
                 (self.old_size.width() - small_range))and
                (self.zoom_flag == False)):
                should_change = True
                
            if ((self.new_size.height() <
                 (self.old_size.height()- small_range)) and
                (self.zoom_flag == False)):
                should_change = True

        #set zoom flag
        self.zoom_flag = False

        #set old size to our new size
        self.old_size = self.new_size
                      
        #reset zoom level to 0
        self.zoom_level = 10
        
        #pass the event to a graphics view so it
        #can resize for us (still do resize)
        #we are just reimplementing it
        resizer_view = QtGui.QGraphicsView(self.scene, self)
        resizer_view.resizeEvent(event)
        rect = resizer_view.sceneRect()
        self.setSceneRect(rect)

        map_origin = self.mapFromScene(QtCore.QPoint(0, 0))

        # check if the origin is not zero and if the
        # fit should change
 
        if ((map_origin.x() != 0) and should_change == True and
            self.pov_mode == False):
            self.fitToScale(map_origin)

        if (should_change == True and self.pov_mode == False):
            self.fitToScale(map_origin)

        if should_change == True and self.pov_mode == True:
            self.focusPov()


    def maximised(self):
        """
        maximised(self) -> None
        Sets a flag to tell the Canvas object that the View has
        resized to full screen.

        Does not return.
        """
        self.is_max = True
        self.is_min = False

    def fitToScale(self, map_origin):
        """
        fitToScale(self) -> None
        Fits the current map to scale.

        Does not return.
        """
        # loop through while the origin is not at zero, zoom in
        while map_origin.x() > 0 and map_origin.y() > 0:
            self.scale(1.01, 1.01)
            map_origin = self.mapFromScene(QtCore.QPoint(0, 0))
            
        # if past zero then map to zero
        while map_origin.x() < 0 and map_origin.y() < 0:
            self.scale(0.99, 0.99)
            map_origin = self.mapFromScene(QtCore.QPoint(0, 0))

        map_edge = self.mapFromScene(
            QtCore.QPoint(self.save_pixmap.width(), 32))
        
        while map_edge.x() > self.width():
            self.scale(0.99, 0.99)
            map_edge = self.mapFromScene(
            QtCore.QPoint(self.save_pixmap.width(), 32))

        map_edge = self.mapFromScene(
            QtCore.QPoint(self.save_pixmap.width(), 32))

        while map_edge.y() > self.height():
            self.scale(0.99, 0.99)
            map_edge = self.mapFromScene(
            QtCore.QPoint(self.save_pixmap.width(), 32))

        pixmap = self.save_pixmap.copy(0, 0, self.save_pixmap.width(), 32)
            
        self.scene.clear()

        # re draw the scene and add the item (now at origin)
        self.scene = QtGui.QGraphicsScene(0,0,pixmap.width(),32)
        item = QtGui.QGraphicsPixmapItem(pixmap)
        self.scene.addItem(item)
        self.setScene(self.scene)

        # draw the border and grid
        self.drawBorderAndGrid(self.scene, pixmap.width(),
                                   pixmap.height(),False)
        
    def mousePressEvent(self, e):
        """
        mousePressEvent(self, e) -> None.
        Handles a mousepressEvent - reimplemented from default.

        Key parameters:
        e -- the event which contains information as to the location
            of the click.
            
        Does not return.
        """
        # get the location of the click
        click_point = QtCore.QPoint(e.pos().x(), e.pos().y())
        pos = self.mapToScene(click_point)
        
        self.start_x = pos.x()
        self.start_y = pos.y()

        # signal the parent (if necessary) 
        if self.pov_mode == True and self.draw_type == 'PIX':
            self.drawInPov(pos.x(),pos.y())
        if self.draw_type == 'PIX' and self.pov_mode == False:
            self.parent.doPixelDraw(self.start_x, self.start_y)
        if self.draw_type == 'LINE' and self.pov_mode == False:
            self.parent.doPixelDraw(self.start_x, self.start_y)

    def mouseMoveEvent(self, e):
        """
        mouseMoveEvent(self, e) -> None.
        Handles a mouseMoveEvent - reimplemented from default.

        Key parameters:
        e -- the event which contains information as to the location
            of the click.
            
        Does not return.
        """
        # get the position of the click
        view_pos = QtCore.QPoint(e.pos().x(), e.pos().y())
        pos = self.mapToScene(view_pos)
        self.end_x = int(round(pos.x()))
        self.end_y = int(round(pos.y()))

        # signal the parent (if necessary)
        if self.draw_type == 'FREE' and self.pov_mode == False:
            self.parent.doLineDraw(self.start_x, self.start_y, self.end_x,
                              self.end_y)
            self.start_x = self.end_x
            self.start_y = self.end_y
        
            
    def mouseReleaseEvent(self, e):
        """
        mouseReleaseEvent(self, e) -> None.
        Handles a mouseReleaseEvent - reimplemented from default.

        Key parameters:
        e -- the event which contains information as to the location
            of the click.
            
        Does not return.
        """
        # get the position of the mouse click
        view_pos = QtCore.QPoint(e.pos().x(), e.pos().y())
        pos = self.mapToScene(view_pos)

        # round of that position
        self.end_x = int(round(pos.x()))
        self.end_y = int(round(pos.y()))

        
        # signal the parent to perform a particular task
        if self.draw_type == 'FREE' and self.pov_mode == False:
            self.parent.doLineDraw(self.start_x, self.start_y, self.end_x,
                              self.end_y)
        if self.draw_type == 'AREA' and self.pov_mode == False:
            self.parent.doAreaDraw(self.start_x, self.start_y, self.end_x,
                                   self.end_y)
        if self.draw_type == 'LINE' and self.pov_mode == False:
            self.parent.doLineDraw(self.start_x, self.start_y, self.end_x,
                                     self.end_y)
        if self.draw_type == 'LINE' and self.pov_mode == True:
            self.doLineDrawPov(self.start_x, self.start_y, self.end_x,
                         self.end_y)
