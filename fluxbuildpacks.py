# License for this script is the CC BY-NC-SA 2.5: https://creativecommons.org/licenses/by-nc-sa/2.5/
# The original author of this script is Danny, of PvXwiki: http://gwpvx.gamepedia.com/UserProfile:Danny11384
import http.client
import re
import os
import os.path
import zipfile
from collections import deque

class BuildData:
    '''Holds the data necessary for saving a build.'''
    def __init__(self, filename, code, directories):
        self.filename = filename
        self.code = code
        self.directories = set(directories)
        self.packs = {'Flux Build Packs'}

class PackData:
    '''Object for handling a pack.'''
    def __init__(self, name):
        self.name = name
        self.builds = set()

    def add(self, build):
        if self.name in build.packs:
            self.builds.add(build)

def setup_categories():
    categories = ['Affected_by_Flux']
    # Fetch the builds from the categories.
    pagelist = deque()
    conn = http.client.HTTPSConnection('gwpvx.gamepedia.com')
    while categories:
        cat = categories.pop()
        catname = re.sub(r'&cmcontinue=page\|.*\|.*', '', cat).replace('_',' ')
        print("Assembling build list for " + catname + "...")
        try:
            conn.request('GET', '/api.php?action=query&format=php&list=categorymembers&cmlimit=max&cmtitle=Category:' + cat)
        except:
            input('Internet connection lost.')
            return
        response = conn.getresponse()
        page = str(response.read())
        conn.close()
        # Check if a continuation was offered due to the category having more members than the display limit
        continuestr = re.search(r'"(page\|.*?\|.*?)"', page)
        if continuestr:
            categories += [catname.replace(' ','_') + '&cmcontinue=' + continuestr.group(1)]
        if response.status == 200:
            catlist = re.findall(r':"(Build:.*?)";\}', page)
            for buildname in catlist:
                current = buildname.replace("\\'","'")
                if not current in pagelist:
                    pagelist += [current]
            print("Builds from " + catname + " added to list!")
        else:
            if build_error('HTTPConnection error encountered: ' + str(response.status) + ' - ' + str(response.reason), cat) != None:
                categories.append(cat)
    print(str(len(pagelist)) + ' builds found!')
    return pagelist

def get_build(i):
    print("Attempting " + i.replace('_',' ') + "...")
    conn = None # conn must be purged between build reloads to get the new version of the page
    conn = http.client.HTTPSConnection('gwpvx.gamepedia.com')
    conn.request('GET', '/api.php?action=parse&prop=text|wikitext&page=' + i.replace(' ','_') + '&format=php')
    response = conn.getresponse()
    page = str(response.read())
    conn.close()
    if response.status == 200:
        # Grab the codes first
        codes = id_codes(page)
        # If no template codes found on the build page, prompt user to fix the page
        if len(codes) == 0:
            return build_error('Warning: No build template found on page for ' + i + '.', i)
        # Template discrepancies (missing profession, impossible atts, duplicated skills, etc.) cause this error
        for c in codes:
            if c[2] == '':
                return build_error('Warning: Blank code found in ' + i + '! (code #' + str(codes.index(c) + 1) + ')', i)
        # Grab all the other build info
        fluxes = id_fluxes(page)
        ratings = id_ratings(page)
        if len(ratings) == 0:
            return build_error('Warning: No rating found on page for ' + i + '.', i)
        # Create the directories
        dirlevels = [fluxes]
        rateinname = ' - ' + str(ratings).replace('[','').replace(']','').replace("'",'').replace(',','-').replace(' ','')
        if 'Team' in i and len(codes) > 1:
            dirlevels.append([(file_name_sub(i) + rateinname)])
        directories = directory_tree(dirlevels)
        # Check to see if the build is a team build
        builddatalist = []
        if 'Team' in i and len(codes) > 1:
            num = 0
            for position, title, code in codes:
                if position == "": # If code is not for a variant
                    num += 1
                    builddatalist += [BuildData(str(num) + ' Standard.txt', code, directories)]
                else: # If code is for a variant (variants without a defined position will be skipped for team builds)
                    if title == "{{{name}}}":
                        print(i + " has an unnamed variant for position " + str(position) + ", which will be saved under a generic name.")
                        tempname = ''
                    else:
                        tempname = ' - ' + title
                    builddatalist += [BuildData(file_name_sub(str(position) + ' Variant' + tempname + '.txt'), code, directories)]
        else:
            # Sort codes between mainbar and variant bars
            mainbars = []
            variants = []
            for position, title, code in codes:
                if title == "":
                    mainbars.append(code) # Only retrieve code for mainbars
                else:
                    variants.append((title, code)) # Skip the position argument (as we are not in team builds here)
            try:
                builddatalist += [BuildData(file_name_sub(i) + rateinname + '.txt', mainbars[0], directories, pvx)]
            except:
                pass # All templates were enclosed in {{variantbar}}, which is a valid page format for certain builds
            # Handle any variant bars
            num = 0
            for title, code in variants:
                num += 1
                if title == "{{{name}}}":
                    print(i + " has an unnamed variant, which will be saved under a generic name. Please fix the issue for future build packs.")
                    tempname = i + ' Variant ' + str(num)
                else:
                    tempname = title
                builddatalist += [BuildData(file_name_sub(tempname) + rateinname + '.txt', code, directories)]
        print(i + " retrieved.")
        return builddatalist
    elif response.status == (301 or 302):
        # Follow the redirect
        headers = str(response.getheaders())
        newpagestr = re.findall("gwpvx.gamepedia.com/(.*?)'\)", headers)
        newpagename = newpagestr[0].replace('_',' ')
        print('Redirection...')
        return newpagename
    else:
        build_error('HTTPConnection error encountered: ' + str(response.status) + ' - ' + str(response.reason), i)

