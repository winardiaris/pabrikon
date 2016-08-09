#!/usr/bin/python

import os
import sys
# untuk option contoh (-a -b -c)
import getopt

version = '0.2-dev-gui'

def newIkon(newfile,directory):
    print '[newIkon]: ' + directory + '/scalable/' + newfile + '.svg'

def makePNG():
    print '[makePNG]'

def makeSYM():
    print '[makeSYM]'

def vaccumSVG():
    print '[vaccumSVG]'

def cleanProject():
    print '[clean]'

def helpPabrik():
    print 'pabrik.py -i <inputfile> -o <outputfile>'
    
def versionPabrik():
    print 'Pabrik-Ikon version:' + version

def main(argv):
    inputfile = ''
    outputfile = ''
    newfile = ''
    directory = ''
    try:
        opts,args = getopt.getopt(argv,"bchpsvd:n:",["build","clean","dir","help","makePNG","makeSYM","new","if","of","version","if=","of=","new=","dir="])
    except getopt.GetoptError:
        helpPabrik()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h","--help"):
            helpPabrik()
            sys.exit()
        elif opt in ("-b","--build"):
            makePNG()
            makeSYM()
            sys.exit()
        elif opt in ("-c","--clean"):
            cleanProject()
            sys.exit()
        elif opt in ("-p","--makePNG"):
            makePNG()
            sys.exit()
        elif opt in ("-s","--makeSYM"):
            makePNG()
            sys.exit()
        elif opt in ("-n", "--new"):
            newfiledir = arg.split(" ")
            

            newIkon(newfiledir[0],newfiledir[1])
            sys.exit()
        elif opt in ("-i", "--if"):
            inputfile = arg
        elif opt in ("-o", "--of"):
            outputfile = arg
        elif opt in ("-v", "--version"):
            versionPabrik()
        else:
            assert False, "unhandle option"
    
    # print 'Input file is :', inputfile
    # print 'Outnput file is :', outputfile

if __name__ == "__main__":
    main(sys.argv[1:])

