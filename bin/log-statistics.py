# MIT License
#
# Copyright (c) 2023 Pascal Brand

import sys, getopt, requests, time, math
import json
from urllib.request import urlopen

# TODO: use https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/stopforumspam_365d.ipset

known_backlinks = [
  '-',
  '188.165.53.185',   # is ovh
  # 'google.', 'facebook.com', 'ecosia.org', 'search.yahoo.com', 'bing.com', 'qwant.com', 'duckduckgo.com',
  # 'yellowlab.tools', 'webpagetest.org', 'dareboost.com'
]

_static_botname = [     # TODO: remove this list
  'ioncrawl',
  # 'bot', 'crawl',
  # 'qwant',              # TODO: qwantmobile is detected, whereas it should not
  # 'google-site-verification',
  # 'chrome-lighthouse',
  # 'exaleadcloudview',
  # 'binglocalsearch',
]

def usage():
  print('python bin/log-statistics.py [-h] [--credential-abuse-ipdb <credential>] [--ip <ip>] <file.log>')
  print(' --credential-abuse-ipdb <credential>: abuseipdb.com credential to filter spammer and crawler')
  print(' --ip-info <ip filename>: json db for ips info')
  print(' --ip <ip>: print every requests about this ip')
  print(' --backlinks: print backlinks')
  sys.exit(2)

def get_args(argv):
  get_args._ip = ''
  get_args._checkerrors = False
  get_args._backlinks = False
  get_args._credential_abuse_ipdb = ''
  get_args._ip_info = ''

  get_args._epoch = math.floor(time.time())

  try:
    opts, args = getopt.getopt(argv,"h", ["ip=", "credential-abuse-ipdb=", "ip-info=", "check-errors", "backlinks"])
  except:
    usage()

  for opt, arg in opts:
    if opt == '-h':
      usage()
    elif opt == '--ip':
      get_args._ip = arg
    elif opt == '--check-errors':
      get_args._checkerrors = True
    elif opt == '--backlinks':
      get_args._backlinks = True
    elif opt == '--credential-abuse-ipdb':
      get_args._credential_abuse_ipdb = arg
    elif opt == '--ip-info':
      get_args._ip_info = arg

  get_args._compute_abuseipdb = (get_args._credential_abuse_ipdb != '')
  get_args._compute_location = True

  if len(args) < 1:
    usage()
  get_args._log_name = args


def parse(line, end_str, start_pos):
  end_pos = line.find(end_str, start_pos)
  return line[start_pos:end_pos], end_pos+len(end_str)

# typical line is
#     78.153.241.205 www.example.com - [27/Dec/2021:05:55:01 +0100] "GET /index.html HTTP/1.1" 200 3092 "-" "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0"
def parse_line(line):
    data = {}
    end_pos = 0
    data['ip'], end_pos = parse(line, ' ', end_pos)             # 78.153.241.205
    data['site'], end_pos = parse(line, ' - [', end_pos)        # www.example/com
    data['date'], end_pos = parse(line, '] "', end_pos)         # 27/Dec/2021:05:55:01 +0100
    data['request'], end_pos = parse(line, '" ', end_pos)       # GET /index.html HTTP/1.1
    data['returned_code'], end_pos = parse(line, ' ', end_pos)  # 200
    code, end_pos = parse(line, ' "', end_pos)                  # 3092
    data['origin'], end_pos = parse(line, '" "', end_pos)       # -
    data['ua'], end_pos = parse(line, '"', end_pos)             # Mozilla/5.0 (Windows NT 10.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0
    return data

def get_file_data_list(filename):
  with open(filename, 'r') as file:
    lines = file.readlines()
    file.close()
    data_list = []
    for line in lines:
      data_list.append(parse_line(line))
  return data_list

def compute_location(ip):
  if (get_args._compute_location):
    try:
      url = 'http://ipinfo.io/' + ip + '/json'
      response = urlopen(url)
      return json.load(response)
    except:
      get_args._compute_location = False
  return None

ipinfo_db = {}

