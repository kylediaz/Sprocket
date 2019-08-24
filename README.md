# Sprocket Generator
A python script for Autodesk Fusion 360 that will generate the sketch for a
sprocket using parameters given to it

Based off [Designing and Drawing a Sprocket](http://www.gearseds.com/files/design_draw_sprocket_5.pdf)

# How to use
Clone this repo into C:\Users\$USER\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\Scripts\

The script can be run from the Scripts menu in Fusion.

![](doc/script-tool-bar.jpg)

When run, there will be a dialogue box asking for the parameter.

![](doc/dialogue.jpg)

This script follows
[Designing and Drawing a Sprocket](http://www.gearseds.com/files/design_draw_sprocket_5.pdf)
up to step 14. The user needs to follow the instructions starting at step 15.

I don't think the Fusion 360 API is capable of trimming, so I will have to
eventually rework this program to fully automate making the sketch.