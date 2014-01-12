#!/bin/bash
rsync -r --remove-source-files --include=*.mp3 --exclude=*.*  audio/ audio-perm/    
sleep 5
find ./audio/ -type d -empty -exec rmdir {} \;
find ./audio/ -type d -empty -exec rmdir {} \;
find ./audio/ -type d -empty -exec rmdir {} \;
find ./audio/ -type d -empty -exec rmdir {} \;
find ./audio/ -type d -empty -exec rmdir {} \;
find ./audio/ -mtime +1 -iname *.dat -exec rm {} \;
find ./audio/ -mtime +1 -iname *.wav -exec rm {} \;
