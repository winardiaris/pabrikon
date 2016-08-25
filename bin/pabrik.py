#!/usr/bin/python

import os, sys, getopt, subprocess

execfile('/opt/pabrik-ikon/config/config.py')


def newIkon(newfile,directory):
    print '[newIkon]: ' + directory + '/scalable/' + newfile + '.svg'

def newProject(iconname,comment):
    if not os.path.exists(iconname):
        print '[newProject]:\nName=' + iconname + "\nComment=" + comment  # print new icon name and description 
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
    current_dir=os.getcwd()
    # icon_sizes.append('scalable')
    
    for icon_ in list_dirs:
        if os.path.exists(current_dir + "/" + icon_ + "/scalable" ):
            print current_dir + "/" + icon_ + "/scalable"

            for size_ in icon_sizes:
                if os.path.exists(current_dir + "/" + icon_ + "/" + size_ ):
                    ##disini for berdasarkan file svg
                    for files in os.listdir(current_dir + "/" + icon_ + "/scalable"
                            ):
                        file_ =  files.replace('.svg','')
                        # print "inkscape " + current_dir + "/" + icon_ + "/scalable/" + file_ + ".svg --export-png=" + file_ + ".png --export-height=" + size_ + " --export-width=" + size_ 
                        os.system("inkscape " + current_dir + "/" + icon_ + "/scalable/" + file_ + ".svg --export-png=" + file_ + ".png --export-height=" + size_ + " --export-width=" + size_ )
                        ## disini move exported file ke folder ukuran masing2
                        os.system("mv " + file_ + ".png " + current_dir + "/" + icon_ + "/" + size_ + "/")

def makeSYM():
    print '[makeSYM]'
    current_dir=os.getcwd()
    icon_sizes.append('scalable')
    
    for icon_ in list_dirs:
        if os.path.exists(current_dir + "/" + icon_ ):
            for size_ in icon_sizes:
                print current_dir + "/" + icon_ + "/" + size_

def vaccumSVG():
    print '[vaccumSVG]'

def cleanProject():
    print '[clean]'
    current_dir=os.getcwd()
    
    for icon_ in list_dirs:
        if os.path.exists(current_dir + "/" + icon_ + "/scalable" ):
            os.system('find ' + current_dir + '/' + icon_ + '/scalable  -type l -exec rm -rf {} \;')
    
        for size_ in icon_sizes:
            if os.path.exists(current_dir + "/" + icon_ + "/" + size_ ):
                os.system('find ' + current_dir + '/' + icon_ + '/' + size_ + ' -type f -name \'*.png\' -exec rm -rf {} \;')

    print '[clean] Finished'


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
    # current_dir = os.getcwd()
    try:
        opts,args = getopt.getopt(argv,"bchpsvd:n:",["build","clean","dir","help","makePNG","makeSYM","new","newproject","opencsv","version","new=","dir="])
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
            makeSYM()
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

