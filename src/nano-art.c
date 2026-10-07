// SPDX-License-Identifier: GPL-3.0-or-later
// First-launch menu artwork. Builds the square menu background, the small logo
// and (for Counter-Strike) the bot-loading sprite from the player's own game
// files, so released builds carry no Valve artwork. Mirrors
// tools/prepare_menu_art.py: Pillow-compatible Lanczos-3 resampling with
// premultiplied alpha, uncompressed bottom-up TGA output, one opaque sprite.
//
// The --icon mode does the same for the launcher icon: release OPKs carry an
// uncompressed placeholder PNG in a fixed-size slot, which is overwritten in
// place with the game's own icon (the image tools/extract_icons.py takes).
//
// usage: nano-art ROOT valve|cstrike
//        nano-art --icon ROOT valve|cstrike OPK
// exit:  0 written, 3 source files not found (nothing written), 2 error
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define MAX_SIDE 8192
#define OUT_SIDE 240
#define PRECISION_BITS (32 - 8 - 2)

typedef struct { int w, h; uint8_t *px; int top; } image_t; // RGBA, top row first; top = source stored top-down

static const char *root;

static void *xcalloc(size_t n, size_t size) {
    void *p = calloc(n, size);
    if (!p) { fprintf(stderr, "nano-art: out of memory\n"); exit(2); }
    return p;
}

static int path_of(char *out, size_t size, const char *game, const char *rel) {
    return snprintf(out, size, "%s/%s/%s", root, game, rel) < (int)size ? 0 : -1;
}

static int exists(const char *game, const char *rel) {
    char path[1024];
    struct stat st;
    return !path_of(path, sizeof(path), game, rel) && !stat(path, &st) && S_ISREG(st.st_mode);
}

static uint8_t *read_all(const char *path, size_t *len) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    uint8_t *data = NULL;
    long size = -1;
    if (!fseek(f, 0, SEEK_END)) size = ftell(f);
    if (size > 0 && size < 64L * 1024 * 1024 && !fseek(f, 0, SEEK_SET)) {
        data = xcalloc(1, (size_t)size);
        if (fread(data, 1, (size_t)size, f) != (size_t)size) { free(data); data = NULL; }
        else *len = (size_t)size;
    }
    fclose(f);
    return data;
}

// Uncompressed and RLE TGA: true colour (24/32), grey (8) and 8-bit colour-mapped.
static int tga_load(const char *game, const char *rel, image_t *img) {
    char path[1024];
    size_t len = 0;
    if (path_of(path, sizeof(path), game, rel)) return -1;
    uint8_t *b = read_all(path, &len);
    if (!b) { fprintf(stderr, "nano-art: cannot read %s\n", path); return -1; }
    int ok = 0;
    if (len >= 18) {
        int idlen = b[0], cmtype = b[1], type = b[2];
        int cmfirst = b[3] | b[4] << 8, cmlen = b[5] | b[6] << 8, cmbits = b[7];
        int w = b[12] | b[13] << 8, h = b[14] | b[15] << 8, bpp = b[16], desc = b[17];
        int base = type & 7, rle = type & 8;
        int pbytes = bpp / 8, cmbytes = (cmbits + 7) / 8;
        size_t pos = 18 + (size_t)idlen;
        const uint8_t *cmap = b + pos;
        if (cmtype) pos += (size_t)cmlen * (size_t)cmbytes;
        int valid = w > 0 && h > 0 && w <= MAX_SIDE && h <= MAX_SIDE && pos <= len &&
            ((base == 2 && (bpp == 24 || bpp == 32)) || (base == 3 && bpp == 8) ||
             (base == 1 && bpp == 8 && cmtype && (cmbits == 24 || cmbits == 32)));
        if (valid) {
            img->w = w; img->h = h; img->top = (desc & 0x20) != 0;
            img->px = xcalloc((size_t)w * h, 4);
            size_t n = (size_t)w * h;
            uint8_t pix[4] = {0};
            // RLE packets: `raw` literal pixels follow, or one pixel repeated `run` times.
            int run = 0, raw = 0, have = 0;
            ok = 1;
            for (size_t i = 0; i < n; i++) {
                if (rle && !run && !raw) {
                    if (pos >= len) { ok = 0; break; }
                    uint8_t c = b[pos++];
                    if (c & 0x80) run = (c & 0x7f) + 1; else raw = c + 1;
                    have = 0;
                }
                if (!rle || raw || !have) {
                    if (pos + (size_t)pbytes > len) { ok = 0; break; }
                    const uint8_t *s = b + pos;
                    pos += (size_t)pbytes;
                    if (base == 2) {
                        pix[0] = s[2]; pix[1] = s[1]; pix[2] = s[0];
                        pix[3] = bpp == 32 ? s[3] : 255;
                    } else if (base == 3) {
                        pix[0] = pix[1] = pix[2] = s[0]; pix[3] = 255;
                    } else {
                        int idx = s[0] - cmfirst;
                        if (idx < 0 || idx >= cmlen) { ok = 0; break; }
                        const uint8_t *c = cmap + (size_t)idx * cmbytes;
                        pix[0] = c[2]; pix[1] = c[1]; pix[2] = c[0];
                        pix[3] = cmbits == 32 ? c[3] : 255;
                    }
                    have = 1;
                }
                if (rle) { if (raw) raw--; else run--; }
                int x = (int)(i % (size_t)w), y = (int)(i / (size_t)w);
                if (!(desc & 0x20)) y = h - 1 - y;
                if (desc & 0x10) x = w - 1 - x;
                memcpy(img->px + ((size_t)y * w + x) * 4, pix, 4);
            }
            if (!ok) { free(img->px); img->px = NULL; }
        }
    }
    free(b);
    if (!ok) fprintf(stderr, "nano-art: unsupported or damaged TGA %s\n", path);
    return ok ? 0 : -1;
}

