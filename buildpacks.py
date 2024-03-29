# License for this script is the CC BY-NC-SA 2.5: https://creativecommons.org/licenses/by-nc-sa/2.5/
# The original author of this script is Danny, of PvXwiki: http://gwpvx.fandom.com/UserProfile:Danny11384
import http.client
import re
import os
import os.path
import time
import zipfile
from collections import deque

class BuildData:
    '''Holds the data necessary for saving a build.'''
    def __init__(self, filename, code, directories, pvx):
        self.filename = filename
        self.code = code
        self.directories = set(directories)
        self.packs = set()
        for d in self.directories:
            try:
                pack = re.search(r"^./PvX Build Packs/([\w ']*)[/$]", d).group(1)
            except AttributeError:
                pack = 'PvX Build Packs'
            self.packs.add(pack)
        if re.search(r'[bclmo]', parameters) == None or 'y' in parameters:
            pvx.add('All')
            if 'PvE' in pvx:
                self.packs.add('PvE Build Packs')
            if 'PvP' in pvx:
                self.packs.add('PvP Build Packs')
            self.packs.add('All Build Packs')

class PackData:
    '''Object for handling a pack.'''
    def __init__(self, name):
        self.name = name
        self.builds = set()

    def add(self, build):
        if self.name in build.packs:
            self.builds.add(build)

def setup_categories():
    # Check for category selection modes. If none of these, just grab all vetting and vetted builds.
    categories = []
    if 'm' in parameters:
        manualcatentry = print_prompt('Enter category (leave blank to end entry): ')
        while manualcatentry != '':
            categories += [manualcatentry.replace(' ','_')]
            manualcatentry = print_prompt('Enter category (leave blank to end entry): ')
    if len(categories) == 0:
        # Default to all currently vetted and vetting builds.
        print_log("Using default categories.", "yes")
        categories = ['All_working_PvP_builds', 'All_working_PvE_builds', 'All_untested_testing_PvE_builds', 'All_untested_testing_PvP_builds', 'All_untested_trial_PvE_builds', 'All_untested_trial_PvP_builds']

    # Fetch the builds from the categories.
    pagelist = deque()
    conn = http.client.HTTPSConnection('gwpvx.fandom.com')
    while categories:
        cat = categories.pop()
        catname = re.sub(r'&cmcontinue=page\|.*\|.*', '', cat).replace('_',' ')
        print_log("Assembling build list for " + catname + "...")
        try:
            conn.request('GET', '/api.php?action=query&format=php&list=categorymembers&cmlimit=max&cmtitle=Category:' + cat)
        except:
            print_prompt('Internet connection lost.')
            return
        response = conn.getresponse()
        page = str(response.read())
        conn.close()
        # Check if a continuation was offered due to the category having more members than the display limit
        continuestr = re.search(r'"(page\|.*?\|.*?)"', page)
        if continuestr:
            categories += [catname.replace(' ','_') + '&cmcontinue=' + continuestr.group(1)]
        if response.status == 200:
            catlist = re.findall(r':"((?:Build|Archive):.*?)";\}', page)
            for buildname in catlist:
                current = buildname.replace("\\'","'")
                if not current in pagelist:
                    pagelist += [current]
            print_log("Builds from " + catname + " added to list!")
        else:
            if build_error('HTTPConnection error encountered: ' + str(response.status) + ' - ' + str(response.reason), cat, response.getheaders()) != None:
                categories.append(cat)
    print_log(str(len(pagelist)) + ' builds found!', 'yes')
    return pagelist

