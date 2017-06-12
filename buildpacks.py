# License for this script is the CC BY-NC-SA 2.5: https://creativecommons.org/licenses/by-nc-sa/2.5/
# The original author of this script is Danny, of PvXwiki: http://gwpvx.gamepedia.com/UserProfile:Danny11384
import http.client
import re
import os
import os.path
import time
import urllib.request, urllib.parse, urllib.error
import zipfile

def main():
    global conn
    global parameters
    conn = http.client.HTTPConnection('gwpvx.gamepedia.com')
    parameters = input('Parameters (h for help): ')
    while 'h' in parameters:
        print('a: don\'t save Any/X builds.')
        print('b: block consolidated packs explicitly.')
        print('c: list and choose from preset categories.')
        print('o: change folder layout.')
        print('q: manual category entry. Enter as many categories as you want.')
        print('s: silent mode.')
        print('t: save text files even when saving zip files.')
        print('w: write log.')
        print('y: build consolidated packs even with category/sort selects (overrides "b")')
        print('z: save as zip files.')
        parameters = input('Parameters: ')
    if 'w' in parameters:
        global logname
        datetime = format_time()
        logname = './buildpacklog ' + datetime[2] + '.txt'
        log_write(datetime[0])
        log_write('Parameters: ' + parameters)
    conn.request('GET', '/PvX_wiki')
    r1 = conn.getresponse()
    conn.close()
    if r1.status == 200:
        print_log("Holy shit! Curse is actually working. Now let's start getting that build data.", 'yes')
    else:
        http_failure('Start', r1.status, r1.response, r1.getheaders())
    # If we're changing the sorts, call the function until the user inputs something valid. Otherwise default to gametype-only sort.
    if 'o' in parameters:
        dirorder = False
        while dirorder == False:
            dirorder = change_dir_order()
    else:
        dirorder = 'g'
    # Check for category selection modes. If none of these, just grab the tested builds.
    categories = []
    if 'q' in parameters:
        manualcatentry = print_prompt('Enter category (leave blank to end entry): ')
        while manualcatentry != '':
            categories += [manualcatentry.replace(' ','_')]
            manualcatentry = print_prompt('Enter category (leave blank to end entry): ')
    if 'c' in parameters:
        if 'y' in print_prompt('Do you want any PvP builds? (y/n) '):
            if 'y' in print_prompt('All of them? (y/n) '):
                categories += ['All_working_PvP_builds']
            else:
                categories += category_selection(['All_working_AB_builds', 'All_working_FA_builds', 'All_working_JQ_builds', 'All_working_RA_builds', 'All_working_GvG_builds', 'All_working_HA_builds', 'All_working_PvP_team_builds'])
        if 'y' in print_prompt('Do you want any PvE builds? (y/n) '):
            if 'y' in print_prompt('All of them? (y/n) '):
                categories += ['All_working_PvE_builds']
            else:
                categories += category_selection(['All_working_general_builds', 'All_working_hero_builds', 'All_working_SC_builds', 'All_working_running_builds', 'All_working_farming_builds', 'All_working_PvE_team_builds'])
        if 'y' in print_prompt('Would you like to compile any misc. categories? (y/n) '):
            categories += category_selection(['Affected_by_Flux', 'Build_stubs', 'Trial_Builds', 'Untested_testing_builds', 'Abandoned', 'Trash_builds', 'Archived_tested_builds','WELL'])
    if len(categories) == 0:
        # Default to all currently vetted builds, including the auto-archiving Flux builds.
        print_log("Using default categories.", "yes")
        categories = ['All_working_PvP_builds', 'All_working_PvE_builds', 'Affected_by_Flux']

    pagelist = []
    for cat in categories:
        # This done so you don't have a massive page id displayed for category continuations.
        catname = re.sub(r'&cmcontinue=page\|.*\|.*', '', cat)
        print_log("Assembling build list for " + catname.replace('_',' ') + "...")
        conn.request('GET', '/api.php?action=query&format=json&list=categorymembers&cmlimit=max&cmtitle=Category:' + cat)
        response = conn.getresponse()
        page = str(response.read())
        conn.close()
        # Check if a continuation was offered due to the category having more members than the display limit
        continuestr = re.search(r'(page\|.*\|.*)",', page)
        if continuestr:
            categories += [catname + '&cmcontinue=' + continuestr.group(1)]
        if response.status == 200:
            pagelist = category_page_list(page, pagelist)
            print_log("Builds from " + catname.replace('_',' ') + " added to list!")
        else:
            http_failure(cat, response.status, response.reason, response.getheaders())
            print_log("Build listing for " + catname.replace('_',' ') + " failed.")
    print_log(str(len(pagelist)) + ' builds found!', 'yes')

    # Process the builds, redirect is defined only if the get_build function encounters an error
    for i in pagelist:
        redirect = get_build(i, dirorder)
        if not redirect == None:
            pagelist.insert(pagelist.index(i) + 1, redirect)
    print_log("Script complete.", 'yes')