// FunKey OS's musl libm (SDK and firmware alike) is built so that its exact-rounding
// tricks fail: ceil(7.5) == 7.5, rint/floor likewise, and sin(9) == 1. Nothing here
// calls libm; these local versions cover the ranges this file needs.
#define PI_HI 3.14159265358979311600e+00
#define PI_LO 1.22464679914735317720e-16
static int ceil_int(double x) { // x >= 0
    int i = (int)x;
    return i < x ? i + 1 : i;
}
static int round_even(double x) { // x >= 0; Python round()
    int i = (int)x;
    double frac = x - i;
    return frac > 0.5 || (frac == 0.5 && (i & 1)) ? i + 1 : i;
}
static double sin_local(double x) { // |x| <= 4 pi
    double q = x / PI_HI;
    int k = (int)(q < 0 ? q - 0.5 : q + 0.5);
    double r = (x - k * PI_HI) - k * PI_LO, r2 = r * r, term = r, sum = r;
    for (int n = 1; n <= 11; n++) { term *= -r2 / ((2.0 * n) * (2.0 * n + 1)); sum += term; }
    return k & 1 ? -sum : sum;
}

// ---- Pillow-compatible resampling (Resample.c, 8 bits per channel) ----
static double sinc(double x) {
    if (x == 0.0) return 1.0;
    x *= PI_HI;
    return sin_local(x) / x;
}
static double lanczos(double x) {
    return (-3.0 <= x && x < 3.0) ? sinc(x) * sinc(x / 3.0) : 0.0;
}
static uint8_t clip8(int in) {
    if (in >= (1 << PRECISION_BITS << 8)) return 255;
    if (in <= 0) return 0;
    return (uint8_t)(in >> PRECISION_BITS);
}
typedef struct { int ksize; int *bounds; int *kk; } coeffs_t;
static void coeffs(coeffs_t *c, int in_size, int out_size) {
    double scale = (double)in_size / out_size, filterscale = scale < 1.0 ? 1.0 : scale;
    double support = 3.0 * filterscale;
    c->ksize = ceil_int(support) * 2 + 1;
    c->bounds = xcalloc((size_t)out_size * 2, sizeof(int));
    c->kk = xcalloc((size_t)out_size * c->ksize, sizeof(int));
    double *k = xcalloc((size_t)c->ksize, sizeof(double));
    for (int xx = 0; xx < out_size; xx++) {
        double center = (xx + 0.5) * scale, ww = 0.0, ss = 1.0 / filterscale;
        int xmin = (int)(center - support + 0.5), xmax = (int)(center + support + 0.5);
        if (xmin < 0) xmin = 0;
        if (xmax > in_size) xmax = in_size;
        xmax -= xmin;
        for (int x = 0; x < xmax; x++) { k[x] = lanczos((x + xmin - center + 0.5) * ss); ww += k[x]; }
        for (int x = 0; x < c->ksize; x++) {
            double v = x < xmax && ww != 0.0 ? k[x] / ww : 0.0;
            c->kk[xx * c->ksize + x] = v < 0 ? (int)(-0.5 + v * (1 << PRECISION_BITS)) : (int)(0.5 + v * (1 << PRECISION_BITS));
        }
        c->bounds[xx * 2] = xmin;
        c->bounds[xx * 2 + 1] = xmax;
    }
    free(k);
}
static void premultiply(image_t *img) { // Pillow RGBA -> RGBa
    for (size_t i = 0, n = (size_t)img->w * img->h; i < n; i++) {
        uint8_t *p = img->px + i * 4;
        for (int c = 0; c < 3; c++) { unsigned t = p[c] * p[3] + 128; p[c] = (uint8_t)(((t >> 8) + t) >> 8); }
    }
}
static void unpremultiply(image_t *img) { // Pillow RGBa -> RGBA
    for (size_t i = 0, n = (size_t)img->w * img->h; i < n; i++) {
        uint8_t *p = img->px + i * 4;
        if (p[3] == 255 || p[3] == 0) continue;
        for (int c = 0; c < 3; c++) { int v = 255 * p[c] / p[3]; p[c] = (uint8_t)(v > 255 ? 255 : v); }
    }
}
// Resize the whole image (Pillow: horizontal pass, then vertical, 8-bit intermediate).
static image_t resize(const image_t *in, int ow, int oh) {
    image_t tmp = { ow, in->h, xcalloc((size_t)ow * in->h, 4), 0 }, out = { ow, oh, xcalloc((size_t)ow * oh, 4), in->top };
    coeffs_t hc, vc;
    coeffs(&hc, in->w, ow);
    coeffs(&vc, in->h, oh);
    for (int y = 0; y < in->h; y++)
        for (int x = 0; x < ow; x++) {
            int xmin = hc.bounds[x * 2], xmax = hc.bounds[x * 2 + 1], ss[4];
            const int *k = hc.kk + x * hc.ksize;
            for (int c = 0; c < 4; c++) ss[c] = 1 << (PRECISION_BITS - 1);
            for (int i = 0; i < xmax; i++) {
                const uint8_t *p = in->px + ((size_t)y * in->w + xmin + i) * 4;
                for (int c = 0; c < 4; c++) ss[c] += p[c] * k[i];
            }
            for (int c = 0; c < 4; c++) tmp.px[((size_t)y * ow + x) * 4 + c] = clip8(ss[c]);
        }
    for (int y = 0; y < oh; y++) {
        int ymin = vc.bounds[y * 2], ymax = vc.bounds[y * 2 + 1];
        const int *k = vc.kk + y * vc.ksize;
        for (int x = 0; x < ow; x++) {
            int ss[4];
            for (int c = 0; c < 4; c++) ss[c] = 1 << (PRECISION_BITS - 1);
            for (int i = 0; i < ymax; i++) {
                const uint8_t *p = tmp.px + ((size_t)(ymin + i) * ow + x) * 4;
                for (int c = 0; c < 4; c++) ss[c] += p[c] * k[i];
            }
            for (int c = 0; c < 4; c++) out.px[((size_t)y * ow + x) * 4 + c] = clip8(ss[c]);
        }
    }
    free(hc.bounds); free(hc.kk); free(vc.bounds); free(vc.kk); free(tmp.px);
    return out;
}
static image_t resize_rgba(image_t *in, int ow, int oh) {
    premultiply(in);
    image_t out = resize(in, ow, oh);
    unpremultiply(&out);
    return out;
}