def get_build(i, dirorder, rdirs):
    primary, secondary = id_profession(i)
    if rdirs[1] != None:
        if not primary[0] in rdirs[1]:
            print_log(i + ' skipped. Primary profession doesn\'t match restriction.')
            return
    if rdirs[2] != None:
        if not secondary[0] in rdirs[2]:
            print_log(i + ' skipped. Secondary profession doesn\'t match restriction.')
            return
    # Check to see if the build has an empty primary profession as that would generate an invalid template code in Guild Wars (but not in build editors)
    if 'Any/' in i and 'a' in parameters:
        print_log(i + " skipped (empty primary profession).")
        return
    print_log("Attempting " + i.replace('_',' ') + "...")
    conn = None # conn must be purged between build reloads to get the new version of the page
    conn = http.client.HTTPSConnection('gwpvx.fandom.com')
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
        gametypes, pvx = id_gametypes(page)
        if pvx == {'PvU'}:
            return build_error('Warning: No gametypes found on page for ' + i + '.', i)
        ratings = id_ratings(page)
        if len(ratings) == 0:
            return build_error('Warning: No rating found on page for ' + i + '.', i)
        if 'w' in parameters:
            log_write('Fluxes found: ' + str(fluxes) + '\r\nProfession: ' + str(primary[0]) + '/' + str(secondary[0]) + '\r\nGametypes found: ' + str(gametypes) + '\r\nPvX found: ' + str(pvx) + '\r\nRatings found: ' + str(ratings) + '\r\nCodes found: ' + str(codes))
        # Check for restrictions and skip build if a restriction has no matches
        rfluxes = []
        rgametypes = []
        rratings = []
        if rdirs[0] != None:
            for f in fluxes:
                if f in rdirs[0]:
                    rfluxes += [f]
            if len(rfluxes) == 0:
                print_log('Fluxes don\'t match restriction. Skipping.')
                return
            fluxes = rfluxes
        # Profession checks (rdirs[1] and rdirs[2]) are done earlier because we can skip unnecessary page loads that way.
        if rdirs[3] != None:
            for g in gametypes:
                if g in rdirs[3]:
                    rgametypes += [g]
            if len(rgametypes) == 0:
                print_log('Gametypes don\'t match restriction. Skipping.')
                return
            gametypes = rgametypes
        if rdirs[4] != None:
            for r in ratings:
                if r in rdirs[4]:
                    rratings += [r]
            if len(rratings) == 0:
                print_log('Ratings don\'t match restriction. Skipping.')
                return
            ratings = rratings
        # Create the directories
        dirlevels = []
        for o in dirorder:
            if o == 'f':
                dirlevels += [fluxes]
            elif o == 'p':
                dirlevels += [primary]
            elif o == 's':
                dirlevels += [secondary]
            elif o == 'g':
                dirlevels += [gametypes]
            elif o == 'r':
                dirlevels += [ratings]
        # Determine if the rating needs to go in the build name
        if 'r' in dirorder:
            rateinname = ''
        else:
            rateinname = ' - ' + str(ratings).replace('[','').replace(']','').replace("'",'').replace(',','-').replace(' ','')
        if 'Team' in i and len(codes) > 1:
            dirlevels += [[(file_name_sub(i) + rateinname)]]
        directories = directory_tree(dirlevels, pvx)
        # If we're making a log file, inlcude the directory info
        if 'w' in parameters:
            log_write('Directories used: ' + str(directories))
        
        builddatalist = []
        # Team builds
        if 'Team' in i and len(codes) > 1:
            num = 0
            for position, title, code in codes:
                if position == "": # If code is not for a variant
                    num += 1
                    builddatalist += [BuildData(str(num) + ' Standard.txt', code, directories, pvx)]
                else: # If code is for a variant (variants without a defined position will be skipped for team builds)
                    if title == "{{{name}}}":
                        print_log(i + " has an unnamed variant for position " + str(position) + ", which will be saved under a generic name.", "yes")
                        tempname = ''
                    else:
                        tempname = ' - ' + title
                    builddatalist += [BuildData(file_name_sub(str(position) + ' Variant' + tempname + '.txt'), code, directories, pvx)]
        # Single builds
        else:
            # Sort codes between mainbar and variant bars
            mainbars = []
            variants = []
            for position, title, code in codes:
                if title == "":
                    mainbars.append(code) # Only retrieve code for mainbars
                else:
                    variants.append((title, code)) # Skip the position argument (as we are not in team builds here)
            # Prepare mainbar files
            try:
                builddatalist += [BuildData(file_name_sub(i) + rateinname + '.txt', mainbars[0], directories, pvx)]
            except:
                pass # All templates were enclosed in {{variantbar}}, which is a valid page format for certain builds
            # Prepare variant files
            num = 0
            for title, code in variants:
                num += 1
                if title == "{{{name}}}":
                    print_log(i + " has an unnamed variant, which will be saved under a generic name. Please fix the issue for future build packs.", "yes")
                    tempname = i + ' Variant ' + str(num)
                else:
                    tempname = title
                builddatalist += [BuildData(file_name_sub(tempname) + rateinname + '.txt', code, directories, pvx)]
        print_log(i + " retrieved.")
        return builddatalist
    elif response.status == (301 or 302):
        # Follow the redirect
        headers = str(response.getheaders())
        newpagestr = re.findall("gwpvx.fandom.com/(.*?)'\)", headers)
        newpagename = newpagestr[0].replace('_',' ')
        print_log('Redirection...')
        return newpagename
    else:
        build_error('HTTPConnection error encountered: ' + str(response.status) + ' - ' + str(response.reason), i, response.getheaders())

