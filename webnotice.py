import tidyxml
import pprint
import datetime
import pytz
import hashlib

wnotice = 'https://www.math.uwaterloo.ca/~wnotice/notice_prgms/wreg'
emailfrom = 'wnotice@math.uwaterloo.ca'

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
  event['where'] = stuff[0][1][3:]
  if len(stuff) > 2:
    event['venue'] = stuff[1][0]['content'][0]
    who = stuff[2][1]
    whosplit = who.split(', ', 1)
    event['who'] = whosplit[0]
    event['affiliation'] = whosplit[1]
    event['title'] = stuff[2][4]['content'][0]['content'][0]
    if stuff[2][6]['content'][0] == 'Abstract:':
      event['abstract'] = stuff[2][7]
    else:
      event['remarks'] = stuff[2][7]
      if len(stuff[2][9]['content']) > 0 and stuff[2][9]['content'][0] == 'Abstract:':
        event['abstract'] = stuff[2][10]
  else:
    stuff.insert(1, [])
    who = stuff[2][1]
    whosplit = who.split(', ', 1)
    event['who'] = whosplit[0]
    event['affiliation'] = whosplit[1]
    event['title'] = stuff[2][4]['content'][0]['content'][0]
    event['venue'] = ''
    remarks = stuff[0][2]['content'][0]['content'][0] + ' - '
    remarks += stuff[0][4]['content'][0]['content'][0] + '\\n\\n'
    remarks += stuff[0][6]['content'][0]
    event['remarks'] = remarks
  event['uid'] = utc_dt.strftime('%Y')+'_'+hashlib.md5(event['who']+'|'+event['title']).hexdigest()+'.'+emailfrom
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
    if 'remarks' in event:
      fd.write(event['remarks'])
      if 'abstract' in event:
        fd.write('\\n\\n'+event['abstract'])
    else:
      if 'abstract' in event:
        fd.write(event['abstract'])
    fd.write('\n')
    fd.write('END:VEVENT\n')
  fd.write('END:VCALENDAR\n')
  fd.close()

depts = get_depts()
for dept in depts:
  dump_ics(dept, depts[dept])
