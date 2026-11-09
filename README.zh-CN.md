# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**在你现有的 2D 和 3D 设备上以 3D 方式创作和探索：绘图，编辑照片和视频，研究分子和地球仪，然后看电影、玩游戏。**
它为各种 3D 屏幕而设计：3D 电视和 3D 投影机、VR 头显、裸眼 3D 显示器，以及配上红青眼镜的任何显示器。
在普通的 2D 显示器上，同一个桌面无需任何改动即可使用。
Sparky Stereo OS 是 Daniel Ramos 的 SparkyLinux 发行版（SparkyLinux 由 Paweł "pavroo" Pijanowski 制作），是一个带有全新 Stereo KDE Plasma 桌面的 Linux 系统。

**对你的电脑和地球都更轻：**每个软件包都去掉了程序从不读取的注释和说明，因此同样的工作需要更少的处理、更少的能耗和更少的磨损。
[实测](docs/lean-code-packages.md#why-it-matters)：读取 C++ 头文件的工作量比 Debian 少 2% 到 4%，且没有任何损失。

<a href="docs/edition-in-detail.zh-CN.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="3D 立体桌面，带半透明窗口：Dolphin 的设置菜单和配色方案列表在前面，后面的玻璃窗口一层层退开，系统监视器和壁纸最深（红青立体图）"></a>

<a href="docs/edition-in-detail.zh-CN.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="窗口中的 DOOM (2016)，3D 显示，下面是平面 Plasma 面板（红青立体图）"></a> <a href="docs/edition-in-detail.zh-CN.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Marble 的地球仪在星空前面，3D 显示（红青立体图）"></a> <a href="docs/edition-in-detail.zh-CN.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="3D 立体桌面：面板在屏幕上，声音弹出窗口在它前面，后面的窗口依次退开（红青立体图）"></a>

*戴上红青眼镜即可看到这些画面的 3D 效果（[更多](docs/edition-in-detail.zh-CN.md#seen-in-3d)）。*

**状态：beta 1，面向测试者。**已在 3D 电视、配红青眼镜的普通显示器以及放进便宜观片盒的 Android 手机上测试；裸眼 3D 显示器和独立头显仍在进行中。

**下一步：在你的 Windows 电脑上用 U 盘试用，无需安装任何东西：**[一页，十个步骤（英文）](docs/guides/try-on-windows.en.md)
<br>索取下载链接，并用你的语言告诉我们你的 3D 设备： [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[科学与工程](docs/edition-in-detail.zh-CN.md#science-and-engineering)：**Marble 的地球仪、KAlgebra 的曲线图和 Kalzium 的分子都以 3D 显示；3D 模型和电路板仍在进行中。
- <a id="create"></a>**[创作](docs/edition-in-detail.zh-CN.md#create)：**在 3D 中绘图，并在深度颜色（每种颜色 16 位而不是 8 位）中绘图，编辑 3D 照片和视频。
- <a id="watch-and-play"></a>**[观看和游玩](docs/edition-in-detail.zh-CN.md#watch-and-play)：**3D 电影、照片和游戏，可以在窗口或全屏中显示。
- <a id="vr-is-also-a-stereo-monitor"></a>**[VR 也是一种立体显示器](docs/edition-in-detail.zh-CN.md#vr-is-also-a-stereo-monitor):** 头显，或放进观片盒的手机，同样是这个桌面的 3D 屏幕。
- <a id="for-developers"></a>**[开发](docs/edition-in-detail.zh-CN.md#for-developers)：**只需把程序做一次 3D 适配；桌面会自动适配到每块屏幕。
- **[其他发行版？](docs/other-distributions.md)** 为什么我们不为它打包，以及它的维护者如何采用我们的修复。

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## 立体桌面：主题设计的新边界

**在这个桌面上，主题可以决定什么浮出、什么沉入：**[主题设计的新边界](docs/edition-in-detail.zh-CN.md#depth-on-the-desktop)。

<a id="how-it-works"></a>
## 工作原理

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**程序描述每一幅画面；桌面把它适配到每一块屏幕。**对立体显示来说，两个视图一起放在同一个完整左右并排的缓冲区中传递。提议的 HDR 扩展会通过同样的分工保留画面的颜色描述和重建信息。
[详细内容](docs/edition-in-detail.zh-CN.md#how-it-works)

## 关于本发行版的更多内容

- <a id="who-builds-it"></a>[谁在构建](docs/edition-in-detail.zh-CN.md#who-builds-it)
- <a id="where-it-is-going"></a>[去向](docs/edition-in-detail.zh-CN.md#where-it-is-going)
- <a id="seen-in-3d"></a>[用 3D 查看](docs/edition-in-detail.zh-CN.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[供主题设计师和自定义者](docs/edition-in-detail.zh-CN.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[开放栈中的立体，而不是单一产品中的立体](docs/edition-in-detail.zh-CN.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[这个发行版为立体 3D 和深度颜色修改的程序](docs/edition-in-detail.zh-CN.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[我们在 KDE GitLab 上的分支](docs/edition-in-detail.zh-CN.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[已合并到 Sparky Stereo 之外](docs/edition-in-detail.zh-CN.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[文档](docs/edition-in-detail.zh-CN.md#documents)
- <a id="tools"></a>[工具](docs/edition-in-detail.zh-CN.md#tools)
- <a id="the-base-three-open-lists"></a>[基础：三份开放列表](docs/edition-in-detail.zh-CN.md#the-base-three-open-lists)

<a id="credit"></a>
## 致谢

Sparky Stereo OS，Daniel Ramos（Capitain Jack）的 SparkyLinux 发行版（SparkyLinux 由 Paweł "pavroo" Pijanowski 制作）。
这个发行版立足的所有人，逐名列出：[ATTRIBUTIONS.md](ATTRIBUTIONS.md)。

**引用它：**[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**支持它：**[![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donate to SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) 赞助 Daniel 可以支持这个发行版，向 SparkyLinux 捐款则支持它赖以构建的 Paweł 的发行版。

[详细内容](docs/edition-in-detail.zh-CN.md#credit)

<a id="licence"></a>
## 许可

文档采用[Creative Commons Attribution 4.0 International 许可](https://creativecommons.org/licenses/by/4.0/)（CC BY 4.0）：可以分享和改编，只需为 Sparky Stereo OS 署名。
[详细内容](docs/edition-in-detail.zh-CN.md#licence)
