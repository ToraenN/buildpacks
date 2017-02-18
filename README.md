# buildpacks.py
The build pack script for PvXwiki
This is a python 2.7.13 script for collecting all of the build template codes for given categories on the wiki.
Danny provided the original version of this script (which can be found in the history on the script's PvXwiki page).

# Initial Setup
The script starts by asking the user a few questions (the default for each is 'n'). First, it asks if the build writing debugger should run (and which mode if 'y'). Then it goes through the preprogrammed categories, asking the user if each one should be compiled. If the user does not answer 'y' to any of them, the script will prompt the user for a single category from PvXwiki.

# Program Flow
The script then builds the list of pages by visiting each category (builds that show up in multiple categories are only added once), and then visits each page in that list. It retrieves from each page: all template codes, the rating, and the gametypes. Each build is then written to all relevant directories (Each gametype gets a directory with subdirectories for each rating - builds go only in the rating subdirectories) in the 'PvX Build Packs' folder.

# Notes
The script only recognizes builds in the 'Build:' and 'Archive:' namespaces on PvXwiki.

It will skip any builds that have an open primary profession (Guild Wars does not recognize template codes that lack a primary profession so there is no point in saving them).

Team builds are saved in their own subfolders and each template is named: Team - Build Name - #.txt. The script does not pull the builds' names or profession prefixes from the page to name the file with.

Non-team builds that have separate player and hero template codes will appropriately be sorted to the 'general' (player build) and 'hero' (hero build) folders.

# Debugging
The script has two debugging outputs: buildpackshttpdebug.txt (for HTTPConnection errors) and buildpacksdebug.txt (for the build-writing portion of the script).

The http log records the attempt (the starting check, the category, or the build), the response code, the response reason, and the headers returned. The http debugger is only called when the response is something other than a 200 code (reason: OK) and is not called on a 301 code (reason: Moved Permanently) for build pages (the redirect is followed).

The build-writing log records the build attempted, the gametypes found, the ratings found, the build template codes found, and the directories created and saved to. The output can also be set to go to StdOut instead of a text file (via the questions at start).
