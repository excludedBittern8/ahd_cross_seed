from datetime import date,timedelta, datetime
from classes import *
import requests
import xmltodict
import subprocess
from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.shortcuts import button_dialog
from prompt_toolkit.shortcuts import checkboxlist_dialog
import os
import re
import logging
import time
ahdlogger = logging.getLogger('AHD')
"""
General Functions
"""
def get_matches(arguments,files):
    wget=arguments['--wget']
    torrentfolder=arguments['--torrent']
    api=arguments['--api']
    cookie=arguments['--cookie']
    datefilter=(date.today()- timedelta(int(arguments['--date'])))
    currentdate=datetime.now().strftime("%m.%d.%Y_%H%M")

    file=files.get_first()
    if file=="No Files":
        return
    filesize=files.get_size()
    fileguessit=guessitinfo(file)
    fileguessit.set_values()
    title=fileguessit.get_name().lower()
    if fileguessit.get_season()!="":
        title=title+": " + fileguessit.get_season()
    imdb=get_imdb(fileguessit.get_info())
    if imdb==None:

        ahdlogger.warn(file," could not find IMDB")
        return
    search = "https://awesome-hd.club/searchapi.php?action=imdbsearch&passkey=" + api + "&imdb=tt" + imdb
    ahdlogger.warn(f"Searching For {files.type} with: {search}:{currentdate}")
    try:
        response = requests.get(search, timeout=300)
    except:
        ahdlogger.warn(f"Issue getting response: {search}:{currentdate}")
        return
    try:
        results=xmltodict.parse(response.content)
    except:
        ahdlogger.warn("unable to parse xml")
        return
    try:
        results['searchresults']['torrent'][1]['name']
        loop=True
        max=len(results['searchresults']['torrent'])
    except KeyError as key:
        if str(key)=="1":
            element=results['searchresults']['torrent']
            max=1
            loop=False
        else:
            ahdlogger.warn("Probably no results")
            return
    for i in range(max):
        titlematch=False
        filedate=False
        group=False
        resolution=False
        source=False
        sizematch=False
        if loop: element = results['searchresults']['torrent'][i]
        querytitle=lower(element['name'])
        if querytitle==None:
            continue
        querygroup=lower(element['releasegroup'])
        if querygroup==None:
            querygroup=""
        queryresolution=element['resolution']
        querysource=lower(element['media'])
        if querysource=="uhd blu-ray":
            querysource="blu-ray"
        if querysource=="web-dl" or querysource=="webrip":
            querysource="web"
        queryencoding=element['encoding']
        querysize= int(element['size'])
        querydate=datetime.strptime(element['time'], '%Y-%m-%d %H:%M:%S').date()
        if querytitle==title:
            titlematch=True
        if querysource==fileguessit.get_source() or fileguessit.get_source()=="":
            source=True
        if querygroup==fileguessit.get_group() or re.search(querygroup,fileguessit.get_group(),re.IGNORECASE)!=None \
        or re.search(fileguessit.get_group(),querygroup,re.IGNORECASE)!=None or fileguessit.get_group()=="":
            group=True
        if queryresolution==fileguessit.get_resolution():
            resolution=True
        if datefilter < querydate:
            filedate=True
        if difference(querysize,filesize)<.01:
            sizematch=True
        if (titlematch is True and source is True and group is True and resolution is True \
        and filedate is True) and (sizematch is True or filesize==0):
            pass
        else:
            continue
        ahdlogger.debug(f"Comparison UserTitle:{title} SiteTite:{querytitle} UserSource{fileguessit.get_source()} SiteSource:{querysource} UserGroup:{fileguessit.get_group()} SiteGroup:{querygroup} UserRes:{fileguessit.get_resolution()} SiteRes:{queryresolution} Date:{filedate}  \n ")

        if arguments['--output']!=None  and arguments['--output']!="" and arguments['--output']!="None":
            link="https://awesome-hd.club/torrents.php?id=" + element['groupid']+"&torrentid="+ element['id']
            t=open(arguments['--output'],'a')
            ahdlogger.warn("writing to file:",arguments['--output'])
            t.write(link+'\n')
        if arguments['--torrent']!=None and arguments['--torrent']!="" and  arguments['--torrent']!="None":
            link="https://awesome-hd.club/torrents.php?action=download&id=" +element['id'] +"&torrent_pass=" +  api
            title=re.sub(": ","-",querytitle)
            name=(f"[AHD]{title}.{querysource}.{queryresolution}.{querygroup}.torrent")
            name=re.sub("/", ".",name)
            torrent=os.path.join(torrentfolder,name)
            ahdlogger.warn(torrent)
            ahdlogger.warn(link)


            try:
                subprocess.run([wget,'--load-cookies',cookie,link,'-O',torrent])
            except:
                ahdlogger.warn(f"{title}: Could not find Download-{currentdate}")

