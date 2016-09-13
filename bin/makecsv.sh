#!/bin/bash
pwd=$(pwd)

for target in $(find . -type l | grep scalable)
  do
    source=`readlink -f $target`
    source=${source/$pwd/.}

    set -- "$target" 
    IFS="/";declare -a Array1=($*)
    dir_target=${Array1[1]}

    set -- "$source"
    IFS="/";declare -a Array2=($*)
    dir_source=${Array2[1]}
   
    unset IFS 

    if [ ! -f data/$dir_target.csv  ]
    then
      mkdir -p data
      touch data/$dir_source.csv
    fi

    if [ "$dir_source" != "$dir_target" ]
    then
      source_replace=${source/.\//}
      source_replace=${source_replace/$dir_source/..\/..\/$dir_source}
      source_replace=${source_replace/scalable/#size#}
      source_replace=${source_replace/.svg/}
     
      target_replace=${target/$dir_target\//} 
      target_replace=${target_replace/scalable\//} 
      target_replace=${target_replace/.svg/}
       
      echo $source_replace','$target_replace >> data/$dir_target.csv
      echo $source_replace','$target_replace
    else
      source_replace=${source/$dir_source\//}
      source_replace=${source_replace/scalable\//}
      source_replace=${source_replace/.svg/}


      target_replace=${target/$dir_target\//}
      target_replace=${target_replace/scalable\//}
      target_replace=${target_replace/.svg/}
      
      echo $source_replace','$target_replace >> data/$dir_target.csv
      echo $source_replace','$target_replace
    fi
     
  done

