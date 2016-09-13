#!/bin/bash
pwd=$(pwd)
export command="$1"

function find_svg {
  if [ -f data/list.csv ]; then
    cat data/list.csv | grep svg | grep -v symlink | sort | sed -e "s/,,/,NULL,/g" | column -s, -t
  fi
}

function find_png {
  if [ -f data/list.csv ]; then
    cat data/list.csv | grep png | grep -v symlink | sort | sed -e "s/,,/,NULL,/g" | column -s, -t
  fi
}

function find_symlink {
  if [ -f data/list.csv ]; then
    cat data/list.csv | grep symlink | sort | sed -e "s/,,/,NULL,/g" | column -s, -t
  fi
}

function list_all {
  if [ -f data/list.csv ]; then
    cat data/list.csv | sort | sed -e "s/,,/,NULL,/g" | column -s, -t
  fi
}

function make_data {
  if [ ! -f data/list.csv ]; then
    mkdir -p data
    touch data/list.csv
    echo "DIRECTORY,FILENAME,TYPE,SOURCE,FILESIZE" >> data/list.csv
  fi

  for file in $(find . -name "*.png" -or -name "*.svg")
  do
      FILESIZE="`du -b $file | awk '{print $1}'`"
      set -- "$file" 
      IFS="/";declare -a Array1=($*)
      FILENAME=${Array1[-1]}
      DIRECTORY=${Array1[-3]}"/"${Array1[-2]}
      unset IFS 

    if [ -f $file ]; then
      if [[ $file == *".svg" ]];then
        TYPE="svg"
      fi
      
      if [[ $file == *".png" ]];then
        TYPE="png"
      fi
        
      SOURCE=""
    fi

    if [ -L $file ]; then
      TYPE="symlink"
      SOURCE="`readlink f $file`"
    fi
    echo "$DIRECTORY,$FILENAME,$TYPE,$SOURCE,$FILESIZE" >> data/list.csv
  done
}

function compare_latest {
  LATESTFILE="`find . -type f -name "*.png" -or -name "*.svg" -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" "`"
  file_latest_modified="`stat -c %Y $LATESTFILE`"
  data_list_modified="`stat -c %Y ./data/list.csv`"

  # echo "file: $file_latest_modified"
  # echo "data: $data_list_modified"
  if [ "$file_latest_modified" -gt "$data_list_modified" ]; then
    if [ -f data/list.csv ]; then
      rm -rf data/list.csv
    fi
    make_data
  fi
}

case $command in
  all)
    compare_latest
    list_all
    ;;
  make)
    rm -rf data/list.csv
    make_data
    ;;
  png)
    compare_latest
    find_png
    ;;
  svg)
    compare_latest
    find_svg
    ;;
  symlink)
    compare_latest
    find_symlink
    ;;
  *)
    echo $"Usage: $0 {svg|png|symlink|make}"
    exit 1
esac