def write_builds_zip(pack):
    with zipfile.ZipFile(pack.name + '.zip', 'a') as ZipPack:
        for build in pack.builds:
            for d in build.directories:
                archivename = d + build.filename
                try:
                    ZipPack.getinfo(archivename)
                except KeyError:
                    ZipPack.writestr(archivename, build.code)
                else:
                    print(archivename + " already present in " + pack.name + ".zip!")

def file_name_sub(build):
    filename = build.replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'').replace("\\", "")
    return filename

def directory_tree(dirlevels):
    while len(dirlevels) < 2:
        dirlevels += [['']]
    directories = []
    for a in dirlevels[0]:
        for b in dirlevels[1]:
            addeddir = a + '/' + b + '/'
            # '//' will mess up zip writing
            while '//' in addeddir:
                addeddir = addeddir.replace('//','/')
            directories += [addeddir]
    return directories

def id_ratings(page):
    ratings = []
    # First if statement for special status
    if re.search('\|meta=yes|{{meta-build', page, re.I):
        ratings += ['Meta']
    elif re.search('\|provisional=yes|{{provisional-build', page, re.I):
        ratings += ['Provisional']
    # Second if statement for rating
    if re.search('\|rating=great|{{great-build', page, re.I):
        ratings += ['Great']
    elif re.search('\|rating=good|{{good-build', page, re.I):
        ratings += ['Good']
    elif re.search('\|rating=trial|{{untested-trial|{{trial-build', page, re.I):
        ratings += ['Trial']
    elif re.search('\|rating=testing|{{untested-testing|{{testing-build', page, re.I):
        ratings += ['Testing']
    return ratings

def id_codes(page):
    # Each retrieved code will be a 3-tuple of the format (position, title, code). The first two will be blank for any code not wrapped in Template:Variantbar
    regex = re.compile('(?s)(?:<th style=""><big>(?:Position (?P<position>\d+)&#160;){0,1}Variant: (?P<title>.*?)<\/big>.*?){0,1}<input id="gws_template_input" type="text" value="(?P<code>.*?)"')
    codes = re.findall(regex, page)
    return codes

def id_fluxes(page):
    regex = re.compile('{{[Ff]lux\|(.*?)[\|}]')
    rawfluxes = re.findall(regex, page)
    fluxes = []
    for rf in rawfluxes: # Xinrae's Revenge
        flux = rf.replace("\\", "")
        fluxes.append(flux)
    return fluxes

def build_error(error, build):
    print(error)
    resolution = input('Please choose one of the following options:\ne = exit the script\nr = reattempt the build (you should fix the issue first)\ns = skip the build\nType the letter corresponding to your choice: ')
    while re.search('^[ers]$', resolution) == None:
        resolution = input('Please enter a valid option: ')
    if resolution == 'e':
        raise SystemExit()
    elif resolution == 'r':
        return build
    elif resolution == 's':
        return None

if __name__ == "__main__":
    conn = http.client.HTTPSConnection('gwpvx.gamepedia.com')
    try:
        conn.request('GET', '/PvX_wiki')
    except:
        print('Turn on your internet scrub.')
    else:
        r1 = conn.getresponse()
        conn.close()
        if r1.status == 200:
            print("Holy shit! Curse is actually working. Now let's start getting that build data.")
        else:
            print("Curse's servers are (probably) down. Try again later.\nThe provided error code is: " + str(r1.status) + ' - ' + str(r1.reason))
            raise SystemExit()
        pagelist = setup_categories()
        buildqueue = deque()
        packnames = set()
        savedpacks = deque()
        while pagelist:
            result = get_build(pagelist.popleft())
            if isinstance(result, list) == True:
                buildqueue += result
                for build in result:
                    packnames.update(build.packs)
            elif isinstance(result, str) == True:
                pagelist.appendleft(result)
        while packnames:
            savedpacks.append(PackData(packnames.pop()))
        while buildqueue:
            currentbuild = buildqueue.popleft()
            for pack in savedpacks:
                pack.add(currentbuild)
        while savedpacks:
            currentpack = savedpacks.popleft()
            print('Saving pack ' + currentpack.name + ' (' + str(len(currentpack.builds)) + ' files)...')
            write_builds_zip(currentpack)
            print('Pack ' + currentpack.name + ' saved!')
    input("Script complete.")
