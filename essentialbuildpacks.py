# License for this script is the CC BY-NC-SA 2.5: https://creativecommons.org/licenses/by-nc-sa/2.5/
# The original author of this script is Danny, of PvXwiki: http://gwpvx.gamepedia.com/UserProfile:Danny11384
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
    # Unfortunately PvXwiki lacks a unified working builds category
    CATEGORIES = ['All_working_PvP_builds', 'All_working_PvE_builds']
    
    if not os.path.isdir('./PvX Build Packs'):
        os.mkdir('./PvX Build Packs')
    
    buildlist = []
    for cat in CATEGORIES:
        print "Assembling build list for " + cat.replace('_',' ') + "..."
        conn.request('GET', '/Category:' + cat)
        response = conn.getresponse()
        page = response.read()
        conn.close()
        if response.status == 200:
            buildlist = category_page_list(page, buildlist)
            print "Builds from " + cat.replace('_',' ') + " added to list!"
        else:
            httpfaildebugger(cat, response.status, response.reason, response.getheaders())
            print "Build listing for " + cat.replace('_',' ') + " failed."
    get_builds_and_write(buildlist)
    print "Script complete."
    
def get_builds_and_write(pagelist):
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
                gametypes = id_gametypes(page)
                ratings = id_ratings(page)
                codes = find_template_code(page)
                # If no template codes found on the build page, skip the build
                if len(codes) == 0:
                    print 'No template code found for ' + i + '. Skipped.'
                    continue
                # Establish directories
                directories = []
                for typ in gametypes:
                    if len(typ) > 3 and typ.find('team') == -1:
                        typdir = './PvX Build Packs/' + typ.title()
                    else:
                        typdir = './PvX Build Packs/' + typ
                    if not os.path.isdir(typdir):
                        os.mkdir(typdir)
                    for rat in ratings:
                        directories += [typdir + '/' + rat]
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
                        if len(codes) > 1 and ('hero' in gametypes) and ('general' in gametypes) and d.find('Hero') > -1:
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
                
def category_page_list(page, newlist):
    pagelist = re.findall(">Build:.*?<", page) + re.findall(">Archive:.*?<", page)
    current = []
    for i in pagelist:
        current = i.replace('?','').replace('>','').replace('<','').replace('&quot;','"')
        if not current in newlist:
            newlist += [current]
    return newlist

def find_template_code(page):
    codelist = re.findall('<input id="gws_template_input" type="text" value="(.*?)"', page)
    newlist = []
    for i in codelist:
        newlist += [i]
    return newlist

def id_gametypes(page):
    types = ['AB','FA','JQ','GvG','HA','RA','PvP team','general','farming','running','hero','SC','PvE team','CM']
    rawtypes = re.findall('<div class="build-types">(.*?)</div>', page, re.DOTALL)
    gametypes = []
    if len(rawtypes) == 0:
        pass
    else:
        for t in types:
            if rawtypes[0].find(t) > -1:
                gametypes += [t]
    if len(gametypes) == 0:
        gametypes = ['Uncategorized']
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

if __name__ == "__main__":
    main()
