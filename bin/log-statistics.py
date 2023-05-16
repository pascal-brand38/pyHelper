# MIT License
#
# Copyright (c) 2023 Pascal Brand

import sys, getopt, requests
import json
from urllib.request import urlopen

known_backlinks = [
  '-',
  '188.165.53.185',   # is ovh
  # 'google.', 'facebook.com', 'ecosia.org', 'search.yahoo.com', 'bing.com', 'qwant.com', 'duckduckgo.com',
  # 'yellowlab.tools', 'webpagetest.org', 'dareboost.com'
]

botname = [
  'Googlebot', 'Google-Site-Verification', 'Chrome-Lighthouse',
  'ExaleadCloudView',   # from Dassault
  'Qwantify/',
  'FacebookBot',
  'PetalBot',
  'bingbot', 'BingLocalSearch',
  'Applebot',
  'SemrushBot',
  'AhrefsBot',
  'Yandex',
  'IonCrawl',
  'DuckDuckBot',  'DuckDuckGo-Favicons-Bot',
  'Twitterbot',

  # bad bot?
  'Seekport Crawler',
  'webprosbot',
  'Mediatoolkitbot',
  'CCBot',
  'MJ12bot',
  'zoominfobot',
  't3versionsBot',
  'archive.org_bot',
  'DataForSeoBot',
  'Internet-structure-research-project-bot',
  'Barkrowler',
  'pingbot',
  'DotBot',
  'GIDBot',
  'Adsbot',
  'linkfluence',
  'MojeekBot',
  'BLEXBot',
  'SafeDNSBot',
  'rc-crawler',
  'SiteCheckerBotCrawler',
  'MegaIndex.ru',
  'LinkedInBot',
  'intelx.io_bot',
  'MauiBot',
  'olbicobot',
  'KomodiaBot',
  'MSIECrawler',
  'SEOlizer',
  'Amazonbot',
  'serpstatbot',
  'bnf.fr_bot',
  'rogerbot',
  'Grover',
  'redbot.org',
  'https://google.com/bot.html'
]

def usage():
  print('python bin/log-statistics.py [-h] [--credential-abuse-ipdb <credential>] [--ip <ip>] [--check-new-bots] <file.log>')
  print(' --credential-abuse-ipdb <credential>: abuseipdb.com credential to filter spammer and crawler')
  print(' --ip <ip>: print every requests about this ip')
  print(' --check-new-bots: print when a useragent may be a bot')
  print(' --backlinks: print backlinks')
  sys.exit(2)

def get_args(argv):
  get_args._ip = ''
  get_args._checknewbots = False
  get_args._checkerrors = False
  get_args._backlinks = False
  get_args._google = False
  get_args._credential_abuse_ipdb = ''
  n = 0

  try:
    opts, args = getopt.getopt(argv,"h", ["ip", "credential-abuse-ipdb", "check-new-bots", "check-errors", "backlinks", "google"])
  except:
    usage()

  for opt, arg in opts:
    if opt == '-h':
      usage()
    elif opt == '--ip':
      get_args._ip = str(args[n])
      n = n + 1
    elif opt == '--check-new-bots':
      get_args._checknewbots = True
    elif opt == '--check-errors':
      get_args._checkerrors = True
    elif opt == '--backlinks':
      get_args._backlinks = True
    elif opt == '--google':
      get_args._google = True
    elif opt == '--credential-abuse-ipdb':
      get_args._credential_abuse_ipdb = str(args[n])
      n = n + 1

  if len(args) < n + 1:
    usage()
  get_args._log_name = args[n : len(args)]


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
    file.close();
    data_list = []
    for line in lines:
      data_list.append(parse_line(line))
  return data_list


all_ips_location = {}
def get_location(ip):
  try:
    return all_ips_location[ip]
  except:
    try:
      url = 'http://ipinfo.io/' + ip + '/json'
      response = urlopen(url)
      all_ips_location[ip] = json.load(response)
      return all_ips_location[ip]
    except:
      all_ips_location[ip] = {
        'city': '???',
        'region': '???',
        'country': '???',
      }
      return all_ips_location[ip]


abuse_ipdb = {}
def get_abuse_ipdb(ip):
  # cf. https://docs.abuseipdb.com/?python#check-endpoint
  if get_args._credential_abuse_ipdb == '':
    abuse_ipdb[ip] = { 'data': { 'computed': False } }
    return abuse_ipdb[ip]

  try:
    return abuse_ipdb[ip]
  except:
    pass
  
  print('.', end='')
  url = 'https://api.abuseipdb.com/api/v2/check'
  querystring = {
      'ipAddress': ip,
      'maxAgeInDays': '90'
  }
  headers = {
      'Accept': 'application/json',
      'Key': get_args._credential_abuse_ipdb
  }

  try:
    response = requests.request(method='GET', url=url, headers=headers, params=querystring)
    decodedResponse = json.loads(response.text)
    decodedResponse['data']['computed'] = True
    abuse_ipdb[ip] = decodedResponse
  except Exception as e:
    abuse_ipdb[ip] = { 'data': { 'computed': False } }

  return abuse_ipdb[ip]

