import xml.parsers.expat
import subprocess
import os

tidycmd = './tidy'

tree = { 'name': None, 'attrs': None, 'content': [] }
stack = []
cur = tree
s = ''

def start_element(name, attrs):
  global stack, cur, s
  attrs_new = {}
  for k in attrs:
    attrs_new[str(k)] = str(attrs[k])
  tag = { 'name': str(name), 'attrs': attrs_new, 'content': [] }
  if s.strip() != '':
    cur['content'].append(s.strip())
  stack.append(cur)
  cur = tag
  s = ''

def end_element(name):
  global stack, cur, s
  tag = stack.pop()
  if s.strip() != '':
    cur['content'].append(s.strip())
  tag['content'].append(cur)
  cur = tag
  s = ''

def char_data(data):
  global cur, s
  s += str(data.encode('latin1', 'ignore')).replace('\n', ' ')

def parse_url(url):
  global tree, stack, cur, s
  tree = { 'name': None, 'attrs': None, 'content': [] }
  stack = []
  cur = tree
  s = ''
  
  devnull = open(os.devnull, 'w')
  
  subprocess.call(['wget', '-q', url, '-O', 'tmp.xml'])
  subprocess.call([tidycmd, '-config', 'tidy.conf', 'tmp.xml'], stderr=devnull)
  
  devnull.close()
  
  p = xml.parsers.expat.ParserCreate()
  p.StartElementHandler = start_element
  p.EndElementHandler = end_element
  p.CharacterDataHandler = char_data
  
  fd = open('tmp.xml', 'r')
  p.ParseFile(fd)
  fd.close()
  os.unlink('tmp.xml')
  return tree
