# buildpacks
The build pack script for PvXwiki
This is a python 2.7 script for collecting all of the build template codes for given categories on the wiki.
Danny provided the original version of this script (which can be found in the history on the script's PvXwiki page).

The changes I've made before creating this repository were to:
-Have the script only visit each page once, instead of once for each category the build was in.
-Add debugging output to troubleshoot builds that fail to be reached or saved.
-Extend the categories supported to the various archive, untested, and trash categories.