def get_build(i, dirorder):
    # Check to see if the build has an empty primary profession as that would generate an invalid template code in Guild Wars (but not in build editors)
    if 'Any/' in i and 'a' in parameters:
        print_log(i + " skipped (empty primary profession).")
        return
    print_log("Attempting " + (urllib.parse.unquote(i)).replace('_',' ') + "...")
    conn.request('GET', '/' + i.replace(' ','_').replace('\'','%27').replace('"','%22'))
    response = conn.getresponse()
    page = str(response.read())
    conn.close()
    if response.status == 200:
        # Grab the codes first
        codes = re.findall('<input id="gws_template_input" type="text" value="(.*?)"', page)
        # If no template codes found on the build page, prompt user to fix the page
        if len(codes) == 0:
            resolution = build_error('No build template found on page for ' + i + '.', 'ers', i)
            return resolution
        # Some people don't remember to assign the secondary profession and this happens...
        for c in codes:
            if c == '':
                resolution = build_error('Warning: Blank code found in ' + i + '! (code #' + str(codes.index(c) + 1) + ')', 'ecrs', i)
                if resolution == 'c':
                    break
                else:
                    return resolution
        # Grab all the other build info
        fluxes = id_fluxes(page)
        profession = id_profession(i)
        gametypes = id_gametypes(page)
        ratings = id_ratings(page)
        # Create the directories
        dirlevels = []
        for o in dirorder:
            if o == 'f':
                dirlevels += [fluxes]
            elif o == 'p':
                dirlevels += [profession]
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
            dirlevels += [[(file_name_sub(i,'') + rateinname)]]
        directories = directory_tree(dirlevels)
        # If we're making a log file, inlcude the build info
        if 'w' in parameters:
            log_write('Fluxes found: ' + str(fluxes) + '\r\nProfession: ' + str(profession) + '\r\nGametypes found: ' + str(gametypes) + '\r\nRatings found: ' + str(ratings) + '\r\nCodes found: ' + str(codes) + '\r\nDirectories used: ' + str(directories))
        # Check to see if the build is a team build
        if 'Team' in i and len(codes) > 1:
            num = 0
            for j in codes:
                num += 1
                for d in directories:
                    write_build(file_name_sub(i, d) + ' - ' + str(num) + '.txt', j)
        else:
            for d in directories:
                # Check for a non-team build with both player and hero versions, and sort them appropriately
                if len(codes) > 1 and 'Hero' in gametypes and 'General' in gametypes:
                    if 'Hero' in d:
                        write_build(file_name_sub(i, d) + ' - Hero' + rateinname + '.txt', codes[1])
                    # If we're not sorting by gametype, save both versions
                    elif not 'g' in dirorder:
                        write_build(file_name_sub(i, d) + ' - Hero' + rateinname + '.txt', codes[1])
                        write_build(file_name_sub(i, d) + rateinname + '.txt', codes[0])
                else:
                    write_build(file_name_sub(i, d) + rateinname + '.txt', codes[0])
        print_log(i + " complete.")
    elif response.status == 301:
        # Follow the redirect
        headers = str(response.getheaders())
        newpagestr = re.findall("gwpvx.gamepedia.com/.*?'\)", headers)
        newpagename = newpagestr[0].replace('gwpvx.gamepedia.com/','').replace("')",'').replace('_',' ')
        print_log('301 redirection...')
        return newpagename
    else:
        http_failure(i, response.status, response.reason, response.getheaders())
        print_log(i + " failed.")