def is_abuse(ip):
  ipdb = get_abuse_ipdb(ip)
  result = (ipdb['data']['computed']) and (ipdb['data']['abuseConfidenceScore'] > 30)
  # print(result)
  return result

def is_crawler(ip):
  ipdb = get_abuse_ipdb(ip)
  result = (ipdb['data']['computed']) and (ipdb['data']['usageType'] == 'Search Engine Spider')
  # print(result)
  return result

def filter_abuse_ipdb(callback, data_list):
  new_data_list = []
  for data in data_list:
    if not(callback(data['ip'])):
      new_data_list.append(data)
  return new_data_list

def filter_not_abuse(data_list):   # remove all 'abuse' connexions
  return filter_abuse_ipdb(is_abuse, data_list)

def filter_not_crawler(data_list):   # remove all 'abuse' connexions
  return filter_abuse_ipdb(is_crawler, data_list)


def in_list(exact_search, str, list, case_sensitive=True):
  if exact_search:
    return str in list
  else:
    for item in list:
      if case_sensitive:
        if str.find(item) != -1:
          return True
      else:
        if str.lower().find(item) != -1:
          return True
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
      #get_location(data['ip'])
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
        #get_location(data['ip'])
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
    location = get_location(ip)
    try:
      print(ip + ': ' + location['city'] + ', ' + location['region'] + ', ' + location['country'])
    except:
      print(ip + ': Cannot print location')


def print_ip(data, data_list):
    location = get_location(data['ip'])
    try:
      print(data['ip'] + ': ' + location['city'] + ', ' + location['region'] + ', ' + location['country'] + ', ua=' + data['ua'])
      # print(location)
      if location['country'] == 'FR':
        print_all_from_ip(data['ip'], data_list)
    except:
      print(data['ip'] + ': Cannot print location')

def get_ips_list(data_list):
  ips_list = []
  for data in data_list:
    if data['ip'] in ips_list:
      continue
    ips_list.append(data['ip'])
  return ips_list

def print_ips(data_list):
  ip_list = []
  for data in data_list:
    if data['ip'] in ip_list:
      continue
    ip_list.append(data['ip'])
    print_ip(data, data_list)


# a bot is
# - access robots.txt ==> remove all requests from this ip
# - or is a know bot
# - or ua contains crawl or bot

def remove_bots(data_list):
  new_list = []
  ip_bot_list = []
  for data in data_list:
    if in_list(False, data['request'], [ ' /robots.txt' ]) or in_list(False, data['ua'], botname, False) or in_list(False, data['ua'], [ 'crawl', 'bot'], False):
      ip_bot_list.append(data['ip'])

  for data in data_list:
    if not(data['ip'] in ip_bot_list):
      new_list.append(data)

  return new_list

def main(argv):
  get_args(argv)

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

    if get_args._checknewbots:
      print('Checking for potential bots not in list')
      data_list = remove_in_list(data_list, False, 'ua', botname)
      print_contain('POTENTIAL BOT (from name):         ', data_list, False, 'ua', False, [ 'crawl', 'bot'])        # print potential bot
      print_contain('POTENTIAL BOT (access robots.txt): ', data_list, False, 'request', True, [ '/robots.txt'])    # print potential bot
      continue

    if get_args._backlinks:
      print('Checking for backlinks')
      known_backlinks.append(data_list[0]['site'][4:])      # from www.example.com, extract example.com only
                                                            # this is to ignore when the page has been accessed using internal link
      data_list = remove_in_list(data_list, False, 'ua', botname)

      print_doesnot_contain('BACKLINKS: ', data_list, False, 'origin', known_backlinks)    # print backlinks
      continue

    if get_args._google:
      data_list = remove_bots(data_list)
      data_list = keep_only(data_list, False, 'request', [ '.html', 'GET / ', 'GET /?' ])
      unique_requests = keep_unique(data_list, False, 'request', [ '.html', 'GET / ', 'GET /?' ])
      for unique_request in unique_requests: 
        all = keep_only(data_list, True, 'request', [ unique_request ])
        print('========= ' + unique_request + ': ' + str(len(all)))

        for c in all:
          print_ip_location(c['ip'])
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

    # remove bots and potential bots
    data_list = remove_in_list(data_list, False, 'ua', botname)
    data_list = remove_in_list(data_list, False, 'ua', [ 'crawl', 'bot'])

    data_list = keep_only(data_list, False, 'request', [ '.html', 'GET / ', 'GET /?' ])
    unique_requests = keep_unique(data_list, False, 'request', [ '.html', 'GET / ', 'GET /?' ])
    # ips_list = get_ips_list(data_list)
    for unique_request in unique_requests: 
      all = keep_only(data_list, True, 'request', [ unique_request ])
      print('========= ' + unique_request + ': ' + str(len(all)))

      for c in all:
        print_ip_location(c['ip'])


    #print_data_list(data_list)
    #print_ips(data_list)


if __name__ == "__main__":
  main(sys.argv[1:])
  #get_location('50.59.99.143')


