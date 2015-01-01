POV-image-editor
================

The supporting software for a persistence of vision device.

This code was part of a university project to develop a persistance of vision (POV) device for a bicycle wheel.
What is POV? Good question. It's when something is moving so fast that it tricks your brain into thinking it's in several places
at once. You might of seen pictures of people who waved sparklers around in the air and they managed to take a photo and make it
look as though there's a love heart made of fire in the air - that is basically POV. Our project was to make a POV PCB which 
attached to a bicycle wheel and when it spun it could show different static RGB images like rainbows, text, or custom drawn images. 

This software was used to achieve several things for the project:
1. load Netpbm images and allow the user to edit them
2. create custom images from scratch
3. allow the user to enter text
4. upload the images to the microncontroller through a USB

Several third party software packages were used to achieve this project. The project was written in Python so the chosen GUI library was PyQt. 
PySerial was utilised for USB communication. Pillow (an offshoot of the Python Imaging Library) was used initially for some development of the image file parsing until custom file parsers were written, so there may still be some parts of that library hiding in the code somewhere!

I'll update here with more information on the structure of the code if anyone wants it, but this is really for me to try out Git :)
