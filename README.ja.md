# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**今ある画面で3Dの制作と探究を。
絵を描き、写真や動画を編集し、分子や地球儀を調べ、映画やゲームも楽しめます。**
3Dテレビや3Dプロジェクター、VRヘッドセット、裸眼3Dディスプレイ、赤・シアンの眼鏡を使う普通のモニターなど、あらゆる種類の3D画面のために作られています。
普通の2Dモニターでは、同じデスクトップが何も変わらずそのまま使えます。
Sparky Stereo OSは、Paweł "pavroo" PijanowskiによるSparkyLinuxを基にDaniel Ramosが制作するエディションで、新しいStereo KDE Plasmaデスクトップを備えたLinuxシステムです。

**マシンにも地球にも軽く：** すべてのパッケージは、プログラムが読むことのないコメントや注記を除いて提供されるため、同じ作業でも処理、電力、機器の消耗が少なくて済みます。
[測定結果](docs/lean-code-packages.md#why-it-matters)：C++ヘッダーの読み込みはDebianより2〜4%少ない作業で済み、失われるものはありません。

<a href="docs/edition-in-detail.ja.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="半透明のウィンドウがある3Dのステレオデスクトップ。手前にDolphinの設定メニューとカラースキームの一覧があり、背後の透明なウィンドウは順に奥へ下がり、システムモニタと壁紙が最も奥にある（赤・シアンのアナグリフ）"></a>

<a href="docs/edition-in-detail.ja.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="ウィンドウ内で3D表示されるDOOM (2016)。下のPlasmaパネルは平面のまま（赤・シアンのアナグリフ）"></a> <a href="docs/edition-in-detail.ja.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="星々の手前に3D表示されるMarbleの地球儀（赤・シアンのアナグリフ）"></a> <a href="docs/edition-in-detail.ja.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="3Dのステレオデスクトップ。パネルは画面の位置に、音量のポップアップはその手前にあり、背後のウィンドウは順に奥へ下がる（赤・シアンのアナグリフ）"></a>

*赤・シアンの眼鏡で、これらの画像が3Dに見えます（[詳しく見る](docs/edition-in-detail.ja.md#seen-in-3d)）。*

**状況：テスター向けのベータ1です。** 3Dテレビ、赤・シアンの眼鏡を使った普通のモニター、安価なビューアーに入れたAndroidスマートフォンでテスト済みです。裸眼3Dディスプレイとスタンドアロンヘッドセットは作業中です。

**次のステップ：お使いのWindows PCで、USBメモリから、何もインストールせずに試してみてください：** [1ページ、10ステップ（英語）](docs/guides/try-on-windows.en.md)
<br>ダウンロードの申し込みと、お持ちの3D機器のご連絡は、あなたの言語でどうぞ： [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[科学と工学](docs/edition-in-detail.ja.md#science-and-engineering)：** Marbleの地球儀、KAlgebraのグラフ、Kalziumの分子を3Dで表示します。
- <a id="create"></a>**[制作](docs/edition-in-detail.ja.md#create)：** 3Dとディープカラー（各色8ビットではなく16ビット）で絵を描き、3D写真や動画を編集します。
- <a id="watch-and-play"></a>**[鑑賞とゲーム](docs/edition-in-detail.ja.md#watch-and-play)：** 3Dの映画、写真、ゲームをウィンドウ内や全画面で楽しめます。
- <a id="vr-is-also-a-stereo-monitor"></a>**[VRもステレオモニター](docs/edition-in-detail.ja.md#vr-is-also-a-stereo-monitor):** お使いのVRヘッドセットが棚の中で埃をかぶっていませんか？
- <a id="for-developers"></a>**[開発](docs/edition-in-detail.ja.md#for-developers)：** プログラムを一度3Dに対応させれば、デスクトップが各画面に合わせます。
- **[ほかのディストリビューションでは？](docs/other-distributions.md)** 私たちがほかのディストリビューション向けのパッケージを作らない理由と、そのメンテナーが修正を取り入れる方法を説明します。

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## ステレオデスクトップ：テーマデザインの新しい領域

**このデスクトップでは、何が飛び出し、何が奥に沈むかをテーマで決めます：** [テーマデザインの新しい領域](docs/edition-in-detail.ja.md#depth-on-the-desktop)。

<a id="how-it-works"></a>
## 仕組み

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**プログラムが各画像の情報を伝え、デスクトップが各画面に合わせます。**
ステレオでは、左右の画像を一つのフル・サイドバイサイドのバッファーで一緒に渡します。
提案中のHDR拡張は、同じ役割分担を通じて、画像の色情報と再構成情報を保持します。
[詳しく](docs/edition-in-detail.ja.md#how-it-works)

## このエディションについてさらに

- <a id="who-builds-it"></a>[制作している人](docs/edition-in-detail.ja.md#who-builds-it)
- <a id="where-it-is-going"></a>[今後の方向性](docs/edition-in-detail.ja.md#where-it-is-going)
- <a id="seen-in-3d"></a>[3Dで見る](docs/edition-in-detail.ja.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[テーマをデザイン・カスタマイズする方へ](docs/edition-in-detail.ja.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[一つの製品ではなく、オープンなスタックでステレオを](docs/edition-in-detail.ja.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[ステレオ3Dとディープカラーのために変更するプログラム](docs/edition-in-detail.ja.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[KDEのGitLabにある私たちのブランチ](docs/edition-in-detail.ja.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[Sparky Stereoの外でマージされた成果](docs/edition-in-detail.ja.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[ドキュメント](docs/edition-in-detail.ja.md#documents)
- <a id="tools"></a>[ツール](docs/edition-in-detail.ja.md#tools)
- <a id="the-base-three-open-lists"></a>[基盤となる三つのオープンなリスト](docs/edition-in-detail.ja.md#the-base-three-open-lists)

<a id="credit"></a>
## クレジット

Sparky Stereo OSは、Paweł "pavroo" PijanowskiによるSparkyLinuxを基に、Daniel Ramos (Capitain Jack)が制作するエディションです。
このエディションの基盤を築いたすべての人を、名前とともに記しています：[ATTRIBUTIONS.md](ATTRIBUTIONS.md)。

**引用するには：** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**支援する：** [![Danielを支援](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![SparkyLinuxに寄付](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Danielへの支援はこのエディションの資金となり、SparkyLinuxへの寄付は、その基盤であるPawełのディストリビューションを支えます。

[詳しく](docs/edition-in-detail.ja.md#credit)

<a id="licence"></a>
## ライセンス

ドキュメントは[Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/)（CC BY 4.0）で提供します。
Sparky Stereo OSのクレジットを表示すれば、共有や改変ができます。
[詳しく](docs/edition-in-detail.ja.md#licence)
