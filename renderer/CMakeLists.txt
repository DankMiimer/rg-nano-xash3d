cmake_minimum_required(VERSION 3.10)
project(nano_renderer C)
set(XASH ${CMAKE_CURRENT_SOURCE_DIR}/../upstream/xash3d)
file(GLOB SOFT ${XASH}/ref/soft/*.c)
file(GLOB COMMON ${XASH}/ref/common/*.c)
add_library(ref_soft SHARED ${SOFT} ${COMMON}
 ${XASH}/public/crtlib.c ${XASH}/public/crclib.c
 ${XASH}/public/matrixlib.c ${XASH}/public/xash3d_mathlib.c
 ${XASH}/public/utflib.c ${XASH}/public/atlas.c)
target_include_directories(ref_soft PRIVATE
 ${XASH}/public ${XASH}/common ${XASH}/engine ${XASH}/engine/common
 ${XASH}/engine/common/imagelib ${XASH}/pm_shared ${XASH}/filesystem
 ${XASH}/ref/common ${XASH}/ref/soft ${CMAKE_CURRENT_SOURCE_DIR}/../upstream/cs16-client/public)
target_compile_definitions(ref_soft PRIVATE REF_DLL=1 XASH_LOW_MEMORY=1 _GNU_SOURCE
 HAVE_STRCASECMP=1 HAVE_STRNCASECMP=1 HAVE_STRCASESTR=1 HAVE_STRCHRNUL=1
 HAVE_STRLCPY=1 HAVE_STRLCAT=1 HAVE_STRNLEN=1 HAVE_TGMATH_H=1)
target_link_libraries(ref_soft PRIVATE m)
target_link_options(ref_soft PRIVATE -Wl,--no-undefined)
