#!/bin/bash 

pytest --capture=no test.py $@
rebot output.xml
