# MIT License
#
# Copyright (c) 2023 Pascal Brand

import os
import datetime
import shutil
from .utilsHelper import create_dir_path

#
# Retrieve logs from OVH
# args contains
# ._login and .pass: credential to access the log system
# _firstYear: the first year to retrieve. Typically 2021
# _site: the site to consider, typically example.com
# _logHttp: the http of the log host, typically 'https://logs.cluster012.hosting.ovh.net/'
#

def getLogOvh(args):
  args._id = '-u' + args._login + ':' + args._pass
  now = datetime.datetime.now()

  for year in range(args._firstYear, now.year+1):
    y = str(year)
    dir = 'logs/' + y
    create_dir_path(dir)

    for month in range(1, 13):
      m = '{:02d}'.format(month)
      dir = 'logs/' + y + '/' + m
      create_dir_path(dir)

      for day in range(1, 32):
        d = '{:02d}'.format(day)

        # check this log has not been downloaded yet
        filename_dst = dir + '/' + y + m + d + '-' + args._site + '.log'
        if os.path.isfile(filename_dst):
          continue

        # check the log file is not a log in the future
        try:
          current = datetime.datetime(year, month, day, 23, 59, 59)
        except:
          # date does not exist, such as 2022/02/31
          continue

        if now < current:
          # No logs for today and beyong
          print('Stop at ' + filename_dst)
          return
        

        filesrc = args._site + '-' + d + '-' + m + '-' + y + '.log'
        address = args._logHttp + args._site + '/logs/logs-' + m + '-' + y + '/' + filesrc + '.gz'
        print('Get ' + filename_dst)
        cmd = 'curl -k -s -O ' + args._id + ' ' + address
        error = os.system(cmd)
        if error != 0:
          print('CANNOT DOWNLOAD ' + address)
          print(cmd)
          continue
        error = os.system('gzip -d ' + filesrc + '.gz')
        error = shutil.move(filesrc, filename_dst)

