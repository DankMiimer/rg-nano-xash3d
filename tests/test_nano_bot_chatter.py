# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parents[1]
s=(r/'upstream/cs16-client/3rdparty/ReGameDLL_CS/regamedll/dlls/bot/cs_bot_chatter.cpp').read_text()
a=s.index('if(filename && strstr(filename,"im_going_to_camp.wav"))');e=s.index('{',a)+1;d=1
while d:d+=(s[e]=='{')-(s[e]=='}');e+=1
code=r"""
#include <cassert>
#include <cstring>
struct {float time;} globals,*gpGlobals=&globals;
struct Bot{int m_iTeam;};
bool allowed(const char *filename,int team,float now){Bot bot={team},*me=&bot;gpGlobals->time=now;bool sayIt=true;
"""+s[a:e]+r"""
return sayIt;}
int main(){
 const char *camp="radio/bot/im_going_to_camp.wav";
 assert(allowed(camp,1,10));for(int i=0;i<6;i++)assert(!allowed(camp,1,11+i));
 assert(allowed(camp,2,12));assert(allowed("radio/bot/enemy_spotted.wav",1,13));
 assert(allowed(camp,1,30));assert(allowed(camp,1,1));assert(!allowed(camp,1,2));
 assert(allowed(nullptr,1,3));
}
"""
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.cpp';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Camp chatter: duplicate team plans suppressed for 20 seconds; other calls, other team and map-clock reset preserved.')
