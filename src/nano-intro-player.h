// SPDX-License-Identifier: GPL-3.0-or-later
// Included by the AVI_NULL backend only on the framebuffer build.
#include "sound.h"
#include <stdio.h>
#include <stdint.h>
#include <stdarg.h>

struct movie_state_s {
    qboolean active, started, paused;
    FILE *video, *audio;
    byte *packed, *dst;
    int xres, yres, fps, frames, rate, samples, audio_pos, last_frame;
    int x, y, w, h, texture, draw_texture, entnum, volume;
    float attn;
    double start, pause_time;
};

static uint32_t NanoIntroLE32(const byte *p) {
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}

void AVI_CloseVideo(movie_state_t *a) {
    if(!a)return;
    if(a->video)fclose(a->video);
    if(a->audio)fclose(a->audio);
    if(a->packed)Mem_Free(a->packed);
    if(a->dst)Mem_Free(a->dst);
    if(a->draw_texture && ref.initialized)ref.dllFuncs.GL_FreeTexture(a->draw_texture);
    if(a->active && a->audio && snd.initialized) {
        rawchan_t *channel=S_FindRawChannel(a->entnum,false);
        if(channel)channel->s_rawend=snd.soundtime;
    }
    memset(a,0,sizeof(*a));
}

void AVI_OpenVideo(movie_state_t *a,const char *filename,qboolean load_audio,int quiet) {
    byte header[32];long length,expected;size_t frame_bytes;
    if(!a)return;
    AVI_CloseVideo(a);
    if(!avi_initialized || !filename || Q_stricmp(COM_FileExtension(filename),"nvi"))return;
    a->video=fopen(filename,"rb");
    if(!a->video)return;
    if(fread(header,1,sizeof(header),a->video)!=sizeof(header) || memcmp(header,"NVI1",4))goto invalid;
    a->xres=NanoIntroLE32(header+4);a->yres=NanoIntroLE32(header+8);
    a->fps=NanoIntroLE32(header+12);a->frames=NanoIntroLE32(header+16);
    a->rate=NanoIntroLE32(header+20);a->samples=NanoIntroLE32(header+24);
    // Validate before multiplication/allocation: assets cannot grow the memory budget.
    if(a->xres<1 || a->xres>240 || a->yres<1 || a->yres>240 || a->fps<1 || a->fps>30 ||
       a->frames<1 || a->frames>30*a->fps || a->rate!=22050 || a->samples<1 ||
       a->samples>30*22050 || NanoIntroLE32(header+28))goto invalid;
    if(fabs((double)a->frames/a->fps-(double)a->samples/a->rate)>.1)goto invalid;
    frame_bytes=(size_t)a->xres*a->yres*2;
    expected=32+(long)frame_bytes*a->frames+a->samples;
    if(fseek(a->video,0,SEEK_END) || (length=ftell(a->video))!=expected)goto invalid;
    if(load_audio) {
        a->audio=fopen(filename,"rb");
        if(!a->audio || fseek(a->audio,32+(long)frame_bytes*a->frames,SEEK_SET))goto invalid;
    }
    a->packed=Mem_Malloc(avi_mempool,frame_bytes);
    a->dst=Mem_Malloc(avi_mempool,frame_bytes*2);
    a->w=a->h=-1;a->last_frame=-1;a->volume=255;a->entnum=S_RAW_SOUND_SOUNDTRACK;
    a->active=true;return;
invalid:
    if(!quiet)Con_Printf(S_WARN "Invalid Nano intro: %s\n",filename);
    AVI_CloseVideo(a);
}

int AVI_GetVideoFrameNumber(movie_state_t *a,float time) {
    return a && a->active?bound(0,(int)(Q_max(0,time)*a->fps),a->frames-1):0;
}
byte *AVI_GetVideoFrame(movie_state_t *a,int frame) {
    size_t pixels;
    if(!a || !a->active || frame<0 || frame>=a->frames)return NULL;
    pixels=(size_t)a->xres*a->yres;
    if(frame!=a->last_frame) {
        if(fseek(a->video,32+(long)pixels*2*frame,SEEK_SET) || fread(a->packed,2,pixels,a->video)!=pixels)
            return NULL;
        for(size_t i=0;i<pixels;++i) {
            unsigned p=a->packed[i*2] | (unsigned)a->packed[i*2+1]<<8;
            a->dst[i*4]=((p>>11)&31)*255/31;
            a->dst[i*4+1]=((p>>5)&63)*255/63;
            a->dst[i*4+2]=(p&31)*255/31;a->dst[i*4+3]=255;
        }
        a->last_frame=frame;
    }
    return a->dst;
}
qboolean AVI_GetVideoInfo(movie_state_t *a,int *x,int *y,float *duration) {
    if(!a || !a->active)return false;
    if(x)*x=a->xres;
    if(y)*y=a->yres;
    if(duration)*duration=(float)a->frames/a->fps;
    return true;
}
qboolean AVI_HaveAudioTrack(const movie_state_t *a) {return a && a->active && a->audio;}