// Python round(): halves go to the even neighbour.
static int round_half_even(long num, long den) {
    long q = num / den, r = num % den;
    if (2 * r > den || (2 * r == den && (q & 1))) q++;
    return (int)q;
}

// ---- output ----
static int mkdirs(const char *game, const char *rel_dir) {
    char path[1024];
    if (path_of(path, sizeof(path), game, rel_dir)) return -1;
    for (char *p = path + strlen(root) + 1; *p; p++)
        if (*p == '/') { *p = 0; if (mkdir(path, 0755) && errno != EEXIST) return -1; *p = '/'; }
    return mkdir(path, 0755) && errno != EEXIST ? -1 : 0;
}
static int write_atomic(const char *game, const char *rel, const uint8_t *data, size_t len) {
    char path[1024], tmp[1100];
    if (path_of(path, sizeof(path), game, rel)) return -1;
    snprintf(tmp, sizeof(tmp), "%s.tmp", path);
    FILE *f = fopen(tmp, "wb");
    if (!f) { perror(tmp); return -1; }
    int ok = fwrite(data, 1, len, f) == len;
    ok = !fflush(f) && !fsync(fileno(f)) && ok;
    ok = !fclose(f) && ok;
    if (!ok || rename(tmp, path)) { perror(path); unlink(tmp); return -1; }
    printf("nano-art: wrote %s/%s\n", game, rel);
    return 0;
}
// Pillow's TGA writer: type 2, the source's row order (bottom-up for new images), alpha bits in
// the descriptor, TRUEVISION footer.
static int save_tga(const char *game, const char *rel, const image_t *img, int alpha) {
    int bpp = alpha ? 4 : 3;
    size_t len = 18 + (size_t)img->w * img->h * bpp + 26;
    uint8_t *out = xcalloc(1, len), *p = out + 18;
    out[2] = 2;
    out[12] = (uint8_t)img->w; out[13] = (uint8_t)(img->w >> 8);
    out[14] = (uint8_t)img->h; out[15] = (uint8_t)(img->h >> 8);
    out[16] = (uint8_t)(bpp * 8);
    out[17] = (alpha ? 8 : 0) | (img->top ? 0x20 : 0);
    for (int row = 0; row < img->h; row++)
        for (int x = 0, y = img->top ? row : img->h - 1 - row; x < img->w; x++) {
            const uint8_t *s = img->px + ((size_t)y * img->w + x) * 4;
            *p++ = s[2]; *p++ = s[1]; *p++ = s[0];
            if (alpha) *p++ = s[3];
        }
    memcpy(p + 8, "TRUEVISION-XFILE.", 17);
    int rc = write_atomic(game, rel, out, len);
    free(out);
    return rc;
}

