// SPDX-FileCopyrightText: 2026 Daniel Ramos (Capitain Jack)
// SPDX-License-Identifier: MIT
//
// qvkdiscs: a QVulkanWindow program that asks for two views (QSurfaceFormat::StereoBuffers) and draws six coloured
// squares on neutral grey, each eye shifted by half the square's parallax (device pixels, positive when nearer: the
// left eye's square to the right of the right eye's), with vkCmdClearAttachments, so no shader is involved and the
// disparity a capture should measure is exactly the parallax asked (ORDER 573).
//   QVKDISCS_PARALLAX="2,-2,6,-6,4,10"   even numbers, so each eye moves by whole pixels
//   QVKDISCS_MONO=1                       the window does not ask for two views (the 2D control)
//   QVKDISCS_STILL=1                      one frame drawn, then nothing more (a still program)
// Built with QVKDISCS_STEREO_API it draws the right eye into QVulkanWindow::currentFramebuffer(RightBuffer) when that
// differs from the left one; built without it, it draws the left eye only, as a program written for today's
// QVulkanWindow does. At 7 s it prints one STATE line.
#include <QGuiApplication>
#include <QTimer>
#include <QVulkanFunctions>
#include <QVulkanInstance>
#include <QVulkanWindow>
#include <atomic>
#include <cstdio>

static const int s_x[6] = {80, 390, 700, 80, 390, 700};
static const int s_y[6] = {90, 90, 90, 370, 370, 370};
static const float s_rgb[6][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}, {1, 1, 0}, {0, 1, 1}, {1, 0, 1}};
static std::atomic<int> s_frames{0};
static std::atomic<bool> s_twoViews{false};

class Renderer : public QVulkanWindowRenderer
{
public:
    explicit Renderer(QVulkanWindow *w) : m_window(w)
    {
        const QStringList p = qEnvironmentVariable("QVKDISCS_PARALLAX", QStringLiteral("2,-2,6,-6,4,10")).split(QLatin1Char(','));
        for (int i = 0; i < 6; ++i)
            m_parallax[i] = i < p.size() ? p.at(i).toInt() : 0;
    }

    void initResources() override
    {
        m_df = m_window->vulkanInstance()->deviceFunctions(m_window->device());
    }

    void startNextFrame() override
    {
        VkCommandBuffer cb = m_window->currentCommandBuffer();
#ifdef QVKDISCS_STEREO_API
        const VkFramebuffer left = m_window->currentFramebuffer(QVulkanWindow::LeftBuffer);
        const VkFramebuffer right = m_window->currentFramebuffer(QVulkanWindow::RightBuffer);
#else
        const VkFramebuffer left = m_window->currentFramebuffer();
        const VkFramebuffer right = left;
#endif
        const bool twoViews = right != left;
        s_twoViews = twoViews;
        drawEye(cb, left, twoViews ? 1 : 0);
        if (twoViews)
            drawEye(cb, right, -1);
        m_window->frameReady();
        ++s_frames;
        if (qEnvironmentVariableIntValue("QVKDISCS_STILL") != 1)
            m_window->requestUpdate();
    }

private:
    // sign: +1 the left eye (half the parallax to the right), -1 the right eye, 0 one picture
    void drawEye(VkCommandBuffer cb, VkFramebuffer fb, int sign)
    {
        const QSize size = m_window->swapChainImageSize();
        const qreal dpr = m_window->devicePixelRatio();
        VkClearValue clear[3] = {};
        clear[0].color = {{128 / 255.0f, 128 / 255.0f, 128 / 255.0f, 1.0f}};
        clear[1].depthStencil = {1.0f, 0};
        clear[2].color = clear[0].color;
        VkRenderPassBeginInfo rp = {};
        rp.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
        rp.renderPass = m_window->defaultRenderPass();
        rp.framebuffer = fb;
        rp.renderArea.extent = {uint32_t(size.width()), uint32_t(size.height())};
        rp.clearValueCount = m_window->sampleCountFlagBits() > VK_SAMPLE_COUNT_1_BIT ? 3 : 2;
        rp.pClearValues = clear;
        m_df->vkCmdBeginRenderPass(cb, &rp, VK_SUBPASS_CONTENTS_INLINE);
        for (int i = 0; i < 6; ++i) {
            VkClearAttachment a = {};
            a.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            a.colorAttachment = 0;
            a.clearValue.color = {{s_rgb[i][0], s_rgb[i][1], s_rgb[i][2], 1.0f}};
            const int side = qRound(160 * dpr);
            VkClearRect r = {};
            r.rect.offset = {qRound(s_x[i] * dpr) + sign * m_parallax[i] / 2, qRound(s_y[i] * dpr)};
            r.rect.extent = {uint32_t(side), uint32_t(side)};
            r.layerCount = 1;
            m_df->vkCmdClearAttachments(cb, 1, &a, 1, &r);
        }
        m_df->vkCmdEndRenderPass(cb);
    }

    QVulkanWindow *m_window;
    QVulkanDeviceFunctions *m_df = nullptr;
    int m_parallax[6];
};

class Window : public QVulkanWindow
{
public:
    QVulkanWindowRenderer *createRenderer() override { return new Renderer(this); }
};

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    QVulkanInstance inst;
    if (!inst.create()) {
        fprintf(stderr, "qvkdiscs: no Vulkan instance: %d\n", inst.errorCode());
        return 2;
    }
    Window w;
    w.setVulkanInstance(&inst);
    w.setTitle(QStringLiteral("qvkdiscs"));
    w.setPreferredColorFormats({VK_FORMAT_B8G8R8A8_UNORM, VK_FORMAT_R8G8B8A8_UNORM});
    if (qEnvironmentVariableIntValue("QVKDISCS_MONO") != 1) {
        QSurfaceFormat format = w.requestedFormat();
        format.setStereo(true);
        w.setFormat(format);
    }
    w.resize(940, 620);
    w.show();
    QTimer::singleShot(7000, &w, [&w] {
        printf("STATE qvulkanwindow stereo-asked %d stereo-format %d two-views %d size %dx%d dpr %.3f frames %d device %s\n",
               w.requestedFormat().stereo(), w.format().stereo(), s_twoViews.load(), w.swapChainImageSize().width(),
               w.swapChainImageSize().height(), w.devicePixelRatio(), s_frames.load(),
               w.physicalDeviceProperties() ? w.physicalDeviceProperties()->deviceName : "?");
        fflush(stdout);
    });
    return app.exec();
}