static void NanoIntroStreamAudio(movie_state_t *a) {
    byte data[4096];rawchan_t *ch;
    if(!a->audio || !snd.initialized || !snd.streaming || a->paused || cl.paused)return;
    ch=S_FindRawChannel(a->entnum,true);if(!ch)return;
    ch->master_vol=a->volume;ch->dist_mult=a->attn/SND_CLIP_DISTANCE;
    if(ch->s_rawend<snd.soundtime)ch->s_rawend=snd.soundtime;
    while(ch->s_rawend<snd.soundtime+ch->max_samples && a->audio_pos<a->samples) {
        int samples=(ch->max_samples-(ch->s_rawend-snd.soundtime))*(double)a->rate/SOUND_DMA_SPEED;
        if(samples<=1)return;
        samples=Q_min(samples,(int)sizeof(data));samples=Q_min(samples,a->samples-a->audio_pos);
        if(fread(data,1,samples,a->audio)!=(size_t)samples) {a->audio_pos=a->samples;return;}
        ch->s_rawend=S_RawSamplesStereo(ch->rawsamples,ch->s_rawend,ch->max_samples,
                                       samples,a->rate,1,1,data);
        a->audio_pos+=samples;
    }
}

qboolean AVI_Think(movie_state_t *a) {
    double elapsed;int frame,previous;rgbdata_t image={0};string name;
    if(!a || !a->active)return false;
    if(!a->started) {a->started=true;a->start=Platform_DoubleTime();}
    if(a->paused) {
        if(a->draw_texture && !a->texture)ref.dllFuncs.R_DrawStretchPic(a->x,a->y,
            a->w<0?refState.width:a->w,a->h<0?refState.height:a->h,0,0,1,1,a->draw_texture);
        return true;
    }
    elapsed=Q_max(0,Platform_DoubleTime()-a->start);
    if(elapsed>=(double)a->frames/a->fps)return false;
    NanoIntroStreamAudio(a);
    frame=AVI_GetVideoFrameNumber(a,elapsed);previous=a->last_frame;
    if(!AVI_GetVideoFrame(a,frame))return false;
    if(previous!=frame || !a->draw_texture) {
        // The software renderer's GL_UpdateTexture is a stub. This API replaces
        // the one owned image safely, with TF_IMAGE preventing needless mipmaps.
        image.width=a->xres;image.height=a->yres;image.type=PF_RGBA_32;
        image.flags=IMAGE_HAS_COLOR;image.size=(size_t)a->xres*a->yres*4;image.buffer=a->dst;
        Q_snprintf(name,sizeof(name),"*nanointro_%p",(void*)a);
        a->draw_texture=ref.dllFuncs.GL_LoadTextureFromBuffer(name,&image,TF_IMAGE,a->draw_texture!=0);
        if(!a->draw_texture)return false;
    }
    if(!a->texture)ref.dllFuncs.R_DrawStretchPic(a->x,a->y,a->w<0?refState.width:a->w,
                                               a->h<0?refState.height:a->h,0,0,1,1,a->draw_texture);
    return true;
}

qboolean AVI_SetParm(movie_state_t *a,enum movie_parms_e parm,...) {
    va_list args;qboolean valid=true;
    if(!a)return false;
    va_start(args,parm);
    while(parm!=AVI_PARM_LAST) {
        switch(parm) {
        case AVI_RENDER_X:a->x=va_arg(args,int);break;
        case AVI_RENDER_Y:a->y=va_arg(args,int);break;
        case AVI_RENDER_W:a->w=va_arg(args,int);break;
        case AVI_RENDER_H:a->h=va_arg(args,int);break;
        case AVI_RENDER_TEXNUM:a->texture=va_arg(args,int);break;
        case AVI_ENTNUM:a->entnum=va_arg(args,int);break;
        case AVI_VOLUME:a->volume=bound(0,va_arg(args,int),255);break;
        case AVI_ATTN:a->attn=va_arg(args,double);break;
        case AVI_REWIND:
            a->started=false;a->audio_pos=0;a->last_frame=-1;
            if(a->audio)fseek(a->audio,32+(long)a->xres*a->yres*2*a->frames,SEEK_SET);
            break;
        case AVI_PAUSE:a->pause_time=Platform_DoubleTime();a->paused=true;break;
        case AVI_RESUME:
            if(a->paused)a->start+=Platform_DoubleTime()-a->pause_time;
            a->paused=false;break;
        default:valid=false;goto done;
        }
        parm=va_arg(args,int);
    }
done:
    va_end(args);return valid;
}
