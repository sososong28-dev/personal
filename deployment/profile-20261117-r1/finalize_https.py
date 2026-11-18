#!/usr/bin/env python3
"""Preserve the old app's HTTP-to-HTTPS behavior for the new static public page."""
from pathlib import Path
import subprocess,re,datetime,json,hashlib,importlib.util
VERSION='20261117-r1'
def run(*args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout
s=run('nginx','-T')
paths=[part.splitlines()[0].rstrip(':') for part in re.split(r'# configuration file ',s) if '/profile-assets/'+VERSION+'/' in part and re.search(r'server_name\s+8[.]136[.]223[.]57',part)]
assert len(paths)==1,paths
config=Path(paths[0]).resolve();original=config.read_text()
rule='        if ($scheme = http) { return 301 https://8.136.223.57$request_uri; }\n'
patched=original
for marker in ['    location = /profile {\n','    location ^~ /profile-assets/'+VERSION+'/ {\n']:
 assert patched.count(marker)==1,marker
 if marker+rule not in patched:patched=patched.replace(marker,marker+rule,1)
patched=patched.replace('location = /profile/ { return 301 /profile$is_args$args; }','location = /profile/ { return 301 https://8.136.223.57/profile$is_args$args; }')
spec=importlib.util.spec_from_file_location('release_installer','/root/profile-release-20261117-r1/install.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);before=mod.account_state()
backup=Path('/root')/('profile-https-backup-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S'));backup.mkdir(mode=0o700);(backup/'nginx.before.conf').write_text(original);(backup/'config-path.txt').write_text(str(config))
try:
 config.write_text(patched);run('nginx','-t');run('systemctl','reload','nginx')
 import time
 for attempt in range(12):
  http=run('curl','--silent','--show-error','--noproxy','*','-I','-H','Host: 8.136.223.57','http://127.0.0.1/profile')
  if '301' in http.splitlines()[0] and 'https://8.136.223.57/profile' in http:break
  time.sleep(.3)
 else:raise RuntimeError('HTTP redirect readiness failed')
 html=run('curl','--fail','--silent','--show-error','--noproxy','*','--resolve','8.136.223.57:443:127.0.0.1','https://8.136.223.57/profile')
 assert '/profile-assets/'+VERSION+'/' in html
 assert before==mod.account_state(),'Account/environment changed'
except BaseException:
 config.write_text(original);run('nginx','-t');run('systemctl','reload','nginx');raise
report=dict(https_redirect=True,config=str(config),backup=str(backup),account_environment_unchanged=True,app_restarted=False)
(backup/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
