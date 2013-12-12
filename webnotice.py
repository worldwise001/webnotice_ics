import tidyxml
import pprint
import datetime
import pytz
import hashlib

wnotice = 'https://www.math.uwaterloo.ca/~wnotice/notice_prgms/wreg'
emailfrom = 'wnotice@math.uwaterloo.ca'
debug = False

def get_depts():
  res = tidyxml.parse_url(wnotice+'/view_notice.pl')
  content = res['content'][0]['content'][1]['content'][3]['content'][1]['content'][0]['content'][0]['content'][0]['content'][0]['content']
  
  s = ''
  dept = None
  deptlist = {}
  for i in content:
    if type(i) is str:
      s = i
    elif type(i) is dict and i['name'] == 'input':
      if dept is not None:
        deptlist[dept] = s
      dept = i['attrs']['value']
  deptlist[dept] = s
  content = res['content'][0]['content'][1]['content'][3]['content'][1]['content'][0]['content'][0]['content'][1]['content'][0]['content']
  
  s = ''
  dept = None
  for i in content:
    if type(i) is str:
      s = i
    elif type(i) is dict and i['name'] == 'input':
      if dept is not None:
        deptlist[dept] = s
      dept = i['attrs']['value']
  deptlist[dept] = s
  deptlist['all_depts'] = 'All Departments'
  return deptlist

def search_and_extract(stuff, key):
  for i in range(0, len(stuff)):
    e = stuff[i]
    if (type(e) == dict) and (len(e['content']) > 0) and (e['content'][0]) == (key+':'):
      j = i+1
      data = ''
      while (j < len(stuff)) and ((type(stuff[j]) != dict) or (stuff[j]['name'] != 'br')):
        if type(stuff[j]) == dict:
          if stuff[j]['name'] == 'p':
            data += '\n\n'
          if type(stuff[j]['content'][0]) == dict:
            data += stuff[j]['content'][0]['content'][0]
          else:
            data += stuff[j]['content'][0]
        else:
          data += stuff[j]
        data += ' '
        j = j+1
      return data.rstrip()
  return None

def format_event(stuff):
  event = {}
  when = stuff[0][0]['content'][0].replace('  ', ' ')
  local = pytz.timezone ('America/Toronto')
  naive = datetime.datetime.strptime(when, '%A, %d %B %Y, %I:%M%p')
  local_dt = local.localize(naive, is_dst=None)
  utc_dt = local_dt.astimezone (pytz.utc)
  event['when'] = utc_dt.strftime('%Y%m%dT%H%M00Z')
  event['when_end'] = (utc_dt + datetime.timedelta(hours=1)).strftime('%Y%m%dT%H%M00Z')
  event['seq'] = utc_dt.strftime('%Y%m%d%H')
  extra = None
  if (len(stuff[0][0]['content']) > 1) and (stuff[0][0]['content'][1]['content'][0] == '*** CANCELLED ***'):
    extra = [stuff[0][0]['content'][1]['content'][0], '']
    event['venue'] = stuff[0][2]['content'][0]
    event['whofull'] = stuff[1][0]
    event['where'] = ''
    event['title'] = stuff[1][2]['content'][0]['content'][0]
    event['abstract'] = None
    event['remarks'] = None
  else:
    event['where'] = stuff[0][1][3:]
    event['where'] = event['where'].replace(' true', '')
    if len(stuff) > 2:
      event['venue'] = stuff[1][0]['content'][0]
    else:
      event['venue'] = ''
      stuff.insert(1, [])
      extra = [stuff[0][2]['content'][0]['content'][0] + ' - ' + stuff[0][4]['content'][0]['content'][0], stuff[0][6]['content'][0]]
    event['whofull'] = search_and_extract(stuff[2], 'Speaker')
    event['title'] = search_and_extract(stuff[2], 'Title')
    event['abstract'] = search_and_extract(stuff[2], 'Abstract')
    event['remarks'] = search_and_extract(stuff[2], 'Remarks')
  # cleaning up data
  title = event['title']
  if title[:1] == '"':
    title = title[1:]
  if title[-1:] == '"':
    title = title[:-1]
  title = title.replace('``', '"')
  title = title.replace('\'\'', '"')
  title = title.replace('""', '"')
  event['title'] = title
  whosplit = event['whofull'].split(', ', 1)
  event['who'] = whosplit[0]
  event['affiliation'] = whosplit[1]
  event['venue'] = event['venue'].replace('Seminar Seminar', 'Seminar')
  if extra != None:
    event['title'] = extra[0] + ' - ' + event['title']
    if event['remarks'] != None:
      event['remarks'] = extra[1] + '\n\n' + event['remarks']
    else:
      event['remarks'] = extra[1]
  event['uid'] = utc_dt.strftime('%Y')+'_'+hashlib.md5(event['who']+'|'+event['title']).hexdigest()+'.'+emailfrom
  #pprint.pprint(stuff)
  #pprint.pprint(event)
  #print '\n\n'
  return event

def get_listing(dept):
  res = tidyxml.parse_url(wnotice+'/list_notices_p.pl?dept='+dept+'&time_frame=month')
  content = res['content'][0]['content'][1]['content'][4]['content']
  events = []
  stuff = []
  for i in content:
    if type(i) is dict:
      if i['name'] == 'dt':
        stuff.append(i['content'])
      elif i['name'] == 'dd':
        stuff.append(i['content'])
        events.append(format_event(stuff))
        stuff = []
  return events

def dump_ics(dept, name):
  listing = get_listing(dept)
  if debug == True:
    return None
  fd = open('webnotice/'+dept+'.ics', 'w')
  fd.write('BEGIN:VCALENDAR\n')
  fd.write('X-WR-CALNAME:Webnotice ('+name+')\n')
  fd.write('X-WR-CALDESC:Webnotice ('+name+') at University of Waterloo\n')
  fd.write('X-PUBLISHED-TTL:PT60M\n')
  fd.write('PRODID:-//UW-Webnotice/NONSGML 0.1//EN\n')
  fd.write('VERSION:2.0\n')
  for event in listing:
    fd.write('BEGIN:VEVENT\n')
    fd.write('DTSTAMP:'+event['when']+'\n')
    fd.write('UID:'+event['uid']+'\n')
    fd.write('DTSTART:'+event['when']+'\n')
    fd.write('DTEND:'+event['when_end']+'\n')
    fd.write('SUMMARY:'+event['title']+' ('+event['venue']+')\n')
    fd.write('LOCATION:'+event['where']+'\n')
    fd.write('DESCRIPTION:'+event['title']+'\\n'+event['who']+', '+event['affiliation']+'\\n\\n')
    if event['remarks'] != None:
      fd.write(event['remarks'])
      fd.write('\\n\\n')
    if event['abstract'] != None:
      fd.write(event['abstract'].replace('\n', '\\n'))
    fd.write('\n')
    fd.write('END:VEVENT\n')
  fd.write('END:VCALENDAR\n')
  fd.close()

depts = get_depts()
for dept in depts:
  dump_ics(dept, depts[dept])
