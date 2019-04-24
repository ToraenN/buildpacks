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
    conn.request('GET', '/api.php?action=parse&prop=text&page=' + i.replace(' ','_') + '&format=php')
    response = conn.getresponse()
    page = str(response.read())
    conn.close()
    if response.status == 200:
        # Grab the codes first
        codes = re.findall('<input id="gws_template_input" type="text" value="(.*?)"', page)
        # If no template codes found on the build page, prompt user to fix the page
        if len(codes) == 0:
            return build_error('Warning: No build template found on page for ' + i + '.', i)
        # Template discrepancies (missing profession, impossible atts, duplicated skills, etc.) cause this error
        for c in codes:
            if c == '':
                return build_error('Warning: Blank code found in ' + i + '! (code #' + str(codes.index(c) + 1) + ')', i)
        # Grab all the other build info
        fluxes = id_fluxes(page)
        ratings = id_ratings(page)
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
            for j in codes:
                num += 1
                builddatalist += [BuildData(file_name_sub(i) + ' - ' + str(num) + '.txt', j, directories)]
        else:
            builddatalist += [BuildData(file_name_sub(i) + rateinname + '.txt', codes[0], directories)]
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
    filename = build.replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'')
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
    if 'This build is part of the current metagame.' in page:
        ratings += ['Meta']
    elif 'This build is provisionally vetted' in page:
        ratings += ['Provisional']
    # A second if statement because builds can have none or one of Meta/Provisional and one of Great/Good
    if 'in the range from 4.75' in page:
        ratings += ['Great']
    elif 'in the range from 3.75' in page:
        ratings += ['Good']
    elif 'in the <i>trial</i> phase.' in page:
        ratings += ['Trial']
    elif 'This build is currently being tested.' in page:
        ratings += ['Testing']
    if ratings == []:
        ratings = ['Nonrated']
    return ratings

def id_fluxes(page):
    rawfluxes = re.findall('>(Affected by [^<>]*?) Flux<', page)
    if len(rawfluxes) == 0:
        fluxes = ['Unaffected by Flux']
    else:
        fluxes = []
        for rf in rawfluxes:
            fluxes.append(rf.replace('\\', ''))
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
