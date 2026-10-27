# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**今ある画面で3Dの制作と探究を。
絵を描き、写真や動画を編集し、分子や地球儀を調べ、映画やゲームも楽しめます。**
3Dテレビのほか、安価な赤・シアンの眼鏡を使えば普通のモニターでも利用でき、対応するAndroidスマートフォンと安価なビューアーでも使えるようになりました。
[USB接続で実用になるステレオデスクトップ](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)を、古い機器でテストしています。
Sparky Stereo OSは、Paweł "pavroo" PijanowskiによるSparkyLinuxを基にDaniel Ramosが制作するエディションで、新しいStereo KDE Plasmaデスクトップを備えたLinuxシステムです。

**アーキテクチャを読む：** [図解ガイドとリポジトリの構成図](docs/architectural-synthesis.md)、[原寸大のインフォグラフィックとテキスト版](docs/architecture-infographic.md)があります。
DanielのGemini / NotebookLMによる調査を基に、内容を整理して検証しています。

<a href="#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="半透明のウィンドウがある3Dのステレオデスクトップ。手前にDolphinの設定メニューとカラースキームの一覧があり、背後の透明なウィンドウは順に奥へ下がり、システムモニタと壁紙が最も奥にある（赤・シアンのアナグリフ）"></a>

**ステレオデスクトップ：** デスクトップそのものに奥行きがあります。
操作中のウィンドウは画面の位置にあり、ここのMarbleのメニューとサブメニューのように、そのメニューが手前に出ます。
背後のウィンドウは重ねた紙のように順に奥へ下がり、壁紙が最も奥にあります。
Marbleの地球儀のように、3Dプログラムはウィンドウ内でそれ自体の奥行きを保ちます。
それぞれ数ピクセルで、利用者が選んだ範囲に収まります。

<a href="#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="ウィンドウ内で3D表示されるDOOM (2016)。下のPlasmaパネルは平面のまま（赤・シアンのアナグリフ）"></a> <a href="#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="星々の手前に3D表示されるMarbleの地球儀（赤・シアンのアナグリフ）"></a> <a href="#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="3Dのステレオデスクトップ。パネルは画面の位置に、音量のポップアップはその手前にあり、背後のウィンドウは順に奥へ下がる（赤・シアンのアナグリフ）"></a>

