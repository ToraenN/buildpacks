import httplib
import re
import os
import os.path
import urllib

conn = httplib.HTTPConnection('gwpvx.gamepedia.com')

def main():
    print
    conn.request('GET', '/PvX_wiki')
    r1 = conn.getresponse()
    conn.close()
    if r1.status == 200:
        print "Holy shit! Curse is actually working. Now let's start getting that build data."
        start_package()
    else:
        httpfaildebugger('Start', r1.status, r1.response, r1.getheaders())

def start_package():
    global conn

    answer = raw_input('Build debugger on? (y/n) ')
    if answer == 'y':
        answer = raw_input('Print to standard output (otherwise goes to logfile)? (y/n) ')
        if answer == 'y':
            log = 2
        else:
            print 'Debug output will write to buildpacksdebug.txt'
            log = 1
    else:
        log = 0
    ALLDIVS = ['All_working_PvP_builds', 'All_working_PvE_builds', 'Archived_tested_builds', 'Trash_builds', 'Untested_testing_builds', 'Trial_Builds']
    DIVISIONS = []
    for a in ALLDIVS:
        answer = raw_input('Would you like to compile ' + a.replace('_',' ') + '? (y/n) ')
        if answer == 'y':
            DIVISIONS += [a]
    # If no categories were selected, give the opportunity for a custom category input.
    if len(DIVISIONS) < 1:
        answer = raw_input('Well what DO you want to compile? ')
        if answer == '':
            raise SystemExit()
        print 'I hope you typed that correctly.'
        DIVISIONS += [answer.replace(' ','_')]
        
    if not os.path.isdir('./PvX Build Packs'):
        os.mkdir('./PvX Build Packs')
    
    for div in DIVISIONS:
        print "Assembling build list for " + div.replace('_',' ') + "..."
        conn.request('GET', '/Category:' + div)
        response = conn.getresponse()
        page = response.read()
        conn.close()
        if response.status == 200:
            pagelist = category_page_list(page)
            print "Build listing for " + div.replace('_',' ') + " created!"
            get_builds_and_write(pagelist, log)
            print "All builds in " + div.replace('_',' ') + " finished!"
        else:
            httpfaildebugger(div, response.status, response.reason, response.getheaders())
            print "Build listing for " + div.replace('_',' ') + " failed."
    print "Script complete."
    
def get_builds_and_write(pagelist, log):
    for i in pagelist:
        # Check to see if the build has an empty primary profession (would generate an invalid template code)
        if i.find('Any/') > -1:
            print i + " skipped (empty primary profession)."
        else:
            print "Attempting " + (urllib.unquote(i)).replace('_',' ') + "..."
            conn.request('GET', '/' + i.replace(' ','_').replace('\'','%27').replace('"','%22'))
            response = conn.getresponse()
            page = response.read()
            conn.close()
            if response.status == 200:
                # Grab the build info
                categories = id_buildtypes(page)
                ratings = id_ratings(page)
                codes = find_template_code(page)
                # If no template codes found on the build page, skip the build
                if len(codes) == 0:
                    print 'No template code found for ' + i + '. Skipped.'
                    continue
                # Establish the directories to be used for the build
                directories = []
                for cat in categories:
                    if len(cat) > 3 and cat.find('team') == -1:
                        catdir = './PvX Build Packs/' + cat.title()
                    else:
                        catdir = './PvX Build Packs/' + cat
                    if not os.path.isdir(catdir):
                        os.mkdir(catdir)
                    for rat in ratings:
                        directories += [catdir + '/' + rat]
                gbawdebugger(i, categories, ratings, codes, directories, log)
                for d in directories:
                    if not os.path.isdir(d):
                        os.mkdir(d)
                # Check to see if the build is a team build
                if i.find('Team') >= 1 and len(codes) > 1:
                    num = 0
                    for j in codes:
                        num += 1
                        for d in directories:
                            #Adds the team folder
                            teamdir = d + '/' + i.replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'')
                            if not os.path.isdir(teamdir):
                                os.mkdir(teamdir)
                            outfile = open(teamdir + '/' + (urllib.unquote(i)).replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'') + ' - ' + str(num) + '.txt','wb')
                            outfile.write(j)
                else:
                    for d in directories:
                        # Check for a non-team build with both player and hero versions, and sort them appropriately
                        if len(codes) > 1 and ('hero' in categories) and ('general' in categories) and d.find('Hero') > -1:
                            outfile = open(d + '/' + (urllib.unquote(i)).replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'') + ' - Hero.txt','wb')
                            outfile.write(codes[1])
                        else:
                            outfile = open(d + '/' + (urllib.unquote(i)).replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'') + '.txt','wb')
                            outfile.write(codes[0])
                print i + " complete."
            elif response.status == 301:
                # Inserts the redirected build name into the pagelist array so it is done next
                headers = str(response.getheaders())
                newpagestr = re.findall("gwpvx.gamepedia.com/.*?'\)", headers)
                newpagename = newpagestr[0].replace('gwpvx.gamepedia.com/','').replace("')",'').replace('_',' ')
                newpagepos = pagelist.index(i) + 1
                pagelist.insert(newpagepos, newpagename)
                print '301 redirection...'
            else:
                httpfaildebugger(i, response.status, response.reason, response.getheaders())
                print i + " failed."

