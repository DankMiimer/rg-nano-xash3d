// SPDX-License-Identifier: MIT
#ifndef NANO_HUD_LAYOUT_H
#define NANO_HUD_LAYOUT_H
#include <math.h>
#include <string.h>
static inline bool NanoHudActive() { return gEngfuncs.pfnGetCvarFloat("nano_hud_profile")!=0; }
static inline int NanoHudTextHeight() {
    int h=(int)gEngfuncs.pfnGetCvarFloat("nano_hud_text_height");return h>=12 && h<=18 ? h : 14;
}
static inline int NanoHudTopEnd() {
    float bottom=gEngfuncs.pfnGetCvarFloat("nano_hud_bottom"),side=gEngfuncs.pfnGetCvarFloat("nano_hud_side");
    return (int)ceilf(12+25*bottom+50*side);
}
typedef int (*NanoTextWidth)(const char *);
static inline void NanoHudFit(const char *source,char *out,size_t capacity,int width,NanoTextWidth measure) {
    if(!capacity)return;
    if(!source)source="";
    size_t n=strlen(source);if(n>=capacity){n=capacity-1;while(n && ((unsigned char)source[n]&0xc0)==0x80)--n;}
    memcpy(out,source,n);out[n]=0;
    if(measure(out)<=width)return;
    int space=measure("...");if(width<space){out[0]=0;return;}
    while(n && measure(out)>width-space) {
        do --n;while(n && ((unsigned char)out[n]&0xc0)==0x80);out[n]=0;
    }
    if(n+3<capacity)strcat(out,"...");
}
static inline int NanoHudColorCode(const char *p) {
    if((*p=='\\' && p[1] && strchr("ywrd",p[1])) || (*p=='^' && p[1]>='0' && p[1]<='9'))return 2;
    return *p==1 || *p==3 || *p==4 ? 1 : 0;
}
static inline int NanoHudWrap(const char *source,char lines[][1024],int limit,int width,NanoTextWidth measure) {
    if(limit<=0)return 0;
    if(!source)source="";
    int row=0,used=0,lastSpace=-1;lines[0][0]=0;
    for(const char *p=source;*p && row<limit;++p) {
        if(*p=='\n') {lines[row][used]=0;if(++row>=limit)break;used=0;lastSpace=-1;lines[row][0]=0;continue;}
        if(used>=1020)break;
        lines[row][used++]=*p;lines[row][used]=0;
        if(*p==' ')lastSpace=used-1;
        if(((unsigned char)p[1]&0xc0)==0x80)continue;
        if(NanoHudColorCode(p)==2)continue;
        if(measure(lines[row])>width && row+1<limit) {
            if(lastSpace>=0) {
                strcpy(lines[row+1],lines[row]+lastSpace+1);lines[row][lastSpace]=0;++row;used=strlen(lines[row]);
            } else {
                int start=used-1;while(start && ((unsigned char)lines[row][start]&0xc0)==0x80)--start;
                strcpy(lines[row+1],lines[row]+start);lines[row][start]=0;++row;used=strlen(lines[row]);
            }
            lastSpace=-1;
        }
    }
    int count=row<limit?row+1:limit;
    // Each separately drawn row inherits the preceding row's colour.
    char color[3]={0,0,0};int colorSize=0;
    for(int i=0;i<count;i++) {
        if(i && colorSize) {
            size_t n=strlen(lines[i]);
            if(n+colorSize<1024){memmove(lines[i]+colorSize,lines[i],n+1);memcpy(lines[i],color,colorSize);}
        }
        for(const char *p=lines[i];*p;p++) {
            int size=NanoHudColorCode(p);
            if(size){memcpy(color,p,size);colorSize=size;p+=size-1;}
        }
    }
    NanoHudFit(lines[count-1],lines[count-1],1024,width,measure);
    return count;
}
#endif
