#!/usr/bin/env python3
"""Install only the reviewed public page. No application import, account or DB writes."""
import argparse,datetime,hashlib,json,os,re,shutil,sqlite3,subprocess,tarfile,tempfile
from pathlib import Path
VERSION='20261117-r1'; HOST='8.136.223.57'
BASE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(*args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout
def account_state():
 result={}
 env=Path('/var/www/profile-site/.env')
 if env.is_file():result['env_sha256']=sha(env)
 db=Path('/var/www/profile-site/data/profile.db')
 if db.is_file():
  with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as c:
   rows=c.execute('SELECT id, username, password_hash, role, enabled FROM users ORDER BY id').fetchall()
  result['accounts_sha256']=hashlib.sha256(json.dumps(rows).encode()).hexdigest()
  result['account_count']=len(rows)
 return result
def blocks(text):
 # Skip comments and quoted strings when balancing server-block braces.
 for m in re.finditer(r'\bserver\s*\{',text):
  start=m.start();depth=1;i=m.end();quote=None;comment=False
  while i<len(text) and depth:
   ch=text[i]
   if comment:
    if ch=='\n':comment=False
   elif quote:
    if ch=='\\':i+=1
    elif ch==quote:quote=None
   elif ch=='#':comment=True
   elif ch in ('"',"'"):quote=ch
   elif ch=='{':depth+=1
   elif ch=='}':depth-=1
   i+=1
  if depth:raise RuntimeError('Unbalanced nginx server block')
  yield start,i,text[start:i]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--server-name',default=HOST);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 config=Path(args.config).resolve();original=config.read_text();matches=[]
 for start,end,block in blocks(original):
  names=re.findall(r'\bserver_name\s+([^;]+);',block)
  if any(args.server_name in x.split() for x in names) and re.search(r'\blisten\s+[^;]*443[^;]*;',block):matches.append((start,end,block))
 if len(matches)!=1:raise RuntimeError('Expected exactly one matching HTTPS server; inspect nginx -T first')
 start,end,block=matches[0]
 old_locations=re.findall(r'location\s*=\s*/profile/?\s*\{[^{}]*\}',block)
 clean_block=block
 for old in old_locations:
  path=re.search(r'location\s*=\s*(/profile/?)',old).group(1)
  expected='location = '+path+' { proxy_pass http://127.0.0.1:5001; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; }'
  if re.sub(r'\s+',' ',old).strip()!=expected:raise RuntimeError('Existing public location differs from the explicitly reviewed proxy block')
  clean_block=clean_block.replace(old,'',1)
 if old_locations and len(old_locations)!=2:raise RuntimeError('Expected both reviewed exact public locations')
 if '/profile-assets/'+VERSION+'/' in block:raise RuntimeError('Version already configured; inspect existing deployment')
 if not args.apply:
  print(json.dumps({'dry_run':True,'config':str(config),'server_name':args.server_name,'target':'/profile','private_routes':'unchanged','reviewed_proxy_blocks_replaced':len(old_locations)}));return
 if os.geteuid()!=0:raise RuntimeError('Root is required')
 archive=BASE/'public.tar.gz';expected=(BASE/'public.tar.gz.sha256').read_text().split()[0]
 if sha(archive)!=expected:raise RuntimeError('Archive SHA-256 mismatch')
 run('nginx','-t');before=account_state()
 if not before.get('accounts_sha256') or not before.get('env_sha256'):raise RuntimeError('Expected production account DB and .env not found; inspect actual paths before deployment')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S');backup=Path('/root')/('profile-public-backup-'+stamp);backup.mkdir(mode=0o700);(backup/'nginx.before.conf').write_text(original);os.chmod(backup/'nginx.before.conf',0o600)
 target=Path('/var/www/profile-public')/VERSION
 if target.exists():raise RuntimeError('Version already exists; inspect prior deployment instead of overwriting')
 target.parent.mkdir(parents=True,exist_ok=True)
 staging=Path(tempfile.mkdtemp(prefix='.profile-stage-',dir=str(target.parent)))
 try:
  with tarfile.open(archive,'r:gz') as tf:
   for member in tf.getmembers():
    if member.name.startswith('/') or '..' in Path(member.name).parts or not member.isfile():raise RuntimeError('Invalid archive member')
    dest=staging/member.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(tf.extractfile(member).read());os.chmod(dest,0o644)
  for folder in staging.rglob('*'):
   if folder.is_dir():os.chmod(folder,0o755)
  os.chmod(staging,0o755);staging.rename(target)
  snippet=f'''\n    # Reviewed public profile {VERSION}; private application routes remain proxied.\n    location = /profile {{\n        alias {target}/index.html;\n        default_type text/html;\n        add_header Cache-Control "no-cache";\n        add_header X-Content-Type-Options nosniff;\n        add_header X-Frame-Options DENY;\n    }}\n    location = /profile/ {{ return 301 /profile$is_args$args; }}\n    location ^~ /profile-assets/{VERSION}/ {{\n        alias {target}/;\n        autoindex off;\n        expires 7d;\n        add_header X-Content-Type-Options nosniff;\n    }}\n'''
  patched=original[:start]+clean_block[:-1]+snippet+clean_block[-1:]+original[end:]
  changed=False
  try:
   config.write_text(patched);changed=True;run('nginx','-t');run('systemctl','reload','nginx')
   html=run('curl','--fail','--silent','--show-error','--resolve',f'{HOST}:443:127.0.0.1',f'https://{HOST}/profile')
   if '产品市场' not in html or f'/profile-assets/{VERSION}/' not in html:raise RuntimeError('Public page smoke check failed')
   after=account_state()
   if before!=after:raise RuntimeError('Account/environment fingerprints changed during deployment; investigate')
  except BaseException:
   if changed:config.write_text(original);run('nginx','-t');run('systemctl','reload','nginx')
   raise
  report={'version':VERSION,'config':str(config),'backup':str(backup),'public_root':str(target),'account_environment_unchanged':True,'app_restarted':False}
  (backup/'report.json').write_text(json.dumps(report,indent=2));(backup/'config-path.txt').write_text(str(config));print(json.dumps(report))
 finally:
  if staging.exists():shutil.rmtree(staging)
if __name__=='__main__':main()
