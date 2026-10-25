# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇫🇷 [Français](README.fr.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**在你现有的 2D 和 3D 设备上以 3D 方式创作和探索：绘图，编辑照片和视频，研究分子和地球仪，然后看电影、玩游戏。**
3D 电视可以使用，任何普通显示器配上便宜的红青眼镜也可以，现在一台兼容的 Android 手机放进便宜的观片盒也能使用：这是一套[可通过 USB 使用的立体桌面](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)，已在旧硬件上测试。
Sparky Stereo OS 是 Daniel Ramos 的 SparkyLinux 发行版（SparkyLinux 由 Paweł "pavroo" Pijanowski 制作），是一个带有全新 Stereo KDE Plasma 桌面的 Linux 系统。

**阅读架构介绍：**[带插图的指南和仓库地图](docs/architectural-synthesis.md)，附带[完整尺寸信息图和文本版](docs/architecture-infographic.md)，改编并核对了 Daniel 的 Gemini / NotebookLM 研究。

<a href="#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="3D 立体桌面，带半透明窗口：Dolphin 的设置菜单和配色方案列表在前面，后面的玻璃窗口一层层退开，系统监视器和壁纸最深（红青立体图）"></a>

**立体桌面：**桌面本身有深度。
你正在使用的界面在屏幕上，它的菜单会向观众靠近，比如这里的 Marble 菜单和子菜单；而后面的一层层窗口则依次退开，像一叠纸张，壁纸最深。
3D 程序会在自己的窗口里保留自身的深度，比如 Marble 的地球仪。
每个只有几像素，并且在你选择的范围内。

<a href="#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="窗口中的 DOOM (2016)，3D 显示，下面是平面 Plasma 面板（红青立体图）"></a> <a href="#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Marble 的地球仪在星空前面，3D 显示（红青立体图）"></a> <a href="#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="3D 立体桌面：面板在屏幕上，声音弹出窗口在它前面，后面的窗口依次退开（红青立体图）"></a>

