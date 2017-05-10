# License for this script is the CC BY-NC-SA 2.5: https://creativecommons.org/licenses/by-nc-sa/2.5/
# The original author of this script is Danny, of PvXwiki: http://gwpvx.gamepedia.com/UserProfile:Danny11384
import http.client
import re
import os
import os.path
import urllib.request, urllib.parse, urllib.error

conn = http.client.HTTPConnection('gwpvx.gamepedia.com')
parameters = input('Parameters (h for help): ')
while parameters.find('h') > -1:
    print('a: save Any/X builds.')
    print('c: list and choose from preset categories.')
    print('f: add flux sort.')
    print('g: remove gametype sort.')
    print('l: limit to single output directory.')
    print('p: add profession sort.')
    print('q: manual category entry. Enter as many categories as you want.')
    print('r: removes rating sort.')
    print('s: silent mode.')
    print('w: write log.')
    parameters = input('Parameters: ')
if parameters.find('w') > -1:
    textlog = open('./buildpackslog.txt', 'a')

def main():
    global conn
    global parameters
    if parameters.find('w') > -1:
        global textlog
    conn.request('GET', '/PvX_wiki')
    r1 = conn.getresponse()
    conn.close()
    if r1.status == 200:
        print_log("Holy shit! Curse is actually working. Now let's start getting that build data.", 'yes')
    else:
        http_failure('Start', r1.status, r1.response, r1.getheaders())

    #Check for category selection mode. 'q' > 'c'. If none of these, just grab the tested builds.
    CATEGORIES = []
    if parameters.find('q') > -1:
        manualcatentry = print_prompt('Enter category (leave blank to end entry): ')
        while manualcatentry != '':
            CATEGORIES += [manualcatentry.replace(' ','_')]
            manualcatentry = print_prompt('Enter category (leave blank to end entry): ')
    elif parameters.find('c') > -1:
        if 'y' in print_prompt('Do you want any PvP builds? (y/n)'):
            CATEGORIES += category_selection(['All_working_AB_builds', 'All_working_FA_builds', 'All_working_JQ_builds', 'All_working_RA_builds', 'All_working_GvG_builds', 'All_working_HA_builds', 'All_working_PvP_team_builds'])
        if 'y' in print_prompt('Do you want any PvE builds? (y/n)'):
            CATEGORIES += category_selection(['All_working_general_builds', 'All_working_hero_builds', 'All_working_SC_builds', 'All_working_running_builds', 'All_working_farming_builds', 'All_working_PvE_team_builds'])
        if 'y' in print_prompt('Would you like to compile any misc. categories? (y/n)'):
            CATEGORIES += category_selection(['Affected_by_Flux', 'Build_stubs', 'Trial_Builds', 'Untested_testing_builds', 'Abandoned', 'Trash_builds', 'Archived_tested_builds'])
        if len(CATEGORIES) < 1:
            print_log("No categories selected.", "yes")
    else:
        # Default to all currently vetted builds, including the auto-archiving Flux builds.
        CATEGORIES = ['All_working_PvP_builds', 'All_working_PvE_builds', 'Affected_by_Flux']

    pagelist = []
    for cat in CATEGORIES:
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
            CATEGORIES += [catname + '&cmcontinue=' + continuestr.group(1)]
        if response.status == 200:
            pagelist = category_page_list(page, pagelist)
            print_log("Builds from " + catname.replace('_',' ') + " added to list!")
        else:
            http_failure(cat, response.status, response.reason, response.getheaders())
            print_log("Build listing for " + catname.replace('_',' ') + " failed.")
    print_log(str(len(pagelist)) + ' builds found!', 'yes')

    # Limit directory mode
    if parameters.find('l') > -1:
        limitdir = print_prompt('Limit output to directory: ')
        while limitdir == '' or (len(re.findall('[/\\\\*?:"<>|.]', limitdir)) > 0):
            limitdir = print_prompt('Invalid directory name. Please choose another name: ')
    else:
        limitdir = ''

    # Process the builds
    for i in pagelist:
        get_build_and_write(i, limitdir)
    print_log("Script complete.", 'yes')
    if parameters.find('w') > -1:
        textlog.close

