// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_MENU_LAYOUT_H
#define NANO_MENU_LAYOUT_H
static inline bool NanoMenuEnabled() {
    return ScreenWidth<=320 && EngFuncs::GetCvarFloat("nano_hud_profile");
}
static inline void NanoMenuRect(CMenuBaseItem &item,int x,int y,int w,int h) {
    Point pos((int)ceilf(x/uiStatic.scaleX),(int)ceilf(y/uiStatic.scaleY));
    Size size((int)ceilf(w/uiStatic.scaleX),(int)ceilf(h/uiStatic.scaleY));
    if(item.pos.x==pos.x && item.pos.y==pos.y && item.size.w==size.w && item.size.h==size.h) {
        // The parent's viewport can move while this child's local rectangle stays fixed.
        item.CalcPosition();item.CalcSizes();return;
    }
    item.pos=pos;item.size=size;item.VidInit();
}
static inline int NanoMenuRowHeight(int kind,int height) {
    if(kind==CMenuBaseItem::NANO_ROW_GROUP) return height-88;
    if(kind==CMenuBaseItem::NANO_ROW_TABLE) return height-88;
    if(kind==CMenuBaseItem::NANO_ROW_TABS) return height-40;
    if(kind==CMenuBaseItem::NANO_ROW_SLIDER || kind==CMenuBaseItem::NANO_ROW_SPIN ||
       kind==CMenuBaseItem::NANO_ROW_FIELD || kind==CMenuBaseItem::NANO_ROW_DROP) return 42;
    if(kind==CMenuBaseItem::NANO_ROW_PREVIEW) return 64;
    return 24;
}
static inline void NanoMenuFit(HFont font,const char *source,char *dest,size_t capacity,int width,int pixels) {
    if(!capacity)return;
    if(!source)source="";
    size_t n=strlen(source);if(n>=capacity){n=capacity-1;while(n && ((unsigned char)source[n]&0xc0)==0x80)--n;}
    memcpy(dest,source,n);dest[n]=0;
    if(g_FontMgr->GetTextWideScaled(font,dest,pixels)<=width)return;
    int dots=g_FontMgr->GetTextWideScaled(font,"...",pixels);if(width<dots){dest[0]=0;return;}
    while(n && g_FontMgr->GetTextWideScaled(font,dest,pixels)>width-dots){do --n;while(n && ((unsigned char)dest[n]&0xc0)==0x80);dest[n]=0;}
    if(n+3<capacity)strcat(dest,"...");
}
static inline void NanoMenuWrap(HFont font,const char *source,char *dest,size_t capacity,int width,int pixels) {
    if(!source) source="";
    size_t used=0,lineStart=0,lastSpace=0;
    for(const char *p=source;*p && used+1<capacity;++p) {
        dest[used++]=*p;dest[used]=0;
        if(*p=='\n') {lineStart=used;lastSpace=0;continue;}
        if(*p==' ') lastSpace=used-1;
        if(((unsigned char)p[1]&0xc0)==0x80) continue;
        if(g_FontMgr->GetTextWideScaled(font,dest+lineStart,pixels)>width) {
            if(lastSpace>lineStart) {dest[lastSpace]='\n';lineStart=lastSpace+1;lastSpace=0;}
            else if(used>lineStart+1 && used+1<capacity) {
                size_t start=used-1;while(start>lineStart && ((unsigned char)dest[start]&0xc0)==0x80) --start;
                memmove(dest+start+1,dest+start,used-start);dest[start]='\n';++used;dest[used]=0;lineStart=start+1;
            }
        }
    }
    dest[used]=0;
}
// Place children in their parent's native viewport; decorations retain legacy coordinates.
template<class Holder> static inline void NanoMenuArrangeRows(Holder &menu,int width,int height,int &nanoScroll,int inset=8,CMenuBaseItem *decoration=nullptr,int topInset=-1) {
    if(topInset<0)topInset=inset;
    int viewport=Q_max(1,(int)height-topInset-inset);
    CMenuBaseItem *rows[128];int heights[128],count=0,total=0,focusTop=-1,focusHeight=0;
    for(int i=0;i<menu.ItemCount() && count<128;++i) {
        CMenuBaseItem *item=menu.GetItemByIndex(i);
        if(item==decoration || !item->IsVisible())continue;
        int kind=item->NanoRowType();
        if(kind==CMenuBaseItem::NANO_ROW_NONE)continue;
        item->iFlags&=~QMF_NOTIFY;item->SetNanoFont();
        int rowHeight=Q_min(NanoMenuRowHeight(kind,height),viewport);
        if(item->szName && kind!=CMenuBaseItem::NANO_ROW_TABLE && kind!=CMenuBaseItem::NANO_ROW_TABS && kind!=CMenuBaseItem::NANO_ROW_PREVIEW && kind!=CMenuBaseItem::NANO_ROW_GROUP) {
            if(item->szName!=item->nanoLabel)item->nanoLabelSource=item->szName;
            NanoMenuWrap(item->font,item->nanoLabelSource,item->nanoLabel,sizeof(item->nanoLabel),width-40,12);
            item->szName=item->nanoLabel;
            for(const char *p=item->nanoLabel;*p;++p)if(*p=='\n')rowHeight+=14;
        }
        if(item==menu.ItemAtCursor()){focusTop=total;focusHeight=rowHeight;}
        rows[count]=item;heights[count++]=rowHeight;total+=rowHeight;
    }
    if(focusTop<0) {
        int top=0;
        for(int i=0;i<count;++i) {
            if(!(rows[i]->iFlags&(QMF_INACTIVE|QMF_GRAYED))) {
                menu.SetCursorToItem(*rows[i]);focusTop=top;focusHeight=heights[i];break;
            }
            top+=heights[i];
        }
    }
    if(focusTop>=0) {
        if(focusTop<nanoScroll)nanoScroll=focusTop;
        if(focusTop+focusHeight>nanoScroll+viewport)nanoScroll=focusTop+focusHeight-viewport;
    }
    nanoScroll=bound(0,nanoScroll,Q_max(0,total-viewport));
    int top=topInset-nanoScroll;
    for(int i=0;i<count;++i) {
        CMenuBaseItem *item=rows[i];int kind=item->NanoRowType();
        bool labelAbove=kind==CMenuBaseItem::NANO_ROW_SLIDER || kind==CMenuBaseItem::NANO_ROW_SPIN || kind==CMenuBaseItem::NANO_ROW_FIELD || kind==CMenuBaseItem::NANO_ROW_DROP;
        bool check=kind==CMenuBaseItem::NANO_ROW_CHECK;
        bool visible=top>=topInset && top+heights[i]<=height-inset;
        if(visible)item->iFlags&=~QMF_HIDDENBYPARENT;else item->iFlags|=QMF_HIDDENBYPARENT;
        int y=visible?top+(labelAbove?heights[i]-24:0):inset;
        int rowWidth=check?14:width-20;
        int rowHeight=check?14:labelAbove?18:heights[i]-4;
        NanoMenuRect(*item,10,y,rowWidth,rowHeight);
        item->SetNanoFont();
        top+=heights[i];
    }
}
// A preview owns its label and an aspect-correct content rectangle within its row.
// Restore cached geometry after drawing so placement never accumulates scaling.
class NanoMenuPreviewFrame {
    Point &position;Size &size;Point originalPosition;Size originalSize;
public:
    NanoMenuPreviewFrame(Point &p,Size &s,Size image,HFont font,const char *label):
        position(p),size(s),originalPosition(p),originalSize(s) {
        if(!NanoMenuEnabled())return;
        int labelHeight=label && *label?16:0;
        if(labelHeight){char fitted[256];NanoMenuFit(font,label,fitted,sizeof(fitted),s.w,12);
            UI_DrawString(font,p.x,p.y,s.w,14,fitted,uiColorHelp,12,QM_LEFT,ETF_SHADOW|ETF_FORCECOL);}
        int w=s.w,h=Q_max(1,s.h-labelHeight);
        if(image.w>0 && image.h>0){w=Q_min(w,h*image.w/image.h);h=Q_max(1,w*image.h/image.w);}
        p.x+=(s.w-w)/2;p.y+=labelHeight;s=Size(w,h);
    }
    ~NanoMenuPreviewFrame(){position=originalPosition;size=originalSize;}
};
#endif
