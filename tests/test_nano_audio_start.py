# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the actual launch function's mixer targeting and failure policy."""
from pathlib import Path
import json, os, subprocess, sys, tempfile
from decimal import Decimal, ROUND_HALF_UP
root=Path(__file__).resolve().parents[1]
source=(root/'tools/nano-run.sh').read_text()
start=source.index('restore_volume() {')
end=source.index('\n}\n',start)+3
function=source[start:end]
with tempfile.TemporaryDirectory() as temp:
    temp=Path(temp); log=temp/'calls';usb=temp/'usb-config'
    script=temp/'test.sh'
    script.write_text(function.replace('/mnt/FunKey/.asoundrc',str(usb))+'\nrestore_volume "$1"\n')
    stub='#!'+sys.executable+'''
import json,os,sys
with open(os.environ['CALL_LOG'],'a') as f: f.write(json.dumps([os.path.basename(sys.argv[0])]+sys.argv[1:])+'\\n')
if os.environ.get('FAIL_TARGET','') in sys.argv and os.environ.get('FAIL_TARGET',''): sys.exit(7)
'''
    for name in ('amixer','volume'):
        path=temp/name;path.write_text(stub);path.chmod(0o755)
    env={**os.environ,'PATH':str(temp)+':'+os.environ['PATH'],'CALL_LOG':str(log)}
    def run(value,fail='',external=False):
        log.write_text('')
        if external: usb.touch()
        else: usb.unlink(missing_ok=True)
        result=subprocess.run(['sh',str(script),str(value)],env={**env,'FAIL_TARGET':fail},capture_output=True,text=True)
        return result.returncode,[json.loads(l) for l in log.read_text().splitlines()]
    volume_id="iface=MIXER,name='Headphone Playback Volume'"
    switch_id="iface=MIXER,name='Headphone Playback Switch'"
    for percent in range(101):
        code,calls=run(percent)
        expected=int((Decimal(percent)*47/100+16).quantize(Decimal(1),rounding=ROUND_HALF_UP))
        assert code==0 and calls==[
            ['amixer','-c','0','-q','cset',volume_id,str(expected)],
            ['amixer','-c','0','-q','cset',switch_id,'on,on']],(percent,code,calls)
    for bad in ('','-1','101','abc','1.5','2;echo bad','99999999999999999999999'):
        code,calls=run(bad);assert code!=0 and calls==[]
    code,calls=run('008');assert code==0 and calls[0][-1]=='20'
    code,calls=run(30,fail=volume_id);assert code==7 and len(calls)==1
    code,calls=run(30,fail=switch_id);assert code==7 and len(calls)==2
    code,calls=run(30,external=True);assert code==0 and calls==[['volume','set','30']]
    code,calls=run(30,external=True,fail='30');assert code==7 and len(calls)==1
print('Audio startup: exact rounding, targeted quiet controls, invalid values, failures and USB policy pass.')
