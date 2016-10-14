# Pabrikon

Pabrikon can run on all GNU/Linux distributions and designed to help GNU/Linux distro developers, especially for the artwork team to create and manage their own icons.

The idea of Pabrik-Ikon was initiated by @herpiko, from artwork team in BlankOn Project. Pabrik-Ikon is currently only a BASH script, but it is very helpful to manage icons.

## Requirements

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
- data/					<= `This contains CSV files of symlinks data`

The `* .svg` files will be stored in the `scalable` folder.

## Installation

```
$ curl https://raw.githubusercontent.com/winardiaris/pabrikon/master/install.sh | bash
```

## Help

```
PABRIKON(1)    USERMANUAL    PABRIKON(1)

NAME
    pabrikon

DESCRIPTION
    Pabrikon can run on all GNU/Linux distributions and designed
    to help GNU/Linux distro developers, especially for the artwork team
    to create and manage their own icons.

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
    make csv file for icon project from symlink or pabrikon default

  -p,--makepng
    build icons in png file

  -s,--makesym
    build symbolic link file from csv file in data directory

  --minizer
    reduce the size of svg file

  --name
    naming a new project or name a new icon

  --new
    copy default icon svg file to new icon

  --newproject
    make a new project icon could be blank projects or from git url

  --opencsv
    open csv file on the project or pabrikon default

  --source
    source of --makecsv , --newproject , --opencsv

  -t, --types
    for --clean {default|png|symlink}
    for --list {all|png|svg|symlink}

  --vaccum
    vaccum size svg file with feature from Inkscape

  -v, --verbose
    increase verbosity

  --version
    show pabrikon version


EXAMPLES
  pabrikon --build
    build icon from svg to png

  pabrikon --clean
    clean the project from png and symlink file

  pabrikon --clean --type=png
    clean the project from png file

  pabrikon --clean --type=symlink
    clean the project from symlink file

  pabrikon -h
    show this help usage

  pabrikon -l -t {all|png|svg|symlink}
    show list file in current project

  pabrikon --makecsv
  pabrikon --makecsv --source=default
    make csv file from symlink in current project

  pabrikon -s
  pabrikon --makesym
    build symbolic link file from csv file in data directory


  pabrikon --makecsv --source=pabrikon
    copy csv file from pabrikon default to current project

  pabrikon -p
  pabrikon --makepng
    build icons in png file

  pabrikon -n --name=NAME.svg --directory=places
  pabrikon --new --name=NAME.svg --directory=places
    copy default icon svg file to <directory>/scalable/<name>

  pabrikon --newproject --name=NAME --comment="comment or description for this icon "
    make new blank project with <name> of icon

  pabrikon --newproject --source=git-url-of-icon-project.git
    make new project with source from git url

  pabrikon --opencsv --name=apps
    open csv file with name apps.csv in current icon project

  pabrikon --opencsv --name=places --source=pabrikon
    open csv file with name places.csv in pabrikon default data


```

# TODO

In the future Pabrik-Ikon will be extended to a GUI-based application with more features: a friendly interface to create a new project, import/export projects, one-on-one/many for export png, use Inkscape for editing, managing symlink, and so on.
