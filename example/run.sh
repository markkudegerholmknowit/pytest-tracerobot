#!/bin/bash 

pytest --capture=no $@
rebot output.xml
