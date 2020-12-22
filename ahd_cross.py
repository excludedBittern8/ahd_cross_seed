#! /usr/bin/env python3
"""NOTE: READ DOCUMENTATION BEFORE USAGE.
Usage:
    ahd_cross.py [(-h | --help) --txt=<txtlocation> --fd <fd> --config <config> --delete --lines-skip <num_lines_skipped]
    [--torrent <torrents_download> --cookie <cookie> --output <output> --api <apikey> --date <int> --size <t_or_f> --misstxt <output>]
    [--root <normal_root(s)>... --ignore <sub_folders_to_ignore>...  --exclude <source_excluded>...]
    ahd_cross.py interactive [--txt=<txtlocation> --fd <fd>  --config <config> --delete --lines-skip <num_lines_skipped]
    [--torrent <torrents_download> --cookie <cookie> --output <output> --api <apikey> --date <int> --size <t_or_f> --misstxt <output>]
    [--root <normal_root(s)>...  --ignore <sub_folders_to_ignore>...  --exclude <source_excluded>...]
    ahd_cross.py scan [--txt=<txtlocation> --fd <fd>  --config <config> --delete]
    [--root <normal_root(s)>... --ignore <sub_folders_to_ignore>...]
    ahd_cross.py grab [--txt=<txtlocation> --fd <fd>  --lines-skip <num_lines_skipped> --torrent <torrents_download> --cookie <cookie> --output <output> ]
    [--api <apikey> --config <config> --date <int> --size <t_or_f>]
    [--exclude <source_excluded>]...
    ahd_cross.py missing [--txt=<txtlocation> --fd <fd>  --misstxt <output>  --api <apikey> --config <config>]
    [--exclude <source_excluded>...]



Options:
  --h ;--help     Show this screen
  --config ; -x <config> load arguments from a config file. Can be used alternatively/with ALL required arguments
  --txt <txtlocation>  txt file with all the file/directory name. Required for scan or grab
  --fd  Use to replace the built in fd file. fd is used to search a folder using criteria pre-determined by this program
========================================================================================================================================================
[interactive]
Note:arguments can be blank for this action
Will display a GUI on the commandline.

<pick 1>
ahd_cross.py [arguments]
ahd_cross.py interactive [arguments]
========================================================================================================================================================

[scan]
 scan a directory to create a document with all folders and files

 ahd_cross.py scan [arguments]

<required arguments>
--root <normal_root(s)> root folder to scan



<optional arguments>
--delete; -d  Will delete the old txt file
--ignore ; -i <sub_folders_to_ignore>  folder will be ignored for scan
========================================================================================================================================================
[grab]
Downloads and/or send to output txt file torrents using input txt file.

ahd_cross.py grab
<required arguments>
--cookie  <cookie> This is a cookie file for ahd, their are numerous extensions to grab this.
--api ; -a <apikey> This is your ahd passkey


<choose at least 1>
--output ; -o <output>  Here are where the torrentlinks will be written
--torrent ; -t <torrents_download>  Here are where the torrent files will downloa

 <optional>
--date ; -d <int> only download torrents newer then this input should be int, and represents days. By default it is set to around 25 years(optional)  [default: 10000 ]
--lines-skip <num_lines_skipped> Number of lines in txt file to skip during grab  [default: 0]
--exclude ; -e <source_excluded>  These file type(s) will not be scanned blu,tv,remux,other,web.(optional)
--size ; -s <t_or_f> set whether a search should be done by name only or include file size restriction. If true then secondary check will be added to find a match [default: t]
========================================================================================================================================================
[missing]
Checks to see if you have any potential uploads by comparing your files to what has already been uploaded

ahd_cross.py missing
--misstxt <txt_where_potential_uploads_are written> here we output to a txt file files that don't have any uploads. This means that we can potentially upload these, for rank. Or to increase the amount of cross seeds we have




  """
import requests
import subprocess
import pathlib
from subprocess import PIPE
from pathlib import Path
import os
from guessit import guessit
from datetime import date,timedelta, datetime
from docopt import docopt
import tempfile
import time
import configparser
import re
config = configparser.ConfigParser(allow_no_value=True)
#import other files
from folders import *
from classes import *
from files import *
from prompt_toolkit.shortcuts import button_dialog
import sys


"""
Setup Function
"""
def setFD():
    if sys.platform=="linux":
        try:
            subprocess.run(['fd'])
            arguments['--fd']="fd"
        except:
            path=os.getcwd()
            fd=f"{path}/ bin/fd"
            arguments['--fd']=fd
    if sys.platform=="win32":
        try:
            subprocess.run(['fd.exe'])
            arguments['--fd']="fd.exe"
        except:
            path=os.getcwd()
            fd=f"{path}/ bin/fd.exe"
            arguments['--fd']=fd
    

