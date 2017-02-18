# buildpacks.py
The build pack script for PvXwiki
This is a python 2.7 script for collecting all of the build template codes for given categories on the wiki.
Danny provided the original version of this script (which can be found in the history on the script's PvXwiki page).

# Initial Setup
The script starts by asking the user a few questions (the default for each is 'n'). First, it asks if the build writing debugger should run (and which mode if 'y'). Then it goes through the preprogrammed categories, asking the user if each one should be compiled. If the user does not answer 'y' to any of them, the script will prompt the user for a single category from PvXwiki.

# Program Flow
The script then builds the list of pages for one of its categories, and then visits each page in that category. It retrieves from each page: all template codes, the build vetting rating, and the gametype categories. Each build is then written to all relevant directories in the 'PvX Build Packs' folder. Once a category is complete, it repeats for the next category until all categories are complete.

# Debugging
The script has two debugging outputs: buildpackshttpdebug.txt (for HTTPConnection errors) and buildpacksdebug.txt (for the build-writing portion of the script).

The http log records the attempt (the starting check, the category, or the build), the response code, the response reason, and the headers returned. The http debugger is only called when the response is something other than a 200 code (reason: OK).

The build-writing log records the build attempted, the categories found, the ratings found, the build template codes found, and the directories created and saved to. The output can also be set to go to StdOut instead of a text file (via the questions at start).
