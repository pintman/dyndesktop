#!/bin/bash

ssh pi@beneg.local "mkdir -p /home/pi/proj/dyndesktop"
rsync -avz --exclude=".git" . pi@beneg.local:/home/pi/proj/dyndesktop

