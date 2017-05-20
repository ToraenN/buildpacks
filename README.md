# buildpacks.py
The build pack script for PvXwiki.

This is a python 3.6.1 script for collecting all of the build template codes for given categories on the wiki.
Danny provided the original version of this script (which can be found in the history on the script's PvXwiki page).

# Program Flow
1. At start the script asks for parameters from the user and checks if the wiki can be reached. 
2. If successful, then the script builds the list of builds to compile by visiting each category (builds that show up in multiple categories are only added once).
3. It visits each build page in that list. It retrieves from each page: all template codes, the rating, the flux categories and the gametypes. 
4. Each build is then written to all relevant directories (by default, all builds are sorted by Gametype and Rating in that order) in the 'PvX Build Packs' folder. 

Parameters modify this basic program flow as follows.

# Parameters
If none are entered, the script will select the 'All working PvP builds' and 'All working PvE builds' categories (all of the currently vetted builds) and process them as stated in the Program Flow section. The parameters that can be entered are:

a : to save builds with an empty primary profession because some build editor programs can read them.

c : to have the program list all preprogrammed categories and ask the user which ones should be compiled from.

f : adds flux sort.

g : removes the gametype sort.

h : displays the list of available parameters. Any other parameters are ignored and the prompt is brought up again.

l : will limit the output directories to just a single user-defined directory. All other sorts are ignored.

p : adds profession sort.

q : to manually enter the categories to compile. Takes priority over c.

r : removes the rating sort. The rating is appended to the title of the build (or the team subdirectory for team builds).

s : blocks most of the progress messages from standard output. Errors are still displayed.

w : writes all progress messages, HTTP error messages and build information + directories to a text file.

z : Creates zip archives instead of saving individual text files.

The sorts are ordered: Flux/Profession/Gametype/Rating

The essential version of the script does not ask for any parameters and just collects the tested builds.

# Notes
The script only recognizes builds in the 'Build:' and 'Archive:' namespaces on PvXwiki.

By default it will skip any builds that have an open primary profession (Guild Wars does not recognize template codes that lack a primary profession).

Team builds are saved in their own subfolders and each template is named: Team - Build Name - #.txt. The script does not pull the builds' names or profession prefixes from the page to name the file with.

Non-team builds that have separate player and hero template codes will appropriately be sorted to the 'general' (player build) and 'hero' (hero build) folders.
