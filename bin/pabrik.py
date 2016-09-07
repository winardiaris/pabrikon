#!/usr/bin/python

import csv
import getopt
import os
import subprocess
import sys

execfile('/opt/pabrik-ikon/config/config.py')

comment = 'default comment'
directory = ''
name = 'default' 
op = ''
source = 'default'
types = 'default'

def pabrik_ikon():
    if op == 'build':
        build()
    elif op == 'cleanproject':
        clean_project()
    elif op =='help':
        help_pabrik()
    elif op == 'makecsv': #not finished
        make_csv_data()
    elif op == 'makepng':
        make_png()
    elif op == 'makesym':
        make_symlink()
    elif op == 'newproject':
        new_project()
    elif op == 'opencsv':
        open_csv()
    elif op == 'version':
        version_pabrik_ikon()
    else:
        help_pabrik()

def build():
    print '[info] Start building icons'
    clean_project()
    make_png()
    make_symlink()
    print '[success] Building icons has been finished'

    # how to use
    # pabrik --build
    # pabrik -b

def clean_project():
    print '[info] Start clean project'
    current_dir=os.getcwd()
    
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

    print '[success] Cleaning project has been  finished with type: ['+types+']'

    # how to use
    # pabrik --clean                    <= this clean the project from png and symlink file 
    # pabrik --clean --type=png         <= this clean the project from png file
    # pabrik --clean --type=symlink     <= this clean the project from symlink file

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def help_pabrik():
    os.system('cat /opt/pabrik-ikon/man/pabrik.man')

    # how to use
    # pabrik -h
    # pabrik --help

def make_csv_data():
    if source == 'pabrik':
        # copy csv file from pabrik-ikon default to current project directory
        print '[info] Start copying csv file to current project'
        os.system('cp -rv /opt/pabrik-ikon/data .')
        print '[success] Copying csv file has been finished'
    elif not source == 'default':
        # make csv file from symlink    <= #not finished
        print 'csv dari symlink'
        for icon_ in list_dirs:
            print icon_
    else:
        print '[error] put --source=pabrik for make csv file from pabrik-ikon default' 
        print '[error] put --source=default for make csv file from symlink file' 

    # how to use
    # pabrik --makecsv     
    # pabrik --makecsv --source=default
    # pabrik --makecsv --source=pabrik

def make_png():
    print '[info] Start export png files'
    current_dir=os.getcwd()
    
    for icon_ in list_dirs:
        if os.path.exists(current_dir + "/" + icon_ + "/scalable" ):
            print current_dir + "/" + icon_ + "/scalable"

            for size_ in icon_sizes:
                if os.path.exists(current_dir + "/" + icon_ + "/" + size_ ):
                    ##disini for berdasarkan file svg
                    for files in os.listdir(current_dir + "/" + icon_ + "/scalable"):
                        file_ =  files.replace('.svg','')
                        os.system("inkscape " + current_dir + "/" + icon_ + "/scalable/" + file_ + ".svg --export-png=" + file_ + ".png --export-height=" + size_ + " --export-width=" + size_ )
                        ## disini move exported file ke folder ukuran masing2
                        os.system("mv " + file_ + ".png " + current_dir + "/" + icon_ + "/" + size_ + "/")
    
    print '[info] Exporting png has been finished'

    # how to use
    # pabrik --makepng

def make_symlink():
    print '[info] Start make symbolic link from data'
    current_dir=os.getcwd()
    icon_sizes.append('scalable')
    
    for icon_ in list_dirs:
        print icon_ + "========================================================================"
        if os.path.exists(current_dir + "/" + icon_ ):
            for size_ in icon_sizes:
                print size_ + "========================================================================"
                os.chdir(current_dir + "/" + icon_ + "/" + size_)
                if size_ == "scalable":
                    ext = '.svg'
                else:
                    ext = '.png'

                with open(current_dir +'/data/'+ icon_ +'.csv','rb') as f:
                    reader = csv.reader(f)
                    csv_list = list(reader)

                for c in csv_list:
                    ln_from = c[0].replace('#size#',size_)
                    ln_to = c[1].replace('#size#',size_)
                    if os.path.exists(ln_from + ext):
                        print 'ln -s ' + ln_from + ext + ' ' + ln_to + ext
                        os.system('ln -s ' + ln_from + ext + ' ' + ln_to + ext)

    print '[success] Making  symlink from data has been finished'
    
    # how to use
    # pabrik --makesym

