#!/bin/bash
sleep `printf "0.%d04\n" $RANDOM `
sleep `printf "0.%d04\n" $RANDOM `
sleep `printf "0.%d04\n" $RANDOM `
sleep `printf "0.%d04\n" $RANDOM `
function run {
RES=`CellSearch -s 7315e5 -e 7315e5 -p 40 -i $1 | grep -E '^[0-9]' | tail -1`
RC=$?
#A: #antenna ports C: CP type ; P: PHICH duration ; PR: PHICH resource type
#CID A      fc   foff RXPWR C nRB P  PR CrystalCorrectionFactor
#423 2  731.5M   874h -5.46 N  25 N 1/6 1.0000011951772214136

CID=`echo $RES | awk '{print $1}'`
A=`echo $RES | awk '{print $2}'`
FC=`echo $RES | awk '{print $3}'`
FOFF=`echo $RES | awk '{print $4}' | grep -Eo '^[0-9]+'` 
RXPWR=`echo $RES | awk '{print $5}'`
CRYSTAL=`echo $RES | awk '{print $10}'`
if [ "$CID" == "" ]; then run $1 $2; fi

}
run $1 $2
echo "cellsearch,host=$HOSTNAME,CID=$CID,fc=$FC,serial=$2,i=$1,rc=$RC foff=$FOFF,RXPWR=$RXPWR,CRYSTAL=$CRYSTAL"
