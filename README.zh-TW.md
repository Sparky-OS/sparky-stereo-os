# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**在你已有的螢幕上以 3D 進行創作與探索：繪畫、編輯照片與影片、研究分子和地球儀，然後看電影、玩遊戲。**
它為各種 3D 螢幕而設計：3D 電視和 3D 投影機、VR 頭戴顯示器、裸眼 3D 顯示器，以及配上紅青眼鏡的任何螢幕。
在一般的 2D 螢幕上，同一個桌面無需任何改動即可使用。
Sparky Stereo OS 是 Daniel Ramos 的 SparkyLinux 版本（SparkyLinux 由 Paweł "pavroo" Pijanowski 製作），是一套搭載全新立體 KDE Plasma 桌面的 Linux 系統。

**對你的電腦和地球都更輕：**每個套件都去掉了程式從不讀取的註解和說明，因此同樣的工作需要更少的處理、更少的能源和更少的磨損。
[實測](docs/lean-code-packages.md#why-it-matters)（一台 2016 年的筆記型電腦）：為編譯器準備程式的工作量比使用未去除註解的相同檔案少 2% 到 4%，且沒有任何損失。

<a href="docs/edition-in-detail.zh-TW.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="帶有半透明視窗的 3D 立體桌面：Dolphin 的「設定」選單與配色方案列表在最前面，玻璃視窗在後方層層退後，系統監控程式與桌布在最深處（紅青立體圖）"></a>

<a href="docs/edition-in-detail.zh-TW.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) 在視窗中以 3D 顯示，下方是平面的 Plasma 面板（紅青立體圖）"></a> <a href="docs/edition-in-detail.zh-TW.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Marble 的地球儀浮在星星前方，以 3D 顯示（紅青立體圖）"></a> <a href="docs/edition-in-detail.zh-TW.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="3D 立體桌面：面板在螢幕平面，音效彈出視窗在它前方，後面的視窗層層退後（紅青立體圖）"></a>

*紅青眼鏡能讓這些圖片呈現 3D（[更多](docs/edition-in-detail.zh-TW.md#seen-in-3d)）。*

**狀態：beta 1，供測試者使用。**已在 3D 電視、配紅青眼鏡的一般螢幕，以及裝在平價觀看器中的 Android 手機上測試；裸眼 3D 顯示器和獨立式頭戴顯示器仍在進行中。

**下一步：在你的 Windows 電腦上用 USB 隨身碟試用，無需安裝任何東西：**[一頁，十個步驟（英文）](docs/guides/try-on-windows.en.md)
<br>索取下載連結，並用你的語言告訴我們你的 3D 裝備： [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[科學與工程](docs/edition-in-detail.zh-TW.md#science-and-engineering)：**Marble 的地球儀、KAlgebra 的函數圖、Kalzium 的分子，都是 3D；3D 模型與電路板正在進行中。掃描已在計畫中：把拍攝零件、現場或標本的影片變成 3D 模型。
- <a id="create"></a>**[創作](docs/edition-in-detail.zh-TW.md#create)：**以 3D 與高色深繪畫（每種顏色 16 位元，而不是 8 位元），並編輯 3D 照片與影片。掃描已在計畫中：把拍攝物體或場所的影片變成可以在其中走動的 3D 模型。
- <a id="watch-and-play"></a>**[觀看與遊玩](docs/edition-in-detail.zh-TW.md#watch-and-play)：**3D 電影、照片與遊戲，可在視窗中或全螢幕觀看。
- <a id="vr-is-also-a-stereo-monitor"></a>**[VR 也是一種立體螢幕](docs/edition-in-detail.zh-TW.md#vr-is-also-a-stereo-monitor):** 頭戴顯示器，或裝在觀看器中的手機，同樣是這個桌面的 3D 螢幕。
- <a id="for-developers"></a>**[開發](docs/edition-in-detail.zh-TW.md#for-developers)：**只要讓程式 3D 化一次，桌面就會為每種螢幕調整它。
- **[其他發行版？](docs/other-distributions.md)** 我們為何不替它們打包，以及其他發行版的維護者如何採用我們的修正。

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## 立體桌面：主題設計的新疆界

**在這個桌面上，主題決定什麼浮出、什麼下沉：**[主題設計的新疆界](docs/edition-in-detail.zh-TW.md#depth-on-the-desktop)。

<a id="how-it-works"></a>
## 運作原理

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**程式描述每張影像；桌面為每種螢幕調整它。**在立體模式下，兩個視角的畫面一起放在同一個完整左右並排的緩衝區中傳遞。提議的 HDR 擴充則是在同樣的分工下，保留影像的色彩描述與重建資訊。
[詳細內容](docs/edition-in-detail.zh-TW.md#how-it-works)

## 關於本版本的更多內容

- <a id="who-builds-it"></a>[誰在打造它](docs/edition-in-detail.zh-TW.md#who-builds-it)
- <a id="where-it-is-going"></a>[它的走向](docs/edition-in-detail.zh-TW.md#where-it-is-going)
- <a id="seen-in-3d"></a>[以 3D 一睹為快](docs/edition-in-detail.zh-TW.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[給主題設計者與客製化愛好者](docs/edition-in-detail.zh-TW.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[立體屬於開放堆疊，而非單一產品](docs/edition-in-detail.zh-TW.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[本版本為立體 3D 與高色深修改的程式](docs/edition-in-detail.zh-TW.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[我們在 KDE GitLab 上的分支](docs/edition-in-detail.zh-TW.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[在 Sparky Stereo 之外被合併](docs/edition-in-detail.zh-TW.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[文件](docs/edition-in-detail.zh-TW.md#documents)
- <a id="tools"></a>[工具](docs/edition-in-detail.zh-TW.md#tools)
- <a id="the-base-three-open-lists"></a>[基底：三份開放清單](docs/edition-in-detail.zh-TW.md#the-base-three-open-lists)

<a id="credit"></a>
## 致謝

Sparky Stereo OS 是 Daniel Ramos (Capitain Jack) 的 SparkyLinux 版本（SparkyLinux 由 Paweł "pavroo" Pijanowski 製作）。
本版本賴以立足的所有人，名列於：[ATTRIBUTIONS.md](ATTRIBUTIONS.md)。

**引用它：** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**支持它：** [![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donate to SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) 贊助 Daniel 是資助本版本，而捐款給 SparkyLinux 則是支持 Paweł 的發行版，也就是本版本賴以建構的基底。

[詳細內容](docs/edition-in-detail.zh-TW.md#credit)

<a id="licence"></a>
## 授權

文件採用 [Creative Commons Attribution 4.0 International 授權](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0)：可以分享與改編，但請註明 Sparky Stereo OS。
[詳細內容](docs/edition-in-detail.zh-TW.md#licence)
