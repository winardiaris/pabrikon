#!/usr/bin/python

import csv
import getopt
import logging
import logging.handlers
import os
import subprocess
import sys

execfile('/opt/pabrikon/config/config.py')

comment = 'default comment'
directory = ''
name = 'default' 
op = ''
source = 'default'
types = 'default'
verbose = False

def pabrikon():
    if op == 'build':
        build()
    elif op == 'cleanproject':
        clean_project()
    elif op =='help':
        help_pabrikon()
    elif op == 'list':
        list_data()
    elif op == 'makecsv':
        make_csv_data()
    elif op == 'makepng':
        make_png()
    elif op == 'makesym':
        make_symlink()
    elif op == 'newikon':
        new_ikon()
    elif op == 'newproject':
        new_project()
    elif op == 'opencsv':
        open_csv()
    elif op == 'opensvg':
        open_svg()
    elif op == 'version':
        version_pabrikon()
    else:
        help_pabrikon()



def build():
    print '[info] Start building icons'
    logging.info("Starting building icons")
    clean_project()
    make_png()
    make_symlink()
    print '[info] Building icons has been finished'
    logging.info("Building icons has been finished")

    # how to use
    # pabrikon --build
    # pabrikon -b

def clean_project():
    print '[info] Start clean project'
    current_dir=os.getcwd()
    
    logging.info("Start Clean project")
    logging.debug("current directory: "+current_dir)

    for icon_ in list_dirs:
        if os.path.exists(current_dir + "/" + icon_ + "/scalable" ):
            if types == 'default' or types == 'symlink':
                os.system('find ' + current_dir + '/' + icon_ + '/scalable  -type l -exec rm -rf {} \;')
        for size_ in icon_sizes:
            if os.path.exists(current_dir + "/" + icon_ + "/" + size_ ):
                if types =='default':
                    os.system('find ' + current_dir + '/' + icon_ + '/' + size_ + ' -type f -name \'*.png\' -exec rm -rf {} \;')
                    os.system('find ' + current_dir + '/' + icon_ + '/' + size_ + ' -type l -exec rm -rf {} \;')
                elif types == 'symlink':
                    os.system('find ' + current_dir + '/' + icon_ + '/' + size_ + ' -type l -exec rm -rf {} \;')
                elif types == 'png':
                    os.system('find ' + current_dir + '/' + icon_ + '/' + size_ + ' -type f -name \'*.png\' -exec rm -rf {} \;')

    print '[info] Cleaning project has been  finished with type: ['+types+']'
    logging.info("Cleaning project has been finished with type ["+types+"]")

    # how to use
    # pabrikon --clean 
    # pabrikon --clean --type=png
    # pabrikon --clean --type=symlink

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def help_pabrikon():
    os.system('cat /opt/pabrikon/man/pabrikon.man')

    # how to use
    # pabrikon -h
    # pabrikon --help
def list_data():
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

def make_csv_data():
    if source == 'pabrikon':
        # copy csv file from pabrikon default to current project directory
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
        print '[info] Start make csv file from symlink in current project'
        logging.info("Start make csv file from symlink in current project")
        
        if verbose:
            os.system('/opt/pabrikon/bin/makecsv.sh v')
        else:
            os.system('/opt/pabrikon/bin/makecsv.sh')

        print '[info] Csv file creation has been finished'
        logging.info("Csv file creation has been finished")
    else:
        print '[error] put --source=pabrikon for make csv file from pabrikon default' 
        print '[error] put --source=default for make csv file from symlink file' 
        logging.error("make_csv_data source not in (pabrikon|default)")

    # how to use
    # pabrikon --makecsv     
    # pabrikon --makecsv --source=default
    # pabrikon --makecsv --source=pabrik

def make_png():
    print '[info] Start export png files'
    logging.info("Start export png files")
    current_dir=os.getcwd()
    
    for icon_ in list_dirs:
        if os.path.exists(current_dir + "/" + icon_ + "/scalable" ):
            print current_dir + "/" + icon_ + "/scalable"

            for size_ in icon_sizes:
                if not os.path.exists(current_dir + "/" + icon_ + "/" + size_):
                    subprocess.check_output(['mkdir', '-p',current_dir + "/" + icon_ + "/" + size_ ])
   
                for files in os.listdir(current_dir + "/" + icon_ + "/scalable"):
                    file_ =  files.replace('.svg','')

                    source = current_dir+"/"+icon_+"/scalable/"+file_+".svg"
                    destination = current_dir+"/"+icon_+"/"+size_+"/"+file_+".png"
                    width = size_
                    height = size_

                    # export svg to png
                    export_png(source,destination,width,height)

    print '[info] Exporting png has been finished'
    logging.info("Exporting png has been finished")
    # how to use
    # pabrikon --makepng

