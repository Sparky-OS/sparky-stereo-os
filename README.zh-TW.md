# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**在你已有的螢幕上以 3D 進行創作與探索：繪畫、編輯照片與影片、研究分子和地球儀，然後看電影、玩遊戲。**
3D 電視可以用，配上便宜紅青眼鏡的一般螢幕也可以，現在連裝在平價觀看器中的相容 Android 手機也行：[一個透過 USB 可用的立體桌面](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)，已在較舊的硬體上測試過。
Sparky Stereo OS 是 Daniel Ramos 的 SparkyLinux 版本（SparkyLinux 由 Paweł "pavroo" Pijanowski 製作），是一套搭載全新立體 KDE Plasma 桌面的 Linux 系統。

**閱讀架構：**[附圖解的指南與倉庫地圖](docs/architectural-synthesis.md)，外加[全尺寸資訊圖表與文字版本](docs/architecture-infographic.md)，改編並核對自 Daniel 的 Gemini / NotebookLM 研究。

<a href="#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="帶有半透明視窗的 3D 立體桌面：Dolphin 的「設定」選單與配色方案列表在最前面，玻璃視窗在後方層層退後，系統監控程式與桌布在最深處（紅青立體圖）"></a>

**立體桌面：**桌面本身就有深度。
你正在使用的東西位於螢幕平面，選單向前浮出，就像這裡 Marble 的選單與子選單；後面的視窗則一個接一個退後，像一疊紙，桌布在最深處。
3D 程式在自己的視窗內保有自己的深度，就像 Marble 的地球儀。
每個層級只有幾個像素，界限由你決定。

<a href="#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) 在視窗中以 3D 顯示，下方是平面的 Plasma 面板（紅青立體圖）"></a> <a href="#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Marble 的地球儀浮在星星前方，以 3D 顯示（紅青立體圖）"></a> <a href="#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="3D 立體桌面：面板在螢幕平面，音效彈出視窗在它前方，後面的視窗層層退後（紅青立體圖）"></a>

