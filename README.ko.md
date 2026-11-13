# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇲🇽 [Español](README.es.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**이미 가지고 있는 화면에서 3D로 만들고 탐험하세요: 그림을 그리고, 사진과 비디오를 편집하고, 분자와 지구본을 연구한 다음, 영화를 보고 게임을 즐기세요.**
3D TV와 3D 프로젝터, VR 헤드셋, 무안경 3D 디스플레이, 적청 안경을 쓴 모든 모니터 등 모든 종류의 3D 화면을 위해 만들어졌습니다.
일반 2D 모니터에서는 같은 데스크톱이 아무 변경 없이 그대로 작동합니다.
Sparky Stereo OS는 Daniel Ramos의 SparkyLinux 에디션(Paweł "pavroo" Pijanowski 제작)으로, 새로운 Stereo KDE Plasma 데스크톱을 갖춘 Linux 시스템입니다.

**컴퓨터에도 지구에도 가볍게:** 모든 패키지는 프로그램이 읽지 않는 주석과 메모를 빼고 제공되므로, 같은 작업에 처리, 전력, 기기 마모가 더 적게 듭니다.
[측정 결과](docs/lean-code-packages.md#why-it-matters)(2016년 노트북): 컴파일러를 위해 프로그램을 준비하는 작업이 주석을 지우지 않은 같은 파일보다 2~4% 적으며, 잃는 것은 없습니다.

<a href="docs/edition-in-detail.ko.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="반투명 창이 있는 3D 스테레오 데스크톱: Dolphin의 설정 메뉴와 색 구성표 목록이 앞에 있고, 유리 창들이 뒤로 한 단계씩 물러서며, 시스템 모니터와 배경화면이 가장 깊은 곳에 있습니다 (적청 애너글리프)"></a>

<a href="docs/edition-in-detail.ko.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="창 안의 DOOM (2016), 3D로, 아래에 평면 Plasma 패널이 있습니다 (적청 애너글리프)"></a> <a href="docs/edition-in-detail.ko.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="별들 앞의 Marble 지구본, 3D로 (적청 애너글리프)"></a> <a href="docs/edition-in-detail.ko.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="3D 스테레오 데스크톱: 화면의 패널, 그 앞의 사운드 팝업, 뒤로 물러서는 창들 (적청 애너글리프)"></a>

*적청 안경으로 이들을 3D로 볼 수 있습니다 ([더 보기](docs/edition-in-detail.ko.md#seen-in-3d)).*

**상태: 테스터용 베타 1입니다.** 3D TV, 적청 안경을 쓴 일반 모니터, 저렴한 뷰어에 넣은 Android 휴대폰에서 테스트했습니다. 무안경 디스플레이와 독립형 헤드셋은 진행 중입니다.

**다음 단계: 사용 중인 Windows PC에서 USB 메모리로, 아무것도 설치하지 않고 사용해 보세요:** [한 페이지, 열 단계(영어)](docs/guides/try-on-windows.en.md)
<br>다운로드를 요청하고 여러분의 3D 장비를 알려 주세요. 원하는 언어로: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇲🇽](https://github.com/Sparky-OS/sparky-stereo-os/issues/351) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[과학 및 공학](docs/edition-in-detail.ko.md#science-and-engineering):** Marble의 지구본, KAlgebra의 그래프, Kalzium의 분자를 3D로; 3D 모델과 회로 기판은 진행 중입니다. 스캔은 계획 중입니다: 부품, 현장, 표본을 찍은 비디오가 3D 모델이 됩니다.
- <a id="create"></a>**[만들기](docs/edition-in-detail.ko.md#create):** 3D로 그리고 딥 컬러(8비트 대신 색상당 16비트)로 그리며, 3D 사진과 비디오를 편집합니다. 스캔은 계획 중입니다: 물체나 장소를 찍은 비디오가 둘러볼 수 있는 3D 모델이 됩니다.
- <a id="watch-and-play"></a>**[보기 및 플레이](docs/edition-in-detail.ko.md#watch-and-play):** 3D 영화, 사진, 게임을 창 또는 전체 화면으로.
- <a id="vr-is-also-a-stereo-monitor"></a>**[VR도 스테레오 모니터입니다](docs/edition-in-detail.ko.md#vr-is-also-a-stereo-monitor):** 헤드셋도, 뷰어에 넣은 휴대폰도 이 데스크톱의 3D 화면이 됩니다.
- <a id="for-developers"></a>**[개발](docs/edition-in-detail.ko.md#for-developers):** 프로그램을 한 번 3D로 만드세요; 데스크톱이 각 화면에 맞게 조정합니다.
- **[다른 배포판?](docs/other-distributions.md)** 패키징하지 않는 이유와 유지 관리자가 우리의 수정 사항을 채택하는 방법.

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## 스테레오 데스크톱: 테마 디자인의 새로운 지평

**이 데스크톱에서 테마가 무엇이 튀어나오고 무엇이 들어가는지 결정합니다:** [테마 디자인의 새로운 지평](docs/edition-in-detail.ko.md#depth-on-the-desktop).

<a id="how-it-works"></a>
## 작동 방식

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**프로그램은 각 그림을 설명하고, 데스크톱은 각 화면에 맞게 조정합니다.** 스테레오에서는 두 보기가 하나의 풀 사이드 바이 사이드 버퍼에서 함께 이동합니다. 제안된 HDR 확장은 같은 작업 분배를 통해 그림의 색상 설명과 복구 정보를 유지합니다.
[자세히](docs/edition-in-detail.ko.md#how-it-works)

## 에디션에 대해 더 알아보기

- <a id="who-builds-it"></a>[누가 만듭니다](docs/edition-in-detail.ko.md#who-builds-it)
- <a id="where-it-is-going"></a>[진행 방향](docs/edition-in-detail.ko.md#where-it-is-going)
- <a id="seen-in-3d"></a>[3D로 보기](docs/edition-in-detail.ko.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[테마 디자이너와 커스터마이저를 위해](docs/edition-in-detail.ko.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[단일 제품이 아닌 열린 스택의 스테레오](docs/edition-in-detail.ko.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[에디션이 스테레오 3D와 딥 컬러를 위해 변경하는 프로그램](docs/edition-in-detail.ko.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[KDE GitLab의 우리 브랜치](docs/edition-in-detail.ko.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[Sparky Stereo 외부에서 병합됨](docs/edition-in-detail.ko.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[문서](docs/edition-in-detail.ko.md#documents)
- <a id="tools"></a>[도구](docs/edition-in-detail.ko.md#tools)
- <a id="the-base-three-open-lists"></a>[기반: 세 개의 열린 목록](docs/edition-in-detail.ko.md#the-base-three-open-lists)

<a id="credit"></a>
## 크레딧

Sparky Stereo OS, Daniel Ramos (Capitain Jack)의 SparkyLinux 에디션 (Paweł "pavroo" Pijanowski 제작).
이 에디션이 기반으로 삼은 모든 사람, 이름으로: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**인용:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**후원:** [![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![SparkyLinux 기부](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Daniel 후원은 이 에디션을 지원하고, SparkyLinux 기부는 그 기반이 되는 Paweł의 배포판을 지원합니다.

[자세히](docs/edition-in-detail.ko.md#credit)

<a id="licence"></a>
## 라이선스

문서는 [Creative Commons Attribution 4.0 International 라이선스](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0)로 제공됩니다: Sparky Stereo OS의 출처를 남기면 공유하고 수정할 수 있습니다.
[자세히](docs/edition-in-detail.ko.md#licence)