def set_ipinfo_db(data_list):
  for data in data_list:
    ip = data['ip']
    if (ipinfo_db.get(ip)):
      if (ipinfo_db[ip]['epoch'] + 365*24*60*60 < get_args._epoch):
        ipinfo_db[ip] = {}    # reset it as old information
    else:
        ipinfo_db[ip] = {}    # init as does not exist

    if ipinfo_db[ip] == {}:
      ipinfo_db[ip]['epoch'] = get_args._epoch
      ipinfo_db[ip]['ua'] = data['ua'].lower()

    ua = data['ua'].lower()
    if not ipinfo_db[ip].get('lua'):
      ipinfo_db[ip]['lua'] = []
    if not ua in ipinfo_db[ip]['lua']:
      ipinfo_db[ip]['lua'].append(ua)
    
    request = data['request']
    if ('GET /robots.txt ' in request):
      ipinfo_db[ip]['botfromaccess'] = True
    for pattern in ['/wp-', '/wso', '/.env']:
      if ('GET ' + pattern in request):
        ipinfo_db[ip]['spamfromaccess'] = True
        break

    if not(ipinfo_db[ip].get('stopforumspam')) and not is_abuse(data) and not is_crawler(data, False):
      stopforumspam = compute_stopforumspam(ip)
      if (stopforumspam):
        ipinfo_db[ip]['stopforumspam'] = stopforumspam
    
    if not(ipinfo_db[ip].get('abuseipdb')) and not is_abuse(data) and not is_crawler(data, False):
      abuseipdb = compute_abuseipdb(ip)
      if (abuseipdb):
        ipinfo_db[ip]['abuseipdb'] = abuseipdb

def get_ipinfo_db(data):
  # cf. https://docs.abuseipdb.com/?python#check-endpoint
  ip = data['ip']
  return ipinfo_db[ip]

def db_read(db_filename):
  try:
    with open(db_filename, encoding='utf-8') as file:
      try:
        json_database = json.load(file)
      except ValueError as err:
        print(err)
        print('Wrong json at ' + db_filename + ' - Exit')
        exit(1)
  except SystemExit:
    raise
  except:
    print("File " + db_filename + ' does not exist - start with empty json')
    json_database = {}
  return json_database

def db_write(db_filename, json_database):
  with open(db_filename, 'w', encoding='utf-8') as file:
    json.dump(json_database, file, indent=2, ensure_ascii=False)    # https://stackoverflow.com/questions/18337407/saving-utf-8-texts-with-json-dumps-as-utf-8-not-as-a-u-escape-sequence
    file.close()

def compute_abuseipdb(ip):
  if get_args._compute_abuseipdb:
    url = 'https://api.abuseipdb.com/api/v2/check'
    querystring = {
        'ipAddress': ip,
        'maxAgeInDays': '365'
    }
    headers = {
        'Accept': 'application/json',
        'Key': get_args._credential_abuse_ipdb
    }

    print(url + '?ipAddress=' + querystring['ipAddress'])
    try:
      response = requests.request(method='GET', url=url, headers=headers, params=querystring)
      decodedResponse = json.loads(response.text)
      if (decodedResponse.get('data')):
        return decodedResponse
    except:
      pass
  
  get_args._compute_abuseipdb = False
  return None

def compute_stopforumspam(ip):
  url = 'https://api.stopforumspam.org/api?ip=' + ip + '&json'
  print(url)

  try:
    response = requests.request(method='GET', url=url)
    decodedResponse = json.loads(response.text)
    if (decodedResponse.get('success')):
      return decodedResponse
  except:
    pass
  
  return None

def get_ip_location(ip):
  location = ipinfo_db[ip].get('location')
  if not location:
    location = compute_location(ip)
    if (location):
      ipinfo_db[ip]['location'] = location
  return location

def is_abuse(data):
  ip_info = get_ipinfo_db(data)
  if (ip_info.get('spamfromaccess')):    # this ip access /wp- or something else to hack me
    return True

  abuseipdb = ip_info.get('abuseipdb')
  result = abuseipdb and (abuseipdb['data']['abuseConfidenceScore'] > 0)

  if not result:
    stopforumspam = get_ipinfo_db(data).get('stopforumspam')
    if stopforumspam and (stopforumspam['success'] == 1) and (stopforumspam['ip']['appears'] > 0):
      confidence = stopforumspam['ip']['confidence']
      if type(confidence) == str:
        confidence = float(confidence)
      result = (confidence > 0)

  return result