*紅青眼鏡能讓這些圖片呈現 3D（[更多](#seen-in-3d)）。*

**開發中：**[Flat Headset 開發用 APK 與對應的 PC 更新說明](https://github.com/Sparky-OS/flat-headset/tree/main/apk)已經釋出，而給測試者的開發用 ISO 現在已能在開啟 Secure Boot 的新 PC、較舊的 BIOS PC 以及 32 位元 UEFI 機器上啟動；正式的立體版 ISO 仍在準備中（[它的走向](#where-it-is-going)）。

- **[創作](#create)：**以 3D 與高色深繪畫（每種顏色 16 位元，而不是 8 位元），並編輯 3D 照片與影片。
- **[科學與工程](#science-and-engineering)：**Marble 的地球儀、KAlgebra 的函數圖、Kalzium 的分子，都是 3D；3D 模型與電路板正在進行中。
- **[觀看與遊玩](#watch-and-play)：**3D 電影、照片與遊戲，可在視窗中或全螢幕觀看。
- **[開發](#for-developers)：**只要讓程式 3D 化一次，桌面就會為每種螢幕調整它。
- **[其他發行版？](docs/other-distributions.md)** 我們為何不替它們打包，以及其他發行版的維護者如何採用我們的修正。

**下一步：告訴我們你的 3D 裝備**，並在它準備好時搶先知道。
<br>用你的語言報名：[🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

### VR 也是一種立體螢幕

大多數頭戴顯示器就是一對小螢幕，每隻眼睛一個；其餘則是把一個螢幕切成兩半，跟 3D 電視一樣，所以同一個桌面兩種都能用。
- **早已在你口袋裡的 3D 螢幕：**一個平價的 Cardboard 式觀看器能把相容的 Android 手機變成立體桌面的螢幕，全彩顯示，每隻眼睛各有獨立畫面。10 月 19 日，Daniel 在 Redmi Note 7 與一台 2016 年的 A10 筆電上，認定 USB 半解析度上下分割的設定已達到可用：桌面能運作，滑鼠反應靈敏。影片大有改善但仍有些跳；第一次家用 Wi-Fi 測試感覺更接近 USB，Direct Wi-Fi 仍會有較長的卡頓。完整解析度與更多裝置仍需測試（[量測與限制](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)）。由 PC 負責繪製，讓舊手機再獲新用。[開發用 APK、原始碼與對應的 PC 更新說明](https://github.com/Sparky-OS/flat-headset/tree/main/apk)已一併提供；請先更新開發用 live USB 或已安裝的 PC。Android 觀看器仍是測試版本。這是[第一次測試](https://github.com/Sparky-OS/flat-headset#the-first-test-12-october-2026)和[手機上的桌面](https://github.com/Sparky-OS/flat-headset#the-desktop-on-the-phone-14-october-2026)的照片。
- **VR 電影：**Bino 能在任何 3D 螢幕上播放 360° 與 180° 電影，平面或 3D 皆可，用滑鼠轉動視角。
- **VR 遊戲：**Half-Life 2 與 DOOM (2016) 透過各自的 VR 模式顯示在 3D 螢幕上。

<a id="who-builds-it"></a>
## 誰在打造它

Daniel，來自巴西利亞的貧民區，到目前為止有兩位人類貢獻者：Jeromy Streets，他的 Plasma 影片桌布（[org.kde.video](https://github.com/Sparky-OS/org.kde.video)）現在歸屬於 Sparky-OS，由他擔任維護者；以及 Eff (effcol)，他讓 iZ3D 的程式碼以 [wiz3D](https://github.com/Sparky-OS/wiz3D) 之名繼續活下去，並在此維護它。
Linux 上的立體顯示苦等志願者多年：早期的嘗試之所以停滯，是因為審查者沒有 3D 顯示器，而這項工作橫跨核心、Mesa、KWin、FFmpeg、各家播放器與網路標準。
沒有其他開發者站出來接手，所以在這裡工作的其他夥伴是 AI，由 Daniel 指揮並檢查，名字都列在 [AI 來源紀錄](docs/ai-provenance.md)。
如果你更希望看到它由人類親手打造，我們非常歡迎：每個分支都是公開的，每項任務都是開放的。
一切都是在兩台普通機器上建構並測試的：一台家用 PC 與一台 2016 年的筆電，見[硬體](docs/hardware.md)。
在那台筆電上，每一種桌面情境在 2D 與 3D 下都能維持 24 fps，見[實測立體對 KWin 的代價](docs/measurements/kwin-stereo-cost-a10-2026-10-23.md)。

<a id="where-it-is-going"></a>
## 它的走向

這個版本是實際運作的證明，而它的發現會回饋到開放標準。
Daniel 與 Milton Ponson 共同主持 W3C [Procedural Memory Knowledge Representation Community Group (PM-KR)](https://www.w3.org/community/pm-kr/)。
我們的報告[Stereo 3D on Linux and the Web](https://www.w3.org/publications/spec-generator/?type=respec&url=https://raw.githubusercontent.com/w3c-cg/pm-kr/main/reports/source/stereo-3d-adoption-report.html)以個人提案的形式放在那裡，供小組討論：哪些既有規格已經支援 3D、Linux 與網路從未採納什麼，以及瀏覽器需要什麼。
這也是我們 2026 年 10 月 13 日在 W3C Media and Entertainment Interest Group 演講的主題（[投影片](docs/talks/2026-10-13-w3c-me-ig.md)）。
只要有 W3C 帳號就能免費加入小組，也歡迎幫忙：在你的顯示器上測試、審閱報告，或提出你的使用情境。

<a id="create"></a>
## 創作

**以 3D 繪畫、編輯照片、編輯影片，並以高色深繪畫：每種顏色 16 位元，而不是 8 位元。**
- **繪畫：**Krita 能在 16 位元畫布上作畫，也能在每隻眼睛各 16 位元的 3D 畫布上作畫。
- **照片：**digiKam 與 Showfoto 在相簿、燈箱、投影片放映與編輯器中顯示 3D 照片；KolourPaint 能編輯 3D 圖片並連同 3D 標記一起儲存。
- **影片：**在 Kdenlive 裡，片段知道自己的 3D 版面，監看視窗能以 3D 顯示，渲染輸出時也會保留 3D 標記。
- **故事：**[StorySplat](https://storysplat.com)（"Turn your 3D scans into interactive tours"）能直接在瀏覽器中，以真實地點的 3D 掃描建構成互動導覽，而且它的 3D View 能在已註冊的任何輸出上以 3D 顯示，最先是在 Sony 的 3D 電視上以並排模式測試的。

每個程式的完整說明：[Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

<a id="for-theme-designers-and-customizers"></a>
### 給主題設計者與客製化愛好者

**在這個桌面上，主題決定什麼浮出、什麼下沉：**[主題設計的新疆界](#depth-on-the-desktop)。

<a id="science-and-engineering"></a>
## 科學與工程

**以 3D 學習與設計：地球儀、函數圖與分子今天就能以 3D 呈現，3D 模型與電路板正在進行中。**
- **學習與科學：**Marble 的地球儀、KAlgebra 的函數圖、Kalzium 的分子，以及 Kubrick 方塊，在 3D 桌面上預設就是 3D。
- **3D 模型與電路板：**OpenSCAD、KiCad 與 F3D 的 3D 預覽正在進行中。
- **從工程師桌面到客戶手中，全程全彩：**同一個模型可以在工程師桌上的裸視 3D 螢幕上以深度呈現（搭配 [DisplayXR](https://displayxr.org)，進行中）、在團隊或訓練課程用的 3D 電視或投影機上呈現，以及在每位工作者與客戶自己手機上的紙板觀看器中呈現（[Flat Headset](https://github.com/Sparky-OS/flat-headset)）。從頭到尾都是開放的，沒有人被綁在單一顯示器廠商上。

每個程式的完整說明：[Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

<a id="watch-and-play"></a>
## 觀看與遊玩

**3D 電影、照片與遊戲能在自己的視窗或全螢幕中以 3D 顯示，桌面其餘部分維持原樣。**
- **螢幕：**3D 電視、螢幕或投影機（含 2010 到 2013 年的 HDMI 3D 機種），或任何配上紅青眼鏡的一般螢幕；每種螢幕可以同時顯示不同類型的 3D，而裸視 3D 螢幕正與 DisplayXR 團隊合作進行中。
- **電影：**3D 影片能在 Haruna、VLC、mpv、Bino、PlasmaTube 等播放器中以 3D 播放。
- **照片：**Gwenview、digiKam 與 KolourPaint 能以 3D 顯示 3D 照片（MPO、JPS 與立體 PNG）。
- **遊戲：**視窗中的 DOOM (2016) 與 Half-Life 2，兩者都透過 VR 模式（[公式](docs/formula.md)）。
- **為遊戲調校的核心：**本版本執行附上我們立體修補的 Linux 7.3。它的新排程器在作者自己的測試中，把一款遊戲在較舊 CPU 上的最低幀率從 4 提升到 29 fps（[數字](https://lore.kernel.org/all/20260511113104.563854162@infradead.org/)），而且能讓視訊記憶體不多的 AMD 顯示卡把遊戲記憶體留在卡上（[這項變更](https://pixelcluster.dev/VRAM-Mgmt-fixed/)）。

每個程式的收穫與驗證方式：[Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

<a id="seen-in-3d"></a>
### 以 3D 一睹為快

本頁的圖片都是用本版本的 Spectacle 拍的螢幕截圖，它會保留兩隻眼睛的畫面。
在這裡用紅青眼鏡就能看到 3D；MPO 檔案則能在本版的照片程式中，於已註冊的任何輸出上以 3D 開啟。完整清單，每張都附紅青版本與直接的 MPO 下載：[螢幕截圖集](docs/screenshots/README.md)。Daniel 自己用 LG Optimus 3D 手機在 2014 到 2016 年間拍的 3D 照片，含原始檔：[照片集](docs/photos/README.md)。

- **立體桌面，半透明**（[MPO](https://raw.githubusercontent.com/Sparky-OS/sparky-stereo-os/main/docs/screenshots/translucent-stereo-desktop.mpo)），2026 年 10 月 15 日在 3D 電視上拍攝。視窗是玻璃的，所以後面那疊會透出來。兩眼之間的實測數值：被聚焦的視窗 Dolphin 為 0 px，它的「設定」選單 +5 px（在前方，位於使用者設定的浮出上限）；很長的配色方案列表為 0 px，因為它頂到螢幕上緣，而浮出且碰到邊緣的東西會留在螢幕平面；Thunderbird 在後方 -3 px；系統監控小工具與桌布 -10 px；面板 0 px。兩個電子郵件地址在雙眼中都已模糊處理。
- **立體桌面，選單疊選單**（[MPO](docs/screenshots/stereo-desktop-dialogs.mpo)），2026 年 10 月 13 日在以 frame packing 顯示的 3D 電視上拍攝。兩眼之間的實測數值：被聚焦的 Marble 視窗 0 px，它的「設定」選單 +2 px、Panels 子選單 +4 px，後面的四個視窗 -3、-5、-8 與 -10 px，小工具與桌布 -10 px；視窗內部是 Marble 自己的 3D：地球標籤 +12 px，星星 -13 px。後方 Diolinux 聊天室裡的訊息已模糊處理。
- **DOOM (2016) 在普通視窗中**（[MPO](docs/screenshots/doom-2016-in-a-window.mpo)），基於 [KHARVOX](https://github.com/CactusVRStudios/KHARVOX)，CactusVRStudios 的 DOOM (2016) VR 轉換模組 (MIT)：遊戲有深度，而面板與視窗邊框在雙眼中都保持平面。兩眼之間的實測數值：最近的岩石相差 23 px，遠山 1 px，面板 0 px。
- **Marble 的地球儀**（[MPO](docs/screenshots/marble-globe.mpo)）：地球在螢幕前方（+11 px），星星在後方（-12 px），側邊面板保持平面。這張圖早於後來完成的修正；要看看 Marble 今天的樣子，請看選單疊選單那張圖。
- **立體桌面，一個彈出視窗**（[MPO](docs/screenshots/stereo-desktop.mpo)），同一天拍攝。兩眼之間的實測數值：面板 0 px（在螢幕平面），音效彈出視窗 +4 px（在前方），後面的三個視窗 -3、-7 與 -10 px，系統監控小工具 -10 px，和桌布一起位於最後方。

<a id="depth-on-the-desktop"></a>
## 立體桌面：主題設計的新疆界

**史上第一次，主題能決定什麼浮出、什麼下沉，而不只是東西看起來怎麼樣。**
幾十年來，陰影、斜角與立體按鈕都只是裝個樣子；在立體桌面上，這是真的，而且很節制：只有幾個像素，界限由你決定（系統設定中的「3D Depth」）。

- **你在用的東西會浮出：**選單、工具提示、通知與對話框向你浮出，而你工作的視窗停在螢幕平面。*已完成，2026 年 10 月 13 日在 3D 電視上見證（[頁首的那張圖](#seen-in-3d)）。*
- **其餘都下沉：**後面的視窗一個接一個退後，像一疊紙，桌布沉得最深。*已完成。*
- **小東西各安其位：**指標會採用它下方東西的深度層級，陰影落在它所落的東西上，而置頂視窗（例如蓋在投影片上的網路攝影機畫面）會一直浮在所有東西上方。*已完成。*
- **3D 桌布：**以 3D 照片當背景時，保留它自己的浮出與下沉，遠遠位於每個視窗之後。*已完成。* 3D 影片背景接下來會上，靠 Jeromy Streets 的影片桌布。*即將推出。*
- **3D 螢幕保護程式：**經典星空與立體保護程式，都是真的 3D。*已完成。*
- **3D 圖片與圖示：**3D 照片在 Dolphin 的預覽與看圖程式中以 3D 顯示。*已完成。* 成對繪製、每隻眼睛各一個版本的圖示，是 Stereo Oxygen 的一部分，那是本版本自己的風格。*即將推出。*
- **真正浮出與下沉的特效：**關閉中的視窗可以碎裂著朝你飛來，或是沉入螢幕後方並在地面上彈跳。*已在我們的 KWin 分支上完成，將包含在下一版套件中。* 以 3D 展開成扇形的視窗切換器，以及真正 3D 的桌面立方體。*即將推出。*
- **一開機就是 3D：**開機畫面與登入畫面會沿用你為主螢幕儲存的 3D 模式。*已完成。*

**而它仍然是一個正常的 2D 桌面。**
在普通螢幕上一切都沒變：同樣的主題、同樣的版面、同樣的特效，只繪製一次。
3D 只出現在能顯示它的螢幕上，或透過紅青眼鏡呈現；一個為 3D 設計的主題，同時也是完整的 2D 主題。

<a id="the-desktop-cube-what-one-format-makes-possible"></a>細節：[桌面上的深度](docs/depth-on-the-desktop.md)與[給主題設計者與客製化愛好者](docs/for-theme-designers.md)；歡迎在[主題 issue](https://github.com/Sparky-OS/sparky-stereo-os/issues/78) 中提出構想、草圖與 3D 模擬圖。

<a id="for-developers"></a>
## 給開發者

**只要讓程式 3D 化一次：把雙眼畫面交給桌面，它就會為每種螢幕處理好。**
你可以在自己已有的螢幕上寫程式並檢查成果。
- [在普通螢幕上開發 3D 與 XR](docs/develop-3d-on-an-ordinary-monitor.md)：從這裡開始。
- [你的 3D 場景，以立體方式從網頁呈現](docs/web-3d-in-stereo.md)：three.js、WebGL 與 WebXR，從任何瀏覽器中的紅青眼鏡，到每一種 3D 螢幕。
- [本專案的格式](docs/house-formats.md)與[立體分工](docs/stereo-labor-division.md)：規則都對應到規格。
- [在沒有 3D 電視的情況下測試立體](docs/test-stereo-without-a-3d-tv.md)與[有 3D 顯示器的虛擬機器](docs/stereo-vm.md)：在虛擬顯示器或虛擬機器中測試 3D 輸出；內建 Stereo KWin 的現成 root 檔案系統放在[我們的倉庫伺服器](https://repo.sparkyos.org/bench/kwin-root/)上。
- [技能](skills/README.md)：給在本版本上工作的人與 AI 助理的說明。

<a id="how-it-works"></a>
## 運作原理

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**程式描述每張影像；桌面為每種螢幕調整它。**在立體模式下，兩個視角的畫面一起放在同一個完整左右並排的緩衝區中傳遞。提議的 HDR 擴充則是在同樣的分工下，保留影像的色彩描述與重建資訊。

**立體契約，三行講完。**
- **Stereo KWin**（KDE Plasma 的 compositor，加上我們的立體變更）講的語言是完整左右並排、任意解析度。
- **程式**以任何標準解碼或產生立體，並以完整左右並排、任意解析度交給 Stereo KWin。
- **輸出**（位於末端、一種螢幕一個的 Stereo KWin 濾鏡）把這轉換成每種螢幕所需的格式。

為什麼是完整的左右並排、同一個桌面如何從兩張 GPU 送到兩台 3D 電視，以及同樣的原則如何延伸到 HDR：[運作原理](docs/how-it-works.md)。[HDR 宣告](docs/stereo-hdr-content.md)是仍待實作與跨格式裝置測試的設計；HDR 交換表示法也仍是待驗證的工程抉擇。既有的立體與高色深測試並不涵蓋這條 HDR 路徑。

<a id="stereo-in-the-open-stack-not-in-one-product"></a>
## 立體屬於開放堆疊，而非單一產品

在別處，立體被綁在一個產品上：一個頭顯、一家廠商的注入器、一家廠商的核心。
在這裡，它是開放層級（KDE、核心、檔案格式）的固有特性，所以能到達你已有的螢幕：[開放堆疊中的立體](docs/open-stack.md)。

<a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>
## 本版本為立體 3D 與高色深修改的程式

3D 為每個程式帶來什麼，從電影、照片到地球儀與分子：[Programs](docs/programs.md)。
每個程式是如何修改與驗證的，按領域分類（顯示路徑、影片、科學與工程、影像、模擬器、系統，以及尚未完成的部分）：[詳細的 Programs](docs/programs-in-detail.md)。

<a id="our-branches-on-kdes-gitlab"></a>
## 我們在 KDE GitLab 上的分支

每一項 KDE 變更都是我們在 [invent.kde.org](https://invent.kde.org/danielcamposramos) 上分叉出來的分支，在提交上游之前會先經過 KDE 自己的 CI 測試，見[分支與其 CI 結果](docs/kde-branches.md)。

<a id="merged-outside-sparky-stereo"></a>
## 在 Sparky Stereo 之外被合併

**2026 年 10 月 26 日，IANA 為 Matroska 分派了 StereoMode 15 至 20**，用於在同一影格內封裝影像與深度的配置。
此前，IANA 已於 10 月 20 日為左眼、右眼與背景的獨立深度軌道分派了平面類型 3 至 5。
兩項登錄均參照我們的 stereo-layer 規格。
[即時登錄表](https://www.iana.org/assignments/matroska)及[登錄里程碑與上游合併](docs/upstream-merges.md#registered-identifiers)。

只要某個程式在通往螢幕的路上弄壞了立體或高色深，修正就會送往該程式自己的專案。
HandBrake、mpv、Qt Multimedia 與 PeerTube 等專案已經合併了我們工作中的修正；每一項、合併它的維護者是誰、以及還在審查中的有哪些，都列在[在 Sparky Stereo 之外被合併](docs/upstream-merges.md)。
每一部分都要先實際運作才算完成，附上數字以及紅青立體圖與 MPO 圖片，見[證據](docs/proofs/README.md)。
立體領域工作者公開的評價與連結，見[大家的說法](docs/what-people-said.md)。

<a id="documents"></a>
## 文件

[從 VR 引擎到 3D 顯示器的公式](docs/formula.md)、[KWin 第一次在真實電視上執行](docs/first-runs/kwin-2026-10-01/README.md)，以及 2026 年 10 月 13 日的 [W3C 演講投影片](docs/talks/2026-10-13-w3c-me-ig.md)；所有頁面都在 [docs](docs/) 中。

<a id="tools"></a>
## 工具

[vkms-stereo-bench](tools/vkms-stereo-bench/README.md) 在虛擬顯示器上檢查 3D 模式，[hibernate-bench](tools/hibernate-bench/README.md) 在 Secure Boot 下檢查休眠，兩者都在虛擬機器中執行。

<a id="the-base-three-open-lists"></a>
## 基底：三份開放清單

本版本背後的研究是公開的，分為三份任何人都能複製的精選清單 (CC0)：[awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy) 對應立體 3D，[awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr) 對應 HDR 與高色深，[awesome-vr](https://github.com/danielcamposramos/awesome-vr) 對應虛擬實境。

<a id="credit"></a>
## 致謝

Sparky Stereo OS 是 Daniel Ramos (Capitain Jack) 的 SparkyLinux 版本（SparkyLinux 由 Paweł "pavroo" Pijanowski 製作）。

**套件維護者**，每位都對自己在 [Sparky-OS](https://github.com/Sparky-OS) 中的倉庫擁有完整權限：

| | |
| --- | --- |
| <a href="https://github.com/effcol"><img src="https://github.com/effcol.png?size=96" width="72" alt="Eff"></a> | **Eff (effcol)**<br>維護 [wiz3D](https://github.com/effcol/wiz3D)，一套以 iZ3D 為基礎、通用於 DirectX、OpenGL、AMD HD3D 與 NVIDIA 3D Vision 的立體 3D wrapper，適用於每個系統，以及它在這裡的套件 [Sparky-OS/wiz3D](https://github.com/Sparky-OS/wiz3D)。<br>[![Follow Eff](https://img.shields.io/badge/Follow-effcol-2777AD?style=flat-square&logo=github)](https://github.com/effcol) |
| <a href="https://github.com/halverneus"><img src="https://github.com/halverneus.png?size=96" width="72" alt="Jeromy Streets"></a> | **Jeromy Streets (halverneus)**<br>建立並維護 [org.kde.video](https://github.com/Sparky-OS/org.kde.video)，KDE Plasma 的影片桌布與鎖定畫面。<br>[![Follow Jeromy](https://img.shields.io/badge/Follow-halverneus-2777AD?style=flat-square&logo=github)](https://github.com/halverneus) |

**版本：**Sparky Stereo OS 9 "Mashtabba"，基於 Debian 14 "Forky"，僅有 KDE Plasma。

本版本賴以立足的所有人，名列於：[ATTRIBUTIONS.md](ATTRIBUTIONS.md)。

**特別感謝：**
- **David Fattal**，Leia 的共同創辦人與 DisplayXR 的維護者，感謝他的鼓勵、他的時間與他的付出，以及在他自己打造的 3D 顯示器上測試我們的桌面。
- **Milton Ponson** 與 **Christoph Dorn**，Daniel 在 W3C PM-KR 小組中的左右手，該小組的每一位成員，以及 W3C 的 **Dave Raggett**、**Ian Jacobs** 與 **Chris Needham**，他們為這項工作敞開了大門。
- **Tim Berners-Lee** 與所有一層一層建造網際網路、並把它分享給大家的人。
- **Foottroller** 團隊，為在 Linux 上用雙腳在 VR 中行走打開了大門。
- **Eric Allard**，在*Short Circuit*片中賦予 Johnny 5 生命的工程師；本片編劇 **S. S. Wilson** 與 **Brent Maddock**；以及配樂 **El DeBarge**、**Peter Wolf**、**Ina Wolf** 與 **David Shire**，在本版本建構過程中播放了無數次。

**引用它：** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**給它星星：** [![GitHub stars](https://img.shields.io/github/stars/Sparky-OS/sparky-stereo-os?style=flat-square&logo=github&label=Stars)](https://github.com/Sparky-OS/sparky-stereo-os/stargazers) ⭐ 如果 Sparky Stereo OS 對你有用，一顆星星能幫助更多人找到它。

**支持它：** [![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donate to SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) 贊助 Daniel 是資助本版本，而捐款給 SparkyLinux 則是支持 Paweł 的發行版，也就是本版本賴以建構的基底。

<a href="https://sourceforge.net/p/sparkyos/"><picture><source media="(prefers-color-scheme: dark)" srcset="https://sourceforge.net/sflogo.php?type=18&amp;group_id=3189517"><img alt="SparkyOS on SourceForge" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3189517" width="200"></picture></a>

<a id="licence"></a>
## 授權

文件採用 [Creative Commons Attribution 4.0 International 授權](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0)：可以分享與改編，但請註明 Sparky Stereo OS。

> 「資訊就是力量。但就像所有力量一樣，總有人想把它占為己有。」
> — Aaron Swartz，[*Guerilla Open Access Manifesto*](https://archive.org/details/GuerillaOpenAccessManifesto)（2008 年 7 月）

`docs/first-runs/` 下的腳本與 `tools/` 下的工具是程式碼，採用 GNU General Public License 第 2 版或更新版本 (GPL-2.0-or-later)，見 [LICENSE-GPL-2.0](LICENSE-GPL-2.0)。
