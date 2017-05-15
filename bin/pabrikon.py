#!/usr/bin/python

import csv
import getopt
import logging
import logging.handlers
import os
import re
import subprocess
import sys
import time

execfile('/opt/pabrikon/config/config.py')

alls = False
comment = 'default comment'
current_dir = os.getcwd()
directory = ''
name = 'default'
op = ''
source = 'default'
types = 'default'
type_dir = 'default'
verbose = False
last_updated = ''
iconslist = ""
directorylist = ""
directory_ar = []

def __pabrikon__():
    if op == 'help':
        __help__()
    elif op == 'makecsv':
        __makecsvdata__()
    elif op == 'newproject':
        __newproject__()
    elif op == 'version':
        __version__()
    elif op == 'update':
        __update__()
    else:
        if os.path.exists(current_dir + "/data"):
            if op == 'build':
                __build__()
            elif op == 'cleanproject':
                __cleanproject__()
            elif op == 'list':
                __listdata__()
            elif op == 'makepng':
                __makepng__()
            elif op == 'makesym':
                __makesym__()
            elif op == 'makesvg':
                __makesvg__()
            elif op == 'makeindex':
                __makeindex__()
            elif op == 'newikon':
                __new__()
            elif op == 'opencsv':
                __opencsv__()
            elif op == 'opensvg':
                __opensvg__()
            elif op == 'readcsv':
                __readcsv__()
            elif op == 'makeicon':
                __makeicon__()
            else:
                __help__()
        else:
            print '[error] for first time please type \'$ pabrikon' \
            ' --makecsv \' for generate csv data'



def __createlastupdated__():
    os.system("rm -rf " + current_dir + "/data/last_updated && echo " + \
     str(time.time()) + " > " + current_dir + "/data/last_updated")

def __checklastupdated__(i):
    if os.path.exists(current_dir + "/data/last_updated"):
        a = os.path.getmtime(current_dir + "/data/last_updated")

        if i == "":
            max_mtime = 0
            for dirname, subdirs, files in os.walk("."):
                for fname in files:
                    full_path = os.path.join(dirname, fname)
                    mtime = os.stat(full_path).st_mtime
                    if mtime > max_mtime:
                        max_mtime = mtime
                        # max_dir = dirname
                        max_file = full_path

            if max_file != "last_updated":

                b = os.path.getmtime(max_file)

                if b > a:
                    return True
            else:
                return False
        else:
            b = os.path.getmtime(i)
            if b > a:
                return True
            else:
                return False
    else:
        return False
        os.system("touch " + current_dir + "/data/last_updated")



def __build__():
    print '[info] Start building icons'
    logging.info("Starting building icons")

    if not __checklastupdated__(""):
        print '[info] No newest files'
        print '[info] Use -a to export all files'
        logging.info("No newest files")

        if not alls:
            quit()
        else:
            __cleanproject__()

    else:
        __cleanproject__()

    if types:
        if types == 'svg':
            __makesvg__()
        else:
            __makepng__()

    __makesym__()
    print '[info] Building icons has been finished'
    logging.info("Building icons has been finished")

    # how to use
    # pabrikon --build
    # pabrikon -b

def __cleanproject__():
    print '[info] Start clean project'

    logging.info("Start Clean project")
    logging.debug("current directory: " + current_dir)


    for icon_ in list_dirs:
        if os.path.exists(current_dir + "/" + icon_ + "/scalable"):
            if types == 'default' or types == 'symlink':
                os.system('find ' + current_dir + '/' + icon_ \
                        + '/scalable  -type l -exec rm -rf {} \;')
        for size_ in icon_sizes:
            if os.path.exists(current_dir + "/" + icon_ + "/" + size_):
                if types == 'default':
                    os.system('find ' + current_dir + '/' + icon_ + \
                            '/' + size_ + ' -type f -name \'*.png\' ' \
                            +'-exec rm -rf {} \;')
                    os.system('find ' + current_dir + '/' + icon_ + \
                            '/' + size_ + ' -type f -name \'*.svg\' ' \
                            + ' -exec rm -rf {} \;')
                    os.system('find ' + current_dir + '/' + icon_ + \
                            '/' + size_ + ' -type l -exec rm -rf {} \;')
                elif types == 'symlink':
                    os.system('find ' + current_dir + '/' + icon_ + \
                            '/' + size_ + ' -type l -exec rm -rf {} \;')
                elif types == 'png':
                    os.system('find ' + current_dir + '/' + icon_ + \
                            '/' + size_ + ' -type f -name \'*.png\'' \
                            ' -exec rm -rf {} \;')
                    os.system('find ' + current_dir + '/' + icon_ + \
                            '/' + size_ + ' -type l -exec rm -rf {} \;')
                elif types == 'svg':
                    os.system('find ' + current_dir + '/' + icon_ + \
                            '/' + size_ + ' -type f -name \'*.svg\'' \
                            ' -exec rm -rf {} \;')
                    os.system('find ' + current_dir + '/' + icon_ + \
                            '/' + size_ + ' -type l -exec rm -rf {} \;')

    print '[info] Cleaning project has been finished with type:' \
            ' [' + types + ']'
    logging.info("Cleaning project has been finished with type ' \
             '[" + types + "]")

    # how to use
    # pabrikon --clean
    # pabrikon --clean --type=png
    # pabrikon --clean --type=symlink

