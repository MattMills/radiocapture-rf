# radiocapture-rf
## What is this?
This repo hosts the RF side of radiocapture.com's trunked radio system bulk collection platform. It is capable of using multiple networked computers and multiple SDR radios to demodulate the control channel of P25, EDACS, and Motorola trunking systems, as well as some limited support (alpha quality) for scanning for systems, LTR trunking, and "police scanner" style audio capture.

It is designed to effectively scale to an infinite capacity of trunked systems, captured transmission volume, and dongle bandwidth (more dongles = more available bandwidth, more cpus = more channels and more systems). (There is one remaining feature to be implemented to really make this work well, dongle redis autodiscovery (frontend_connect should autodiscover and use available dongles) and splitting the rc_frontend/receiver.py into one process per dongle. 

This piece of software is not currently, as of the date of this writing (12/11/2019) not what I'd consider a "ready to distribute" application. If you are well versed in Linux and python, you can likely get it running with some effort. The repo in it's current state is the radio platform that is currently running in production. I have left all my existing configurations to provide "example" configurations for people to copy. You will see some identifiers and UUIDs within these configs, these identifiers integrate into the web infrastructure of Radiocapture.com, and can be ignored.

If you'd like to get this running, you should look at the systemd scripts, you need the frontend (side connected to radio via USB, handles channelization), and backend (handles demodulation, metadata coordination and recording). You will also need to create a config.py (or symlink to one).

Here is my 10 minute summary of how it works:

The frontend initializes the SDRs in whatever configured frequency range, and presents a server interface where clients can connect and request a specific channel be created and forward to them. The frontend will then attach a channel, and output to a UDP sink (might be something better now, I forget). On the backend side, a control_demodulator is listening to that sink and doing the actual RF demodulation, which is passed into redis for distribution to other services. The backend is effectively a bunch of microservices that work together to track & record all ongoing transmissions and do some amount of deduplication. This entire setup is designed such that it can be scaled across as many servers/computers as necessary (although there are a few caveats/things I never got around to implementing in how it actually works). Recorded transmissions are decorated with a metadata scheme in their mp3 tags that is designed to be able to be loaded into the Radiocapture.com database. Finally completed mp3s are dropped into an activemq queue for publishing.

Note: The audio this software captures is intended to be handled and managed programatically. While you can view it in a directory and listen to mp3s one after another, it's very tedious. Ideally I'd like to build the functionality into Radiocapture.com to allow anyone to upload their own data... and I think we're going in that direction slowly.


## Do you have any large architecture diagrams?

(Note: software in this repo is to the right of "upload process")

![](https://github.com/MattMills/radiocapture-rf/blob/master/doc/Radiocapture%201.0%20Architecture.png)


## Why is it being released?

Well, I can't really work on it anymore. I mean I can, but I haven't been able to get interested in it, and I need to find a way to make money (a day job).

Additionally, I like building large infrastructure projects, and I'm secretly hoping a bunch of people will become interested in a national/worldwide version of RadioCapture, both for the public accountability aspects and for the interesting historical value that the data holds. 

This was an interesting project to me when I first moved to Denver, to reverse engineer these really strange radio protocols and figure out how to pick them apart and capture them...

## How can I help make this better?

At this point, pull requests are welcome (small PRs preferred). I've linked the Radiocapture LLC Patreon to this repo, those resources are currently used to support and grow the capacity of the website.

Contibutors will need to sign a contributor license agreement with Radiocapture LLC which I don't have yet, so PRs will not be accepted until that is in place (but feel free to submit them pending). 

Also, specifically I don't know what I was thinking when I used the terms frontend and backend, then subsequently flipped the meaning within the systemd scripts... so someone could probably fix that by removing all frontends and backends and replacing them with names that make sense.

## Where can I find help?

You can find me in [https://radiocapture.chat](https://radiocapture.chat).

In the future I plan to have a release build that is more friendly to people who aren't linux sysadmins (like a bootable DVD). I'm not sure what functionality that release will have yet though.

## How to install:
### WARNING WARNING WARNING: Install instructions are still work in progress

These are my install instruction notes from a fresh ubuntu 20.04 server install

```
sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list
apt-get update
apt-get install gnuradio gnuradio-dev python3-redis gr-osmosdr librtlsdr-dev libuhd-dev  
apt-get install libhackrf-dev libitpp-dev libpcap-dev git python3-pip redis-tools redis-server activemq
apt-get build-dep gnuradio
pip3 install stompest manhole multiprocessing_logging
cd /opt
git pull git@github.com:MattMills/radiocapture-rf.git

# OP25 build DEFINITELY doesn't work right now
# needs some code changes to work with python 3.8 and swig right TODO

git pull git@github.com:MattMills/op25.git
cd op25
mkdir build
cd build
cmake ..
make -j 8
make install

# </ op25 build>

cd /opt/radiocapture-rf
#make a config.py
cd rc_frontend
ln -s ../config.py

#activemq stomp enable
#activemq instance enable
#activemq start
#redis start

#if cluster:
#activemq bind 0.0.0.0
#redis bind 0.0.0.0
#firewall warning
#put all redis servers into the config
#set hosts file hostname to LAN IP not 127.0.0.1
#systemctl files install
service radiocapture-channelizer start
service radiocapture-rf start

```