def write_builds_txt(pack):
    for build in pack.builds:
        dirs = []
        for ad in build.directories:
            if pack.name in re.search(r'./PvX Build Packs/(.*?)/', ad)[1]:
                dirs.append(ad)
        for d in dirs:
            fullpath = d + build.filename
            with open(fullpath, 'w') as outfile:
                outfile.write(build.code)

def write_builds_zip(pack):
    if not os.path.isdir('./Zipped Build Packs'):
        os.makedirs('./Zipped Build Packs')
    with zipfile.ZipFile('./Zipped Build Packs/' + pack.name + '.zip', 'a') as ZipPack:
        for build in pack.builds:
            dirs = []
            for ad in build.directories:
                if pack.name in re.search(r'./PvX Build Packs/(.*?)/', ad)[1]:
                    dirs.append(ad.replace('./PvX Build Packs/',''))
            for d in dirs:
                archivename = d + build.filename
                try:
                    ZipPack.getinfo(archivename)
                except KeyError:
                    ZipPack.writestr(archivename, build.code)
                else:
                    print_log(archivename + " already present in " + pack.name + ".zip!")

def file_name_sub(build):
    filename = build.replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'').replace("\\","")
    return filename

def change_dir_order():
    orderstr = print_prompt('Enter the order of the sorts (using "f", "p", "s", "g", "r") or leave blank for no sorting.\r\n   f = flux\r\n   p = primary\r\n   s = secondary\r\n   g = gametype\r\n   r = rating\r\nSort order: ')
    if re.search(r'[^fgprs]', orderstr):
        print_log('Invalid characters in selection.', 'yes')
        return False
    if re.search(r'([fgprs]).*\1', orderstr):
        print_log('Multiple of same character in selection.', 'yes')
        return False
    return orderstr

def restrict_dirs(sort):
    answer = print_prompt('Which ' + sort + ' do you want to save? ')
    while re.search(r'[^\'A-Za-z,\s]', answer) != None:
        answer = print_prompt('Invalid characters entered. Please reenter: ')
    if len(answer) == 0:
        return None
    list = answer.split(',')
    final = []
    for l in list:
        final += [l.strip()]
    return final

def category_selection(catlist):
    categories = []
    for a in catlist:
        answer = print_prompt('Would you like to compile ' + a.replace('_',' ') + '? (y/n) ')
        if answer == 'y':
            categories += [a]
    return categories

def directory_tree(dirlevels, pvx):
    while len(dirlevels) < 6:
        dirlevels += [['']]
    directories = []
    for a in dirlevels[0]:
     for b in dirlevels[1]:
      for c in dirlevels[2]:
       for d in dirlevels[3]:
        for e in dirlevels[4]:
         for f in dirlevels[5]:
          addeddir = './PvX Build Packs/' + a + '/' + b + '/' + c + '/' + d + '/' + e + '/' + f + '/'
          # '//' will mess up zip writing
          while '//' in addeddir:
              addeddir = addeddir.replace('//','/')
          directories += [addeddir]
          # Conditionally add the directories for the consolidated packs
          if re.search(r'[bclmo]', parameters) == None or 'y' in parameters:
              pvx.add('All')
              for area in pvx:
                  directories += [addeddir.replace('./PvX Build Packs/', './PvX Build Packs/' + area + ' Build Packs/')]
    # Only create directories if saving text files
    if 't' in parameters:
        for folder in directories:
            if not os.path.isdir(folder):
                os.makedirs(folder)
    return directories

