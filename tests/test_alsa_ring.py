# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
text=(native/'xash3d/engine/platform/linux/s_alsa.c').read_text()
start=text.index('void SNDDMA_Submit( void )')
end=text.index('\n/*',start)
function=text[start:end]
begin=text.index('void SNDDMA_BeginPainting(void)')
begin_end=text.index('\n/*',begin)
function+='\n'+text[begin:begin_end]
activate=text.index('void SNDDMA_Activate(')
activate_end=text.index('\nqboolean VoiceCapture_Init',activate)
function+='\n'+text[activate:activate_end]
header=r'''#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
typedef long snd_pcm_sframes_t;
typedef int qboolean;
#define false 0
#define true 1
struct { int paused,period_size; void *pcm_handle; unsigned long long frames_written; } s_alsa;
struct { unsigned char *buffer; int samples,samplepos,initialized; unsigned paintedtime,soundtime; } snd;
static long available[16], written[16];
static int ai,wi,prepares,writes,drops,clears;
static void S_StopAllSounds(int ambient) { (void)ambient;clears++; }
static int snd_pcm_drop(void *p) { (void)p;drops++;return 0; }
static long hardware_delay;
static int delay_error,starts,state;
#define SND_PCM_STATE_PREPARED 2
static int snd_pcm_state(void *p) { (void)p; return state; }
static int snd_pcm_start(void *p) { (void)p;starts++;state=3;return 0; }
static unsigned char storage[64];
static long snd_pcm_avail_update(void *p) { (void)p; return available[ai++]; }
static int snd_pcm_delay(void *p,long *delay) { (void)p;*delay=hardware_delay;return delay_error; }
static int snd_pcm_prepare(void *p) { (void)p; prepares++; return 0; }
static long snd_pcm_writei(void *p,const void *start,int frames) {
    (void)p;
    assert((const unsigned char*)start>=storage);
    assert((const unsigned char*)start+frames*4<=storage+sizeof(storage));
    writes++;
    return written[wi++];
}
static void reset(void) {
    memset(available,0,sizeof(available)); memset(written,0,sizeof(written));
    ai=wi=prepares=writes=drops=clears=0;
    snd.buffer=storage;snd.samples=32;snd.samplepos=0;
    s_alsa.paused=0;s_alsa.period_size=8;s_alsa.frames_written=0;
    snd.paintedtime=128;snd.soundtime=0;snd.initialized=1;hardware_delay=0;delay_error=0;starts=0;state=3;
}
'''
tests=r'''
int main(void) {
    reset(); available[0]=8;written[0]=-EAGAIN;
    SNDDMA_Submit(); assert(snd.samplepos==0 && prepares==0 && writes==1);
    reset(); available[0]=8;written[0]=-EPIPE;
    SNDDMA_Submit(); assert(snd.samplepos==0 && prepares==1);
    reset(); available[0]=8;written[0]=3;
    SNDDMA_Submit(); assert(s_alsa.frames_written==3 && snd.samplepos==0 && writes==1);
    reset(); snd.samplepos=10;s_alsa.frames_written=14;available[0]=8;written[0]=2;available[1]=8;written[1]=5;
    SNDDMA_Submit(); assert(snd.samplepos==10 && s_alsa.frames_written==21 && writes==2);
    reset(); s_alsa.paused=1;
    SNDDMA_Submit(); assert(writes==0 && ai==0);
    reset(); for(int i=0;i<16;i++){available[i]=8;written[i]=8;}
    SNDDMA_Submit(); assert(writes==8 && ai==8);
    reset(); snd.paintedtime=0;available[0]=8;
    SNDDMA_Submit(); assert(writes==0 && s_alsa.frames_written==0);
    reset();s_alsa.frames_written=9;hardware_delay=4;
    SNDDMA_BeginPainting();assert(snd.samplepos==10 && snd.soundtime==5);
    reset();snd.paintedtime=3;available[0]=8;written[0]=3;
    SNDDMA_Submit();assert(s_alsa.frames_written==3 && writes==1);
    reset();s_alsa.frames_written=35;hardware_delay=0;
    SNDDMA_BeginPainting();assert(snd.samplepos==6 && snd.soundtime==35);
    reset();s_alsa.frames_written=20;hardware_delay=0;delay_error=-EPIPE;
    SNDDMA_BeginPainting();assert(snd.soundtime==20);
    reset();available[0]=8;written[0]=8;state=SND_PCM_STATE_PREPARED;
    SNDDMA_Submit();assert(starts==1 && s_alsa.frames_written==8);
    reset();s_alsa.frames_written=0x40000000ULL+36;snd.paintedtime=0x40000000U+44;
    SNDDMA_BeginPainting();assert(snd.soundtime==20 && snd.paintedtime==28 && s_alsa.frames_written==20 && clears==1);
    reset();SNDDMA_Activate(1);assert(prepares==0 && drops==0);
    SNDDMA_Activate(0);assert(s_alsa.paused && drops==1);
    SNDDMA_Activate(0);assert(drops==1);
    SNDDMA_Activate(1);assert(!s_alsa.paused && prepares==1 && starts==0);
    puts("ALSA ring tests passed: full queue, underrun, partial writes, wrap, pause, bounded drain, mixed-data limit, absolute hardware clock, whole-ring advance, underrun clock, restart, long-run rebase, activation transitions.");
}
'''
path=root/'build/tests/alsa-ring-test.c';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(header+function+tests)

binary=root/'build/tests/alsa-ring-test'
subprocess.run(['gcc','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(path),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