// Pillow Image.alpha_composite (AlphaComposite.c) for one source over a destination.
static void alpha_composite(image_t *dst, const image_t *src, int ox, int oy) {
    for (int y = 0; y < src->h; y++)
        for (int x = 0; x < src->w; x++) {
            int dx = ox + x, dy = oy + y;
            if (dx < 0 || dy < 0 || dx >= dst->w || dy >= dst->h) continue;
            const uint8_t *s = src->px + ((size_t)y * src->w + x) * 4;
            uint8_t *d = dst->px + ((size_t)dy * dst->w + dx) * 4;
            if (s[3] == 0) continue;
            uint32_t blend = d[3] * (255u - s[3]), outa255 = s[3] * 255u + blend;
            uint32_t coef1 = s[3] * 255u * 255u * (1u << 7) / outa255, coef2 = 255u * (1u << 7) - coef1;
            for (int c = 0; c < 3; c++) {
                uint32_t t = s[c] * coef1 + d[c] * coef2 + (0x80u << 7);
                d[c] = (uint8_t)(((((t >> 8) + t) >> 8)) >> 7);
            }
            uint32_t a = outa255 + 0x80;
            d[3] = (uint8_t)(((a >> 8) + a) >> 8);
        }
}

// Median-cut palette: split the box with the widest channel range at its median.
typedef struct { int start, count; } box_t;
static int axis_of(const uint8_t (*c)[3], const int *idx, const box_t *b, int *range) {
    int lo[3] = {255, 255, 255}, hi[3] = {0, 0, 0};
    for (int i = b->start; i < b->start + b->count; i++)
        for (int k = 0; k < 3; k++) {
            int v = c[idx[i]][k];
            if (v < lo[k]) lo[k] = v;
            if (v > hi[k]) hi[k] = v;
        }
    int best = 0;
    for (int k = 1; k < 3; k++) if (hi[k] - lo[k] > hi[best] - lo[best]) best = k;
    *range = hi[best] - lo[best];
    return best;
}
static const uint8_t (*sort_colors)[3];
static int sort_axis;
static int by_axis(const void *a, const void *b) {
    return sort_colors[*(const int *)a][sort_axis] - sort_colors[*(const int *)b][sort_axis];
}
static void quantize(const image_t *img, uint8_t palette[768], uint8_t *indices) {
    int n = img->w * img->h, boxes = 1;
    uint8_t (*c)[3] = xcalloc((size_t)n, 3);
    int *idx = xcalloc((size_t)n, sizeof(int));
    box_t box[256] = {{0, n}};
    for (int i = 0; i < n; i++) { memcpy(c[i], img->px + (size_t)i * 4, 3); idx[i] = i; }
    while (boxes < 256) {
        int pick = -1, pick_range = 0, pick_axis = 0;
        for (int b = 0; b < boxes; b++) {
            int range, axis = axis_of((const uint8_t (*)[3])c, idx, &box[b], &range);
            if (box[b].count > 1 && range > pick_range) { pick = b; pick_range = range; pick_axis = axis; }
        }
        if (pick < 0) break;
        sort_colors = (const uint8_t (*)[3])c; sort_axis = pick_axis;
        qsort(idx + box[pick].start, (size_t)box[pick].count, sizeof(int), by_axis);
        int half = box[pick].count / 2;
        box[boxes].start = box[pick].start + half;
        box[boxes].count = box[pick].count - half;
        box[pick].count = half;
        boxes++;
    }
    memset(palette, 0, 768);
    for (int b = 0; b < boxes; b++) {
        long sum[3] = {0, 0, 0};
        for (int i = box[b].start; i < box[b].start + box[b].count; i++)
            for (int k = 0; k < 3; k++) sum[k] += c[idx[i]][k];
        for (int k = 0; k < 3; k++) palette[b * 3 + k] = (uint8_t)((sum[k] + box[b].count / 2) / box[b].count);
    }
    for (int i = 0; i < n; i++) {
        int best = 0;
        long best_d = -1;
        for (int b = 0; b < boxes; b++) {
            long d = 0;
            for (int k = 0; k < 3; k++) { long e = (long)c[i][k] - palette[b * 3 + k]; d += e * e; }
            if (best_d < 0 || d < best_d) { best_d = d; best = b; }
        }
        indices[i] = (uint8_t)best;
    }
    free(c); free(idx);
}
static void put32(uint8_t **p, uint32_t v) { for (int i = 0; i < 4; i++) *(*p)++ = (uint8_t)(v >> (8 * i)); }
static void putf(uint8_t **p, float f) { uint32_t v; memcpy(&v, &f, 4); put32(p, v); }
// One opaque GoldSrc v2 sprite frame (same layout as prepare_menu_art.py).
static int save_sprite(const char *game, const char *rel, const image_t *img) {
    size_t n = (size_t)img->w * img->h, len = 40 + 2 + 768 + 20 + n;
    uint8_t *out = xcalloc(1, len), *p = out;
    memcpy(p, "IDSP", 4); p += 4;
    put32(&p, 2); put32(&p, 2); put32(&p, 0); putf(&p, 170.0f);
    put32(&p, (uint32_t)img->w); put32(&p, (uint32_t)img->h); put32(&p, 1); putf(&p, 0.0f); put32(&p, 0);
    *p++ = 0; *p++ = 1; // 256 palette entries
    quantize(img, p, p + 768 + 20);
    p += 768;
    put32(&p, 0); put32(&p, 0); put32(&p, 0); put32(&p, (uint32_t)img->w); put32(&p, (uint32_t)img->h);
    int rc = write_atomic(game, rel, out, len);
    free(out);
    return rc;
}