def id_codes(page):
    # Each retrieved code will be a 3-tuple of the format (position, title, code). The first two will be blank for any code not wrapped in Template:Variantbar
    regex = re.compile('(?s)(?:<th colspan="2" align="left" style="background:#\w{6}"><big>(?:Position (?P<position>\d+)&#160;){0,1}Variant: (?P<title>.*?)<\/big>.*?){0,1}<input class="gws_template_input" type="text" value="(?P<code>.*?)"')
    codes = re.findall(regex, page)
    return codes

def id_fluxes(page):
    regex = re.compile('{{[Ff]lux\|(.*?)[\|}]')
    rawfluxes = re.findall(regex, page)
    fluxes = []
    for rf in rawfluxes: # Xinrae's Revenge
        flux = rf.replace("\\", "")
        fluxes.append(flux)
    if len(fluxes) == 0:
        fluxes = ['Unaffected by Flux']
    return fluxes

def id_profession(name):
    profdict = {'A':'Assassin','Any':'Any','any':'any','D':'Dervish','E':'Elementalist','Me':'Mesmer','Mo':'Monk','N':'Necromancer','P':'Paragon','R':'Ranger','Rt':'Ritualist','Team':'Team', 'W':'Warrior'}
    prefix = (re.search(r':(\w+)\s*/*-*', name)).group(1)
    primary = [profdict[prefix]]
    if primary != ['Team']:
        suffix = (re.search(r':\w+/(\w+)', name)).group(1)
        secondary = [profdict[suffix]]
    else:
        secondary = [None]
    return primary, secondary

def id_gametypes(page):
    # Finds the build-types div, and then extracts the tags. Returns early if div or tags not found.
    builddiv = re.search('<div class="build-types">.*?</div>', page, re.DOTALL)
    if not builddiv:
        return ['Uncategorized'], {'PvU'}
    rawtypes = re.findall('Pv[EP]<br />\w+', builddiv.group())
    if len(rawtypes) == 0:
        return ['Uncategorized'], {'PvU'}
    # Build the gametypes and pvx sets based on the tags
    gametypes = set()
    pvx = set()
    for t in rawtypes:
        pvx.add(re.search('(Pv[EP])<br />', t).group(1))
        if 'team' in t:
            cleanedtype = re.sub('<br />', ' ', t)
        elif len(t) > 12:
            cleanedtype = (re.sub('Pv[EP]<br />', '', t)).title()
        else:
            cleanedtype = re.sub('Pv[EP]<br />', '', t)
        gametypes.add(cleanedtype)
    return gametypes, pvx

def id_ratings(page):
    ratings = []
    # First if statement for special status
    if re.search('\|status=meta', page, re.I):
        ratings += ['Meta']
    elif re.search('\|status=provisional', page, re.I):
        ratings += ['Provisional']
    # Second if statement for rating
    if re.search('\|rating=great', page, re.I):
        ratings += ['Great']
    elif re.search('\|rating=good', page, re.I):
        ratings += ['Good']
    elif re.search('\|rating=trash', page, re.I):
        ratings += ['Trash']
    elif re.search('\|rating=trial', page, re.I):
        ratings += ['Trial']
    elif re.search('\|rating=testing', page, re.I):
        ratings += ['Testing']
    elif re.search('\|rating=archived', page, re.I):
        ratings += ['Archived']
    elif re.search('\|rating=abandoned', page, re.I):
        ratings += ['Abandoned']
    return ratings

def print_prompt(string):
    answer = input(string)
    if 'w' in parameters:
        log_write(string + answer)
    return answer

def print_log(string, alwaysdisplay = 'no'):
    if not 's' in parameters or alwaysdisplay == 'yes':
        print(string)
    if 'w' in parameters:
        log_write(str(string))

