#!/bin/bash 

pytest --capture=no testgameserver.py testmath.py $@
rebot output.xml