def export_png(source,destination,width,height):
    logging.info("Exporting "+source+" to "+destination)
    if verbose:
        os.system("inkscape "+source+" --export-png="+destination+" --export-height="+height+" --export-width="+width)
    else:
        os.system("inkscape "+source+" --export-png="+destination+" --export-height="+height+" --export-width="+width+" >> "+log_dir+log_file )

def make_symlink():
    print '[info] Start make symbolic link from data'
    logging.info("Start make symbolic link from data")
    current_dir=os.getcwd()
    icon_sizes.append('scalable')
    
    for icon_ in list_dirs:
        if verbose:
            print icon_ + "========================================================================"

        if os.path.exists(current_dir + "/" + icon_ ):
            for size_ in icon_sizes:
                if verbose:
                    print size_ + "========================================================================"
                if not os.path.exists(current_dir + "/" + icon_ + "/" + size_):
                    subprocess.check_output(['mkdir', '-p',current_dir + "/" + icon_ + "/" + size_ ])


                os.chdir(current_dir + "/" + icon_ + "/" + size_)
                if size_ == "scalable":
                    ext = '.svg'
                else:
                    ext = '.png'
                

                if os.path.exists(current_dir +'/data/'+ icon_ +'.csv'):
                    with open(current_dir +'/data/'+ icon_ +'.csv','rb') as f:
                        reader = csv.reader(f)
                        csv_list = list(reader)

                    for c in csv_list:
                        ln_from = c[0].replace('#size#',size_)
                        ln_to = c[1].replace('#size#',size_)
                        if os.path.exists(ln_from + ext):
                            if not os.path.exists(ln_to + ext):
                                os.system('ln -s ' + ln_from + ext + ' ' + ln_to + ext)
                                if verbose:
                                    print 'ln -s ' + ln_from + ext + ' ' + ln_to + ext
                        
                        

    print '[info] Making  symlink from data has been finished'
    logging.info("Making symlink from data has been finished")
    
    # how to use
    # pabrikon --makesym

def minizer_svg():
    # this is for reduce the size of svg file
    #not finished
    print 'minizer'
    # how to use
    # pabrikon --minizer

def new_ikon():
    # this is for copy default default.svg to spesific 
    print '[info]: make new icon ' + directory + '/scalable/' + name + '.svg'
    logging.info('make new icon ' + directory + '/scalable/' + name + '.svg')
    os.system("cp -rv /opt/pabrikon/data/default.svg ./"+directory+"/scalable/"+name+".svg")


    # how to use
    # pabrikon --new --name=nameoficon --directory=categories

def new_project():
    if not name == "default":
        if not os.path.exists(name):
            print '[info] Start make new project \nName=' + name + "\nComment=" + comment
            logging.info("start make new project Name="+name+", Comment="+comment)
            
            subprocess.check_output(['mkdir', '-p', name ])
            logging.debug("making new project with name="+name)

            os.system('cp -r /opt/pabrikon/data ' + name)
            os.system('mv ./' + name + '/data/index.theme ' + name + '/index.theme')
            os.system('sed -i "s/ICONNAME/' + name  + '/g" ' + name + '/index.theme') 
            os.system('sed -i "s/COMMENT/' + comment  + '/g" ' + name + '/index.theme') 
            
            for icon_ in list_dirs:
                subprocess.check_output(['mkdir', '-p', name + '/' + icon_ + '/scalable'])

            print '[info] make project with name `'+name+'` has been created '
            logging.info('make project with name `'+name+'` has been created ')
        else:
            print '[error] cannot create directory `' + name + '`: File exists'
            logging.error('cannot create directory `' + name + '`: File exists')
    elif not source == "default":
        if source.find(".git") != -1:
            if cmd_exists("git"):
                print '[info] Start make new project from source:' + source
                logging.info('Start make new project from source:' + source)
                os.system('git clone ' + source)
                print '[info] make new project from git repository'
                logging.info('make new project from git repository')
            else:
                print '[error] please install git for make new project from git reposity'
                logging.error('please install git for make new project from git reposity')

        else:
            print '[error] its not valid git url'
            logging.error('its not valid git url')
    else:
        help_pabrikon()

    # how to use
    # this make new project with empty icon with defauls csv data for make symlink
    # pabrikon --newproject --name=NAME --comment="This Comment for icon"
    # this make new project with source from git uri
    # pabrikon --newproject --source=GIT_URL