*戴上红青眼镜即可看到这些画面的 3D 效果（[更多](#seen-in-3d)）。*

**开发中：**[Flat Headset 开发 APK 和配套的电脑更新说明](https://github.com/Sparky-OS/flat-headset/tree/main/apk)已经提供，供测试者使用的开发 ISO 现在可以在开启 Secure Boot 的新电脑、旧 BIOS 电脑和 32 位 UEFI 机器上启动；最终的立体发行版 ISO 仍在准备中（[去向](#where-it-is-going)）。

- **[创作](#create)：**在 3D 中绘图，并在深度颜色（每种颜色 16 位而不是 8 位）中绘图，编辑 3D 照片和视频。
- **[科学与工程](#science-and-engineering)：**Marble 的地球仪、KAlgebra 的曲线图和 Kalzium 的分子都以 3D 显示；3D 模型和电路板仍在进行中。
- **[观看和游玩](#watch-and-play)：**3D 电影、照片和游戏，可以在窗口或全屏中显示。
- **[开发](#for-developers)：**只需把程序做一次 3D 适配；桌面会自动适配到每块屏幕。
- **[其他发行版？](docs/other-distributions.md)** 为什么我们不为它打包，以及它的维护者如何采用我们的修复。

**下一步：告诉我们你的 3D 设备**，它准备好时你会最先收到消息。
<br>用你的语言报名：[🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

### VR 也是一种立体显示器

大多数头显是两块小屏幕，每只眼睛一块；其余设备则像 3D 电视一样把一块屏幕分成两半，所以同一个桌面可以同时服务这两类设备。
- **口袋里已有的 3D 屏幕：**便宜的 Cardboard 式观片盒可以把一台兼容的 Android 手机变成立体桌面屏幕，全彩显示，每只眼睛有独立画面。10 月 19 日，Daniel 认可了在 Redmi Note 7 和一台 2016 年 A10 笔记本上通过 USB 上下半屏的设置：桌面可用，鼠标响应正常。视频已大幅改善，但仍有些不流畅；首次家庭 Wi-Fi 测试感觉接近 USB，而 Direct Wi-Fi 的停顿更长。完整分辨率和更多设备仍需测试（[测量和限制](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)）。由电脑负责绘制，旧手机因此有了新用途。[开发 APK、源码和配套电脑更新说明](https://github.com/Sparky-OS/flat-headset/tree/main/apk)一起提供；请先更新开发 Live USB 或已安装的电脑。Android 观片盒仍为测试版本。这里有一组照片：[首次测试](https://github.com/Sparky-OS/flat-headset#the-first-test-12-october-2026)和[手机上的桌面](https://github.com/Sparky-OS/flat-headset#the-desktop-on-the-phone-14-october-2026)。
- **VR 电影：**Bino 可以在任何 3D 屏幕上播放 360° 和 180° 电影，平面或 3D 均可，鼠标可以转动视角。
- **VR 游戏：**Half-Life 2 和 DOOM (2016) 可通过它们的 VR 模式显示到 3D 屏幕。

## 谁在构建

Daniel 来自巴西利亚的一个贫民区，目前有两位人类贡献者：Jeromy Streets，他的 Plasma 视频壁纸（[org.kde.video](https://github.com/Sparky-OS/org.kde.video)）现已进入 Sparky-OS，并由他维护；还有 Eff（effcol），他让 iZ3D 的代码以 [wiz3D](https://github.com/Sparky-OS/wiz3D) 的形式继续存在，并在这里维护它。
Linux 上的立体显示已经等待志愿者多年：早期尝试停滞，是因为评审者没有 3D 显示器，而这项工作横跨内核、Mesa、KWin、FFmpeg、播放器和网页标准。
没有其他开发者站出来接手，所以这里其他的工作伙伴是 AI，由 Daniel 指挥和核对，并列入[AI 来源记录](docs/ai-provenance.md)。
如果你更希望它由人类亲手构建，我们非常欢迎：每个 fork 都公开，每个任务都开放。
所有内容都在两台普通机器上构建和测试：一台家用电脑和一台 2016 年的笔记本（[硬件](docs/hardware.md)）。
在那台笔记本上，每个桌面用例在 2D 和 3D 中都保持 24 fps：[KWin 为立体付出的代价，已测量](docs/measurements/kwin-stereo-cost-a10-2026-10-23.md)。

## 去向

这个发行版是工作的证据，它发现的问题会回流到开放标准。
Daniel 和 Milton Ponson 共同主持 W3C [Procedural Memory Knowledge Representation Community Group (PM-KR)](https://www.w3.org/community/pm-kr/)。
我们的报告 [Stereo 3D on Linux and the Web](https://www.w3.org/publications/spec-generator/?type=respec&url=https://raw.githubusercontent.com/w3c-cg/pm-kr/main/reports/source/stereo-3d-adoption-report.html) 在那里作为个人提案，是小组讨论的输入：哪些既有规范已经支持 3D，Linux 和网页从未采用什么，以及浏览器还需要什么。
它也是我们在 2026 年 10 月 13 日 W3C Media and Entertainment Interest Group 演讲的主题（[幻灯片](docs/talks/2026-10-13-w3c-me-ig.md)）。
使用 W3C 账号加入小组免费，欢迎帮助：在你的显示器上测试、审阅报告，或带上你的使用场景。

## 创作

**在 3D 中绘图、编辑照片和编辑视频，并在深度颜色中绘图：每种颜色 16 位，而不是 8 位。**
- **绘画：**Krita 可以在 16 位画布上绘画，也可以在每只眼睛 16 位的 3D 画布上绘画。
- **照片：**digiKam 和 Showfoto 在相册、光桌、幻灯片和编辑器中显示 3D 照片；KolourPaint 可以编辑 3D 图片，并保存它的 3D 标记。
- **视频：**在 Kdenlive 中，片段会识别自己的 3D 布局，监视器可以 3D 显示，渲染结果也会保留 3D 标记。
- **故事：**[StorySplat](https://storysplat.com)（"把你的 3D 扫描变成互动漫游"）可以在浏览器中直接在真实场所的 3D 扫描里构建漫游，它的 3D View 可以在任何已注册的输出上以 3D 显示这些漫游，并首次在 Sony 3D 电视上左右并排测试。

每个程序的完整说明：[程序](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

### 供主题设计师和自定义者

**在这个桌面上，主题可以决定什么浮出、什么沉入：**[主题设计的新边界](#depth-on-the-desktop)。

## 科学与工程

**在 3D 中学习和设计：地球仪、曲线图和分子今天就能以 3D 工作，3D 模型和电路板仍在进行中。**
- **学习和科学：**Marble 的地球仪、KAlgebra 的曲线图、Kalzium 的分子和 Kubrick 立方体，在 3D 桌面上默认以 3D 显示。
- **3D 模型和电路板：**OpenSCAD、KiCad 和 F3D 的 3D 预览正在进行中。
- **从工作台到客户，全程全彩：**同一个模型可以显示在工程师桌上的裸眼 3D 显示器（配合 [DisplayXR](https://displayxr.org)，进行中）、团队或培训教室使用的 3D 电视或投影仪，以及每位工人和客户自己手机插入纸板观片盒的画面（[Flat Headset](https://github.com/Sparky-OS/flat-headset)）。它端到端开放，因此没有人被绑定到某一家显示器厂商。

每个程序的完整说明：[程序](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

## 观看和游玩

**3D 电影、照片和游戏可以在自己的窗口或全屏中显示，桌面的其余部分保持不变。**
- **屏幕：**3D 电视、显示器或投影仪，包括 2010 到 2013 年的 HDMI 3D 套件，或者任何普通显示器配红青眼镜；每块屏幕可以同时显示不同类型的 3D，裸眼 3D 显示器正在与 DisplayXR 团队一起推进。
- **电影：**3D 视频可以在 Haruna、VLC、mpv、Bino、PlasmaTube 等播放器中以 3D 播放。
- **照片：**Gwenview、digiKam 和 KolourPaint 以 3D 显示 3D 照片（MPO、JPS 和立体 PNG）。
- **游戏：**窗口中的 DOOM (2016) 和 Half-Life 2，都通过 VR 模式（[公式](docs/formula.md)）。
- **为游戏调优的内核：**发行版运行 Linux 7.3，带我们的立体补丁。它的全新调度器在作者自己的测试中，把一款游戏在旧 CPU 上的最低帧率从 4 fps 提高到 29 fps（[数据](https://lore.kernel.org/all/20260511113104.563854162@infradead.org/)），并让显存很小的 AMD 显卡把游戏内存留在显卡上（[修改](https://pixelcluster.dev/VRAM-Mgmt-fixed/)）。

每个程序、它得到了什么以及如何证明：[程序](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

### 用 3D 查看

本页图片是用发行版中的 Spectacle 截取的，它保留了两只眼睛的画面。
戴上红青眼镜即可在这里看到它们的 3D 效果；MPO 文件可以在发行版图片程序中，在任意已注册的输出上以 3D 打开。所有图片，每张都带红青版本和直接 MPO 下载：[截图画廊](docs/screenshots/README.md)。Daniel 用 LG Optimus 3D 手机在 2014 到 2016 年拍摄的 3D 照片，含原图：[照片画廊](docs/photos/README.md)。

- **立体桌面，半透明**（[MPO](https://raw.githubusercontent.com/Sparky-OS/sparky-stereo-os/main/docs/screenshots/translucent-stereo-desktop.mpo)），在 3D 电视上，2026 年 10 月 15 日。窗口是玻璃，所以能透过它看到后面的层。双眼间测量：Dolphin，焦点窗口，0 px，它的设置菜单 +5 px（前面，位于用户设置的浮出上限）；很长的配色方案列表 0 px，因为它碰到屏幕顶部，而碰到边缘的浮出元素会留在屏幕上；Thunderbird 后面 -3 px；系统监视器部件和壁纸 -10 px；面板 0 px。两个电子邮件地址在两只眼睛中都做了模糊处理。
- **立体桌面，菜单上叠菜单**（[MPO](docs/screenshots/stereo-desktop-dialogs.mpo)），在帧封装的 3D 电视上，2026 年 10 月 13 日。双眼间测量：焦点 Marble 窗口 0 px，它的设置菜单 +2 px，面板子菜单 +4 px，后面的四个窗口 -3、-5、-8 和 -10 px，部件和壁纸 -10 px；窗口内部，Marble 自身的 3D：地球标签 +12 px，星星 -13 px。后面 Diolinux 聊天中的消息是模糊的。
- **普通窗口中的 DOOM (2016)**（[MPO](docs/screenshots/doom-2016-in-a-window.mpo)），基于 [KHARVOX](https://github.com/CactusVRStudios/KHARVOX)，CactusVRStudios 的 DOOM (2016) VR 转换模组（MIT）：游戏有深度，而面板和窗口边框在两只眼睛中都保持平面。双眼间测量：最近的岩石相距 23 px，远山 1 px，面板 0 px。
- **Marble 的地球仪**（[MPO](docs/screenshots/marble-globe.mpo)）：地球在屏幕前（+11 px），星星在它后面（-12 px），侧面板保持平面。这张截图早于之后的修复；菜单上叠菜单的图片展示的是今天的 Marble。
- **立体桌面，弹出窗口**（[MPO](docs/screenshots/stereo-desktop.mpo)），同一天。双眼间测量：面板 0 px（在屏幕上），声音弹出窗口 +4 px（前面），后面的三个窗口 -3、-7 和 -10 px，系统监视器部件 -10 px，和壁纸一起在最深处。

<a id="depth-on-the-desktop"></a>
## 立体桌面：主题设计的新边界

**这是第一次，主题不只决定外观，还决定什么浮出、什么沉入。**
几十年来，阴影、斜边和凸起按钮都只是装样子；在立体桌面上，这是真的，而且是温和的：每个只有几像素，在你选择的范围内（系统设置，"3D 深度"）。

- **你使用的东西会浮出：**菜单、工具提示、通知和对话框朝你浮现，你正在工作的窗口保持在屏幕上。*已构建，并已在 2026 年 10 月 13 日在 3D 电视上看到（[顶部图片](#seen-in-3d)）。*
- **其余的会沉入：**后面的窗口像一叠纸张一样依次退后，壁纸沉得最深。*已构建。*
- **小东西会守住位置：**指针会跟随它所在元素的层级，阴影落在它碰到的东西上，而像投影上方的摄像头那样的置顶窗口，会继续浮在所有东西上方。*已构建。*
- **3D 壁纸：**一张 3D 照片作为背景时会保留自身的浮出和沉入，远远落在每个窗口后面。*已构建。*接下来是配合 Jeromy Streets 的视频壁纸实现的 3D 视频背景。*即将到来。*
- **3D 屏幕保护程序：**经典的星空屏保和立体屏保，以真实 3D 显示。*已构建。*
- **3D 图片和图标：**3D 照片会在 Dolphin 的预览和图片查看器中以 3D 显示。*已构建。*成对绘制的图标，每只眼睛一个，是 Stereo Oxygen 的一部分，这是发行版自己的外观。*即将到来。*
- **真正会浮出和沉入的效果：**正在关闭的窗口可以碎片状飞向你，或者沉到屏幕后面并在地板上反弹。*已在我们的 KWin 分支上构建，即将进入下一个软件包。*在 3D 中展开的窗口切换器，以及真实 3D 的桌面立方体。*即将到来。*
- **开机就有 3D：**启动画面和登录界面会跟随你为主屏幕保存的 3D 模式。*已构建。*

**而它仍然是一个普通的 2D 桌面。**
在普通屏幕上没有变化：同样的主题、同样的布局、同样的效果，只绘制一次。
3D 只出现在能显示它的屏幕上，或者通过红青眼镜显示，而为 3D 制作的主题也是完整的 2D 主题。

<a id="the-desktop-cube-what-one-format-makes-possible"></a>详细信息：[桌面上的深度](docs/depth-on-the-desktop.md)和[供主题设计师和自定义者](docs/for-theme-designers.md)；欢迎在[主题 issue](https://github.com/Sparky-OS/sparky-stereo-os/issues/78)中提出想法、草图和 3D 草图。

## 面向开发者

**只需把程序做一次 3D 适配：把双眼画面交给桌面，它会照顾每一块屏幕。**
你可以在自己已有的屏幕上编写并检查工作。
- [在普通显示器上开发 3D 和 XR](docs/develop-3d-on-an-ordinary-monitor.md)：从这里开始。
- [从网页开始的立体 3D 场景](docs/web-3d-in-stereo.md)：three.js、WebGL 和 WebXR，从任何浏览器中的红青眼镜到每一块 3D 屏幕。
- [内部格式](docs/house-formats.md)和[立体分工](docs/stereo-labor-division.md)：与规范绑定的规则。
- [不用 3D 电视测试立体](docs/test-stereo-without-a-3d-tv.md)和[带 3D 显示器的虚拟机](docs/stereo-vm.md)：在虚拟显示器或虚拟机中测试 3D 输出；带 Stereo KWin 的现成根文件系统在[我们的仓库服务器](https://repo.sparkyos.org/bench/kwin-root/)上。
- [技能](skills/README.md)：为参与发行版的人和 AI 助手提供的说明。

## 工作原理

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**程序描述每一幅画面；桌面把它适配到每一块屏幕。**对立体显示来说，两个视图一起放在同一个完整左右并排的缓冲区中传递。提议的 HDR 扩展会通过同样的分工保留画面的颜色描述和重建信息。

**三行立体契约。**
- **Stereo KWin**（KDE Plasma 的合成器，带我们的立体修改）支持完整左右并排，任意分辨率。
- **程序**按任意标准解码或生成立体画面，并以完整左右并排、任意分辨率交给 Stereo KWin。
- **输出**（Stereo KWin 末端的滤镜，每种屏幕一种）把它转换成每块屏幕需要的形式。

为什么是完整左右并排，怎么让一台桌面使用两块 GPU 上的两台 3D 电视，以及同样的原则如何扩展到 HDR：[工作原理](docs/how-it-works.md)。[HDR 声明](docs/stereo-hdr-content.md)是等待实现和跨格式设备测试的设计；HDR 交换表示仍是一个需要验证的工程选择。既有的立体和深度颜色测试没有验证那条 HDR 路径。

## 开放栈中的立体，而不是单一产品中的立体

在其他地方，立体和单一产品绑在一起：一台头显、一家厂商的注入器、一家厂商的内核。
在这里，它是开放层（KDE、内核、文件格式）的属性，因此它能到达你已经拥有的屏幕：[开放栈中的立体](docs/open-stack.md)。

## 这个发行版为立体 3D 和深度颜色修改的程序

3D 给每个程序带来了什么，从电影和照片到地球仪和分子：[程序](docs/programs.md)。
每个程序如何修改、如何证明，按领域分列（显示路径、视频、科学与工程、图像、模拟器、系统，以及尚未完成的部分）：[程序详情](docs/programs-in-detail.md)。

## 我们在 KDE GitLab 上的分支

每一个 KDE 修改都是我们 fork 上的分支，托管在 [invent.kde.org](https://invent.kde.org/danielcamposramos)，先经过 KDE 自己的 CI 测试，再提交上游：[分支及其 CI 结果](docs/kde-branches.md)。

## 已合并到 Sparky Stereo 之外

**2026 年 10 月 20 日：IANA 注册了三种 Matroska 深度平面类型**，引用了我们的立体图层规范。左眼、右眼和背景平面现在分别有已分配的独立深度轨道标识符。六个提议的打包帧模式仍在专家评审中。[注册表里程碑和上游合并](docs/upstream-merges.md#registered-identifiers)。

如果某个程序在通往屏幕的路上破坏了立体或深度颜色，修复会提交给那个程序自己的项目。
HandBrake、mpv、Qt Multimedia 和 PeerTube 等项目已经合并了我们工作中的修复；每一个项目，连同合并它的维护者以及正在评审的内容，都在[已合并到 Sparky Stereo 之外](docs/upstream-merges.md)。
每个部分都会先展示它确实工作，再称为完成，并附带数据和一张红青与 MPO 图片：[证明](docs/proofs/README.md)。
从事立体工作的同行如何评价它，公开并且带链接：[他们的评价](docs/what-people-said.md)。

## 文档

[VR 引擎到 3D 显示器的公式](docs/formula.md)，[KWin 在真实电视上的首次运行](docs/first-runs/kwin-2026-10-01/README.md)，以及 2026 年 10 月 13 日的[W3C 演讲幻灯片](docs/talks/2026-10-13-w3c-me-ig.md)；每一页都在[docs](docs/)中。

## 工具

[vkms-stereo-bench](tools/vkms-stereo-bench/README.md) 在虚拟显示器上检查 3D 模式，[hibernate-bench](tools/hibernate-bench/README.md) 在 Secure Boot 下检查休眠，两者都在虚拟机中运行。

## 基础：三份开放列表

这个发行版背后的研究是公开的，分为三份任何人都可以复制的精选列表（CC0）：立体 3D 的[awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy)，HDR 和深度颜色的[awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr)，以及虚拟现实的[awesome-vr](https://github.com/danielcamposramos/awesome-vr)。

## 致谢

Sparky Stereo OS，Daniel Ramos（Capitain Jack）的 SparkyLinux 发行版（SparkyLinux 由 Paweł "pavroo" Pijanowski 制作）。

**软件包维护者**，各自对自己的仓库拥有完整权利，位于[Sparky-OS](https://github.com/Sparky-OS)：

| | |
| --- | --- |
| <a href="https://github.com/effcol"><img src="https://github.com/effcol.png?size=96" width="72" alt="Eff"></a> | **Eff (effcol)**<br>维护[wiz3D](https://github.com/effcol/wiz3D)，这是用于 DirectX、OpenGL、AMD HD3D 和 NVIDIA 3D Vision 的通用立体 3D 包装器，基于 iZ3D，面向所有系统，同时维护这里的软件包[Sparky-OS/wiz3D](https://github.com/Sparky-OS/wiz3D)。<br>[![Follow Eff](https://img.shields.io/badge/Follow-effcol-2777AD?style=flat-square&logo=github)](https://github.com/effcol) |
| <a href="https://github.com/halverneus"><img src="https://github.com/halverneus.png?size=96" width="72" alt="Jeromy Streets"></a> | **Jeromy Streets (halverneus)**<br>创建并维护[org.kde.video](https://github.com/Sparky-OS/org.kde.video)，这是 KDE Plasma 的视频壁纸和锁屏。<br>[![Follow Jeromy](https://img.shields.io/badge/Follow-halverneus-2777AD?style=flat-square&logo=github)](https://github.com/halverneus) |

**版本：**Sparky Stereo OS 9 "Mashtabba"，基于 Debian 14 "Forky"，仅使用 KDE Plasma。

这个发行版立足的所有人，逐名列出：[ATTRIBUTIONS.md](ATTRIBUTIONS.md)。

**特别感谢：**
- **David Fattal**，Leia 联合创始人和 DisplayXR 维护者，感谢他的鼓励、时间和努力，也感谢他在自己制造的 3D 显示器上测试我们的桌面。
- **Milton Ponson** 和 **Christoph Dorn**，Daniel 在 W3C PM-KR 小组中的代表，该小组的每位成员，以及 W3C 的 **Dave Raggett**、**Ian Jacobs** 和 **Chris Needham**，是他们为这项工作打开了门。
- **Tim Berners-Lee**，以及所有一层一层建成互联网，并把它交给所有人的人。
- **Foottroller** 团队，感谢他们为 Linux 打开了用双脚走进 VR 的大门。
- **Eric Allard**，让 Johnny 5 在 *Short Circuit* 中活过来的工程师；这部电影的编剧 **S. S. Wilson** 和 **Brent Maddock**；以及它的音乐作者 **El DeBarge**、**Peter Wolf**、**Ina Wolf** 和 **David Shire**，在这版系统制作期间反复播放。

**引用它：**[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**点星：**[![GitHub stars](https://img.shields.io/github/stars/Sparky-OS/sparky-stereo-os?style=flat-square&logo=github&label=Stars)](https://github.com/Sparky-OS/sparky-stereo-os/stargazers) ⭐ 如果 Sparky Stereo OS 对你有用，一颗星可以帮助更多人找到它。

**支持它：**[![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donate to SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) 赞助 Daniel 可以支持这个发行版，向 SparkyLinux 捐款则支持它赖以构建的 Paweł 的发行版。

<a href="https://sourceforge.net/p/sparkyos/"><picture><source media="(prefers-color-scheme: dark)" srcset="https://sourceforge.net/sflogo.php?type=18&amp;group_id=3189517"><img alt="SparkyOS on SourceForge" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3189517" width="200"></picture></a>

## 许可

文档采用[Creative Commons Attribution 4.0 International 许可](https://creativecommons.org/licenses/by/4.0/)（CC BY 4.0）：可以分享和改编，只需为 Sparky Stereo OS 署名。

> "信息就是力量。但和所有力量一样，总有人想把它只留给自己。"
> — Aaron Swartz，[*Guerilla Open Access Manifesto*](https://archive.org/details/GuerillaOpenAccessManifesto)（2008 年 7 月）

`docs/first-runs/` 下的脚本和 `tools/` 下的工具是代码，采用 GNU General Public License, version 2 or later（GPL-2.0-or-later）许可；见[LICENSE-GPL-2.0](LICENSE-GPL-2.0)。
