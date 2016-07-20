#!/bin/bash
#========================
#Nama=Pabrik-ikon
#Versi=2
#========================


pwd=$('pwd')
dir_=""
dir=(actions animations apps categories devices emblems io mimetypes places status stock)
size=(16 22 24 32 48 64 96)

## fungsi membuat berkas png
function makePNG {
    for icon in ${dir[@]}
    do
      echo $pwd/$icon

     if [ -d $pwd/${icon}/scalable ]
     then
         echo "-----------------------------------------------------------------------------------------------------"
        cd $pwd/${icon}/scalable
         echo "-----------------------------------------------------------------------------------------------------"
        for sizx in ${size[@]}
        do
           SAVEIF=$IFS
           IFS=$(echo -en "\n\b")
         
           echo "-----------------------------------------------------------------------------------------------------"
           echo $pwd/$icon/$sizx
           mkdir -p ../${sizx}
           echo "-----------------------------------------------------------------------------------------------------"

            for file in $(ls *svg)
            do
                name=${file%%.svg}
                inkscape $name.svg --export-png=$name.png --export-height=${sizx} --export-width=${sizx}
                mv $name.png $pwd/${icon}/${sizx}/

            done
        done
      fi
    done
  echo "=============================================="
  echo "Selesai Membuat berkas *.png"
  echo "=============================================="
}

## fungsi membuat berkas symlink
function makeSYM {
  size+=('scalable')
    for icon in ${dir[@]}
    do
      if [ -d $pwd/$icon ]
      then
        for sizx in ${size[@]}
        do
     
        if [ -d $pwd/$icon/$sizx ]
        then
         echo "-----------------------------------------------------------------------------------------------------"
         echo $pwd/$icon/$sizx
         cd $pwd/$icon/$sizx 
         echo "-----------------------------------------------------------------------------------------------------"
         
         if [ $sizx == 'scalable' ]
         then
          ex=".svg"
        else
          ex=".png"
         fi

            for file in $(cat $pwd/data/${icon}.csv)
            do
              data=${file%%}
              IFS=',' read -a array <<< "$data" 
             
              aa=$(echo ${array[0]} | sed "s/\#size\#/${sizx}/")
              if [ -f $aa$ex ]
              then
                ln -sv $aa$ex ${array[1]}$ex
              fi

            done
          fi
       done
      fi
   done
  echo "=============================================="
  echo "Selesai Membuat berkas sysmlink"
  echo "=============================================="
}

function vacuumSVG {
echo "=============================================="
  echo "Sedang men-vacuum berkas SVG"
  for i in $(find . -type f -name "*.svg")
  do
    echo $i
    inkscape --vacuum-defs $i
  done
  echo "=============================================="
  echo "Selesai men-vacuum berkas SVG"
  echo "=============================================="
}

function minizer {
  echo "Sedang men-minizer berkas SVG"
  
}

function clean {
  #ini untuk membersihkan berkas hasil export & symlink
  for a in ${dir[@]}
  do
      for i in ${size[@]}
      do
        dir_=$pwd/$a/$i
        if [ -d $dir_ ]
        then
            echo "rm -rf $a/$i "
            find $a/$i -type l -exec rm -rf {} \;
            rm -rf $a/$i
        fi
      done
  done

  echo "=============================================="
  echo "Selesai Membersihkan Area Kerja"
  echo "=============================================="
}

function menu {
    echo "=============================================="
    echo "Nama=Pabrik-ikon"
    echo "Versi=2"
    echo "=============================================="
    echo "1 Buat berkas png"
    echo "2 Buat berkas symlink"
    echo "3 Buat berkas png + symlink"
    echo "4 Vacuum SVG"
    echo "5 Minizer SVG (Belum tersedia)"
    echo "C Bersihkan area kerja"
    echo "Q Keluar"
    echo "=============================================="
    echo -n "Pilih [1..5 C|Q] [ENTER]: "
    read opsi
}
menu

case $opsi in
     1)
       find . -type f -name "*.png" -exec rm -rf {} \;
       makePNG
       menu
       ;;
     2)
       find . -type l  -exec rm -rf {} \;
       makeSYM
       menu
       ;;
     3)
       find . -type f -name "*.png" -exec rm -rf {} \;
       find . -type l  -exec rm -rf {} \;
       makePNG
       makeSYM
       menu
       ;;
     4)
       find . -type l  -exec rm -rf {} \;
       vacuumSVG
       makeSYM
       menu
      ;;
     5)
      echo "fungsi belum tersedia"
       menu
       ;;
    C|c)
      clean
       menu
      ;;
    Q|q)
      exit
      ;;
 esac