def open_csv():
    if name:
        if source == 'pabrikon':
            dirs = '/opt/pabrikon'
        else:
            dirs = '.'
            
        print '[info] Start open '+name+'.csv files in directory'+dirs
        logging.info('Start open '+name+'.csv files in directory'+dirs)

        if not name == "default":
            if os.path.exists(dirs + '/data/' + name + '.csv'):
                os.system(csv_editor +' '+ dirs + '/data/' + name + '.csv')
            else:
                print '[error] please put the name of csv in data directory'
                print '[info]: $ pabrikon --opencsv --name=apps'

                logging.error(dirs + '/data/' + name + '.csv : no such file directory')
    else:
        print '[error] please put the name of csv in data directory'
        print '[example]: $ pabrikon --opencsv --name=apps'
        os.system('ls '+dirs+'/data | grep csv | sed \'s/.csv//\' ')
        logging.error(dirs + '/data/' + name + '.csv : no such file directory')

    print '[info] Edit csv file has been finished'
    logging.info('Edit csv file has been finished')


    # how to use
    # pabrikon --opencsv --name=NAME.csv 
    # this open default csv file from pabrikon
    # pabrikon --opencsv --name=NAME.csv --source=pabrikon

def open_svg():
    if not name == "default":
        if directory:
            files = "./"+directory+"/scalable/"+name+".svg"
            if os.path.exists(files):
                os.system("inkscape "+files)
            else:
                print "[error] "+files+" no such file or directory"
                logging.info(files+" no such file or directory")

        else:
            os.system("find . -name '"+name+".svg' -exec inkscape {} \;")
    else:
        help_pabrikon()
    
    print '[info] Open svg file has been finished'
    logging.info('Open svg file has been finished')
    
    # how to use
    # pabrikon --open --name inkscape --directory apps

def vaccum_svg():
    # this is for vaccum size  svg file with inkscape
    print '[vaccum_svg]' #not finished

    # how to use
    # pabrikon --vaccum


def version_pabrikon():
    print 'pabrikon version:' + version

    # how to use
    # pabrikon -v
    # pabrikon --version



def main(argv):
    global comment
    global directory
    global name
    global op
    global source
    global types
    global verbose
   

    if not os.path.exists(log_dir+log_file):
        os.system("mkdir -p "+log_dir)
        os.system("touch "+log_dir+log_file)

    logging.basicConfig(
        filename=log_dir+log_file,
        level=logging.DEBUG,
        format=log_format)

    try:
        opts,args = getopt.getopt(argv,"bcd:hlnopst:v",["build","clean","directory=","help","list","makepng","makesym","new","newproject","opencsv","opensvg","makecsv","verbose","version","name=","comment=","source=","type="])
    except getopt.GetoptError:
        help_pabrikon()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-b','--build'):
            op = 'build'
        elif opt in ('-c','--clean'):
            op = 'cleanproject'
        elif opt in ('--comment'):
            comment = arg
        elif opt in ('-d','--directory'):
            directory = arg
        elif opt in ("-h","--help"):
            op = 'help'
        elif opt in ("-l","--list"):
            op = 'list'
        elif opt == '--makecsv':
            op = 'makecsv'
        elif opt in ('-p','--makepng'):
            op = 'makepng'
        elif opt in ('-s','--makesym'):
            op = 'makesym'
        elif opt in ('--name'):
            name = arg
        elif opt in ('-n','--new'):
            op = 'newikon'
        elif opt == '--newproject':
            op = 'newproject'
        elif opt == "--opencsv":
            op = 'opencsv'
        elif opt in ("-o","--open"):
            op = 'opensvg'
        elif opt in ('--source'):
            source = arg
        elif opt in ('-t','--type'):
            types = arg
        elif opt in ('-v','--verbose'):
            verbose = True
        elif opt in ('--version'):
            op = 'version'
        else:
            print False, "unhandle option"
 
    pabrikon()

if __name__ == "__main__":
    main(sys.argv[1:])