// Paste a tile into the crop canvas (canvas origin = crop origin).
static void paste(image_t *canvas, const image_t *tile, int x, int y) {
    for (int ty = 0; ty < tile->h; ty++) {
        int cy = y + ty;
        if (cy < 0 || cy >= canvas->h) continue;
        for (int tx = 0; tx < tile->w; tx++) {
            int cx = x + tx;
            if (cx < 0 || cx >= canvas->w) continue;
            memcpy(canvas->px + ((size_t)cy * canvas->w + cx) * 4, tile->px + ((size_t)ty * tile->w + tx) * 4, 4);
        }
    }
}

typedef struct { char name[256]; int x, y; } tile_t;

// Build the square background: only the cropped region of the layout is assembled.
static int background(const char *game, const tile_t *tiles, int count, int lw, int lh, double position, image_t *out) {
    int side = lw < lh ? lw : lh;
    int cx = round_even((lw - side) * position);
    int cy = (lh - side) / 2;
    image_t canvas = { side, side, xcalloc((size_t)side * side, 4), 0 };
    for (int i = 0; i < count; i++) {
        image_t tile;
        if (tga_load(game, tiles[i].name, &tile)) { free(canvas.px); return -1; }
        paste(&canvas, &tile, tiles[i].x - cx, tiles[i].y - cy);
        free(tile.px);
    }
    *out = resize_rgba(&canvas, OUT_SIDE, OUT_SIDE);
    free(canvas.px);
    for (size_t i = 0, n = (size_t)OUT_SIDE * OUT_SIDE; i < n; i++) out->px[i * 4 + 3] = 255; // convert('RGB')
    return 0;
}

static int logo(const char *game, const char *rel, int width, image_t *out) {
    image_t src;
    if (tga_load(game, rel, &src)) return -1;
    int h = round_half_even((long)src.h * width, src.w);
    *out = resize_rgba(&src, width, h < 1 ? 1 : h);
    free(src.px);
    return 0;
}

static int read_layout(const char *game, const char *rel, tile_t **tiles, int *count, int *w, int *h) {
    char path[1024], line[512];
    if (path_of(path, sizeof(path), game, rel)) return -1;
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    int cap = 0, first = 1;
    *count = 0; *w = *h = 0; *tiles = NULL;
    while (fgets(line, sizeof(line), f)) {
        char a[256], b[64];
        int x, y;
        if (first) {
            if (sscanf(line, "%255s %d %d", a, &x, &y) == 3) { *w = x; *h = y; first = 0; }
            continue;
        }
        if (sscanf(line, "%255s %63s %d %d", a, b, &x, &y) != 4) continue;
        if (*count == cap) {
            cap = cap ? cap * 2 : 64;
            tile_t *grown = realloc(*tiles, (size_t)cap * sizeof(tile_t));
            if (!grown) { fclose(f); return -1; }
            *tiles = grown;
        }
        snprintf((*tiles)[*count].name, sizeof((*tiles)[*count].name), "%s", a);
        (*tiles)[*count].x = x; (*tiles)[*count].y = y;
        (*count)++;
    }
    fclose(f);
    return *w > 0 && *h > 0 && *w <= MAX_SIDE && *h <= MAX_SIDE && *count > 0 ? 0 : -1;
}

