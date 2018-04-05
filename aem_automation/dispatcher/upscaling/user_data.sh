#!/bin/bash

## install pip and virtualenv

home='/home/jeffin/scripts/new_aem/dispatcher'
# cd $home && . .env/bin/activate
# cd $home && pip install -r requirement.txt
cd $home && python autoscale.py
