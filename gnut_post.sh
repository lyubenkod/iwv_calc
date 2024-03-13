#!/bin/bash

#Define root script folder
SCRIPT_DIR=/work/mg/pl/wrf/scripts/bulgaria/23_GNUT_PPP

#Define checkfile
CHECK_FILE=".running"

#Load modules since script is executed from non-interactive session (crontab)
. /opt/Modules/modules.sh 

#Change to work folder
cd ${SCRIPT_DIR}


#Check if .running file is present and there is existing job
if [ -f ${CHECK_FILE} ]; then
  if [ $(qstat | grep -e '^ [0-9]' | awk '{print $1}' | grep $(cat ${CHECK_FILE})) ]; then
    echo 'The task is already running...'
    exit 0
  else
    rm -f ${CHECK_FILE}
  fi
fi

#Run the simulation with job name fcs_op
qsub -N gnut_post gnut_post.job


#Run postprocess job
#qsub -hold_jid op_fcs -N pp  pprocess_new.job 