def __cmdexists__(cmd):
    return subprocess.call("type " + cmd, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def __help__():
    os.system('cat /opt/pabrikon/man/pabrikon.man')

    # how to use
    # pabrikon -h
    # pabrikon --help
def __listdata__():
    print '[info] List data'
    logging.info("List data")
    if types:
        if types != 'default':
            os.system('/opt/pabrikon/bin/list.sh ' + types + ' ')
        else:
            os.system('/opt/pabrikon/bin/list.sh all')
    # how to use
    # pabrikon -l
    # pabrikon -l -t {all|png|svg|symlink}

def __makecsvdata__():
    if source == 'pabrikon':
        # copy csv file from pabrikon default to current directory
        print '[info] Start copying csv file to current project'
        logging.info("Start copying csv file to current project")

        if verbose:
            os.system('cp -rv /opt/pabrikon/data .')
        else:
            os.system('cp -r /opt/pabrikon/data .')

        print '[info] Copying csv file has been finished'
        logging.info("Copying csv file has been finished")
    elif source == 'default':
        # make csv file from symlink
        print '[info] Start make csv file from symlink in current ' \
                ' project'
        logging.info("Start make csv file from symlink in current ' \
                'project")

        if verbose:
            os.system('/opt/pabrikon/bin/makecsv.sh v')
        else:
            os.system('/opt/pabrikon/bin/makecsv.sh')

        print '[info] Csv file creation has been finished'
        logging.info("Csv file creation has been finished")
    else:
        print '[error] put --source=pabrikon for make csv file from ' \
                'pabrikon default'
        print '[error] put --source=default for make csv file from ' \
                'symlink file'
        logging.error("__makecsvdata__ source not in (pabrikon|default)")
    __createlastupdated__()

    # how to use
    # pabrikon --makecsv
    # pabrikon --makecsv --source=default
    # pabrikon --makecsv --source=pabrik

def __makepng__():
    global types
    types = "png"
    __makeicon__()

    # how to use
    # pabrikon --makepng

def __makesym__():
    print '[info] Start make symbolic link from data'
    logging.info("Start make symbolic link from data")
    current_dir = os.getcwd()
    icon_sizes.append('scalable')

    for icon_ in list_dirs:
        if verbose:
            print icon_ + "==========================================" \
                    "=============================="

        if os.path.exists(current_dir + "/" + icon_):
            for size_ in icon_sizes:
                if verbose:
                    print size_ + "=================================" \
                            "======================================="
                if not os.path.exists(current_dir + "/" + icon_ + "/" \
                        + size_):
                    subprocess.check_output(['mkdir', '-p', current_dir \
                            + "/" + icon_ + "/" + size_])


                os.chdir(current_dir + "/" + icon_ + "/" + size_)
                if size_ == "scalable":
                    ext = '.svg'
                else:
                    if types:
                        if types == "svg":
                            ext = '.svg'
                        else:
                            ext = '.png'

                if os.path.exists(current_dir  + '/data/' +  \
                        icon_  + '.csv'):
                    with open(current_dir  + '/data/' +  icon_  \
                            + '.csv', 'rb') as f:
                        reader = csv.reader(f)
                        csv_list = list(reader)

                    for c in csv_list:
                        ln_from = c[0].replace('#size#', size_)
                        ln_to = c[1].replace('#size#', size_)
                        if os.path.exists(ln_from + ext):
                            if not os.path.exists(ln_to + ext):
                                os.system('ln -s ' + ln_from + ext \
                                        + ' ' + ln_to + ext)
                                if verbose:
                                    print 'ln -s ' + ln_from + ext \
                                            + ' ' + ln_to + ext



    print '[info] Making  symlink from data has been finished'
    logging.info("Making symlink from data has been finished")

    # how to use
    # pabrikon --makesym

def __makesvg__():
    global types
    types = "svg"
    __makeicon__()

    # how to use
    # pabrikon --makesvg

def __export__(source, destination, width, height):
    if (types == 'svg'):
        t = 'svg'
    else:
        t = 'png'

    logging.info("Exporting " + source + " => " + destination)
    os.system("rsvg-convert " + source + " -o " + destination \
                + " -f " + t + " -w " + width + " -h " + height)
    if verbose:
        print "Exporting " + source + " => " + destination

def __makeindex__():
    target = open(current_dir + "/index.theme", "w")
    target.truncate()
    print '[info] Creating index.theme files'
    logging.info("Creating index.theme files")

    if verbose:
        print iconslist
        print directorylist

    target.write(iconslist)
    target.write(directorylist)

    print '[info] Creating index.themes has been finished'
    logging.info("Creating index.themes has been finished")

    # how to use
    # pabrikon -i
    # pabrikon --makeindex

def __minizer__():
    # this is for reduce the size of svg file
    #not finished
    print 'minizer'
    # how to use
    # pabrikon --minizer

def __new__():
    # this is for copy default default.svg to spesific
    print '[info]: make new icon ' + directory + '/scalable/' \
            + name + '.svg'
    logging.info('make new icon ' + directory + '/scalable/' \
            + name + '.svg')
    os.system("cp -rv /opt/pabrikon/data/default.svg ./" \
            + directory + "/scalable/" + name + ".svg")

    # how to use
    # pabrikon --new --name=nameoficon --directory=categories

def __newproject__():
    if not name == "default":
        if not os.path.exists(name):
            print '[info] Start make new project \nName=' + name \
                    + "\nComment=" + comment
            logging.info("start make new project Name=" + name \
                    + ", Comment=" + comment)

            subprocess.check_output(['mkdir', '-p', name])
            logging.debug("making new project with name=" + name)

            os.system('cp -r /opt/pabrikon/data ' + name)
            os.system('mv ./' + name + '/data/index.theme ' \
                    + name + '/index.theme')
            os.system('sed -i "s/ICONNAME/' + name  + '/g" ' \
                    + name + '/index.theme')
            os.system('sed -i "s/COMMENT/' + comment  + '/g" ' \
                    + name + '/index.theme')

            for icon_ in list_dirs:
                subprocess.check_output(['mkdir', '-p', name \
                        + '/' + icon_ + '/scalable'])

            print '[info] make project with name `' + name \
                    + '` has been created '
            logging.info('make project with name `' + name \
                    + '` has been created ')
        else:
            print '[error] cannot create directory `' + name \
                    + '`: File exists'
            logging.error('cannot create directory `' + name \
                    + '`: File exists')
    elif not source == "default":
        if source.find(".git") != -1:
            if __cmdexists__("git"):
                print '[info] Start make new project from source:' \
                        + source
                logging.info('Start make new project from source:' \
                        + source)
                os.system('git clone ' + source)
                print '[info] make new project from git repository'
                logging.info('make new project from git repository')
            else:
                print '[error] please install git for make new ' \
                        'project from git reposity'
                logging.error('please install git for make new ' \
                        'project from git reposity')

        else:
            print '[error] its not valid git url'
            logging.error('its not valid git url')
    else:
        __help__()

    # how to use
    # this make new project with empty icon with defauls csv data for make symlink
    # pabrikon --newproject --name=NAME --comment="This Comment for icon"
    # this make new project with source from git uri
    # pabrikon --newproject --source=GIT_URL

def __opencsv__():
    if name:
        if source == 'pabrikon':
            dirs = '/opt/pabrikon'
        else:
            dirs = '.'

        print '[info] Start open ' + name + '.csv files in directory' \
                + dirs
        logging.info('Start open ' + name + '.csv files in directory' \
                + dirs)

        if not name == "default":
            if os.path.exists(dirs + '/data/' + name + '.csv'):
                os.system(csv_editor  + ' ' +  dirs + '/data/' \
                        + name + '.csv')
            else:
                print '[error] please put the name of csv in ' \
                        'data directory'
                print '[info]: $ pabrikon --opencsv --name=apps'

                logging.error(dirs + '/data/' + name \
                        + '.csv : no such file directory')
    else:
        print '[error] please put the name of csv in data directory'
        print '[example]: $ pabrikon --opencsv --name=apps'
        os.system('ls ' + dirs + '/data | grep csv | sed \'s/.csv//\' ')
        logging.error(dirs + '/data/' + name \
                + '.csv : no such file directory')

    print '[info] Edit csv file has been finished'
    logging.info('Edit csv file has been finished')


    # how to use
    # pabrikon --opencsv --name=NAME.csv
    # this open default csv file from pabrikon
    # pabrikon --opencsv --name=NAME.csv --source=pabrikon

def __opensvg__():
    if not name == "default":
        if directory:
            files = "./" + directory + "/scalable/" + name + ".svg"
            if os.path.exists(files):
                os.system("inkscape " + files)
            else:
                print "[error] " + files + " no such file or directory"
                logging.info(files + " no such file or directory")

        else:
            os.system("find . -name '" + name \
                    + ".svg' -exec inkscape {} \;")
    else:
        __help__()

    print '[info] Open svg file has been finished'
    logging.info('Open svg file has been finished')

    # how to use
    # pabrikon --open --name inkscape --directory apps

def __makeicon__():
    print '[info] Start export ' + types +' files'
    logging.info("Start export " + types +" files")

    if not __checklastupdated__(""):
        print '[info] No newest files'
        print '[info] Use -a to export all files'
        logging.info("No newest files")

        if not alls:
            quit()

    if __cmdexists__("rsvg-convert"):
        r = re.compile(".*scalable*")
        n = filter(r.match,directory_ar)
        # print n
        for s in n:
            # print s
            x = s.split("/")

            if(type_dir == "1"):
                cat_ = x[0]
            else:
                cat_ = x[1]
            # print cat_
            r_ = re.compile(".*" + cat_ + "*")
            n_ = filter(r_.match,directory_ar)
            f = ['.*scalable*','.*symbolic*']
            e = [re.compile(x) for x in f]
            fl = [s_ for s_ in n_ if any(re.match(s_) for re in e)]
            # print fl

            d = list(set(n_)-set(fl))
            # print d
            for xx in d:
                # print "export " + s + " => " + xx
                size = xx.split("/")
                if(type_dir == "1"):
                    size_ = size[1]
                elif(type_dir == "2"):
                    sizes = size[0].split("x")
                    size_ = sizes[0]
                else:
                    size_ = size[0]

                for files in os.listdir(current_dir + "/" + s):
                    file_ = files.replace('.svg', '')

                    if (types == 'svg'):
                        t = 'svg'
                    else:
                        t = 'png'

                    source = current_dir + "/" + s + "/" + file_ + ".svg"
                    destination = current_dir + "/" + xx + "/" + file_ + "." + t
                    width = size_
                    height = size_
                    # print "export : " + source + " => " + destination + "["+ width + "x" + height + "]"
                    if alls:
                        __export__(source, destination, width, height)
                    else:
                        if __checklastupdated__(source):
                            __export__(source, destination, width, height)

        __createlastupdated__()
        print '[info] Exporting ' + types + ' has been finished'
        logging.info("Exporting " + types + " has been finished")
    else:
        print '[error] please install librsvg2-bin for export to svg'
        logging.error('please install librsvg2-bin for export to svg')

def __readcsv__():
    global iconslist
    global directorylist
    global type_dir
    global directory_ar
    iconscsv = current_dir + "/data/Icon.csv"
    directorycsv = current_dir + "/data/Directory.csv"

    if os.path.exists(iconscsv):
        if os.path.exists(directorycsv):
            with open(iconscsv, 'rb') as csvicons:
                iconsreader = csv.reader(csvicons, delimiter=',', quotechar='"')
                iconslist = ""
                iconslist += "[Icon Theme]\n"
                for row in iconsreader:
                    if(row[0] == "type") or (row[0] == "Type"):
                        type_dir = row[1]
                    else:
                        iconslist += row[0] + "=" + row[1] + "\n"

            with open(directorycsv, 'rb') as csvdirectory:
                diretoryreader = csv.reader(csvdirectory, delimiter=',', quotechar='"')
                directorylist = ""
                for row in diretoryreader:
                    # print row
                    if('#size#' in row[0]):
                        name_split = row[0].split("/")
                        size_split = row[1].split(",")

                        for size_ in size_split:
                            if (type_dir == "1"):
                                directorylist += "\n\n[" + name_split[0] + "/" + size_ + "]"
                                directory_ar.append(name_split[0] + "/" + size_)
                            elif (type_dir == "3"):
                                directorylist += "\n\n[" + size_ + "/" + name_split[1] + "]"
                                directory_ar.append(size_ + "/" + name_split[1])

                            directorylist += "\nSize=" + size_
                            directorylist += "\nContext=" + row[2]
                            directorylist += "\nType=" + row[3]

                    elif ("scalable" in row[0]):
                        directory_ar.append(row[0])
                        directorylist += "\n\n[" + row[0] +"]"
                        directorylist += "\nSize=" + row[1]
                        directorylist += "\nContext=" + row[2]
                        directorylist += "\nType=" + row[3]
                        directorylist += "\nMinSize=" + row[4]
                        directorylist += "\nMaxSize=" + row[5]
                    else:
                        directory_ar.append(row[0])
                        directorylist += "\n\n[" + row[0] +"]"
                        directorylist += "\nSize=" + row[1]
                        directorylist += "\nContext=" + row[2]
                        directorylist += "\nType=" + row[3]

                d = "\nDirectories="
                for i in directory_ar:
                    i.replace(' ', '').replace('[', '').replace(']', '').replace('\'', '')
                    os.system("mkdir -p " + i)
                    if not directory_ar.index(i) == 0:
                        d += "," + i
                    else:
                        d += i

                iconslist += d

        else:
            print '[error] data/Directory.csv no such file directory'
    else:
        print '[error] data/Icon.csv no such file directory'

def __update__():
    # for update pabrikon
    os.system('cd /opt/pabrikon/ && sudo  git pull')

    print '[info] update pabrikon has been finished'
    logging.info('update pabrikon has been finished')


def __vaccum__():
    # this is for vaccum size  svg file with inkscape
    print '[__vaccum__]' #not finished

    # how to use
    # pabrikon --vaccum


def __version__():
    print 'Pabrikon ' + version + \
            '\n\nGeneral Information: http://github.com/winardiaris/' \
            'pabrikon' \
            '\nBug Reports: http://github.com/winardiaris/pabrikon/' \
            'issues?state=open'
    # how to use
    # pabrikon --version

def __main__(argv):
    global alls
    global comment
    global directory
    global directorylist
    global iconslist
    global name
    global op
    global source
    global types
    global verbose

    if not os.path.exists(log_dir + log_file):
        os.system("mkdir -p " + log_dir)
        os.system("touch " + log_dir + log_file)

    logging.basicConfig(
        filename=log_dir + log_file,
        level=logging.DEBUG,
        format=log_format)

    try:
        opts, args = getopt.getopt(argv, "abcd:ghilnoprst:uv", ["all", "build", "clean", \
                                    "directory=", "help", "list", "makepng", \
                                    "makesym", "makesvg", "new", "newproject", "opencsv", \
                                    "opensvg", "makecsv", "update", "verbose", "version", \
                                    "readcsv", "makeindex", "name=", "comment=", "source=", \
                                    "type=", "makeicon",])
    except getopt.GetoptError:
        __help__()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            op = 'help'
        elif opt in ('-a', '--all'):
            alls = True
        elif opt in ('-b', '--build'):
            op = 'build'
        elif opt in ('-c', '--clean'):
            op = 'cleanproject'
        elif opt == '--comment':
            comment = arg
        elif opt in ('-d', '--directory'):
            directory = arg
        elif opt in ("-l", "--list"):
            op = 'list'
        elif opt == '--makecsv':
            op = 'makecsv'
        elif opt in ('-p', '--makepng'):
            op = 'makepng'
        elif opt in ('-s', '--makesym'):
            op = 'makesym'
        elif opt in ('-g', '--makesvg'):
            op = 'makesvg'
        elif opt in ('-i', '--makeindex'):
            op = 'makeindex'
        elif opt == '--name':
            name = arg
        elif opt in ('-n', '--new'):
            op = 'newikon'
        elif opt == '--newproject':
            op = 'newproject'
        elif opt == "--opencsv":
            op = 'opencsv'
        elif opt in ("-o", "--open"):
            op = 'opensvg'
        elif opt in ("-r", "--readcsv"):
            op = 'readcsv'
        elif opt == '--source':
            source = arg
        elif opt in ('-t', '--type'):
            types = arg
        elif opt in ('-u', '--update'):
            op = 'update'
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt == '--version':
            op = 'version'
        elif opt == '--makeicon':
            op = 'makeicon'
        else:
            print False, "unhandle option"
    __readcsv__()
    __pabrikon__()

if __name__ == "__main__":
    __main__(sys.argv[1:])