def get_build_and_write(i, limitdir):
    # Check to see if the build has an empty primary profession as that would generate an invalid template code in Guild Wars (but not in build editors)
    if (i.find('Any/') > -1) and (parameters.find('a') == -1):
        print_log(i + " skipped (empty primary profession).")
    else:
        print_log("Attempting " + (urllib.parse.unquote(i)).replace('_',' ') + "...")
        conn.request('GET', '/' + i.replace(' ','_').replace('\'','%27').replace('"','%22'))
        response = conn.getresponse()
        page = str(response.read())
        conn.close()
        if response.status == 200:
            # Grab the codes first
            codes = re.findall('<input id="gws_template_input" type="text" value="(.*?)"', page)
            # If no template codes found on the build page, skip the build
            if len(codes) == 0:
                print_log('No template code found for ' + i + '. Skipped.')
            else:
                #Grab all the other build info
                fluxes = id_fluxes(page)
                profession = id_profession(i)
                gametypes = id_gametypes(page)
                ratings = id_ratings(page)
                # Create the directories
                if parameters.find('l') == -1:
                    dirlevels = []
                    if parameters.find('f') > -1:
                        dirlevels += [fluxes]
                    if parameters.find('p') > -1:
                        dirlevels += [profession]
                    if parameters.find('g') == -1:
                        dirlevels += [gametypes]
                    if parameters.find('r') == -1:
                        dirlevels += [ratings]
                        rateinname = ''
                    else:
                        rateinname = ' - ' + str(ratings).replace('[','').replace(']','').replace("'",'').replace(',','-').replace(' ','')
                    directories = directory_tree(dirlevels)
                else:
                    directories = ['./' + limitdir]
                    if not os.path.isdir(directories[0]):
                        os.mkdir(directories[0])
                # If we're making a log file, inlcude the build info
                if parameters.find('w') > -1:
                    textlog.write('Fluxes found:' + str(fluxes) + '\r\nGametypes found:' + str(gametypes) + '\r\nRatings found:' + str(ratings) + '\r\nCodes found:' + str(codes) + '\r\nDirectories used:' + str(directories) + '\r\n')
                # Check to see if the build is a team build
                if i.find('Team') >= 1 and len(codes) > 1:
                    num = 0
                    for j in codes:
                        num += 1
                        for d in directories:
                            #Adds the team folder
                            teamdir = file_name_sub(i, d) + rateinname
                            if not os.path.isdir(teamdir):
                                os.mkdir(teamdir)
                            outfile = open(file_name_sub(i, teamdir) + ' - ' + str(num) + '.txt','w')
                            outfile.write(j)
                else:
                    for d in directories:
                        # Check for a non-team build with both player and hero versions, and sort them appropriately
                        if (len(codes) > 1) and ('Hero' in gametypes) and ('General' in gametypes):
                            if d.find('Hero') > -1:
                                outfile = open(file_name_sub(i, d) + ' - Hero' + rateinname + '.txt','w')
                                outfile.write(codes[1])
                            elif parameters.find('g') > -1:
                                outfile = open(file_name_sub(i, d) + ' - Hero' + rateinname + '.txt','w')
                                outfile.write(codes[1])
                                outfile.close
                                outfile = open(file_name_sub(i, d) + rateinname + '.txt','w')
                                outfile.write(codes[0])
                                outfile.close
                        else:
                            outfile = open(file_name_sub(i, d) + rateinname + '.txt','w')
                            outfile.write(codes[0])
                outfile.close
                print_log(i + " complete.")
        elif response.status == 301:
            # Follow the redirect
            headers = str(response.getheaders())
            newpagestr = re.findall("gwpvx.gamepedia.com/.*?'\)", headers)
            newpagename = newpagestr[0].replace('gwpvx.gamepedia.com/','').replace("')",'').replace('_',' ')
            print_log('301 redirection...')
            get_build_and_write(newpagename)
        else:
            http_failure(i, response.status, response.reason, response.getheaders())
            print_log(i + " failed.")