def category_page_list(page):
    pagelist = re.findall(">Build:.*?<", page) + re.findall(">Archive:.*?<", page)
    current = ''
    newlist = []
    for i in pagelist:
        current = i.replace('?','').replace('>','').replace('<','').replace('&quot;','"')
        newlist += [current]
    return newlist

def find_template_code(page):
    codelist = re.findall('<input id="gws_template_input" type="text" value="(.*?)"', page)
    newlist = []
    for i in codelist:
        newlist += [i]
    return newlist

def id_buildtypes(page):
    types = ['AB','FA','JQ','GvG','HA','RA','PvP team','general','farming','running','hero','SC','PvE team','CM']
    rawtypes = re.findall('<div class="build-types">(.*?)</div>', page, re.DOTALL)
    categories = []
    for t in types:
        if rawtypes[0].find(t) > -1:
            categories += [t]
    if len(categories) == 0:
        categories += ['Uncategorized']
    return categories

def id_ratings(page): 
    ratings = []
    if page.find('This build is part of the current metagame.') > -1:
        ratings += ['Meta']
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
    else:
        ratings += ['Nonrated']
    return ratings

def httpfaildebugger(attempt, response, reason, headers):
    debuglog = open('./buildpackshttpdebug.txt', 'ab')
    debuglog.write(str(attempt) + '\r\n' + str(response) + ' - ' + str(reason) + '\r\n' + str(headers) + '\r\n' + '----' + '\r\n')
    print 'HTTPConnection error encountered: ' + str(response) + ' - ' + str(reason)
    if attempt == 'Start':
        print "Curse's servers are (probably) down. Try again later."
        raise SystemExit()
    answer = ''
    while not answer == ('y' or 'n'):
        answer = raw_input('Do you wish to continue the script? ' + str(attempt) + ' will be skipped. (y/n) ')
        if answer == 'y':
            print 'Ok, continuing...'
        elif answer == 'n':
            print 'Ok, exiting...'
            raise SystemExit()
        else:
            print 'Please enter \'y\' or \'n\'.'

def gbawdebugger(build, categories, ratings, codes, directories, log = 0):
    if log == 1:
        # Write to a file
        debuglog = open('./buildpacksdebug.txt', 'ab')
        debuglog.write(build + '\r\n' + str(categories) + '\r\n' + str(ratings) + '\r\n' + str(codes) + '\r\n' + str(directories) + '\r\n----\r\n') 
    elif log == 2:
        # Display in the window
        print categories
        print ratings
        print codes
        print directories

if __name__ == "__main__":
    main()
