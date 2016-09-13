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

If this is the first time you create an icon for GNU / Linux, type the following command in the terminal:
```
$ cd path/to/your/icons/project
$ mkdir -p {actions,animations,apps,categories,devices,emblems,io,mimetypes,places,status,stock}/scalable

```
The files `* .svg` stored in the folder` scalable`

## Installation
```
$ cd /tmp
$ wget https://raw.githubusercontent.com/winardiaris/pabrik-ikon/dev-gui/install.sh && bash ./install.sh 
```


## How to use
```
$ cd path/to/your/icons/project
$ pabrik -h


```

