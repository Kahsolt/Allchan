# Allchan

    A image crawler for xChan(4chan/8ch/...)

----

# xChan Support
  [ ] 2chan
  [x] 4chan  
  [x] 8chan
  [ ] ...

# Quick Start
  `pip3 install -r requirement.txt`
  `make watch`
  follow the prompting message, enter thread urls that you'd like to watch

# User Setting File
  - [Config](/allchan.json), these configs override defaults in [settings.py](/allchan/settings.py)
  - [Watchlist](/allchan.watchlist), manaully create one if not exists, one thread url per line

# Dev/Debug
  [Makefile](/Makefile), some frequently used targets
  [debug script](/debug.py), I use it to correct database if something is broken

----
   
by kahsolt
2018/11/24