# Original skyboxes

The pinned software renderer loaded the original six sky textures but filled sky surfaces with a flat color. It now samples those textures in visible BSP sky spans. Cube orientation follows the pinned [FWGS OpenGL renderer](https://github.com/FWGS/xash3d-fwgs/blob/e3e459bb6735c9e6a6bf18658f637bc71cdc73df/ref/gl/gl_warp.c). Camera rotation changes the view; translation does not move the sky.

Original converted pixels and resolution are retained. There is no additional texture copy or full-screen buffer. Missing faces use the existing clear color. Background holes and sky depth retain their previous behavior. Map changes free and reset the old sky IDs before loading the next set.

The projection helper is newly written under MIT; renderer integration retains the upstream license. No game artwork is published.

The actual span/setup tests compare thousands of rays with upstream cube tables and check ties, edges, corners, guarded framebuffer stride, clipping, overflowing spans, non-square textures, missing faces and unload/reload. Sanitizers, native and standalone ARM builds and repeated patch application pass.

Fresh captures show original de_dust mountains/clouds and the cs_italy sky. The user confirmed de_dust on the physical screen. Death/Use checks stayed responsive. Hardware results are in VALIDATION.md. Separate scenes/cache states do not establish zero rendering cost.