def get_missing(arguments,files,encode=None):


    currentdate=datetime.now().strftime("%m.%d.%Y_%H%M")

    if encode==None:
        encode=False
    api=arguments['--api']
    output=arguments['--misstxt']
    file=files.get_first()

    if file=="No Files":
        return
    filesize=files.get_size()
    fileguessit=guessitinfo(file)
    fileguessit.set_values()
    title=fileguessit.get_name().lower()
    if fileguessit.get_season()!="":
        title=title+": " + fileguessit.get_season()
    imdb=get_imdb(fileguessit.get_info())
    if imdb==None:
        ahdlogger.warn(f"{file}: could not find IMDB")

        return
    search = "https://awesome-hd.club/searchapi.php?action=imdbsearch&passkey=" + api + "&imdb=tt" + imdb
    ahdlogger.warn(f"Searching For {files.type} with: {search}")

    try:
        response = requests.get(search, timeout=300)
    except:
        ahdlogger.warn(f"{search}: Could not find Get a response from AHD URL:{files.get_type()}-{currentdate}")
        return
    try:
        results=xmltodict.parse(response.content)
    except:
        ahdlogger.warn(f"{title}: Could not find parse AHD XML:{search} {files.get_type()}-{currentdate}")
        return
    try:
        results['searchresults']['torrent'][1]['name']
        loop=True
        max=len(results['searchresults']['torrent'])
    except KeyError as key:
        if str(key)=="1":
            element=results['searchresults']['torrent']
            max=1
            loop=False
        else:
            ahdlogger.warn(f"{title}:Probably no results")
            addmissing(output,files,file)
            return
    for i in range(max):

        titlematch=False
        group=False
        resolution=False
        source=False
        sizematch=False
        if loop: element = results['searchresults']['torrent'][i]
        querytitle=lower(element['name'])
        if querytitle==None:
            continue
        querygroup=lower(element['releasegroup'])
        if querygroup==None:
            querygroup=""
        queryresolution=element['resolution']
        querysource=lower(element['media'])
        if querysource=="uhd blu-ray":
            querysource="blu-ray"
        if querysource=="web-dl" or querysource=="webrip":
            querysource="web"
        queryencoding=element['encoding']
        querysize= int(element['size'])

        if querytitle==title:
            titlematch=True
        if querysource==fileguessit.get_source() or fileguessit.get_source()=="":
            source=True
        if querygroup==fileguessit.get_group() or re.search(querygroup,fileguessit.get_group(),re.IGNORECASE)!=None \
        or re.search(fileguessit.get_group(),querygroup,re.IGNORECASE)!=None or fileguessit.get_group()=="":
            group=True
        if queryresolution==fileguessit.get_resolution():
            resolution=True
        if difference(querysize,filesize)<.01:
            sizematch=True


        ahdlogger.debug(f"Comparison UserTitle:{title} SiteTite:{querytitle} UserSource:{fileguessit.get_source()} SiteSource:{querysource} UserGroup:{fileguessit.get_group()} SiteGroup:{querygroup} UserRes:{fileguessit.get_resolution()} SiteRes:{queryresolution}  \n ")
        if encode is False and source is True and resolution is True:
            return
        if titlematch is True and source is True and group is True and resolution is True \
        and sizematch is True and filesize!=0:
            return

    addmissing(output,files,file)
def addmissing(output,files,file):
    ahdlogger.warn("Adding Potential Upload to File")
    output=open(output,"a+")
    output.write("AHD:")
    if files.get_dir()=="0":
        output.write("Directory:Single-File:")
        output.write(file)
    else:
        output.write(f"Directory:{files.get_dir()}:")
        output.write(file)
    output.write('\n')
    output.close()


def get_imdb(details):
   title = details.get('title')
   ia = IMDb()
   if title==None:
       return title
   for i in range(0,16):
       if i==15:
           return None
       try:
         results = ia.search_movie(title)
         break
       except Exception as e:
           time.sleep(10)
   if len(results) == 0:
        return None
   for movie in results:
        if ((details.get('year')==movie.get('year')) and (movie.get('year')!=None or details.get('year')!=None )):
            return movie.movieID
   else:
      return results[0].movieID
