# License for this script is the CC BY-NC-SA 2.5: https://creativecommons.org/licenses/by-nc-sa/2.5/
# The original author of this script is Danny, of PvXwiki: http://gwpvx.gamepedia.com/UserProfile:Danny11384
import http.client
import re
import os
import os.path
import urllib.request, urllib.parse, urllib.error
import zipfile
from collections import deque

def setup_builds():
    categories = ['All_working_PvP_builds', 'All_working_PvE_builds', 'Affected_by_Flux']
    buildlist = deque()
    for cat in categories:
        catname = re.sub(r'&cmcontinue=page\|.*\|.*', '', cat)
        print("Assembling build list for " + catname.replace('_',' ') + "...")
        try:
            conn.request('GET', '/api.php?action=query&format=json&list=categorymembers&cmlimit=max&cmtitle=Category:' + cat)
        except:
            input('Internet connection lost.')
            return
        response = conn.getresponse()
        page = str(response.read())
        conn.close()
        continuestr = re.search(r'(page\|.*\|.*)",', page)
        if continuestr:
            categories += [catname + '&cmcontinue=' + continuestr.group(1)]
        if response.status == 200:
            buildlist = category_page_list(page, buildlist)
            print("Builds from " + catname.replace('_',' ') + " added to list!")
        else:
            print("Curse's servers are (probably) down. Try again later.")
            return
    print(str(len(buildlist)) + ' builds found!')
    return buildlist

def get_build(i):
    print("Attempting " + (urllib.parse.unquote(i)).replace('_',' ') + "...")
    conn.request('GET', '/' + i.replace(' ','_').replace('\'','%27').replace('"','%22'))
    response = conn.getresponse()
    page = str(response.read())
    conn.close()
    if response.status == 200:
        codes = re.findall('<input id="gws_template_input" type="text" value="(.*?)"', page)
        if len(codes) == 0:
            return build_error('No build template found on page for ' + i + '.', i)
        for c in codes:
            if c == '':
                return build_error('Warning: Blank code found in ' + i + '! (code #' + str(codes.index(c) + 1) + ')', i)

        gametypes = id_gametypes(page)
        ratings = id_ratings(page)

        dirlevels = [gametypes]
        rateinname = ' - ' + str(ratings).replace('[','').replace(']','').replace("'",'').replace(',','-').replace(' ','')
        if 'Team' in i and len(codes) > 1:
            dirlevels += [[(file_name_sub(i,'') + rateinname)]]
        directories = directory_tree(dirlevels)

        if 'Team' in i and len(codes) > 1:
            num = 0
            for j in codes:
                num += 1
                for d in directories:
                    write_build(file_name_sub(i, d) + ' - ' + str(num) + '.txt', j)
        else:
            for d in directories:
                if len(codes) > 1 and 'Hero' in gametypes and 'General' in gametypes:
                    if 'Hero' in d:
                        write_build(file_name_sub(i, d) + ' - Hero' + rateinname + '.txt', codes[1])
                else:
                    write_build(file_name_sub(i, d) + rateinname + '.txt', codes[0])
        print(i + " complete.")
    elif response.status == 301 or 302:
        headers = str(response.getheaders())
        newpagestr = re.findall("gwpvx.gamepedia.com/.*?'\)", headers)
        newpagename = newpagestr[0].replace('gwpvx.gamepedia.com/','').replace("')",'').replace('_',' ')
        print('redirection...')
        return newpagename
    else:
        return build_error('HTTPConnection error encountered: ' + str(response.status) + ' - ' + str(response.reason), i)

def write_build(filename, code):
    if not os.path.isdir('./Zipped Build Packs'):
        os.makedirs('./Zipped Build Packs')
    TopDir = (re.search(r'PvX Build Packs/([\w\s]*?)/', filename)).group(1)
    archivename = filename.replace('./PvX Build Packs/','')
    zip_file_write(TopDir, archivename, code)
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
            print(archivename + " already present in " + packname + ".zip!")

def file_name_sub(build, directory):
    filename = directory + (urllib.parse.unquote(build)).replace('Build:','').replace('Archive:','').replace('/','_').replace('"','\'\'')
    return filename

def category_page_list(page, newlist):
    pagelist = re.findall('"(Build:.*?)"\}', page) + re.findall('"(Archive:.*?)"\}', page)
    for i in pagelist:
        current = i.replace('\\','')
        if not current in newlist:
            newlist += [current]
    return newlist

def directory_tree(dirlevels):
    while len(dirlevels) < 2:
        dirlevels += [['']]
    directories = []
    for a in dirlevels[0]:
        for b in dirlevels[1]:
            addeddir = './PvX Build Packs/' + a + '/' + b + '/'
            while '//' in addeddir:
                addeddir = addeddir.replace('//','/')
            directories += [addeddir]
    return directories

def id_gametypes(page):
    builddiv = re.search('<div class="build-types">.*?</div>', page, re.DOTALL)
    if not builddiv:
        return ['Uncategorized']
    rawtypes = re.findall('Pv[EP]<br />\w+', builddiv.group())
    if len(rawtypes) == 0:
        return ['Uncategorized']
    gametypes = []
    for t in rawtypes:
        if 'team' in t:
            cleanedtype = re.sub('<br />', ' ', t)
        elif len(t) > 12:
            cleanedtype = (re.sub('Pv[EP]<br />', '', t)).title()
        else:
            cleanedtype = re.sub('Pv[EP]<br />', '', t)
        if not cleanedtype in gametypes:
            gametypes += [cleanedtype]
    return gametypes

def id_ratings(page): 
    ratings = []
    if 'This build is part of the current metagame.' in page:
        ratings += ['Meta']
    if 'in the range from 4.75' in page:
        ratings += ['Great']
    elif 'in the range from 3.75' in page:
        ratings += ['Good']
    if ratings == []:
        ratings = ['Nonrated']
    return ratings

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
    global conn
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
            builds = setup_builds()
            while builds:
                redirect = get_build(builds.popleft())
                if redirect != None:
                    builds.appendleft(redirect)
        else:
            print(str(r1.status) + "Curse's servers are (probably) down. Try again later.")
    input("Script complete.")