// ---- launcher icon ----
// Slot layout shared with tools/make_icons.py: PNG signature, IHDR, an "npAd" chunk
// whose data starts with the marker, IDAT, IEND; exactly ICON_SLOT bytes in total.
#define ICON_SLOT 8192
#define SLOT_MARKER "NANO-ICON-SLOT:"
#define SET_MARKER "NANO-ICON-SET:"

static uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | p[1] << 8); }
static uint32_t le32(const uint8_t *p) { return p[0] | p[1] << 8 | p[2] << 16 | (uint32_t)p[3] << 24; }
static void be32(uint8_t *p, uint32_t v) { p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16); p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v; }

// Pillow's ICO choice: the largest size, then the lowest colour depth, then file order;
// BMP entries take alpha from the AND mask unless the directory says 32 bpp.
static int ico_load(const char *game, image_t *img) {
    char path[1024];
    size_t len = 0;
    if (path_of(path, sizeof(path), game, "game.ico")) return -1;
    uint8_t *b = read_all(path, &len);
    if (!b) return -1;
    int ok = 0, pick = -1;
    long best_area = 0;
    int best_depth = 0;
    int n = len >= 6 && le16(b) == 0 && le16(b + 2) == 1 ? le16(b + 4) : 0;
    if ((size_t)6 + (size_t)n * 16 > len) n = 0;
    for (int i = 0; i < n; i++) {
        const uint8_t *e = b + 6 + i * 16;
        int w = e[0] ? e[0] : 256, h = e[1] ? e[1] : 256, bpp = le16(e + 6);
        int depth = 256; // Pillow: bpp, else ceil(log2(colours)), else 256
        if (bpp) depth = bpp;
        else if (e[2] > 1) for (depth = 0; (1 << depth) < e[2]; depth++) {}
        if (w * h > best_area || (w * h == best_area && depth < best_depth)) { pick = i; best_area = w * h; best_depth = depth; }
    }
    if (pick >= 0) {
        const uint8_t *e = b + 6 + pick * 16;
        uint32_t size = le32(e + 8), off = le32(e + 12);
        const uint8_t *d = b + off;
        if (off + 40 <= len && size <= len - off && le32(d) >= 40 && le32(d + 16) == 0) {
            int w = (int)le32(d + 4), h = (int)le32(d + 8) / 2, bits = le16(d + 14);
            uint32_t colors = bits <= 8 ? (le32(d + 32) ? le32(d + 32) : 1u << bits) : 0;
            size_t stride = ((size_t)w * bits + 31) / 32 * 4, mask_stride = ((size_t)w + 31) / 32 * 4;
            size_t pal = off + le32(d), pix = pal + colors * 4, mask = off + size - mask_stride * h;
            int valid = w > 0 && h > 0 && w <= 256 && h <= 256 && (bits == 1 || bits == 4 || bits == 8 || bits == 24 || bits == 32) &&
                colors <= 256 && mask_stride * h <= size && pix + stride * h <= off + size && mask >= pix + stride * h;
            if (valid) {
                img->w = w; img->h = h; img->top = 0;
                img->px = xcalloc((size_t)w * h, 4);
                for (int y = 0; y < h; y++) {
                    const uint8_t *row = b + pix + (size_t)(h - 1 - y) * stride, *mrow = b + mask + (size_t)(h - 1 - y) * mask_stride;
                    for (int x = 0; x < w; x++) {
                        uint8_t *o = img->px + ((size_t)y * w + x) * 4;
                        if (bits <= 8) {
                            unsigned idx = bits == 8 ? row[x] : bits == 4 ? (row[x / 2] >> (x & 1 ? 0 : 4)) & 15 : (row[x / 8] >> (7 - x % 8)) & 1;
                            const uint8_t *c = idx < colors ? b + pal + idx * 4 : (const uint8_t *)"\0\0\0\0";
                            o[0] = c[2]; o[1] = c[1]; o[2] = c[0];
                        } else {
                            const uint8_t *c = row + (size_t)x * (bits / 8);
                            o[0] = c[2]; o[1] = c[1]; o[2] = c[0];
                        }
                        if (le16(e + 6) == 32 && bits == 32) o[3] = row[(size_t)x * 4 + 3];
                        else o[3] = (mrow[x / 8] >> (7 - x % 8)) & 1 ? 0 : 255;
                    }
                }
                ok = 1;
            }
        }
    }
    free(b);
    if (!ok) fprintf(stderr, "nano-art: %s/game.ico has no supported icon\n", game);
    return ok ? 0 : -1;
}