def difference(value1,value2):
    dif=abs((value2-value1)/((value1+value2)/2))
    return dif
def lower(input):
    if input==None:
        return input
    else:
        input=input.lower()
        return input
def createconfig(config):
    configpath=os.path.dirname(os.path.abspath(__file__))+"/ahd_cross.txt"
    config.read(configpath)


    if config.has_section('general') ==False:
        config.add_section('general')
    if config.has_section('grab') ==False:
        config.add_section('grab')
    if config.has_section('scan') ==False:
        config.add_section('scan')
    message_dialog(
        title="Config Creator",
        text="Welcome to the Config Creator.\nA config File is recommended to run this program\nWe will Start by adding root or Folders to Scan\nNote You'll need at least one root\nNote:This will overright ahd_cross.txt if you confirm at the end",
    ).run()

    newroot =True
    root=None
    rootstr=""
    ignorestr=""
    while newroot:
        if root==None:
            root = input_dialog(title='Getting Root Directories ',text='Please Enter the Path to a Root Directory:').run()
        if root==None:
            break
        addstring="Adding:"+root + " is this Okay? "
        option = button_dialog(
             title=addstring,
             buttons=[("Yes", True), ("No", False)],
        ).run()
        if option==False:
            root=None
            pass
        else:
            rootstr=rootstr+root+","
            root=None
        newroot= button_dialog(
                 title="Add Another Root Folder ",
                 buttons=[("Yes", True), ("No", False)],
        ).run()
    config.set('scan', "root", rootstr)

    confirm = button_dialog(
                 title="Add a Folder or File to ignore ",
                 buttons=[("Yes", True), ("No", False),("Info", None)],
    ).run()
    while confirm!=False:
        if confirm==None:
            message_dialog(
                    title="Ignore Folders and Files",
                    text="Ignored Directories will not be scanned As a subdirectory of another Root Folder.\nHowever note that a ignored Folder can still be added as a root .\nIn that case the subdirectories of the ignore folder would be added\nIgnored Files will not be added at all",
            ).run()
        if confirm:
            ignorepath = input_dialog(title='Getting ignore Path ',text='Please Enter the Path to ignore:').run()

        if ignorepath==None:
            break
        addstring="Adding:"+ignorepath + " is this Okay? "
        option = button_dialog(
             title=addstring,
             buttons=[("Yes", True), ("No", False)],
        ).run()
        if addstring==True:
             ignorestr= ignorestr+ignorepath
        confirm = button_dialog(
                     title="Add Another Folder to ignore ",
                     buttons=[("Yes", True), ("No", False)],
        ).run()

    config.set('scan', "ignore", ignorestr)


    #setup next few options as empty
    config.set('general', "txt", "")
    config.set('grab', "api", "")
    config.set('grab', "cookie", "")
    config.set('grab', "output", "")
    config.set('general', "misstxt", "")
    config.set('grab', "torrent", "")


    confirm=False
    while confirm==False:
        txtpath = input_dialog(title='Scanner TXT File',text='Please Enter the Path for scanner and grabber.\nFile Paths will Writen Here and is required ').run()
        if txtpath==None:
            break
        config.set('general', "txt", txtpath)
        confirmtxt="You entered:"+txtpath+" is this Okay?"
        confirm = button_dialog(
                 title=confirmtxt,
                 buttons=[("Yes", True), ("No", False)],
            ).run()
    confirm=False
    while confirm==False:
        torrent = input_dialog(title='Torrent Folder',text='Please Enter the Path for downloading Torrents\nIf you leave this blank make sure to set Output\nThat step will come up later in this setup\nIt is okay to setup Both Torrent and Output\nHowever if None are selected then Nothing will happen when Downloader finds a match').run()
        if torrent==None:
            break
        config.set('grab', "torrent", torrent)
        confirmtxt="You entered:"+torrent+" is this Okay?"
        confirm = button_dialog(
             title=confirmtxt,
             buttons=[("Yes", True), ("No", False)],
        ).run()



    confirm=False
    while confirm==False:
        key = input_dialog(title='AHD KEY',text='Please Enter your AHD passkey.\n   This will be used to Download Torrent Files and Scan AHD\nThis is Required').run()
        if key==None:
            break
        config.set('grab', "api", key)
        confirmtxt="You entered:"+key+" is this Okay?"
        confirm = button_dialog(
                 title=confirmtxt,
                 buttons=[("Yes", True), ("No", False)],
            ).run()
    confirm=False
    while confirm==False:
        cookie = input_dialog(title='Cookie',text='You Will need a Cookie File For Downloading\n[cookies.txt by Lennon Hill and Get cookies.txt are good options for exporting\nfrom browser]\nFile should be in .txt and not a json. Paste the path Here\nPress Cancel to Leave Blank\nThis is Required if you want to Download').run()
        if cookie==None:
            break
        config.set('grab', "cookie", cookie)
        confirmtxt="You entered:"+cookie+" is this Okay?"
        confirm = button_dialog(
            title=confirmtxt,
            buttons=[("Yes", True), ("No", False)],
        ).run()

    confirm= button_dialog(
        title="Do you want to Exclude Certain Sources\nFor example all blu-ray encodes,etc\nThese will be ignored during grabbing/matching\nNote: Other are Files that don't fit in other selectors\nPress Cancel to Leave Blank",
        buttons=[("Yes", True), ("No", False)],
    ).run()
    excludestr=""
    if confirm:
        exclude= checkboxlist_dialog(
        values=[
            ("remux", "Remux"),
            ("blu", "Blu-Ray Encode"),
            ("tv", "HDTV"),
            ("web", "WEB"),
            ("other", "Other"),
        ],
        title="Exclude",
        text="Pick the Source Types you would like to ignore ",
        ).run()

        for type in exclude:
            excludestr=excludestr+type+","
    config.set('grab', "exclude", excludestr)


    confirm=False
    while confirm==False:
        outpath = input_dialog(title='Download Links Output TXT',text='Please Enter a path for Writing Matched Links to.\nWith This Every Time a Match is found a download url will be written here\nPress Cancel to Leave Blank').run()
        if txtpath==None:
            break
        config.set('grab', "output", outpath)
        confirmtxt="You entered:"+outpath+" is this Okay?"
        confirm = button_dialog(
                 title=confirmtxt,
                 buttons=[("Yes", True), ("No", False)],
            ).run()

    confirm=False
    while confirm==False:
        missingpath = input_dialog(title='Missing Files Output TXT',text='Please Enter a path for Writing Potential Missing Files.\nDuring a "Missing Scan"  Every File is Compared to AHD Libary if the Slot is not already filled or your file is a encode.\nThe Path will be written to this TXT File\nThis is Required if you want to Find Files to upload').run()
        if txtpath==None:
            break
        config.set('general', "misstxt", missingpath)
        confirmtxt="You entered:"+outpath+" is this Okay?"
        confirm = button_dialog(
                 title=confirmtxt,
                 buttons=[("Yes", True), ("No", False)],
            ).run()






    fd=""
    confirm=False
    while confirm==False:
        fd = input_dialog(title='FD' ,text='FD is required for Program\nDownloads Can be found here https://github.com/sharkdp/fd/releases\nBy Default the program comes with a version of fd for your OS\nIf you want to use your own binary, you can enter your choice here \nPress Cancel to use the Default  ').run()
        if txtpath==None:
            break
        config.set('general', "fd", fd)
        confirmtxt="You entered:"+fd+" is this Okay?"
        confirm = button_dialog(
                 title=confirmtxt,
                 buttons=[("Yes", True), ("No", False)],
            ).run()
    wget=""
    confirm=False
    while confirm==False:
        wget = input_dialog(title='WGET' ,text='WGET is required for Program\nLinux comes with this Preinstalled usually for windows:https://eternallybored.org/misc/wget/\nBy Default the program comes with a version of wget for Windows\nIf you want to use your own binary, you can enter your choice here \nPress Cancel to use the Default  ').run()
        if txtpath==None:
            break
        config.set('general', "wget", wget)
        confirmtxt="You entered:"+wget+ " is this Okay?"
        confirm = button_dialog(
                 title=confirmtxt,
                 buttons=[("Yes", True), ("No", False)],
            ).run()








    sections = config.sections()
    config_string=""
    for section in sections:
        options = config.options(section)
        for option in options:
              temp_dict={}
              temp_dict[option] = config.get(section,option)
              config_string=config_string+str(temp_dict)+"\n"






    txt="These are the Options that will be written to the configfile\nPlease Confirm if you want to save these Options\n Current File wil be overwritten\n\n"+config_string



    option = button_dialog(
             title="Confirm Options",
             text=txt,
             buttons=[("Yes", True), ("No", False)],
    ).run()
    if option==False:
        return
    with open(configpath, 'w') as configfile:
      print("Writing to configfile")
      config.write(configfile)