def write_build(filename, code):
    # Check if we're writing text files
    if 't' in parameters or not 'z' in parameters:
        with open(filename, 'w') as outfile:
            outfile.write(code)
    # Check if we're writing zip files
    if 'z' in parameters:
        if not os.path.isdir('./Zipped Build Packs'):
            os.makedirs('./Zipped Build Packs')
        try:
            TopDir = (re.search(r'PvX Build Packs/([\w\s]*?)/', filename)).group(1)
        # If we aren't doing any sorts, make sure we have a top-level directory to put everything in
        except AttributeError:
            TopDir = 'PvX Build Packs'
        archivename = filename.replace('./PvX Build Packs/','')
        zip_file_write(TopDir, archivename, code)
        # If there are any non-default sorts or limited categories in use, don't continue to the consolidated packs. Overridden by 'y'.
        if re.search(r'[bcoq]', parameters) and not 'y' in parameters:
            return
        zip_file_write('All Build Packs', archivename, code)
        if TopDir in ['HA','GvG','RA','AB','FA','JQ','PvP team','TA','CM','HB']:
            zip_file_write('PvP Build Packs', archivename, code)
        if TopDir in ['General','Hero','Farming','Running','SC','PvE team']:
            zip_file_write('PvE Build Packs', archivename, code)

def zip_file_write(packname, archivename, code):
    with zipfile.ZipFile('./Zipped Build Packs/' + packname + '.zip', 'a') as ZipPack:
        try:
            ZipPack.getinfo(archivename)
        except KeyError:
            ZipPack.writestr(archivename, code)
        else:
            print_log(archivename + " already present in " + packname + ".zip!")

def file_name_sub(build, directory):
    # Handles required substitutions for build filenames
    filename = directory + (urllib.parse.unquote(build)).replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'')
    return filename

def change_dir_order():
    orderstr = print_prompt('Enter the order of the sorts (using "f", "p", "g", "r") or leave blank for no sorting.\r\n   f = flux\r\n   p = profession\r\n   g = gametype\r\n   r = rating\r\nSort order: ')
    if re.search(r'[^fgpr]', orderstr):
        print_log('Invalid characters in selection.', 'yes')
        return False
    if re.search(r'([fgpr]).*\1', orderstr):
        print_log('Multiple of same character in selection.', 'yes')
        return False
    return orderstr

def category_selection(catlist):
    categories = []
    for a in catlist:
        answer = print_prompt('Would you like to compile ' + a.replace('_',' ') + '? (y/n) ')
        if answer == 'y':
            categories += [a]
    return categories

def category_page_list(page, newlist):
    pagelist = re.findall('"(Build:.*?)"\}', page) + re.findall('"(Archive:.*?)"\}', page)
    for i in pagelist:
        current = i.replace('\\','')
        if not current in newlist:
            newlist += [current]
    return newlist

def directory_tree(dirlevels):
    while len(dirlevels) < 5:
        dirlevels += [['']]
    directories = []
    for a in dirlevels[0]:
     for b in dirlevels[1]:
      for c in dirlevels[2]:
       for d in dirlevels[3]:
        for e in dirlevels[4]:
         addeddir = './PvX Build Packs/' + a + '/' + b + '/' + c + '/' + d + '/' + e + '/'
         # '//' will mess up zip writing
         while '//' in addeddir:
             addeddir = addeddir.replace('//','/')
         directories += [addeddir]
    # Only create directories if saving text files
    if 't' in parameters or not 'z' in parameters:
        for folder in directories:
            if not os.path.isdir(folder):
                os.makedirs(folder)
    return directories

def id_fluxes(page):
    fluxes = re.findall('>(Affected by [^<>]*?) Flux<', page)
    if len(fluxes) == 0:
        fluxes = ['Unaffected by Flux']
    return fluxes

def id_profession(name):
    prefix = (re.search(r':(\w+)\s*/*-*', name)).group(1)
    profdict = {'A':'Assassin','Any':'Any','D':'Dervish','E':'Elementalist','Me':'Mesmer','Mo':'Monk','N':'Necromancer','P':'Paragon','R':'Ranger','Rt':'Ritualist','Team':'Team', 'W':'Warrior'}
    profession = [profdict[prefix]]
    return profession

