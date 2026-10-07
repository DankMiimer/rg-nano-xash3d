// SPDX-License-Identifier: MIT
#ifndef NANO_UI_ALPHA_H
#define NANO_UI_ALPHA_H
// Software pixels store RGB332 in the high byte and GBRGBRGB detail below.
// Blend complete colour channels for 2D UI instead of the coarse colour LUT.
static inline unsigned short NanoUIBlend(int alpha,unsigned short src,unsigned short dst) {
    unsigned r1=((src>>11)&28)|((src>>4)&2)|((src>>2)&1);
    unsigned g1=((src>>7)&56)|((src>>5)&4)|((src>>3)&2)|((src>>1)&1);
    unsigned b1=((src>>5)&24)|((src>>4)&4)|((src>>2)&2)|(src&1);
    unsigned r2=((dst>>11)&28)|((dst>>4)&2)|((dst>>2)&1);
    unsigned g2=((dst>>7)&56)|((dst>>5)&4)|((dst>>3)&2)|((dst>>1)&1);
    unsigned b2=((dst>>5)&24)|((dst>>4)&4)|((dst>>2)&2)|(dst&1);
    unsigned r=(r1*alpha+r2*(7-alpha)+3)/7;
    unsigned g=(g1*alpha+g2*(7-alpha)+3)/7;
    unsigned b=(b1*alpha+b2*(7-alpha)+3)/7;
    unsigned major=((r>>2)<<5)|((g>>3)<<2)|(b>>3);
    unsigned minor=((r&2)<<4)|((r&1)<<2)|((g&4)<<5)|((g&2)<<3)|((g&1)<<1)|((b&4)<<4)|((b&2)<<2)|(b&1);
    return (unsigned short)((major<<8)|minor);
}
#endif
