# Pabrik-ikon
Pabrik-Ikon can run on all distributions of GNU / Linux, Pabrik-Ikon is designed to help developers distributions of GNU / Linux, especially on the art team to create and manage an icon created for the typical GNU / Linux distribution developed.

The idea to create a Pabrik-Ikon leveled by Herpiko Dwi Aguno artwork team in BlankOn Project. Pabrik-Ikon is currently only a BASH script, but it is very helpful to manage icons.

In the future Pabrik-Ikon will be made a GUI-based application with features: a friendly interface, create a new project, import / export projects, one-on-one / many for export png, use Inkscape for editing, managing symlink

## Requirement
- [inkscape](https://inkscape.org/en/)
- [svgcleaner](https://sourceforge.net/projects/svgcleaner/)

## Directory structure
In the folder in your working folder requires at least one of the following list:

- actions/scalable/
- animations/scalable/
- apps/scalable/
- categories/scalable/
- devices/scalable/
- emblems/scalable/
- io/scalable/
- mimetypes/scalable/
- places/scalable/
- status/scalable/
- stock/scalable/  
- data/					<= `this use for place a csv files data for make symlink`

The files `* .svg` stored in the folder` scalable`

## Installation
```
$ curl https://raw.githubusercontent.com/winardiaris/pabrik-ikon/master/install.sh | bash 
```

## Help
```
PABRIK-IKON(1)    USERMANUAL    PABRIK-IKON(1)

NAME
    pabrik-ikon 

DESCRIPTION
    Pabrik-Ikon can run on all distributions of GNU / Linux,
    Pabrik-Ikon is designed to help developers distributions of GNU / Linux,
    especially on the art team to create and manage an icon created for
    the typical GNU / Linux distribution developed.

OPTION
  -b, --build
    build icon from svg to png

  -c, --clean 
    clean project dir from png files

  --comment
    this for comment a new icon project

  -d, --directory
    select the type of directory icon project [ex:apps, categories, places, etc..]    

  -h, --help
    output usage information

  -l, --list
    list file in current project

  --makecsv
    make csv file for icon project from symlink or pabrik-ikon default

  -p,--makepng
    build icons in png file

  -s,--makesym
    build symbolic link file from csv file in data directory

  --minizer
    this is for reduce the size of svg file

  --name
    this is for naming a new project or name a new icon

  --new
    this is for copy default icon svg file to new icon

  --newproject
    this is for make a new project icon could be blank projects or from git url
  
  --opencsv
    this for open csv file on the project or pabrik-ikon default

  --source
    this use for source of --makecsv , --newproject , --opencsv

  -t, --types 
    for --clean {default|png|symlink} 
    for --list {all|png|svg|symlink}
    
  --vaccum
    this is for vaccum size svg file with feature from inkscape

  -v, --verbose
    increase verbosity

  --version
    show pabrik-ikon version


EXAMPLES
  pabrik --build
    build icon from svg to png
  
  pabrik --clean
    this clean the project from png and symlink file 

  pabrik --clean --type=png
    this clean the project from png file
  
  pabrik --clean --type=symlink
    this clean the project from symlink file

  pabrik -h
    show this help usage

  pabrik -l -t {all|png|svg|symlink}
    show list file in current project
  
  pabrik --makecsv     
  pabrik --makecsv --source=default
    make csv file from symlink in current project
  
  pabrik -s
  pabrik --makesym
    build symbolic link file from csv file in data directory
    
  
  pabrik --makecsv --source=pabrik
    copy csv file from pabrik-ikon default to current project

  pabrik -p
  pabrik --makepng
    build icons in png file
   
  pabrik -n --name=NAME.svg --directory=places
  pabrik --new --name=NAME.svg --directory=places
    this is for copy default icon svg file to <directory>/scalable/<name>

  pabrik --newproject --name=NAME --comment="comment or description for this icon "
    this is make new blank project with <name> of icon

  pabrik --newproject --source=git-url-of-icon-project.git
    this make new project with source from git url

  pabrik --opencsv --name=apps 
    this open csv file with name apps.csv in current icon project 

  pabrik --opencsv --name=places --source=pabrik
    this open csv file with name places.csv in pabrik-ikon default data


```

