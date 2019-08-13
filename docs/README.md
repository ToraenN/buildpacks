These are the build pack scripts for PvXwiki.

They are python 3.6 scripts for collecting all of the build template codes for given categories on the wiki.
Danny provided the original version of this script (which can be found in the history on the script's PvXwiki page).

# Program Flow
1. At start the full version of the script asks for parameters from the user and checks if the wiki can be reached. 
2. If successful, then the script builds the list of builds to compile by visiting each category (builds that show up in multiple categories are only added once).
3. It visits each build page in that list. It retrieves from each page: all template codes, the rating, the flux categories and the gametypes. 
4. Each build is then written to all relevant directories in the 'PvX Build Packs' and/or the 'Zipped Build Packs' folder. 

Parameters modify this basic program flow as follows.

# Parameters
If none are entered, the script will select the 'All working PvP builds', 'All working PvE builds', 'Affected by Flux', 'Untested testing builds' and 'Trial Builds' categories (all of the currently vetted and vetting in progress builds) and process them as stated in the Program Flow section. The parameters that can be entered are:

a : to not save builds with an empty primary profession (some build editor programs can read them but Guild Wars cannot).

b : prevents the consolidated zip files from being made.

c : to have the program list all preprogrammed categories and ask the user which ones should be compiled from.

h : displays the list of available parameters. Any other parameters are ignored and the prompt is brought up again.

l : limits builds saved based on sort criteria.

m : to manually enter categories to compile.

o : allows the user to add, remove, and reorganize the sorting. Builds can be sorted by Flux, Primary, Secondary, Gametype and Rating in any order. By default, builds are sorted by Gametype only (the rating is placed in the filename).

s : blocks most of the progress messages from standard output. Errors are still displayed.

t : save text files even if saving zip files.

w : writes all progress messages, HTTP error messages and build information + directories to a text file.

y : forces the consolidated zip files to be made even if sort/category/'b' options are enabled.

z : Creates zip archives instead of saving individual text files. Will create the three consolidated zip files if no sort or category parameters are entered.

fluxbuildpacks.py creates the standard Flux build pack as a zip without any user input. Made as a separate script because of program flow issues with trying to integrate it into buildpacks.py (not that I tried very hard). 

# Notes
The scripts only recognize builds in the 'Build:' and 'Archive:' namespaces on PvXwiki.

Team builds are saved in their own subfolders and each template is named: Team - Build Name - #.txt. The scripts do not pull the builds' names or profession prefixes from the page to name the file with.

Non-team builds that have separate player and hero template codes will appropriately be sorted to the 'general' (player build) and 'hero' (hero build) folders.
