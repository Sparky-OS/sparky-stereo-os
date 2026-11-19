// SPDX-License-Identifier: MIT
// depthtest: a static GX scene with three planes of vertical stripes at known distances (40, 80 and 160 units), each
// plane filling one third of the picture, so a stereo view of it shows three known horizontal disparities.
// Written for ORDER 39 of Sparky Stereo OS; built on the libogc GX API (zlib licence), same set-up as devkitPro's triangle example.
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <math.h>
#include <gccore.h>
#include <wiiuse/wpad.h>

#define FIFO_SIZE (256 * 1024)
#define STRIPES 10

static GXRModeObj *rmode;
static void *frameBuffer;
static vu8 readyForCopy;

static void copy_buffers(u32 unused)
{
	if (readyForCopy == GX_TRUE) {
		GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
		GX_SetColorUpdate(GX_TRUE);
		GX_CopyDisp(frameBuffer, GX_TRUE);
		GX_Flush();
		readyForCopy = GX_FALSE;
	}
}

static void plane(float z, int third, float aspect, u8 r, u8 g, u8 b)
{
	const float half_h = -z * tanf(30.0f * M_PI / 180.0f);
	const float half_w = half_h * aspect;
	const float x0 = -half_w + third * (2.0f * half_w / 3.0f);
	const float sw = (2.0f * half_w / 3.0f) / (2 * STRIPES);
	for (int i = 0; i < STRIPES; i++) {
		const float xa = x0 + (2 * i) * sw, xb = xa + sw;
		GX_Begin(GX_QUADS, GX_VTXFMT0, 4);
		GX_Position3f32(xa, -half_h * 0.6f, z); GX_Color4u8(r, g, b, 255);
		GX_Position3f32(xb, -half_h * 0.6f, z); GX_Color4u8(r, g, b, 255);
		GX_Position3f32(xb, half_h * 0.6f, z);  GX_Color4u8(r, g, b, 255);
		GX_Position3f32(xa, half_h * 0.6f, z);  GX_Color4u8(r, g, b, 255);
		GX_End();
	}
}

int main(void)
{
	Mtx view;
	Mtx44 projection;
	GXColor background = {40, 40, 40, 255};
	void *fifoBuffer;

	VIDEO_Init();
	WPAD_Init();
	rmode = VIDEO_GetPreferredMode(NULL);
	frameBuffer = MEM_K0_TO_K1(SYS_AllocateFramebuffer(rmode));
	VIDEO_Configure(rmode);
	VIDEO_SetNextFramebuffer(frameBuffer);
	VIDEO_SetPostRetraceCallback(copy_buffers);
	VIDEO_SetBlack(false);
	VIDEO_Flush();

	fifoBuffer = MEM_K0_TO_K1(memalign(32, FIFO_SIZE));
	memset(fifoBuffer, 0, FIFO_SIZE);
	GX_Init(fifoBuffer, FIFO_SIZE);
	GX_SetCopyClear(background, 0x00ffffff);
	GX_SetViewport(0, 0, rmode->fbWidth, rmode->efbHeight, 0, 1);
	GX_SetDispCopyYScale((f32)rmode->xfbHeight / (f32)rmode->efbHeight);
	GX_SetScissor(0, 0, rmode->fbWidth, rmode->efbHeight);
	GX_SetDispCopySrc(0, 0, rmode->fbWidth, rmode->efbHeight);
	GX_SetDispCopyDst(rmode->fbWidth, rmode->xfbHeight);
	GX_SetCopyFilter(rmode->aa, rmode->sample_pattern, GX_TRUE, rmode->vfilter);
	GX_SetFieldMode(rmode->field_rendering, ((rmode->viHeight == 2 * rmode->xfbHeight) ? GX_ENABLE : GX_DISABLE));
	GX_SetCullMode(GX_CULL_NONE);
	GX_CopyDisp(frameBuffer, GX_TRUE);
	GX_SetDispCopyGamma(GX_GM_1_0);

	const float aspect = (CONF_GetAspectRatio() == CONF_ASPECT_16_9) ? 16.0F / 9.0F : 4.0F / 3.0F;
	guVector camera = {0.0F, 0.0F, 0.0F}, up = {0.0F, 1.0F, 0.0F}, look = {0.0F, 0.0F, -1.0F};
	guPerspective(projection, 60, aspect, 10.0F, 300.0F);
	GX_LoadProjectionMtx(projection, GX_PERSPECTIVE);

	GX_ClearVtxDesc();
	GX_SetVtxDesc(GX_VA_POS, GX_DIRECT);
	GX_SetVtxDesc(GX_VA_CLR0, GX_DIRECT);
	GX_SetVtxAttrFmt(GX_VTXFMT0, GX_VA_POS, GX_POS_XYZ, GX_F32, 0);
	GX_SetVtxAttrFmt(GX_VTXFMT0, GX_VA_CLR0, GX_CLR_RGBA, GX_RGBA8, 0);
	GX_SetNumChans(1);
	GX_SetNumTexGens(0);
	GX_SetTevOrder(GX_TEVSTAGE0, GX_TEXCOORDNULL, GX_TEXMAP_NULL, GX_COLOR0A0);
	GX_SetTevOp(GX_TEVSTAGE0, GX_PASSCLR);

	while (SYS_MainLoop()) {
		guLookAt(view, &camera, &up, &look);
		GX_SetViewport(0, 0, rmode->fbWidth, rmode->efbHeight, 0, 1);
		GX_InvVtxCache();
		GX_InvalidateTexAll();
		GX_LoadPosMtxImm(view, GX_PNMTX0);
		plane(-40.0f, 0, aspect, 255, 40, 40);
		plane(-80.0f, 1, aspect, 40, 255, 40);
		plane(-160.0f, 2, aspect, 80, 80, 255);
		GX_DrawDone();
		readyForCopy = GX_TRUE;
		VIDEO_WaitVSync();
		WPAD_ScanPads();
		if (WPAD_ButtonsDown(0) & WPAD_BUTTON_HOME) exit(0);
	}
	return 0;
}
