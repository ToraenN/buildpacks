# License for this script is the CC BY-NC-SA 2.5: https://creativecommons.org/licenses/by-nc-sa/2.5/
# The original author of this script is Danny, of PvXwiki: http://gwpvx.gamepedia.com/UserProfile:Danny11384
import httplib
import re
import os
import os.path
import urllib

conn = httplib.HTTPConnection('gwpvx.gamepedia.com')

def main():
    global conn
    conn.request('GET', '/PvX_wiki')
    r1 = conn.getresponse()
    conn.close()
    if r1.status == 200:
        print "Holy shit! Curse is actually working. Now let's start getting that build data."
    else:
        print "Curse's servers are (probably) down. Try again later."
        raise SystemExit()
    
    # Unfortunately PvXwiki lacks a unified working builds category
    CATEGORIES = ['All_working_PvP_builds', 'All_working_PvE_builds']
    
    if not os.path.isdir('./PvX Build Packs'):
        os.mkdir('./PvX Build Packs')
    
    buildlist = []
    for cat in CATEGORIES:
        catname = re.sub(r'&cmcontinue=page\|.*\|.*', '', cat)
        print "Assembling build list for " + catname.replace('_',' ') + "..."
        conn.request('GET', '/api.php?action=query&format=json&list=categorymembers&cmlimit=max&cmtitle=Category:' + cat)
        response = conn.getresponse()
        page = response.read()
        conn.close()
        continuestr = re.search(r'(page\|.*\|.*)",', page)
        if continuestr:
            CATEGORIES += [catname + '&cmcontinue=' + continuestr.group(1)]
        if response.status == 200:
            buildlist = category_page_list(page, buildlist)
            print "Builds from " + catname.replace('_',' ') + " added to list!"
        else:
            print "Build listing for " + catname.replace('_',' ') + " failed."
    print str(len(buildlist)) + ' builds found!'
    get_builds_and_write(buildlist)
    print "Script complete."
    
def get_builds_and_write(pagelist):
    for i in pagelist:
        # Check to see if the build has an empty primary profession (would generate an invalid template code)
        buildname = urllib.unquote(i)
        if i.find('Any/') > -1:
            print buildname + " skipped (empty primary profession)."
            continue
        print "Attempting " + buildname + "..."
        conn.request('GET', '/' + i.replace(' ','_').replace("'",'%27').replace('"','%22'))
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
                print 'No template code found for ' + buildname + '. Skipped.'
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
                        teamdir = file_name_sub(i, d)
                        if not os.path.isdir(teamdir):
                            os.mkdir(teamdir)
                        outfile = open(file_name_sub(buildname, teamdir) + ' - ' + str(num) + '.txt','wb')
                        outfile.write(j)
            else:
                for d in directories:
                    # Check for a non-team build with both player and hero versions, and sort them appropriately
                    if len(codes) > 1 and ('hero' in gametypes) and ('general' in gametypes) and d.find('Hero') > -1:
                        outfile = open(file_name_sub(buildname, d) + ' - Hero.txt','wb')
                        outfile.write(codes[1])
                    else:
                        outfile = open(file_name_sub(buildname, d) + '.txt','wb')
                        outfile.write(codes[0])
            print buildname + " complete."
        elif response.status == 301:
            # Inserts the redirected build name into the pagelist array so it is done next
            headers = str(response.getheaders())
            newpagestr = re.findall("gwpvx.gamepedia.com/(.*?)'\)", headers)
            newpagename = newpagestr[0].replace('_',' ')
            newpagepos = pagelist.index(i) + 1
            pagelist.insert(newpagepos, newpagename)
            print '301 redirection...'
        else:
            print i + " failed."

def file_name_sub(build, directory):
    #Handles required substitutions for build filenames
    filename = directory + '/' + build.replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'')
    return filename

def category_page_list(page, newlist):
    pagelist = re.findall('"(Build:.*?)"\}', page) + re.findall('"(Archive:.*?)"\}', page)
    for i in pagelist:
        current = i.replace('\\','')
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
    return ratings

if __name__ == "__main__":
    main()
