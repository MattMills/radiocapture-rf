# radiocapture-rf
## What is this?
This repo hosts the RF side of radiocapture.com's trunked radio system bulk collection platform. It is capable of using multiple networked computers and multiple SDR radios to demodulate the control channel of P25, EDACS, and Motorola trunking systems, as well as some limited support (alpha quality) for scanning for systems, LTR trunking, and "police scanner" style audio capture.

This piece of software is not currently, as of the date of this writing (12/11/2019) not what I'd consider a "ready to distribute" application. If you are well versed in Linux and python, you can likely get it running with some effort. The repo in it's current state is the radio platform that is currently running in production. I have left all my existing configurations to provide "example" configurations for people to copy.

If you'd like to get this running, you should look at the systemd scripts, you need the frontend (side connected to radio via USB, handles channelization), and backend (handles demodulation, metadata coordination and recording). You will also need to create a config.py (or symlink to one).

Here is my 10 minute summary of how it works:

The frontend initializes the SDRs in whatever configured frequency range, and presents a server interface where clients can connect and request a specific channel be created and forward to them. The frontend will then attach a channel, and output to a UDP sink (might be something better now, I forget). On the backend side, a control_demodulator is listening to that sink and doing the actual RF demodulation, which is passed into redis for distribution to other services. The backend is effectively a bunch of microservices that work together to track & record all ongoing transmissions and do some amount of deduplication. This entire setup is designed such that it can be scaled across as many servers/computers as necessary (although there are a few caveats/things I never got around to implementing in how it actually works). Recorded transmissions are decorated with a metadata scheme in their mp3 tags that is designed to be able to be loaded into the Radiocapture.com database. Finally completed mp3s are dropped into an activemq queue for publishing.

Note: The audio this software captures is intended to be handled and managed programatically. While you can view it in a directory and listen to mp3s one after another, it's very tedious. Ideally I'd like to build the functionality into Radiocapture.com to allow anyone to upload their own data... and I think we're going in that direction slowly.

## Why is it being released?

Well, I can't really work on it anymore. I mean I can, but I haven't been able to get interested in it, and I need to find a way to make money (a day job).

Additionally, I like building large infrastructure projects, and I'm secretly hoping a bunch of people will become interested in a national/worldwide version of RadioCapture, both for the public accountability aspects and for the interesting historical value that the data holds. 

This was an interesting project to me when I first moved to Denver, to reverse engineer these really strange radio protocols and figure out how to pick them apart and capture them...

## How can I help make this better?

At this point, pull requests are welcome (small PRs preferred). I've linked the Radiocapture LLC Patreon to this repo, those resources are currently used to support and grow the capacity of the website.

Contibutors will need to sign a contributor license agreement with Radiocapture LLC which I don't have yet, so PRs will not be accepted until that is in place.

## Where can I find help?

Well... you can't. 

You can find me in [https://radiocapture.chat](https://radiocapture.chat) and ask whatever you like, but as I don't intend this to be a product for anyone to use (sorry! it just isn't documented/written well enough for that yet, it needs work to make it easy to use), I may not be much help. 

Let me put it this way: I am happy to provide direction, guidance, and help to anyone that wants to contribute to the project, via Patreon or with your own efforts to improve the project. Unfortunately my time is limited (and I need to spend it strategically to remain housed/fed).

But don't let that discourage you; I didn't know anything about radio before I started working on this app.
