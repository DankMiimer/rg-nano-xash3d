/* SPDX-License-Identifier: MIT */
#ifndef NANO_TEXTURE_SHARE_H
#define NANO_TEXTURE_SHARE_H

#include <stdint.h>
#include <stddef.h>
#include <string.h>

/* Buffers are immutable after Intern. Reuploads release their references and
 * build fresh buffers. Texture dimensions, flags and source images stay private.
 * Hashes select candidates; byte comparisons decide equality. */
#define NANO_TEXTURE_SHARE_BUCKETS 512
typedef struct NanoTextureBuffer {
    void *data;
    size_t bytes, refs;
    uint32_t hash;
    struct NanoTextureBuffer *hash_next, *pointer_next;
} NanoTextureBuffer;

typedef struct {
    void *(*alloc)(size_t);
    void (*free)(void *);
    /* Optional hash override permits collision testing. NULL uses FNV-1a. */
    uint32_t (*hash)(const void *, size_t);
    NanoTextureBuffer *by_hash[NANO_TEXTURE_SHARE_BUCKETS];
    NanoTextureBuffer *by_pointer[NANO_TEXTURE_SHARE_BUCKETS];
    size_t logical_bytes, unique_bytes, buffers, references;
} NanoTextureShare;

static uint32_t NanoTextureHash(const void *data, size_t bytes)
{
    const unsigned char *p = (const unsigned char *)data;
    uint32_t hash = UINT32_C(2166136261);
    while (bytes--) hash = (hash ^ *p++) * UINT32_C(16777619);
    return hash;
}

static size_t NanoTexturePointerBucket(const void *p)
{
    uintptr_t v = (uintptr_t)p;
    return ((v >> 4) ^ (v >> 13)) & (NANO_TEXTURE_SHARE_BUCKETS - 1);
}

/* Takes ownership of a fresh buffer, including when metadata allocation fails. */
static void *NanoTextureIntern(NanoTextureShare *s, void *data, size_t bytes)
{
    NanoTextureBuffer *b;
    uint32_t hash;
    size_t bucket, pointer_bucket;
    if (!data || !bytes) return data;
    hash = s->hash ? s->hash(data, bytes) : NanoTextureHash(data, bytes);
    bucket = hash & (NANO_TEXTURE_SHARE_BUCKETS - 1);
    for (b = s->by_hash[bucket]; b; b = b->hash_next) {
        if (b->hash != hash || b->bytes != bytes || memcmp(b->data, data, bytes)) continue;
        s->free(data);
        b->refs++;
        s->references++;
        s->logical_bytes += bytes;
        return b->data;
    }
    b = (NanoTextureBuffer *)s->alloc(sizeof(*b));
    /* The engine allocator aborts on failure. Other callers may retain an
     * untracked buffer; Release still frees it correctly. */
    if (!b) return data;
    b->data = data;
    b->bytes = bytes;
    b->refs = 1;
    b->hash = hash;
    b->hash_next = s->by_hash[bucket];
    s->by_hash[bucket] = b;
    pointer_bucket = NanoTexturePointerBucket(data);
    b->pointer_next = s->by_pointer[pointer_bucket];
    s->by_pointer[pointer_bucket] = b;
    s->logical_bytes += bytes;
    s->unique_bytes += bytes;
    s->buffers++;
    s->references++;
    return data;
}

static void NanoTextureRelease(NanoTextureShare *s, void *data)
{
    NanoTextureBuffer **link, *b;
    if (!data) return;
    link = &s->by_pointer[NanoTexturePointerBucket(data)];
    while (*link && (*link)->data != data) link = &(*link)->pointer_next;
    b = *link;
    if (!b) { s->free(data); return; }
    s->logical_bytes -= b->bytes;
    s->references--;
    if (--b->refs) return;
    *link = b->pointer_next;
    link = &s->by_hash[b->hash & (NANO_TEXTURE_SHARE_BUCKETS - 1)];
    while (*link != b) link = &(*link)->hash_next;
    *link = b->hash_next;
    s->unique_bytes -= b->bytes;
    s->buffers--;
    s->free(b->data);
    s->free(b);
}

#endif