def duperemove(txt):
    print("Removing Duplicate lines from ",txt)
    if txt==None:
        return
    input=open(txt,"r")
    lines_seen = set() # holds lines already seen
    for line in input:
        if line not in lines_seen: # not a duplicate
            lines_seen.add(line)
    input.close()
    outfile = open(txt, "w")
    for line in lines_seen:
        outfile.write(line)
    outfile.close()
def updateargs(arguments):
    configpath=arguments.get('--config')
    if os.path.isfile(configpath)==False:
        print("Could Not Read Config Path")
        return arguments
    try:
        configpath=arguments.get('--config')
        config.read(configpath)
    except:
        print("Could Not Read Config Path")
        return arguments
    if arguments['--txt']==None:
        arguments['--txt']=config['general']['txt']
    if arguments['--cookie']==None:
        arguments['--cookie']=config['grab']['cookie']
    if arguments['--api']==None:
        arguments['--api']=config['grab']['api']
    if arguments['--torrent']==None:
        arguments['--torrent']=config['grab']['torrent']
    if arguments['--output']==None:
        arguments['--output']=config['grab']['output']
    if arguments['--misstxt']==None:
        arguments['--misstxt']=config['general']['misstxt']
    if arguments['--exclude']==[] or  arguments['--exclude']==None:
        arguments['--exclude']=config['grab']['exclude']
    if arguments['--root']==[] or  arguments['--root']==None:
        arguments['--root']=config['scan']['root']
    if arguments['--ignore']==[] or arguments['--ignore']==None:
        arguments['--ignore']=config['scan']['ignore']
    if arguments['--size']=="1":
        arguments['--size']=config['grab']['size']
    return arguments
def releasetype(arguments):
    source={'remux':'yes','web':'yes','blu':'yes','tv':'yes','other':'yes'}
    if arguments['--exclude']==None or arguments['--exclude']==[] or arguments['--exclude']=="" or len(arguments['--exclude'])==0:
        return source
    if type(arguments['--exclude'])==str:
        arguments['--exclude']=arguments['--exclude'].split(",")
    for element in arguments['--exclude']:
        if element=="":
            continue
        try:
            source[element]="no"
        except KeyError:
            pass
    return source
def download(arguments,txt):
    index=0
    list=open(txt,"r")
    source=releasetype(arguments)
    errorfile=errorpath=pathlib.Path(__file__).parent.absolute().as_posix()+"/Errors/"
    if os.path.isdir(errorfile)==False:
            os.mkdir(errorfile)
    errorfile=errorfile+"ahdcross_errors_"+datetime.now().strftime("%m.%d.%Y_%H%M")+".txt"
    for line in list:
        index=index+1
        print('\n',line)
        if index<=int(arguments["--lines-skip"]):
            print("Skipping Line")
            continue
        if line=='\n' or line=="" or len(line)==0:
            continue
        line=line.rstrip("\n")


        if os.path.isdir(line)==True:
            download_folder(arguments,txt,line,source,errorfile)
        elif os.path.isfile(line)==True:
            download_file(arguments,txt,line,source,errorfile)

        else:
            print("File or Dir Not found")
            errorpath=open(errorfile,"a+")
            errorstring=line +": File or Dir Not found "  + " - " +datetime.now().strftime("%m.%d.%Y_%H%M") + "\n"
            errorpath.write(errorstring)
            errorpath.close()
            continue
        print("Waiting 5 Seconds")
        time.sleep(5)
def missing(arguments):
    if arguments['--misstxt']=='' or len(arguments['--misstxt'])==0 or arguments['--misstxt']==None:
        print("misstxt must be configured for missing scan ")
        quit()
    source=releasetype(arguments)
    list=open(arguments['--txt'],"r")
    index=0
    errorfile=pathlib.Path(__file__).parent.absolute().as_posix()+"/Errors/"
    if os.path.isdir(errorfile)==False:
            os.mkdir(errorfile)
    errorfile=errorfile+datetime.now().strftime("%m.%d.%Y_%H%M")+".txt"
    for line in list:
        index=index+1
        print('\n',line)
        if index<=int(arguments["--lines-skip"]):
            print("Skipping Line")
            continue
        elif line=='\n' or line=="" or len(line)==0:
            continue
        if  re.search("#",line)!=None:
            print("Skipping Line")
            continue
        line=line.rstrip("\n")

        if os.path.isdir(line)==True:
            scan_folder(arguments,line,source,errorfile)
        elif os.path.isfile(line)==True:
            scan_file(arguments,line,source,errorfile)
        else:
            print("File or Dir Not found")
            errorpath=open(errorfile,"a+")
            errorstring=line +": File or Dir Not found "  + " - " +datetime.now().strftime("%m.%d.%Y_%H%M") + "\n"
            errorpath.write(errorstring)
            errorpath.close()
            continue

        print("Waiting 5 Seconds")
        # time.sleep(5)
def setup(arguments,interactive=None):
    if interactive==None:
        interactive=False
    updateargs(arguments)
    file=arguments['--txt']
    os.chdir(Path.home())
    try:
        open(file,"a+").close()
    except:
        if interactive==False:
            print("No txt file")
            quit()
        else:
            message_dialog(
                title="Interactive Mode",
                text="Unable to read text file\nPlease Change Config Location\nOr Start Config Wizard",
            ).run()
            return False