request_outside_france = []
crawler_by_name = []
def is_crawler(data, use_name=True):
  ip = data['ip']
  ip_info = get_ipinfo_db(data)
  if (ip_info.get('botfromaccess')):    # this ip access /robots.txt
    return True
  
  abuseipdb = ip_info.get('abuseipdb')
  # Whitelisted netblocks are typically owned by trusted entities, such as Google or Microsoft who may use them for search engine spiders
  result = (abuseipdb is not None) and ((abuseipdb['data']['usageType'] == 'Search Engine Spider') or (abuseipdb['data']['isWhitelisted']))
  result_using_name = False
  if not result and use_name:
    for ua in ip_info['lua']:
      for bot in _static_botname:
        if bot in ua:
          result = True
          result_using_name = True
          break
      if result:
        break

  if result_using_name and (ip not in crawler_by_name):
    crawler_by_name.append(ip)

  return result

def filter_ipinfo_db(callback, data_list):
  new_data_list = []
  for data in data_list:
    if not(callback(data)):
      new_data_list.append(data)
  return new_data_list

def filter_not_abuse(data_list):   # remove all 'abuse' connexions
  return filter_ipinfo_db(is_abuse, data_list)

def filter_not_crawler(data_list):   # remove all 'abuse' connexions
  return filter_ipinfo_db(is_crawler, data_list)


def in_list(exact_search, str, list, case_sensitive=True):
  if exact_search:
    if str in list:
      return str
  else:
    for item in list:
      if case_sensitive:
        if str.find(item) != -1:
          return str
      else:
        if str.lower().find(item) != -1:
          return str.lower()
    return False



def code_expected(data):
  expected_code = [
    '200',    # no error
    '206',    # partial content, as requested
    '301',    # redirection: from example.com to www.example.com
    '302',    # temporary redirection: when opening mail_confirmation
    '304',    # resource not modified, so cache can be used
  ]
  return data['returned_code'] in expected_code

def get_number_errors(data_list):
  print('Request with errors:')
  nb = 0
  total = 0
  for data in data_list:
    if not(code_expected(data)):
      print('  ', data['request'])
      nb = nb + 1
    total = total + 1
  return nb, total

def filter_errors(data_list):
  new_data_list = []
  for data in data_list:
    if not(code_expected(data)):
      print('ERROR RETURNED: ' + str(data))
      print_ip(data, data_list)
    else:
      new_data_list.append(data)
  return new_data_list

def check_return_an_error(data_list, exact_search, field, exclude_list):
  new_data_list = []
  ok = True
  for data in data_list:
    if in_list(exact_search, data[field], exclude_list):
      if not(data['returned_code'] in [ '301', '403', '404', '410', '503' ]):
        print('EXPECTING AN ERROR ON: ' + str(data))
        ok = False
    else:
      new_data_list.append(data)
  # if not(ok):
  #   sys.exit(3)
  return new_data_list

def keep_only(data_list, exact_search, field, exclude_list):
  new_data_list = []
  for data in data_list:
    if in_list(exact_search, data[field], exclude_list):
      new_data_list.append(data)
  return new_data_list

def keep_unique(data_list, exact_search, field, exclude_list):
  unique_list = []
  for data in data_list:
    if (data[field] not in unique_list) and (in_list(exact_search, data[field], exclude_list)):
      unique_list.append(data[field])
  return unique_list


def remove_in_list(data_list, exact_search, field, exclude_list):
  new_data_list = []
  for data in data_list:
    if not(in_list(exact_search, data[field], exclude_list)):
      new_data_list.append(data)
  return new_data_list


def print_contain(text, data_list, exact_search, field, case_sensitive, contain_list):
  ok = True
  ip_list = []
  for data in data_list:
    if data['ip'] in ip_list:
      continue
    if in_list(exact_search, data[field], contain_list, case_sensitive):
      print(text + str(data))
      ip_list.append(data['ip'])
      print_ip(data, data_list)
      ok = False
  # if not(ok):
  #   sys.exit(3)

def print_doesnot_contain(text, data_list, exact_search, field, doesnot_contain_list):
  ok = True
  ip_list = []
  for data in data_list:
    if data['ip'] in ip_list:
      continue
    if not(in_list(exact_search, data[field], doesnot_contain_list)):
      print(text + str(data))
      ip_list.append(data['ip'])
      ok = False
  # if not(ok):
  #   sys.exit(3)


def print_data_list(data_list):
  for data in data_list:
    print(data)


def print_all_from_ip(ip, data_list):
  for data in data_list:
    if data['ip'] == ip:
      print('    ' + data['ip'] + ' ' + data['request'] + ' ' + data['date'])