*赤・シアンの眼鏡で、これらの画像が3Dに見えます（[詳しく見る](#seen-in-3d)）。*

**開発中：** [Flat Headsetの開発版APKと、それに対応するPCの更新手順](https://github.com/Sparky-OS/flat-headset/tree/main/apk)を公開しています。
テスター向けの開発版ISOは、Secure Bootが有効な新しいPC、BIOSを使う古いPC、32ビットUEFIのマシンで起動するようになりました。
ステレオエディションの最終版ISOは準備中です（[今後の方向性](#where-it-is-going)）。

- **[制作](#create)：** 3Dとディープカラー（各色8ビットではなく16ビット）で絵を描き、3D写真や動画を編集します。
- **[科学と工学](#science-and-engineering)：** Marbleの地球儀、KAlgebraのグラフ、Kalziumの分子を3Dで表示します。
  3Dモデルと回路基板への対応は作業中です。
- **[鑑賞とゲーム](#watch-and-play)：** 3Dの映画、写真、ゲームをウィンドウ内や全画面で楽しめます。
- **[開発](#for-developers)：** プログラムを一度3Dに対応させれば、デスクトップが各画面に合わせます。
- **[ほかのディストリビューションでは？](docs/other-distributions.md)** 私たちがほかのディストリビューション向けのパッケージを作らない理由と、そのメンテナーが修正を取り入れる方法を説明します。

**次の一歩：お使いの3D機器を教えてください。**
準備が整ったら、いち早くお知らせします。
<br>お使いの言語で登録してください：[🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

<a id="vr-is-also-a-stereo-monitor"></a>
### VRもステレオモニター

ほとんどのヘッドセットは左右の目にそれぞれ小さな画面を備え、それ以外のものは3Dテレビと同じように1枚の画面を二つに分けます。
そのため、この一つのデスクトップで両方に対応できます。
- **ポケットの中にある3D画面：** 安価なCardboard型ビューアーを使うと、対応するAndroidスマートフォンがステレオデスクトップの画面になり、左右の目に別々の映像をフルカラーで表示できます。
  10月19日、DanielはRedmi Note 7と2016年製のA10ノートPCを使い、USB接続のハーフ・トップアンドボトム構成を実用になると判断しました。
  デスクトップが動作し、マウスもよく反応します。
  動画は大きく改善しましたが、まだ多少のかくつきがあります。
  家庭内Wi-Fiでの最初のテストはUSBに近い感触でしたが、Direct Wi-Fiでは停止が長くなります。
  フル解像度やほかの機器では、引き続きテストが必要です（[測定結果と制約](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)）。
  描画はPCが行うため、古いスマートフォンを別の用途に生かせます。
  [開発版APK、ソースコード、対応するPCの更新手順](https://github.com/Sparky-OS/flat-headset/tree/main/apk)をまとめて公開しています。
  まず開発版のライブUSBか、インストール済みのPCを更新してください。
  Androidビューアーは引き続きテスト版です。
  [最初のテスト](https://github.com/Sparky-OS/flat-headset#the-first-test-12-october-2026)と[スマートフォン上のデスクトップ](https://github.com/Sparky-OS/flat-headset#the-desktop-on-the-phone-14-october-2026)の写真もあります。
- **VR映画：** Binoは360°や180°の映画を、平面でも3Dでも、どの3D画面でも再生でき、マウスで視点を回せます。
- **VRゲーム：** Half-Life 2とDOOM (2016)は、VRモードを通じて3D画面に表示できます。

<a id="who-builds-it"></a>
## 制作している人

ブラジリアのファヴェーラからDanielが制作し、これまでに二人の人間の貢献者が参加しています。
Jeromy StreetsのPlasma向け動画壁紙（[org.kde.video](https://github.com/Sparky-OS/org.kde.video)）は、現在はSparky-OSに置かれ、本人がメンテナーを務めています。
Eff (effcol)は、iZ3Dのコードを[wiz3D](https://github.com/Sparky-OS/wiz3D)として存続させ、ここで保守しています。
Linuxのステレオ対応は何年もボランティアを待っていました。
以前の取り組みはレビュー担当者に3Dディスプレイがなかったために停滞し、作業はカーネル、Mesa、KWin、FFmpeg、プレーヤー、ウェブ標準にまたがります。
ほかにこの作業を引き受ける開発者が現れなかったため、ここで働くほかのパートナーはAIで、Danielが指示と検証を行い、[AIによる貢献の記録](docs/ai-provenance.md)に名前を記しています。
人の手で作りたいと思う方の参加も歓迎します。
すべてのフォークを公開し、どの作業にも参加できます。
ビルドとテストはすべて、家庭用PCと2016年製ノートPCという普通の2台で行っています：[使用機器](docs/hardware.md)。
そのノートPCでは、デスクトップのすべてのテストケースで2Dでも3Dでも24 fpsを維持しています：[KWinのステレオ表示にかかる負荷の実測](docs/measurements/kwin-stereo-cost-a10-2026-10-23.md)。

<a id="where-it-is-going"></a>
## 今後の方向性

このエディションは動作する実証であり、そこで得た知見をオープンな標準に還元します。
DanielはMilton Ponsonとともに、W3Cの[Procedural Memory Knowledge Representation Community Group (PM-KR)](https://www.w3.org/community/pm-kr/)の議長を務めています。
私たちの報告書[Linuxとウェブにおけるステレオ3D](https://www.w3.org/publications/spec-generator/?type=respec&url=https://raw.githubusercontent.com/w3c-cg/pm-kr/main/reports/source/stereo-3d-adoption-report.html)は、個人提案として公開した、グループでの議論のための資料です。
既存のどの仕様がすでに3Dを扱っているか、Linuxやウェブが何を採用してこなかったか、ブラウザーには何が必要かを扱っています。
2026年10月13日にW3CのMedia and Entertainment Interest Groupで行った発表も、この内容です（[スライド](docs/talks/2026-10-13-w3c-me-ig.md)）。
W3Cアカウントがあれば無料でグループに参加できます。
お使いのディスプレイでのテスト、報告書のレビュー、利用事例の提供を歓迎します。

<a id="create"></a>
## 制作

**3Dで絵を描き、写真や動画を編集できます。
各色8ビットではなく16ビットのディープカラーで絵を描くこともできます。**
- **ペイント：** Kritaでは16ビットのキャンバスで描けるほか、左右の目それぞれ16ビットの3Dキャンバスでも描けます。
- **写真：** digiKamとShowfotoは、アルバム、ライトテーブル、スライドショー、エディタで3D写真を表示します。
  KolourPaintは3D画像を編集し、3Dの識別情報を付けて保存します。
- **動画：** Kdenliveではクリップが自身の3Dレイアウトを保持し、モニターで3D表示でき、レンダリング結果にも3Dの識別情報が残ります。
- **ストーリー：** [StorySplat](https://storysplat.com)（「3Dスキャンをインタラクティブなツアーに」）は、実在する場所の3Dスキャン内を巡るツアーをブラウザー上で作成します。
  その3D Viewは、登録されているどの出力でもツアーを3D表示でき、最初のテストはSonyの3Dテレビでサイドバイサイド表示を使って行いました。

各プログラムの詳細：[プログラム](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

<a id="for-theme-designers-and-customizers"></a>
### テーマをデザイン・カスタマイズする方へ

**このデスクトップでは、何が飛び出し、何が奥に沈むかをテーマで決めます：** [テーマデザインの新しい領域](#depth-on-the-desktop)。

<a id="science-and-engineering"></a>
## 科学と工学

**3Dで調べ、設計できます。
地球儀、グラフ、分子はすでに3Dで動作し、3Dモデルと回路基板への対応は作業中です。**
- **学習と科学：** Marbleの地球儀、KAlgebraのグラフ、Kalziumの分子、Kubrickのキューブは、3Dデスクトップ上では標準で3D表示されます。
- **3Dモデルと回路基板：** OpenSCAD、KiCad、F3Dの3Dプレビューに取り組んでいます。
- **デスクから顧客まで、フルカラーで：** 同じモデルを、技術者のデスクにある裸眼3Dモニター（[DisplayXR](https://displayxr.org)との連携を作業中）、チームや研修向けの3Dテレビやプロジェクター、Cardboard型ビューアーに入れた従業員や顧客それぞれのスマートフォン（[Flat Headset](https://github.com/Sparky-OS/flat-headset)）で、奥行きを持って表示します。
  端から端までオープンなので、一つのディスプレイメーカーに縛られません。

各プログラムの詳細：[プログラム](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

<a id="watch-and-play"></a>
## 鑑賞とゲーム

**3Dの映画、写真、ゲームは、それぞれのウィンドウ内や全画面で3D表示され、デスクトップのほかの部分はそのままです。**
- **画面：** 2010年から2013年のHDMI 3D機器を含む3Dテレビ、モニター、プロジェクターのほか、赤・シアンの眼鏡を使えば普通のモニターにも対応します。
  各画面で同時に異なる方式の3Dを表示でき、DisplayXRチームと裸眼3Dモニターへの対応も進めています。
- **映画：** Haruna、VLC、mpv、Bino、PlasmaTubeなどで3D動画を3D再生できます。
- **写真：** Gwenview、digiKam、KolourPaintは、3D写真（MPO、JPS、ステレオPNG）を3D表示します。
- **ゲーム：** DOOM (2016)はウィンドウ内で、Half-Life 2も、いずれもVRモードを通じて動作します（[その仕組み](docs/formula.md)）。
- **ゲーム向けに調整したカーネル：** このエディションは、私たちのステレオパッチを適用したLinux 7.3を使います。
  新しいスケジューラは、作者自身のテストで、古いCPU上のあるゲームの最低フレームレートを4 fpsから29 fpsへ引き上げました（[測定値](https://lore.kernel.org/all/20260511113104.563854162@infradead.org/)）。
  また、ビデオメモリの少ないAMDカードで、ゲームのメモリをカード上に保持できるようにします（[変更内容](https://pixelcluster.dev/VRAM-Mgmt-fixed/)）。

各プログラムで何ができるようになり、どう実証したか：[プログラム](#programs-the-edition-changes-for-stereo-3d-and-deep-colour)。

<a id="seen-in-3d"></a>
### 3Dで見る

このページの画像は、左右の目の画像を両方とも保存する、このエディションのSpectacleで撮影したスクリーンショットです。
ここでは赤・シアンの眼鏡で3Dに見えます。
MPOファイルは、このエディションの写真プログラムで開くと、登録されているどの出力でも3D表示できます。
すべての画像の赤・シアン版とMPOの直接ダウンロードは、[スクリーンショットギャラリー](docs/screenshots/README.md)にあります。
Danielが2014年から2016年にLG Optimus 3Dで撮影した3D写真とオリジナルファイルは、[写真ギャラリー](docs/photos/README.md)にあります。

- **ステレオデスクトップ、半透明**（[MPO](https://raw.githubusercontent.com/Sparky-OS/sparky-stereo-os/main/docs/screenshots/translucent-stereo-desktop.mpo)）。
  2026年10月15日に3Dテレビで撮影しました。
  ウィンドウがガラスのように透け、重なりが見えます。
  左右の目の画像間で測定したずれは、フォーカスのあるDolphinのウィンドウが0 px、その設定メニューが+5 px（手前で、利用者が設定した飛び出しの上限）、長いカラースキームの一覧が0 pxです。
  一覧は画面上端に接しており、手前に出るものが端に触れる場合は画面の位置にとどまるためです。
  背後のThunderbirdは-3 px、システムモニタのウィジェットと壁紙は-10 px、パネルは0 pxです。
  二つのメールアドレスは、左右両方の画像でぼかしています。
- **ステレオデスクトップ、メニューの上にメニュー**（[MPO](docs/screenshots/stereo-desktop-dialogs.mpo)）。
  2026年10月13日、フレームパッキングの3Dテレビで撮影しました。
  左右の目の画像間で測定したずれは、フォーカスのあるMarbleのウィンドウが0 px、その設定メニューが+2 px、パネルのサブメニューが+4 px、背後の四つのウィンドウが-3、-5、-8、-10 px、ウィジェットと壁紙が-10 pxです。
  ウィンドウ内のMarble自体の3Dでは、地球のラベルが+12 px、星のラベルが-13 pxです。
  背後にあるDiolinuxのチャットメッセージはぼかしています。
- **普通のウィンドウ内のDOOM (2016)**（[MPO](docs/screenshots/doom-2016-in-a-window.mpo)）。
  CactusVRStudiosによるDOOM (2016)のVR化MOD、[KHARVOX](https://github.com/CactusVRStudios/KHARVOX)（MIT）を基にしています。
  ゲームには奥行きがあり、パネルとウィンドウ枠は左右両方の目で平面のままです。
  左右の目の画像間で測定したずれは、最も近い岩が23 px、遠くの山が1 px、パネルが0 pxです。
- **Marbleの地球儀**（[MPO](docs/screenshots/marble-globe.mpo)）。
  地球は画面の手前（+11 px）、星は奥（-12 px）にあり、サイドパネルは平面です。
  この画像は、その後の修正より前に撮影しました。
  現在のMarbleの様子は、メニューが重なる画像にあります。
- **ステレオデスクトップ、ポップアップ**（[MPO](docs/screenshots/stereo-desktop.mpo)）。
  同じ日に撮影しました。
  左右の目の画像間で測定したずれは、パネルが0 px（画面の位置）、音量のポップアップが+4 px（手前）、背後の三つのウィンドウが-3、-7、-10 pxです。
  システムモニタのウィジェットは-10 pxで、壁紙とともに奥にあります。

<a id="depth-on-the-desktop"></a>
<a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## ステレオデスクトップ：テーマデザインの新しい領域

**見た目だけでなく、何が飛び出し、何が奥に沈むかを、初めてテーマで決められます。**
何十年もの間、影、面取り、盛り上がったボタンは見かけだけの表現でした。
ステレオデスクトップでは本当の奥行きになり、利用者が選んだ範囲の数ピクセルで穏やかに表現します（KDE システム設定の「3D Depth」）。

- **使うものは手前に：** メニュー、ツールチップ、通知、ダイアログが手前に出て、作業中のウィンドウは画面の位置にとどまります。
  *実装済みで、2026年10月13日に3Dテレビで確認しています（[上の画像](#seen-in-3d)）。*
- **残りは奥に：** 背後のウィンドウは重ねた紙のように順に奥へ下がり、壁紙が最も奥に沈みます。
  *実装済み。*
- **小さなものも位置を保つ：** ポインターはその下にあるものと同じ奥行きになり、影は落ちる先の面に付きます。
  スライドの上に置いたウェブカメラのような固定ウィンドウは、すべての手前に出続けます。
  *実装済み。*
- **3Dの壁紙：** 3D写真を背景にすると、すべてのウィンドウよりも奥で、その写真自体の飛び出しと奥行きを保ちます。
  *実装済み。*
  次はJeromy Streetsの動画壁紙で、3D動画の背景に対応します。
  *今後対応。*
- **3Dのスクリーンセーバー：** 定番の星空やステレオスクリーンセーバーを、本当の3Dで表示します。
  *実装済み。*
- **3Dの画像とアイコン：** Dolphinのプレビューや画像ビューアーで、3D写真を3D表示します。
  *実装済み。*
  左右の目それぞれの画像を一対として描くアイコンは、このエディション独自の外観であるStereo Oxygenの一部です。
  *今後対応。*
- **本当に飛び出し、奥に沈む効果：** 閉じるウィンドウが破片となって手前に飛んできたり、画面の奥に沈んで床で跳ね返ったりします。
  *私たちのKWinブランチに実装済みで、次のパッケージに入ります。*
  ウィンドウを3Dで扇状に並べる切り替え画面や、本当の3DによるDesktop Cubeにも対応します。
  *今後対応。*
- **電源を入れたときから3D：** 起動スプラッシュとログイン画面は、メイン画面に保存した3Dモードに従います。
  *実装済み。*

**普通の2Dデスクトップとしても使えます。**
普通の画面では何も変わりません。
同じテーマ、同じ配置、同じ効果を、一度だけ描画します。
3Dは、表示できる画面か赤・シアンの眼鏡を通した場合にだけ現れ、3D向けのテーマは2Dのテーマとしても完全に機能します。

<a id="the-desktop-cube-what-one-format-makes-possible"></a>詳しくは、[デスクトップの奥行き](docs/depth-on-the-desktop.md)と[テーマをデザイン・カスタマイズする方へ](docs/for-theme-designers.md)をご覧ください。
[テーマのIssue](https://github.com/Sparky-OS/sparky-stereo-os/issues/78)では、アイデア、スケッチ、3Dモックアップを歓迎します。

<a id="for-developers"></a>
## 開発者向け

**プログラムを一度3Dに対応させれば、左右の目の画像を受け取ったデスクトップが、すべての画面への表示を引き受けます。**
今ある画面で開発し、確認できます。
- [普通のモニターで3DとXRを開発する](docs/develop-3d-on-an-ordinary-monitor.md)：ここから始めてください。
- [ウェブページから3Dシーンをステレオ表示する](docs/web-3d-in-stereo.md)：three.js、WebGL、WebXRを使い、どのブラウザーでも使える赤・シアンの眼鏡から、あらゆる3D画面まで対応します。
- [内部で使う形式](docs/house-formats.md)と[ステレオの役割分担](docs/stereo-labor-division.md)：仕様に基づく規則です。
- [3Dテレビなしでステレオをテストする](docs/test-stereo-without-a-3d-tv.md)と[3Dディスプレイを備えた仮想マシン](docs/stereo-vm.md)：仮想ディスプレイや仮想マシンで3D出力をテストします。
  Stereo KWinを備えた準備済みのルートファイルシステムは、[私たちのリポジトリサーバー](https://repo.sparkyos.org/bench/kwin-root/)にあります。
- [スキル](skills/README.md)：このエディションの作業に参加する人とAIアシスタント向けの手順です。

<a id="how-it-works"></a>
## 仕組み

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**プログラムが各画像の情報を伝え、デスクトップが各画面に合わせます。**
ステレオでは、左右の画像を一つのフル・サイドバイサイドのバッファーで一緒に渡します。
提案中のHDR拡張は、同じ役割分担を通じて、画像の色情報と再構成情報を保持します。

**ステレオの取り決めを3行で。**
- **Stereo KWin**（私たちのステレオ対応を加えたKDE Plasmaのコンポジター）は、任意の解像度のフル・サイドバイサイドを扱います。
- **プログラム**は、どの標準のステレオでもデコードまたは生成し、任意の解像度のフル・サイドバイサイドとしてStereo KWinに渡します。
- **出力**（画面の種類ごとに用意する、Stereo KWinの最終段のフィルター）が、各画面に必要な形式へ変換します。

フル・サイドバイサイドを使う理由、2基のGPUから2台の3Dテレビに一つのデスクトップを表示する方法、同じ原理をHDRに拡張する方法は、[仕組み](docs/how-it-works.md)で説明しています。
[HDRの宣言](docs/stereo-hdr-content.md)は、実装と、形式をまたいだ機器でのテストを待つ設計です。
HDRの受け渡しに使う表現形式は、検証が必要な技術上の選択肢として残っています。
既存のステレオとディープカラーのテストでは、このHDR経路を検証したことにはなりません。

<a id="stereo-in-the-open-stack-not-in-one-product"></a>
## 一つの製品ではなく、オープンなスタックでステレオを

ほかでは、ステレオは一つのヘッドセット、一社のインジェクター、一社のカーネルという、一つの製品に結び付いています。
ここではオープンな層（KDE、カーネル、ファイル形式）の性質として実現するので、今お持ちの画面に届きます：[オープンなスタックでのステレオ](docs/open-stack.md)。

<a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>
## ステレオ3Dとディープカラーのために変更するプログラム

映画や写真から地球儀や分子まで、3Dが各プログラムにもたらすもの：[プログラム](docs/programs.md)。
各プログラムをどう変更し、実証したかを、表示経路、動画、科学と工学、画像、シミュレーター、システム、未完成の項目に分けて説明しています：[プログラムの詳細](docs/programs-in-detail.md)。

<a id="our-branches-on-kdes-gitlab"></a>
## KDEのGitLabにある私たちのブランチ

KDEへの変更はすべて、[invent.kde.org](https://invent.kde.org/danielcamposramos)上の私たちのフォークのブランチに置き、上流への提案前にKDE自身のCIでテストしています：[ブランチとCIの結果](docs/kde-branches.md)。

<a id="merged-outside-sparky-stereo"></a>
## Sparky Stereoの外でマージされた成果

**2026年10月26日：IANAがMatroskaのStereoMode 15から20を割り当てました。**
これらは画像と奥行きを一つのフレームに収める配置を表します。
先に10月20日には、左目、右目、背景の独立した奥行きトラックに平面型3から5が割り当てられました。
どちらの登録も私たちのstereo-layer仕様を参照しています。
[現在の登録表](https://www.iana.org/assignments/matroska)と[識別子の登録と上流でのマージ](docs/upstream-merges.md#registered-identifiers)。

画面に届くまでの途中でプログラムがステレオやディープカラーを損なう場合は、そのプログラム自身のプロジェクトへ修正を届けます。
HandBrake、mpv、Qt Multimedia、PeerTubeなどが、私たちの作業から生まれた修正をマージしています。
各修正と、それをマージしたメンテナー、審査中のものは、[Sparky Stereoの外でマージされた成果](docs/upstream-merges.md)にまとめています。
それぞれの作業は、完了と呼ぶ前に、動作していることを数値とアナグリフ・MPOの画像で示します：[実証](docs/proofs/README.md)。
ステレオに携わる人々が公開の場で述べたことを、リンク付きで紹介しています：[寄せられた言葉](docs/what-people-said.md)。

<a id="documents"></a>
## ドキュメント

[VRエンジンから3Dディスプレイへ表示する方法](docs/formula.md)、[実機のテレビでKWinを初めて動かした記録](docs/first-runs/kwin-2026-10-01/README.md)、2026年10月13日の[W3C発表スライド](docs/talks/2026-10-13-w3c-me-ig.md)があります。
すべてのページは[docs](docs/)にあります。

<a id="tools"></a>
## ツール

[vkms-stereo-bench](tools/vkms-stereo-bench/README.md)は仮想ディスプレイの3Dモードを検査し、[hibernate-bench](tools/hibernate-bench/README.md)はSecure Boot下でのハイバネーションを検査します。
どちらも仮想マシン内で行います。

<a id="the-base-three-open-lists"></a>
## 基盤となる三つのオープンなリスト

このエディションの基になった調査は、誰でもコピーできる三つのリスト（CC0）として公開しています。
ステレオ3Dの[awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy)、HDRとディープカラーの[awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr)、VRの[awesome-vr](https://github.com/danielcamposramos/awesome-vr)です。

<a id="credit"></a>
## クレジット

Sparky Stereo OSは、Paweł "pavroo" PijanowskiによるSparkyLinuxを基に、Daniel Ramos (Capitain Jack)が制作するエディションです。

**パッケージメンテナー：** それぞれが[Sparky-OS](https://github.com/Sparky-OS)にある自分のリポジトリの全権限を持ちます。

| | |
| --- | --- |
| <a href="https://github.com/effcol"><img src="https://github.com/effcol.png?size=96" width="72" alt="Eff"></a> | **Eff (effcol)**<br>[wiz3D](https://github.com/effcol/wiz3D)と、このエディション向けのパッケージ[Sparky-OS/wiz3D](https://github.com/Sparky-OS/wiz3D)を保守しています。wiz3DはiZ3Dを基にした、DirectX、OpenGL、AMD HD3D、NVIDIA 3D Vision向けの汎用ステレオスコピック3Dラッパーで、あらゆるシステムを対象とします。<br>[![Effをフォロー](https://img.shields.io/badge/Follow-effcol-2777AD?style=flat-square&logo=github)](https://github.com/effcol) |
| <a href="https://github.com/halverneus"><img src="https://github.com/halverneus.png?size=96" width="72" alt="Jeromy Streets"></a> | **Jeromy Streets (halverneus)**<br>KDE Plasma向けの動画壁紙とロック画面、[org.kde.video](https://github.com/Sparky-OS/org.kde.video)を作成し、保守しています。<br>[![Jeromyをフォロー](https://img.shields.io/badge/Follow-halverneus-2777AD?style=flat-square&logo=github)](https://github.com/halverneus) |

**バージョン：** Sparky Stereo OS 9 "Mashtabba"。
Debian 14 "Forky"を基にし、KDE Plasmaのみを使います。

このエディションの基盤を築いたすべての人を、名前とともに記しています：[ATTRIBUTIONS.md](ATTRIBUTIONS.md)。

**特別な感謝：**
- **David Fattal**。
  Leiaの共同創業者でDisplayXRのメンテナーとして、励まし、時間、労力を寄せ、自ら製作する3Dディスプレイで私たちのデスクトップをテストしてくれました。
- **Milton Ponson**と**Christoph Dorn**。
  W3C PM-KRグループでDanielを支える二人と、グループのすべてのメンバー、そしてこの取り組みに扉を開いてくれたW3Cの**Dave Raggett**、**Ian Jacobs**、**Chris Needham**に感謝します。
- **Tim Berners-Lee**と、インターネットを一層ずつ築き、皆に開放してくれたすべての人。
- Linuxで自分の足を使ってVRの中を歩く道を開いてくれた、**Foottroller**チーム。
- *Short Circuit*でJohnny 5に命を吹き込んだ技術者、**Eric Allard**。
  映画の脚本家、**S. S. Wilson**と**Brent Maddock**。
  そして、このエディションの制作中に何度も聴いた、**El DeBarge**、**Peter Wolf**、**Ina Wolf**、**David Shire**による音楽。

**引用するには：** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**スターを付ける：** [![GitHub stars](https://img.shields.io/github/stars/Sparky-OS/sparky-stereo-os?style=flat-square&logo=github&label=Stars)](https://github.com/Sparky-OS/sparky-stereo-os/stargazers) ⭐ Sparky Stereo OSが役立つと感じたら、スターを付けると、ほかの人が見つける助けになります。

**支援する：** [![Danielを支援](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![SparkyLinuxに寄付](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Danielへの支援はこのエディションの資金となり、SparkyLinuxへの寄付は、その基盤であるPawełのディストリビューションを支えます。

<a href="https://sourceforge.net/p/sparkyos/"><picture><source media="(prefers-color-scheme: dark)" srcset="https://sourceforge.net/sflogo.php?type=18&amp;group_id=3189517"><img alt="SourceForge上のSparkyOS" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3189517" width="200"></picture></a>

<a id="licence"></a>
## ライセンス

ドキュメントは[Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/)（CC BY 4.0）で提供します。
Sparky Stereo OSのクレジットを表示すれば、共有や改変ができます。

> 「情報は力です。
> しかし、あらゆる力と同じように、それを独り占めしようとする人がいます。」
> — Aaron Swartz、[*Guerilla Open Access Manifesto*](https://archive.org/details/GuerillaOpenAccessManifesto)（2008年7月）

`docs/first-runs/`のスクリプトと`tools/`のツールはコードで、GNU General Public License, version 2 or later（GPL-2.0-or-later）で提供します。
[LICENSE-GPL-2.0](LICENSE-GPL-2.0)をご覧ください。