def setupscan(arguments):
    setFD()
    print("Scanning for folders")
    if arguments['--delete']:
        open(file, 'w').close()
    fdignore=arguments['--fdignore']
    if fdignore==None:
        try:
            arguments['--fdignore']=os.path.dirname(os.path.abspath(__file__))+ "/.fdignore"
        except:
            print("Error setting fdignore")
            exit()
    t=open(arguments['--fdignore'], 'w')
    t.close()

"""
Scanning Functions
"""
def set_ignored(arguments):
    ignore=arguments.get("--fdignore")
    if ignore==None or ignore==[] or ignore=="" or len(ignore)==0:
       return
    if type(arguments['--ignore'])==str:
        arguments['--ignore']=arguments['--ignore'].split(",")
    ignorelist=arguments['--ignore']
    if len(ignorelist)==0:
        return
    open(ignore,"w+").close()
    ignore=open(ignore,"a+")
    for element in ignorelist:
        if element=="":
            continue
        ignore.write(element)
        ignore.write('\n')
def searchdir(arguments,ignorefile):
    if arguments['--normalrt']==[] or arguments['--normalrt']==None:
        return
    folders=open(arguments['--txt'],"a+")
    print("Adding Normal Folders to", arguments['--txt'])
    if type(arguments['--normalrt'])==str:
        arguments['--normalrt']=arguments['--normalrt'].split(",")
    list=arguments['--normalrt']
    for root in list:
        if root=="":
          continue
        if os.path.isdir(root)==False:
          print(root," is not valid directory")
          continue
        subprocess.run([arguments['--fd'],'.',root,'-t','d','--max-depth','1','--ignore-file',ignorefile],stdout=folders)
        subprocess.run([arguments['--fd'],'.',root,'-t','f','-e','.mkv','--max-depth','1','--ignore-file',ignorefile],stdout=folders)
    print("Done")

#Main
if __name__ == '__main__':
    arguments = docopt(__doc__, version='ahd_cross_seed_scan 1.2')
#interactive Mode
    if arguments.get("--config")==None:
        arguments['--config']=os.path.dirname(os.path.abspath(__file__))+"/ahd_cross.txt"
    if (arguments['scan']!=True  and arguments['grab']!=True and arguments['missing']!=True) or arguments['interactive']:
            message_dialog(
                title="Interactive Mode",
                text="Welcome to AHD Cross you are starting the programs in interactive Mode\nBefore Deciding on the next question note a config File is required in this mode",
            ).run()
            startconfig = button_dialog(
                title="Start Config Wizard",
                buttons=[("Yes", True), ("No", False)],
            ).run()
            if startconfig:
                createconfig(config)
            continueloop =True
            while continueloop!=None:

                continueloop= radiolist_dialog(
                values=[

                    ("download", "Cross Seed Scan"),
                    ("missing", "Upload Finder"),
                    ("scan", "Update Folder/Files"),
                    ("config", "Change Config Location"),
                    ("config2", "Start Config Wizard")
                ],
                title="Interactive Mode",
                text="",
                ).run()
                if continueloop==None:
                    quit()
                elif continueloop=="scan":
                    t=setup(arguments,True)
                    if t==False:
                        continue
                    setupscan(arguments)
                    set_ignored(arguments)
                    duperemove(arguments['--fdignore'])
                    searchdir(arguments,arguments['--fdignore'])
                    duperemove(arguments['--txt'])
                elif continueloop=="missing":
                    t=setup(arguments,True)
                    if t==False:
                        continue
                    setupscan(arguments)
                    missing(arguments)
                    duperemove(arguments['--misstxt'])
                elif continueloop=="download":
                    t=setup(arguments,True)
                    if t==False:
                        continue
                    setupscan(arguments)
                    download(arguments,arguments['--txt'])
                elif continueloop=="config":
                    arguments['--config']=input_dialog(title='Config Path',text='Please Enter the Path to your Config File:').run()
                    t=setup(arguments,True)
                    if t==False:
                        continue
                    info="Please Check if the arguments are correct for New Config\nIf not their was probably an issue reading the file\nNote all that matters for this mode are the entries with -- at the beginning\n\n"+ str(arguments)
                    message_dialog(
                        title="Options Change",
                        text=info
                    ).run()
                elif continueloop=="config2":
                    createconfig(config)
                    setup(arguments,True)



#Non interactive Mode
    if arguments['scan']:
        setup(arguments)
        setupscan(arguments)
        set_ignored(arguments)
        duperemove(arguments['--fdignore'])
        searchdir(arguments,arguments['--fdignore'])
        duperemove(arguments['--txt'])
    elif arguments['grab']:
        setup(arguments)
        download(arguments,arguments['--txt'])
    elif arguments['missing']:
        setup(arguments)
        missing(arguments)
        duperemove(arguments['--misstxt'])
