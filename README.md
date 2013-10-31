webnotice_ics
=============

Crawl webnotice and convert it to ICS format.

Dependencies:
 - tidy (just the program, not the python library)
 - wget
 - pytz (python lib)

Usage: python webnotice.py

Things you might want to modify:

In tidyxml.py:
 - tidycmd - change to the location of tidy

In webnotice.py
 - webnotice - change this to the root of your http webnotice installation

Output:
  - creates folder webnotice/ containing all the .ics files
  - autodetects the categories/departments available and generates the appropriate ics
