# License for this script is the CC BY-NC-SA 2.5: https://creativecommons.org/licenses/by-nc-sa/2.5/
# The original author of this script is Danny, of PvXwiki: http://gwpvx.gamepedia.com/UserProfile:Danny11384
import http.client
import re
import os
import os.path
import urllib.request, urllib.parse, urllib.error
import zipfile

conn = http.client.HTTPConnection('gwpvx.gamepedia.com')

def main():
    global conn
    conn.request('GET', '/PvX_wiki')
    r1 = conn.getresponse()
    conn.close()
    if r1.status == 200:
        print("Holy shit! Curse is actually working. Now let's start getting that build data.")
    else:
        input("Curse's servers are (probably) down. Try again later.")
        raise SystemExit()

    CATEGORIES = ['All_working_PvP_builds', 'All_working_PvE_builds', 'Affected_by_Flux']

    pagelist = []
    for cat in CATEGORIES:
        # This done so you don't have a massive page id displayed for category continuations.
        catname = re.sub(r'&cmcontinue=page\|.*\|.*', '', cat)
        print("Assembling build list for " + catname.replace('_',' ') + "...")
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
            print("Builds from " + catname.replace('_',' ') + " added to list!")
        else:
            input("Build listing for " + catname.replace('_',' ') + " failed. Ending script.")
            raise SystemExit()
    print(str(len(pagelist)) + ' builds found!')

    # Process the builds
    for i in pagelist:
        redirect = get_build(i)
        if redirect == True:
            pagelist.insert(pagelist.index(i) + 1, redirect)
    input("Script complete.")

def get_build(i):
    if i.find('Any/') > -1:
        print(i + " skipped (empty primary profession).")
        return
    print("Attempting " + (urllib.parse.unquote(i)).replace('_',' ') + "...")
    conn.request('GET', '/' + i.replace(' ','_').replace('\'','%27').replace('"','%22'))
    response = conn.getresponse()
    page = str(response.read())
    conn.close()
    if response.status == 200:
        # Grab the codes first
        codes = re.findall('<input id="gws_template_input" type="text" value="(.*?)"', page)
        # If no template codes found on the build page, skip the build
        if len(codes) == 0:
            print('No template code found for ' + i + '. Skipped.')
            return
        #Grab all the other build info
        gametypes = id_gametypes(page)
        ratings = id_ratings(page)
        # Create the directories
        directories = []
        for g in gametypes:
         for r in ratings:
          directories += ['./PvX Build Packs/' + g + '/' + r]
        # Check to see if the build is a team build
        if i.find('Team') >= 1 and len(codes) > 1:
            num = 0
            for j in codes:
                num += 1
                for d in directories:
                    #Adds the team folder
                    teamdir = file_name_sub(i, d)
                    write_build(file_name_sub(i, teamdir) + ' - ' + str(num) + '.txt', j)
        else:
            for d in directories:
                # Check for a non-team build with both player and hero versions, and sort them appropriately
                if (len(codes) > 1) and ('Hero' in gametypes) and ('General' in gametypes):
                    if d.find('Hero') > -1:
                        write_build(file_name_sub(i, d) + ' - Hero.txt', codes[1])
                else:
                    write_build(file_name_sub(i, d) + '.txt', codes[0])
        print(i + " complete.")
    elif response.status == 301:
        # Follow the redirect
        headers = str(response.getheaders())
        newpagestr = re.findall("gwpvx.gamepedia.com/.*?'\)", headers)
        newpagename = newpagestr[0].replace('gwpvx.gamepedia.com/','').replace("')",'').replace('_',' ')
        print('301 redirection...')
        return newpagename
    else:
        input(i + " failed. Ending script.") 
        raise SystemExit()

def write_build(filename, code):
    if not os.path.isdir('./Zipped Build Packs'):
        os.makedirs('./Zipped Build Packs')
    TopDir = (re.search(r'PvX Build Packs/([\w\s]*?)/', filename)).group(1)
    with zipfile.ZipFile('./Zipped Build Packs/' + TopDir + '.zip', 'a') as ZipPack:
        archivename = filename.replace('./PvX Build Packs/','')
        while archivename.find('//') > -1:
            archivename = archivename.replace('//','/')
        ZipPack.writestr(archivename, code)
    with zipfile.ZipFile('./Zipped Build Packs/All Build Packs.zip', 'a') as AllPack:
        AllPack.writestr(archivename, code)
    if TopDir in ['HA','GvG','RA','AB','FA','JQ','PvP team']:
        with zipfile.ZipFile('./Zipped Build Packs/PvP Build Packs.zip', 'a') as PvPPack:
            PvPPack.writestr(archivename, code)
    if TopDir in ['General','Hero','Farming','Running','SC','PvE team']:
        with zipfile.ZipFile('./Zipped Build Packs/PvE Build Packs.zip', 'a') as PvEPack:
            PvEPack.writestr(archivename, code)

def file_name_sub(build, directory):
    #Handles required substitutions for build filenames
    filename = directory + '/' + (urllib.parse.unquote(build)).replace('Build:','').replace('/','_').replace('"','\'\'')
    return filename

def category_page_list(page, newlist):
    pagelist = re.findall('"(Build:.*?)"\}', page)
    for i in pagelist:
        current = i.replace('\\','')
        if not current in newlist:
            newlist += [current]
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
    return ratings

if __name__ == "__main__":
    main()