def minizer_svg():
    # this is for reduce the size of svg file
    #not finished

    # how to use
    # pabrik --minizer

def new_ikon():
    # this is for copy default default.svg to spesific 
    print '[new_ikon]: ' + directory + '/scalable/' + name + '.svg'

    # how to use
    # pabrik --newikon --name=nameoficon --directory=categories

def new_project():
    if not name == "default":
        if not os.path.exists(name):
            print '[info] Start make new project \nName=' + name + "\nComment=" + comment  # print new icon name and description 
            subprocess.check_output(['mkdir', '-p', name ])
            os.system('cp -r /opt/pabrik-ikon/data ' + name)
            os.system('mv ./' + name + '/data/index.theme ' + name + '/index.theme')
            os.system('sed -i "s/ICONNAME/' + name  + '/g" ' + name + '/index.theme') 
            os.system('sed -i "s/COMMENT/' + comment  + '/g" ' + name + '/index.theme') 
            
            for icon_ in list_dirs:
                subprocess.check_output(['mkdir', '-p', name + '/' + icon_])

            print '[success] make project with name `'+name+'` has been created '
        else:
            print '[error] cannot create directory `' + name + '`: File exists'
    elif not source == "default":
        if source.find(".git") != -1:
            if cmd_exists("git"):
                print '[info] Start make new project from source:' + source
                os.system('git clone ' + source)
                print '[success] make new project from git repository'
            else:
                print '[error] please install git for make new project from git reposity'

        else:
            print '[error] its not valid git url'
    else:
        help_pabrik()

    # how to use
    # pabrik --newproject --name=NAME --comment="This Comment for icon" <= this make new project with empty icon with defauls csv data for make symlink
    # pabrik --newproject --source=GIT_URI                              <= this make new project with source from git uri

def open_csv():
    if name:
        print '[info] Start open '+name+'.csv files'
        if source == 'pabrik':
            dirs = '/opt/pabrik-ikon'
        else:
            dirs = '.'

        print dirs 

        if not name == "default":
            if os.path.exists(dirs + '/data/' + name + '.csv'):
                os.system(csv_editor +' '+ dirs + '/data/' + name + '.csv')
            else:
                print '[error] please put the name of csv in data directory'
                print '[example]: $ pabrik --opencsv --name=apps'
    else:
        print '[error] please put the name of csv in data directory'
        print '[example]: $ pabrik --opencsv --name=apps'
        os.system('ls '+dirs+'/data | grep csv | sed \'s/.csv//\' ')

    print '[info] Edit csv file has been finished'

    # how to use
    # pabrik --opencsv --name=NAME.csv 
    # pabrik --opencsv --name=NAME.csv --source=pabrik      <= this open default csv file from pabrik-ikon

def vaccum_svg():
    # this is for vaccum size  svg file with inkscape
    print '[vaccum_svg]' #not finished

    # how to use
    # pabrik --vaccum


def version_pabrik_ikon():
    print 'pabrik-ikon version:' + version

    # how to use
    # pabrik -v
    # pabrik --version



def main(argv):
    global comment
    global name
    global op
    global source
    global types
    
    try:
        opts,args = getopt.getopt(argv,"bchpstvd:n",["build","clean","help","makepng","makesym","new","newproject","opencsv","makecsv","version","name=","comment=","source=","types="])
    except getopt.GetoptError:
        help_pabrik()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-b','--build'):
            op = 'build'
        elif opt in ('-c','--clean'):
            op = 'cleanproject'
        elif opt in ('--comment'):
            comment = arg
        elif opt in ("-h","--help"):
            op = 'help'
        elif opt == "--makecsv":
            op = 'makecsv'
        elif opt in ('-p','--makepng'):
            op = 'makepng'
        elif opt in ('-s','--makesym'):
            op = 'makesym'
        elif opt in ('--name'):
            name = arg
        elif opt in ("--newproject"):
            op = 'newproject'
        elif opt == "--opencsv":
            op = 'opencsv'
        elif opt in ('-s','--source'):
            source = arg
        elif opt in ('-t','--type'):
            types = arg
        elif opt in ("-v", "--version"):
            op = 'version'
        else:
            print False, "unhandle option"

    pabrik_ikon()

if __name__ == "__main__":
    main(sys.argv[1:])