static uint32_t crc_update(uint32_t c, const uint8_t *p, size_t n) {
    static uint32_t table[256];
    if (!table[1])
        for (uint32_t i = 0; i < 256; i++) {
            uint32_t v = i;
            for (int k = 0; k < 8; k++) v = v & 1 ? 0xedb88320u ^ (v >> 1) : v >> 1;
            table[i] = v;
        }
    for (size_t i = 0; i < n; i++) c = table[(c ^ p[i]) & 255] ^ (c >> 8);
    return c;
}
static uint8_t *chunk(uint8_t *p, const char *type, const uint8_t *data, size_t len) {
    be32(p, (uint32_t)len);
    memcpy(p + 4, type, 4);
    if (len && data != p + 8) memmove(p + 8, data, len);
    be32(p + 8 + len, crc_update(0xffffffffu, p + 4, len + 4) ^ 0xffffffffu);
    return p + 12 + len;
}
// RGBA PNG with stored (uncompressed) deflate blocks, padded to exactly ICON_SLOT bytes.
static int icon_png(const image_t *img, const char *marker, uint8_t *out) {
    size_t raw_len = (size_t)img->h * (1 + (size_t)img->w * 4);
    size_t blocks = (raw_len + 65534) / 65535, zlen = 2 + raw_len + blocks * 5 + 4;
    size_t used = 8 + 25 + 12 + 12 + zlen + 12, mlen = strlen(marker) + 1;
    if (used + mlen > ICON_SLOT) return -1;
    uint8_t *raw = xcalloc(1, raw_len), *z = xcalloc(1, zlen), *p = out;
    for (int y = 0; y < img->h; y++) memcpy(raw + (size_t)y * (1 + img->w * 4) + 1, img->px + (size_t)y * img->w * 4, (size_t)img->w * 4);
    uint32_t a = 1, s = 0;
    for (size_t i = 0; i < raw_len; i++) { a = (a + raw[i]) % 65521; s = (s + a) % 65521; }
    uint8_t *q = z;
    *q++ = 0x78; *q++ = 0x01;
    for (size_t done = 0; done < raw_len;) {
        size_t n = raw_len - done > 65535 ? 65535 : raw_len - done;
        *q++ = done + n == raw_len;
        *q++ = (uint8_t)n; *q++ = (uint8_t)(n >> 8); *q++ = (uint8_t)~n; *q++ = (uint8_t)(~n >> 8);
        memcpy(q, raw + done, n); q += n; done += n;
    }
    be32(q, s << 16 | a);
    memset(out, 0, ICON_SLOT);
    memcpy(p, "\x89PNG\r\n\x1a\n", 8); p += 8;
    uint8_t ihdr[13] = {0};
    be32(ihdr, (uint32_t)img->w); be32(ihdr + 4, (uint32_t)img->h);
    ihdr[8] = 8; ihdr[9] = 6;
    p = chunk(p, "IHDR", ihdr, 13);
    size_t pad = ICON_SLOT - used;
    memcpy(p + 8, marker, mlen - 1);
    p = chunk(p, "npAd", p + 8, pad);
    p = chunk(p, "IDAT", z, zlen);
    p = chunk(p, "IEND", NULL, 0);
    free(raw); free(z);
    return p == out + ICON_SLOT ? 0 : -1;
}
static int write_whole(const char *path, const uint8_t *data, size_t len) {
    char tmp[1100];
    snprintf(tmp, sizeof(tmp), "%s.tmp", path);
    FILE *f = fopen(tmp, "wb");
    if (!f) return -1;
    int ok = fwrite(data, 1, len, f) == len;
    ok = !fflush(f) && !fsync(fileno(f)) && ok;
    ok = !fclose(f) && ok;
    if (!ok || rename(tmp, path)) { unlink(tmp); return -1; }
    return 0;
}
// Replace this game's placeholder in its launcher OPK and the box art beside it.
static int icon_main(const char *game, const char *opk) {
    char slot[64], set[64];
    snprintf(slot, sizeof(slot), "npAd" SLOT_MARKER "%s", game);
    snprintf(set, sizeof(set), SET_MARKER "%s", game);
    struct stat st;
    if (stat(opk, &st) || !S_ISREG(st.st_mode) || st.st_size > 1024 * 1024) return 3;
    size_t len = 0;
    uint8_t *b = read_all(opk, &len);
    if (!b) return 3;
    size_t at = 0, found = 0;
    if (len >= 4 && !memcmp(b, "hsqs", 4))
        for (uint8_t *p = b; (p = memmem(p, len - (size_t)(p - b), slot, strlen(slot))); p++) { at = (size_t)(p - b); found++; }
    if (found != 1 || at < 37 || at - 37 + ICON_SLOT > len || memcmp(b + at - 37, "\x89PNG\r\n\x1a\n", 8)) {
        free(b);
        return 3; // already set, or not a release OPK
    }
    size_t start = at - 37;
    free(b);
    image_t icon;
    if (ico_load(game, &icon)) return 3;
    uint8_t png[ICON_SLOT];
    int rc = icon_png(&icon, set, png);
    free(icon.px);
    if (rc) return 2;
    int fd = open(opk, O_WRONLY);
    if (fd < 0 || pwrite(fd, png, ICON_SLOT, (off_t)start) != ICON_SLOT || fsync(fd)) { perror(opk); if (fd >= 0) close(fd); return 2; }
    close(fd);
    printf("nano-art: launcher icon set in %s\n", opk);
    // RetroFE shows NAME.png beside NAME.opk; replace only our own placeholder.
    char side[1024];
    size_t base = strlen(opk) > 4 && !strcmp(opk + strlen(opk) - 4, ".opk") ? strlen(opk) - 4 : 0;
    if (base && base + 5 < sizeof(side)) {
        memcpy(side, opk, base); strcpy(side + base, ".png");
        size_t old_len = 0;
        uint8_t *old = read_all(side, &old_len);
        int ours = !old || memmem(old, old_len, slot, strlen(slot)) != NULL;
        free(old);
        if (ours && !write_whole(side, png, ICON_SLOT)) printf("nano-art: box art written to %s\n", side);
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 5 && !strcmp(argv[1], "--icon") && (!strcmp(argv[3], "valve") || !strcmp(argv[3], "cstrike"))) {
        root = argv[2];
        return icon_main(argv[3], argv[4]);
    }
    if (argc != 3 || (strcmp(argv[2], "valve") && strcmp(argv[2], "cstrike"))) {
        fprintf(stderr, "usage: %s ROOT valve|cstrike\n       %s --icon ROOT valve|cstrike OPK\n", argv[0], argv[0]);
        return 2;
    }
    root = argv[1];
    const char *game = argv[2];
    tile_t *tiles = NULL;
    int count = 0, lw = 0, lh = 0, logo_width;
    double position;
    const char *logo_rel;
    if (!strcmp(game, "valve")) {
        const char *layout = exists(game, "resource/HD_BackgroundLayout.txt") ? "resource/HD_BackgroundLayout.txt" : "resource/BackgroundLayout.txt";
        if (!exists(game, layout) || !exists(game, "resource/logo.tga")) { puts("nano-art: Half-Life menu artwork sources not found"); return 3; }
        if (read_layout(game, layout, &tiles, &count, &lw, &lh)) { fprintf(stderr, "nano-art: unreadable %s\n", layout); return 2; }
        position = 0.60; logo_rel = "resource/logo.tga"; logo_width = 154;
    } else {
        lw = 800; lh = 600; count = 12;
        tiles = xcalloc((size_t)count, sizeof(tile_t));
        for (int row = 1, i = 0; row <= 3; row++)
            for (int col = 0; col < 4; col++, i++) {
                snprintf(tiles[i].name, sizeof(tiles[i].name), "resource/background/800_%d_%c_loading.tga", row, 'a' + col);
                tiles[i].x = col * 256; tiles[i].y = (row - 1) * 256;
            }
        position = 1.0; logo_rel = "resource/game_menu.tga"; logo_width = 156;
    }
    for (int i = 0; i < count; i++)
        if (!exists(game, tiles[i].name)) { printf("nano-art: %s not found; menus keep their plain background\n", tiles[i].name); free(tiles); return 3; }
    if (!exists(game, logo_rel)) { printf("nano-art: %s not found\n", logo_rel); free(tiles); return 3; }

    image_t bg, lg;
    if (background(game, tiles, count, lw, lh, position, &bg)) { free(tiles); return 2; }
    free(tiles);
    if (logo(game, logo_rel, logo_width, &lg)) { free(bg.px); return 2; }
    int rc = mkdirs(game, "gfx/nano") ? 2 : 0;
    // The background is written last: the launcher treats it as "artwork complete".
    if (!rc && save_tga(game, "gfx/nano/menu_logo.tga", &lg, 1)) rc = 2;
    if (!rc && !strcmp(game, "cstrike")) {
        image_t loading = { OUT_SIDE, OUT_SIDE, xcalloc((size_t)OUT_SIDE * OUT_SIDE, 4), 0 };
        memcpy(loading.px, bg.px, (size_t)OUT_SIDE * OUT_SIDE * 4);
        alpha_composite(&loading, &lg, 14, OUT_SIDE - lg.h - 10);
        if (mkdirs(game, "sprites") || save_sprite(game, "sprites/nano_menu_background.spr", &loading)) rc = 2;
        free(loading.px);
    }
    if (!rc && save_tga(game, "gfx/nano/menu_background.tga", &bg, 0)) rc = 2;
    free(bg.px); free(lg.px);
    return rc;
}
