# SPDX-License-Identifier: GPL-3.0-or-later
"""Execute the real bounded player and cinematic transitions without a device."""
from pathlib import Path
import os, struct, subprocess, tempfile

root = Path(__file__).resolve().parents[1]
native = Path(os.environ.get('NANO_NATIVE_DIR', str(root / 'build/native')))
cinematic = (native / 'xash3d/engine/client/cl_video.c').read_text()
cinematic = cinematic.replace('#include "common.h"', '').replace('#include "client.h"', '')
code = r'''
#include <assert.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <stdio.h>
#include <stdint.h>
typedef unsigned char byte;typedef int qboolean;typedef unsigned int uint;
typedef char string[1024];typedef int poolhandle_t;typedef FILE file_t;
#define true 1
#define false 0
#define Q_max(a,b) ((a)>(b)?(a):(b))
#define Q_min(a,b) ((a)<(b)?(a):(b))
#define bound(a,b,c) Q_max(a,Q_min(b,c))
#define Q_stricmp strcasecmp
static void copyString(char *dest,const char *source,size_t size){if(size){size_t n=strnlen(source,size-1);memcpy(dest,source,n);dest[n]=0;}}
#define Q_strncpy copyString
#define Q_snprintf snprintf
#define Q_rint(x) ((int)lround(x))
#define S_WARN ""
#define S_ERROR ""
#define Con_Printf(...) ((void)0)
#define XASH_VIDEO 1
#define VIDEO_FBDEV 1
#define XASH_AVI 0
#define AVI_NULL 0
#define DEFAULT_VIDEOLIST_PATH "media/StartupVids.txt"
#define MAX_MOVIES 8
#define MAX_STRING 1024
#define SOUND_DMA_SPEED 44100
#define SND_CLIP_DISTANCE 1000
#define S_RAW_SOUND_SOUNDTRACK -1
#define TF_IMAGE 15
#define TF_NOMIPMAP 1
#define TF_CLAMP 2
#define PF_RGBA_32 1
#define IMAGE_HAS_COLOR 1
#define REF_BLACK_TEXTURE 0
#define kRenderNormal 0
#define CIN_MAIN 0
#define CIN_LOGO 1
enum {STATE_RUNFRAME,STATE_LOAD_LEVEL,STATE_LOAD_GAME,STATE_GAME_SHUTDOWN};
enum {ca_disconnected,ca_cinematic};enum {key_menu,key_game};
enum movie_parms_e {AVI_PARM_LAST,AVI_RENDER_TEXNUM,AVI_RENDER_X,AVI_RENDER_Y,
 AVI_RENDER_W,AVI_RENDER_H,AVI_REWIND,AVI_ENTNUM,AVI_VOLUME,AVI_ATTN,AVI_PAUSE,AVI_RESUME};
typedef struct {int width,height,type,flags;size_t size;byte *buffer;} rgbdata_t;
typedef struct {uint s_rawend,max_samples;int master_vol;float dist_mult;int rawsamples[128];} rawchan_t;
static rawchan_t channel={0,128,0,0,{0}};
static struct {int initialized,streaming;uint soundtime;} snd={1,1,0};
static struct {int paused;} cl={0};
static struct {int state,key_dest,signon,movienum,demonum;char movies[8][256];} cls={0,key_menu,0,-1,-1,{{0}}};
static struct {int nextstate;} state={STATE_RUNFRAME};
#define GameState (&state)
static double clockTime;static int visible,noIntro,noAvi,matchCommand,available;
static int stopSounds,demos,uploads,draws,textureAlive,texturePeak,drawX,drawY,drawW,drawH;
static char command[1024],media[1024];
static size_t allocated,peak;
static poolhandle_t avi_mempool=1;static qboolean avi_initialized=1;
static void *allocate(size_t size){size_t *p=malloc(size+sizeof(size_t));assert(p);*p=size;allocated+=size;peak=Q_max(peak,allocated);return p+1;}
static void release(void *ptr){size_t *p=(size_t*)ptr-1;allocated-=*p;free(p);}
#define Mem_Malloc(pool,size) ((void)(pool),allocate(size))
#define Mem_Free(ptr) release(ptr)
static const char *COM_FileExtension(const char *name){const char *p=strrchr(name,'.');return p?p+1:"";}
static double Platform_DoubleTime(void){return clockTime;}
static rawchan_t *S_FindRawChannel(int entnum,int create){(void)create;assert(entnum==-1);return &channel;}
static uint S_RawSamplesStereo(int *raw,uint end,uint max,uint count,uint rate,int width,int channels,const byte *data){
 (void)raw;(void)max;(void)data;assert(width==1 && channels==1 && rate==22050);return end+count*2;
}
static int loadTexture(const char *name,rgbdata_t *image,int flags,int update){
 assert(strncmp(name,"*nanointro_",11)==0 && flags==TF_IMAGE && image->type==PF_RGBA_32);
 assert(image->size==(size_t)image->width*image->height*4 && image->buffer[3]==255);
 if(update)assert(textureAlive);else{++textureAlive;texturePeak=Q_max(texturePeak,textureAlive);}
 ++uploads;return 9;
}
static void freeTexture(unsigned int number){assert(number==9 && textureAlive==1);--textureAlive;}
static void drawPicture(int x,int y,int w,int h,float a,float b,float c,float d,int texture){
 (void)a;(void)b;(void)c;(void)d;assert(texture==9 || texture==1);++draws;
 if(texture==9){drawX=x;drawY=y;drawW=w;drawH=h;assert(x>=0 && y>=0 && x+w<=240 && y+h<=240);}
}
static void renderMode(int mode){(void)mode;}
static int createTexture(const char *name,int w,int h,void *data,int flags){(void)name;(void)w;(void)h;(void)data;(void)flags;return 7;}
static struct {int initialized;struct {
 int (*GL_LoadTextureFromBuffer)(const char*,rgbdata_t*,int,int);
 void (*GL_FreeTexture)(unsigned int);
 void (*R_DrawStretchPic)(int,int,int,int,float,float,float,float,int);
 void (*GL_SetRenderMode)(int);
 int (*GL_CreateTexture)(const char*,int,int,void*,int);
} dllFuncs;} ref={1,{loadTexture,freeTexture,drawPicture,renderMode,createTexture}};
static struct {int width,height;} refState={240,240};
typedef struct movie_state_s movie_state_t;
// The production sound.h has engine dependencies; the tested API above models
// its mixer/clock, while every playback function comes from the actual header.
#define SOUND_H
#include "nano-intro-player.h"
static movie_state_t movies[2];
static movie_state_t *AVI_GetState(int index){return movies+index;}
static qboolean AVI_IsActive(movie_state_t *movie){return movie && movie->active;}
static void AVI_Initailize(void){}
static void AVI_Shutdown(void){}
static void S_StopAllSounds(int ambient){(void)ambient;++stopSounds;channel.s_rawend=snd.soundtime;}
static void S_StartStreaming(void){snd.streaming=1;}
static void S_StopStreaming(void){snd.streaming=0;}
static int UI_IsVisible(void){return visible;}
static void UI_SetActiveMenu(int active){visible=active;cls.key_dest=active?key_menu:key_game;}
static void Key_SetKeyDest(int key){cls.key_dest=key;}
static void Con_FastClose(void){}
static void CL_CheckStartupDemos(void){++demos;}
static int R_GetBuiltinTexture(int texture){(void)texture;return 1;}
static int Sys_CheckParm(const char *name){return !strcmp(name,"-nointro")?noIntro:!strcmp(name,"-noavi")?noAvi:!strcmp(name,"+menu_nano_match")?matchCommand:0;}
static int FS_FileExists(const char *name,int gameOnly){(void)gameOnly;return !strcmp(name,"media/nano_valve.nvi")?available:!strcmp(name,DEFAULT_VIDEOLIST_PATH);}
static const char *FS_GetDiskPath(const char *name,int gameOnly){(void)gameOnly;return !strcmp(name,"media/nano_valve.nvi")?media:NULL;}
static file_t *FS_Open(const char *name,const char *mode,int only){(void)name;(void)mode;(void)only;return NULL;}
static void FS_Print(file_t *f,const char *text){(void)f;(void)text;}
static void FS_Close(file_t *f){(void)f;}
static byte *FS_LoadFile(const char *name,void *length,int only){(void)name;(void)length;(void)only;return NULL;}
static char *COM_ParseFile(char *file,char *token,size_t count){(void)file;(void)token;(void)count;return NULL;}
static void Cbuf_AddText(const char *text){snprintf(command,sizeof(command),"%s",text);}
static void Cbuf_InsertText(const char *text){Cbuf_AddText(text);}
static void Cbuf_Execute(void){}
qboolean SCR_NextMovie(void);void SCR_StopCinematic(void);qboolean SCR_PlayCinematic(const char*);
'''
code += cinematic
code += r'''
int main(int argc,char **argv){
 assert(argc>=3);snprintf(media,sizeof(media),"%s",argv[1]);available=1;
 SCR_InitCinematic();
 // Decode actual RGB565 primaries and reject truncated/unsupported inputs.
 movie_state_t standalone={0};AVI_OpenVideo(&standalone,media,true,0);assert(standalone.active);
 byte *pixels=AVI_GetVideoFrame(&standalone,0);assert(pixels && pixels[0]==255 && pixels[1]==0 && pixels[2]==0);
 assert(pixels[4]==0 && pixels[5]==255 && pixels[6]==0 && pixels[8]==0 && pixels[10]==255);
 assert(!AVI_GetVideoFrame(&standalone,-1) && !AVI_GetVideoFrame(&standalone,4));
 assert(AVI_Think(&standalone));assert(textureAlive==1);AVI_CloseVideo(&standalone);assert(!allocated && !textureAlive);
 AVI_OpenVideo(&standalone,argv[2],true,0);assert(!standalone.active && !allocated);
 // Oversized/malformed header fields fail before they can allocate buffers.
 for(int field=1;field<=7;++field){
  FILE *source=fopen(media,"rb"),*bad=fopen(argv[2],"wb");assert(source && bad);
  byte buffer[512];size_t count;while((count=fread(buffer,1,sizeof(buffer),source)))assert(fwrite(buffer,1,count,bad)==count);
  fclose(source);assert(!fseek(bad,field*4,SEEK_SET));
  byte value[4]={255,255,255,255};assert(fwrite(value,1,4,bad)==4);fclose(bad);
  AVI_OpenVideo(&standalone,argv[2],true,0);assert(!standalone.active && !allocated);
 }
 AVI_OpenVideo(&standalone,"missing.avi",true,0);assert(!standalone.active && !allocated);
 // Suppressed intros and a missing asset retain the pending launcher destination.
 state.nextstate=STATE_LOAD_LEVEL;noIntro=1;SCR_CheckStartupVids();assert(!SCR_NanoIntroActive() && state.nextstate==STATE_LOAD_LEVEL);
 noIntro=0;noAvi=1;SCR_CheckStartupVids();assert(!SCR_NanoIntroActive());noAvi=0;
 available=0;SCR_CheckStartupVids();assert(!SCR_NanoIntroActive() && state.nextstate==STATE_LOAD_LEVEL);available=1;
 // A queued Half-Life map is deferred until playback completes.
 clockTime=1;SCR_CheckStartupVids();assert(SCR_NanoIntroActive() && cls.state==ca_cinematic && !visible && state.nextstate==STATE_RUNFRAME);
 int oldUploads=uploads;assert(SCR_DrawCinematic());assert(uploads==oldUploads+1);
 assert(drawX==0 && drawY==0 && drawW==240 && drawH==240);
 clockTime=1.05;snd.soundtime=2205;assert(SCR_DrawCinematic());assert(uploads==oldUploads+1);
 AVI_SetParm(AVI_GetState(CIN_MAIN),AVI_PAUSE,AVI_PARM_LAST);int oldDraws=draws;
 clockTime=2;assert(SCR_DrawCinematic());assert(draws==oldDraws+2);
 AVI_SetParm(AVI_GetState(CIN_MAIN),AVI_RESUME,AVI_PARM_LAST);
 clockTime=2.11;assert(SCR_DrawCinematic());assert(uploads==oldUploads+2);
 clockTime=2.5;SCR_DrawCinematic();assert(!SCR_NanoIntroActive() && state.nextstate==STATE_LOAD_LEVEL && !textureAlive && !allocated && !snd.streaming);
 // A skip returns to the CS setup command; a later quit is never overwritten.
 state.nextstate=STATE_RUNFRAME;matchCommand=1;clockTime=3;SCR_CheckStartupVids();assert(SCR_NanoIntroActive());SCR_DrawCinematic();
 SCR_NanoIntroSkip();assert(!SCR_NanoIntroActive() && visible && !strcmp(command,"menu_nano_match\n") && !allocated && !textureAlive);
 matchCommand=0;state.nextstate=STATE_LOAD_GAME;SCR_CheckStartupVids();SCR_DrawCinematic();state.nextstate=STATE_GAME_SHUTDOWN;
 SCR_NanoIntroSkip();assert(state.nextstate==STATE_GAME_SHUTDOWN && !allocated);
 // UI interruption also frees the clip and restores the pending state.
 state.nextstate=STATE_RUNFRAME;SCR_CheckStartupVids();SCR_DrawCinematic();visible=1;SCR_RunCinematic();assert(!SCR_NanoIntroActive() && !allocated && !textureAlive);
 if(argc>3){
  snprintf(media,sizeof(media),"%s",argv[3]);clockTime=10;state.nextstate=STATE_RUNFRAME;
  SCR_CheckStartupVids();assert(SCR_NanoIntroActive());int x,y;float duration;
  assert(AVI_GetVideoInfo(AVI_GetState(CIN_MAIN),&x,&y,&duration) && x==240 && y==180 && duration==10);
  SCR_DrawCinematic();assert(drawX==0 && drawY==30 && drawW==240 && drawH==180);
  clockTime=15;snd.soundtime=220500;SCR_DrawCinematic();assert(AVI_GetState(CIN_MAIN)->last_frame==75);
  assert(peak<=240*180*6);SCR_NanoIntroSkip();assert(!allocated && !textureAlive);
 }
 assert(texturePeak==1);SCR_FreeCinematic();assert(!allocated);
 puts("Actual intro player: bounded decoding, audio streaming, texture reuse/release, timing, pause, EOF, skip and launcher destination passed.");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='nano-intro-test-') as directory:
    directory = Path(directory)
    fixture = directory / 'valid.nvi'
    fixture.write_bytes(struct.pack('<4s7I', b'NVI1', 2, 2, 10, 4, 22050, 8820, 0)
                        + struct.pack('<4H', 0xf800, 0x07e0, 0x001f, 0xffff) * 4
                        + bytes(range(256)) * 34 + bytes(116))
    invalid = directory / 'invalid.nvi'
    invalid.write_bytes(fixture.read_bytes()[:-1])
    (directory / 'sound.h').write_text('')
    source = directory / 'test.c'
    source.write_text(code)
    binary = directory / 'test'
    subprocess.run(['gcc', '-std=gnu99', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
                    '-I', str(directory), '-I', str(root / 'src'), str(source), '-lm', '-o', str(binary)], check=True)
    args = [str(binary), str(fixture), str(invalid)]
    if os.environ.get('NANO_INTRO_FILE'): args.append(os.environ['NANO_INTRO_FILE'])
    subprocess.run(args, check=True)