def print_ip_location(ip):
  try:
    location = get_ip_location(ip)
    print(ip + ': ' + location['city'] + ', ' + location['region'] + ', ' + location['country'])
    if (location['country'] != 'FR') and (ip not in request_outside_france):
      request_outside_france.append(ip)
  except:
    print(ip + ': Cannot print locations')


def print_ip(data, data_list):
    location = get_location(data['ip'])
    try:
      print(data['ip'] + ': ' + location['city'] + ', ' + location['region'] + ', ' + location['country'] + ', ua=' + data['ua'])
      # print(location)
      if location['country'] == 'FR':
        print_all_from_ip(data['ip'], data_list)
    except:
      print(data['ip'] + ': Cannot print location')


def main(argv):
  for filename in get_args._log_name:
    print('================= Get IP info of ' + filename)
    data_list = get_file_data_list(filename)
    set_ipinfo_db(data_list)
    db_write(get_args._ip_info, ipinfo_db)

  for filename in get_args._log_name:
    print('================= ANALYZE ' + filename)
    data_list = get_file_data_list(filename)
    data_list = filter_not_abuse(data_list)   # remove all 'abuse' connexions
    data_list = filter_not_crawler(data_list)   # remove all 'crawler' connexions

    nb_errors, total = get_number_errors(data_list)
    print('Number of errors:     ' + str(nb_errors))
    print('Number of requests:   ' + str(total))
    print('Percentage of errors: ' + str(round((100 * nb_errors) / total, 2)) + '%')
      
    if get_args._ip != '':
      data_list = keep_only(data_list, False, 'ip', [ get_args._ip ])
      print_data_list(data_list)
      continue

    if get_args._backlinks:
      print('Checking for backlinks')
      known_backlinks.append(data_list[0]['site'][4:])      # from www.example.com, extract example.com only
                                                            # this is to ignore when the page has been accessed using internal link
      print_doesnot_contain('BACKLINKS: ', data_list, False, 'origin', known_backlinks)    # print backlinks
      continue

    # Check following request return an error. if not, something's wrong
    # these ones are filtered
    data_list = check_return_an_error(data_list, False, 'request', [
      '.htaccess',
      ' /.well-known',
      ' /humans.txt ', '/ads.txt',
      ' /google947fbbdb126554fc.html ',   # googlesiteverification access the correct file, and also this incorrect one
    ])

    # check known attacks
    data_list = check_return_an_error(data_list, False, 'request', [
      ' /wp',
      ' /href ',
      '.html/js', ' /filemanager/', ' /kI6',
      ' /util/', ' /magento', ' /install.php',
      ' /.vscode/', ' /.env ', ' /cgi-bin', ' /assets', ' /cache', ' /bc ', ' /mt/',
      ' /mail-erreur.html',
      ' /style.php', ' /moduless.php', ' /Install', 'GET /404 ', 'GET //',
    ])

    # remove redirection
    data_list = remove_in_list(data_list, False, 'returned_code', [ '301' ])

    # remove old links that do not exist anymore
    data_list = remove_in_list(data_list, False, 'request', [
      ' /img/200', ' /img/201', ' /img/2021', ' /img/21',
      ' /img/slidehalf-24.jpg ', ' /img/slidehalf-26', ' /img/slidehalf-2021', ' /img/slidehalf-20220',
      ' /img/pictures',
      ' /galerie-photos-construction.html ',
      ' /_test_/', 
      ])

    if get_args._checkerrors:
      data_list = filter_errors(data_list)
      continue

    data_list = keep_only(data_list, False, 'request', [ '.html', 'GET / ', 'GET /?' ])
    unique_requests = keep_unique(data_list, False, 'request', [ '.html', 'GET / ', 'GET /?' ])
    for unique_request in unique_requests: 
      all = keep_only(data_list, True, 'request', [ unique_request ])
      print('========= ' + unique_request + ': ' + str(len(all)))

      for c in all:
        print_ip_location(c['ip'])



  print('=========================== crawler_by_name')
  print(crawler_by_name)
  print('=========================== request_outside_france')
  print(request_outside_france)
  

if __name__ == "__main__":
  get_args(sys.argv[1:])
  ipinfo_db = db_read(get_args._ip_info)
  main(sys.argv[1:])
  db_write(get_args._ip_info, ipinfo_db)

  #get_location('50.59.99.143')