def log_write(string):
    actiontime = time.gmtime()
    timestamp = str(actiontime[3]).zfill(2) + ':' + str(actiontime[4]).zfill(2) + ':' + str(actiontime[5]).zfill(2)
    with open(logname, 'a') as textlog:
        textlog.write(timestamp + ': ' + string.replace('\r\n', '\n' + ' ' * 10) + '\n')

def build_error(error, build, headers = None):
    print_log(error, 'yes')
    if 'w' in parameters and headers != None:
        log_write('----\r\n' + str(headers) + '\r\n----')
    resolution = print_prompt('Please choose one of the following options:\ne = exit the script\nr = reattempt the build (you should fix the issue first)\ns = skip the build\nType the letter corresponding to your choice: ')
    while re.search('^[ers]$', resolution) == None:
        resolution = print_prompt('Please enter a valid option: ')
    if resolution == 'e':
        raise SystemExit()
    elif resolution == 'r':
        return build
    elif resolution == 's':
        return None

if __name__ == "__main__":
    global parameters
    parameters = input('Parameters (h for help): ')
    while 'h' in parameters:
        print('a: don\'t save Any/X builds.')
        print('b: block consolidated zip packs explicitly.')
        print('l: limit saved builds by sort attribute.')
        print('m: manual category entry. Enter as many categories as you want.')
        print('o: change folder layout.')
        print('s: silent mode.')
        print('t: save text files.')
        print('w: write log.')
        print('y: build consolidated packs even with category/sort selects (overrides "b")')
        print('z: save zip files even when saving text files.')
        parameters = input('Parameters: ')
    if 'w' in parameters:
        global logname
        datetime = time.gmtime()
        logname = './buildpacklog ' + str(datetime[1]).zfill(2) + str(datetime[2]).zfill(2) + str(datetime[3]).zfill(2) + str(datetime[4]).zfill(2) + str(datetime[5]).zfill(2) + '.txt'
        log_write(str(datetime[0]) + '.' + str(datetime[1]).zfill(2) + '.' + str(datetime[2]).zfill(2))
        log_write('Parameters: ' + parameters)
    # Setup the connection and test the servers
    conn = http.client.HTTPSConnection('gwpvx.fandom.com')
    try:
        conn.request('GET', '/api.php')
    except:
        print_log('Turn on your internet scrub.','yes')
    else:
        r1 = conn.getresponse()
        conn.close()
        if r1.status == 200:
            print_log("Holy shit! Curse is actually working. Now let's start getting that build data.", 'yes')
        else:
            print_log("Curse's servers are (probably) down. Try again later.\nThe provided error code is: " + str(r1.status) + ' - ' + str(r1.reason), 'yes')
            raise SystemExit()
        # If we're changing the sorts, call the function until the user inputs something valid. Otherwise default to gametype-only sort.
        if 'o' in parameters:
            dirorder = False
            while dirorder == False:
                dirorder = change_dir_order()
        else:
            dirorder = 'g'
        # Restriction filtering setup
        if 'l' in parameters:
            print_log('For each sort, enter a comma-separated list of which attributes you\'d like to limit to. Leave blank to ignore that sort.', 'yes')
            rdfluxes = restrict_dirs('fluxes')
            rdprimaries = restrict_dirs('primaries')
            rdsecondaries = restrict_dirs('secondaries')
            rdgametypes = restrict_dirs('gametypes')
            rdratings = restrict_dirs('ratings')
            rdirs = [rdfluxes, rdprimaries, rdsecondaries, rdgametypes, rdratings]
        else:
            rdirs = [None, None, None, None, None]
        pagelist = setup_categories()
        # Process the builds
        buildqueue = deque()
        packnames = set()
        savedpacks = deque()
        while pagelist:
            result = get_build(pagelist.popleft(), dirorder, rdirs)
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
            print_log('Saving pack ' + currentpack.name + ' (' + str(len(currentpack.builds)) + ' builds)...', 'yes')
            if 't' in parameters:
                write_builds_txt(currentpack)
            if 'z' in parameters or not 't' in parameters:
                write_builds_zip(currentpack)
            print_log('Pack ' + currentpack.name + ' saved!', 'yes')
    print_prompt("Script complete.")
