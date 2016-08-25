#!/usr/bin/python

import os, sys, getopt, subprocess

execfile('/opt/pabrik-ikon/config/config.py')


def newIkon(newfile,directory):
    print '[newIkon]: ' + directory + '/scalable/' + newfile + '.svg'

def newProject(iconname,comment):
    if not os.path.exists(iconname):
        print '[newProject]:\nName=' + iconname + "\nComment=" + comment
        subprocess.check_output(['mkdir', '-p', iconname ])
        os.system('cp -r /opt/pabrik-ikon/data ' + iconname)
        os.system('mv ./' + iconname + '/data/index.theme ' + iconname + '/index.theme')
        os.system('sed -i "s/ICONNAME/' + iconname  + '/g" ' + iconname + '/index.theme') 
        os.system('sed -i "s/COMMENT/' + comment  + '/g" ' + iconname + '/index.theme') 
        
        print '[success] project `'+iconname+'` has been created '

        for dir_ in list_dirs:
            subprocess.check_output(['mkdir', '-p', iconname + '/' + dir_])
    else:
        print '[error] cannot create directory `' + iconname + '`: File exists'


def makePNG():
    print '[makePNG]'

def makeSYM():
    print '[makeSYM]'

def vaccumSVG():
    print '[vaccumSVG]'

def cleanProject():
    print '[clean]'

def helpPabrikIkon():
    os.system('cat /opt/pabrik-ikon/man/pabrik.man')
    
def versionPabrikIkon():
    print 'pabrik-ikon version:' + version

def openCSV(filename):
    os.system(csv_editor + ' ' + filename)

def main(argv):
    inputfile = ''
    outputfile = ''
    newfile = ''
    directory = ''
    try:
        opts,args = getopt.getopt(argv,"bchpsvd:n:",["build","clean","dir","help","makePNG","makeSYM","new","newproject","opencsv","if","of","version","if=","of=","new=","dir="])
    except getopt.GetoptError:
        helpPabrikIkon()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h","--help"):
            helpPabrikIkon()
            sys.exit()
        elif opt in ("-b","--build"):
            makePNG()
            makeSYM()
            sys.exit()
        elif opt in ("-c","--clean"):
            cleanProject()
            sys.exit()
        elif opt in ("--opencsv"):
            openCSV(argv[1])
            sys.exit()
        elif opt in ("-p","--makePNG"):
            makePNG()
            sys.exit()
        elif opt in ("-s","--makeSYM"):
            makePNG()
            sys.exit()
        elif opt in ("-n", "--new"):
            newIkon(argv[1],argv[2])

            sys.exit()
        elif opt in ("--newproject"):
            newProject(argv[1],argv[2])
            sys.exit()
        elif opt in ("-i", "--if"):
            inputfile = arg
        elif opt in ("-o", "--of"):
            outputfile = arg
        elif opt in ("-v", "--version"):
            versionPabrikIkon()
        else:
            assert False, "unhandle option"
    
    # print 'Input file is :', inputfile
    # print 'Outnput file is :', outputfile

if __name__ == "__main__":
    main(sys.argv[1:])