def file_name_sub(build, directory):
    #Handles required substitutions for build filenames
    filename = directory + '/' + (urllib.parse.unquote(build)).replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'')
    return filename

def category_selection(ALLCATS):
    CATEGORIES = []
    for a in ALLCATS:
        answer = print_prompt('Would you like to compile ' + a.replace('_',' ') + '? (y/n) ')
        if answer == 'y':
            CATEGORIES += [a]
    return CATEGORIES

def category_page_list(page, newlist):
    pagelist = re.findall('"(Build:.*?)"\}', page) + re.findall('"(Archive:.*?)"\}', page)
    for i in pagelist:
        current = i.replace('\\','')
        if not current in newlist:
            newlist += [current]
    return newlist

def directory_tree(dirlevels):
    while len(dirlevels) < 4:
        dirlevels += [['']]
    directories = []
    for a in dirlevels[0]:
     for b in dirlevels[1]:
      for c in dirlevels[2]:
       for d in dirlevels[3]:
        directories += ['./PvX Build Packs/' + a + '/' + b + '/' + c + '/' + d]
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
    prefix = (re.search(r'Build:(\w+)\s*/*-*', name)).group(1)
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
        if t.find('team') > -1:
            gametypes += [re.sub('<br />', ' ', t)]
        elif len(t) > 12:
            gametypes += [(re.sub('Pv[EP]<br />', '', t)).title()]
        else:
            gametypes += [re.sub('Pv[EP]<br />', '', t)]
    return gametypes

def id_ratings(page): 
    ratings = []
    if page.find('This build is part of the current metagame.') > -1:
        ratings += ['Meta']
    #A second if statement because builds can have both Meta and one of Good/Great
    if page.find('in the range from 4.75') > -1:
        ratings += ['Great']
    elif page.find('in the range from 3.75') > -1:
        ratings += ['Good']
    elif page.find('below 3.75') > -1:
        ratings += ['Trash']
    elif page.find('in the <i>trial</i> phase.') > -1:
        ratings += ['Trial']
    elif page.find('This build is currently being tested.') > -1:
        ratings += ['Testing']
    elif page.find('been archived') > -1:
        ratings += ['Archived']
    elif page.find('File:Image_Abandoned.jpg') > -1:
        ratings += ['Abandoned']
    if ratings == []:
        ratings = ['Nonrated']
    return ratings

def print_prompt(string):
    answer = input(string)
    if parameters.find('w') > -1:
        textlog.write(string + answer + '\r\n')
    return answer

def print_log(string, alwaysdisplay = 'no'):
    if (parameters.find('s') == -1) or (alwaysdisplay == 'yes'):
        print(string)
    if parameters.find('w') > -1:
        textlog.write(str(string) + '\r\n')

def http_failure(attempt, response, reason, headers):
    print_log('HTTPConnection error encountered: ' + str(response) + ' - ' + str(reason), 'yes')
    if parameters.find('w') > -1:
        textlog.write('----\r\n' + str(attempt) + '\r\n' + str(response) + ' - ' + str(reason) + '\r\n' + str(headers) + '\r\n----\r\n')
    if attempt == 'Start':
        print_log("Curse's servers are (probably) down. Try again later.", 'yes')
        raise SystemExit()
    # Require a definitive answer from the user
    answer = ''
    while not answer == ('y' or 'n'):
        answer = print_prompt('Do you wish to continue the script? ' + str(attempt) + ' will be skipped. (y/n) ')
        if answer == 'y':
            print_log('Ok, continuing...', 'yes')
        elif answer == 'n':
            print_log('Ok, exiting...', 'yes')
            raise SystemExit()
        else:
            print_log("Please enter 'y' or 'n'.", 'yes')

if __name__ == "__main__":
    main()