def id_gametypes(page):
    # Finds the build-types div, and then extracts the tags. Two checks for: build-types div isn't found or if it has no tags in it.
    builddiv = re.search('<div class="build-types">.*?</div>', page, re.DOTALL)
    if not builddiv:
        return ['Uncategorized']
    rawtypes = re.findall('Pv[EP]<br />\w+', builddiv.group())
    if len(rawtypes) == 0:
        return ['Uncategorized']
    # Build the gametypes list based on the tags
    gametypes = []
    for t in rawtypes:
        if 'team' in t:
            cleanedtype = re.sub('<br />', ' ', t)
        elif len(t) > 12:
            cleanedtype = (re.sub('Pv[EP]<br />', '', t)).title()
        else:
            cleanedtype = re.sub('Pv[EP]<br />', '', t)
        # Apparently I cannot trust that everyone will avoid putting in duplicate tags
        if not cleanedtype in gametypes:
            gametypes += [cleanedtype]
    return gametypes

def id_ratings(page): 
    ratings = []
    if 'This build is part of the current metagame.' in page:
        ratings += ['Meta']
    # A second if statement because builds can have both Meta and one of Good/Great
    if 'in the range from 4.75' in page:
        ratings += ['Great']
    elif 'in the range from 3.75' in page:
        ratings += ['Good']
    elif 'below 3.75' in page:
        ratings += ['Trash']
    elif re.search(r'This build article is a <a.*?>stub</a>', page):
        ratings += ['Stub']
    elif 'in the <i>trial</i> phase.' in page:
        ratings += ['Trial']
    elif 'This build is currently being tested.' in page:
        ratings += ['Testing']
    elif 'been archived' in page:
        ratings += ['Archived']
    elif 'File:Image_Abandoned.jpg' in page:
        ratings += ['Abandoned']
    if ratings == []:
        ratings = ['Nonrated']
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
    with open(logname, 'a') as textlog:
        timestamp = format_time()
        textlog.write(timestamp[1] + ': ' + string.replace('\r\n', '\r\n' + ' ' * 10) + '\r\n')

def http_failure(attempt, response, reason, headers):
    print_log('HTTPConnection error encountered: ' + str(response) + ' - ' + str(reason), 'yes')
    if 'w' in parameters:
        log_write('----\r\n' + str(attempt) + '\r\n' + str(response) + ' - ' + str(reason) + '\r\n' + str(headers) + '\r\n----')
    if attempt == 'Start':
        print_log("Curse's servers are (probably) down. Try again later.", 'yes')
        raise SystemExit()
    # Require a definitive answer from the user
    answer = print_prompt('Do you wish to continue the script? ' + str(attempt) + ' will be skipped. (y/n) ')
    while not re.search('^[ny]$',answer):
        answer = print_prompt('Please enter "y" or "n".')
        if answer == 'y':
            print_log('Ok, continuing...', 'yes')
        elif answer == 'n':
            print_log('Ok, exiting...', 'yes')
            raise SystemExit()
        else:
            print_log("Please enter 'y' or 'n'.", 'yes')

def format_time():
    datetime = time.gmtime()
    curdate = str(datetime[0]) + '.' + str(datetime[1]).zfill(2) + '.' + str(datetime[2]).zfill(2)
    curtime = str(datetime[3]).zfill(2) + ':' + str(datetime[4]).zfill(2) + ':' + str(datetime[5]).zfill(2)
    filesuffix = str(datetime[1]).zfill(2) + str(datetime[2]).zfill(2) + str(datetime[3]).zfill(2) + str(datetime[4]).zfill(2) + str(datetime[5]).zfill(2)
    return (curdate, curtime, filesuffix)

def build_error(error, options, build):
    print_log(error, 'yes')
    resprompt = 'Please choose one of the following options:\r\n'
    if 'c' in options:
        resprompt += 'c = continue the build (with errors)\r\n'
    if 'e' in options:
        resprompt += 'e = exit the script\r\n'
    if 'r' in options:
        resprompt += 'r = reattempt the build\r\n'
    if 's' in options:
        resprompt += 's = skip the build\r\n'
    resprompt += 'Type the letter corresponding to your choice: '
    resolution = print_prompt(resprompt)
    while re.search('^[' + options +']$', resolution) == None:
        resolution = print_prompt('Please enter a valid option: ')
    if resolution == 'c':
        return resolution
    elif resolution == 'e':
        raise SystemExit()
    elif resolution == 'r':
        return build
    elif resolution == 's':
        return None

if __name__ == "__main__":
    main()
