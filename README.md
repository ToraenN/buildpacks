# buildpacks.py
The build pack script for PvXwiki.

This is a python 2.7.13 script for collecting all of the build template codes for given categories on the wiki.
Danny provided the original version of this script (which can be found in the history on the script's PvXwiki page).

# Program Flow
1. At start the script asks for parameters from the user and checks if the wiki can be reached. 
2. If successful, then the script builds the list of builds to compile by visiting each category (builds that show up in multiple categories are only added once).
3. It visits each build page in that list. It retrieves from each page: all template codes, the rating, and the gametypes. 
4. Each build is then written to all relevant directories (Each gametype gets a directory with subdirectories for each rating - builds go only in the rating subdirectories) in the 'PvX Build Packs' folder. 

Parameters modify this basic program flow as follows.

# Parameters
If none are entered, the script will select the 'All working PvP builds' and 'All working PvE builds' categories (all of the currently vetted builds) and process them as stated in the Program Flow section. The parameters that can be entered are:

a : to save builds with an empty primary profession because some build editor programs can read them.

c : to have the program list all preprogrammed categories and ask the user which ones should be compiled from.

q : to ask the user for a single category to compile. Takes priority over c.

l : will limit the output directories to just a single user-defined directory ('user-directory/rating').

p : sorts the builds by 'profession/gametype/rating' instead of 'gametype/rating'. Is overridden by 'l'. It is recommended to also specify 'r' to sort by just 'profession/gametype', but not required.

r : removes the rating subdirectories. Builds are saved directly to the gametype directories (or user-defined directory, if 'l' was specified). The rating is appended to the title of the build (or the team subdirectory for team builds).

w : writes the progress messages and build information + directories to the text file normally reserved for HTTPConnection errors.

z : blocks most of the progress messages from standard output. Errors are still displayed.

The essential version of the script does not ask for any parameters and just collects the tested builds.

# Notes
The script only recognizes builds in the 'Build:' and 'Archive:' namespaces on PvXwiki.

By default it will skip any builds that have an open primary profession (Guild Wars does not recognize template codes that lack a primary profession).

Team builds are saved in their own subfolders and each template is named: Team - Build Name - #.txt. The script does not pull the builds' names or profession prefixes from the page to name the file with.

Non-team builds that have separate player and hero template codes will appropriately be sorted to the 'general' (player build) and 'hero' (hero build) folders.

# Logging
Any HTTPConnection errors are automatically logged to 'buildpackslog.txt' for review. Optionally, you can specify 'w' to add all messages, prompts, answers, and per-build info to the log.

The httpdebugger function records the attempt (the starting check, the category, or the build), the response code, the response reason, and the headers returned. The http debugger is only called when the response is something other than a 200 code (reason: OK) and is not called on a 301 code (reason: Moved Permanently) for build pages (the redirect is followed).

The build-writing log records the build attempted, the gametypes found, the ratings found, the build template codes found, and the directories created and saved to.
