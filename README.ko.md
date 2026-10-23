# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇫🇷 [Français](README.fr.md) · 🇰🇷 [한국어](README.ko.md)

**이미 가지고 있는 화면에서 3D로 만들고 탐험하세요: 그림을 그리고, 사진과 비디오를 편집하고, 분자와 지구본을 연구한 다음, 영화를 보고 게임을 즐기세요.**
3D TV가 작동하고, 값싼 적청 안경을 쓴 일반 모니터도 작동하며, 이제 저렴한 뷰어에 넣은 호환 Android 휴대폰도 작동합니다: [USB를 통한 사용 가능한 스테레오 데스크톱](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md), 구형 하드웨어에서 테스트되었습니다.
Sparky Stereo OS는 Daniel Ramos의 SparkyLinux 에디션(Paweł "pavroo" Pijanowski 제작)으로, 새로운 Stereo KDE Plasma 데스크톱을 갖춘 Linux 시스템입니다.

**아키텍처 읽기:** [그림 가이드 및 저장소 지도](docs/architectural-synthesis.md), [전체 크기 인포그래픽 및 텍스트 버전](docs/architecture-infographic.md) 포함, Daniel의 Gemini / NotebookLM 연구에서 각색 및 검증되었습니다.

<a href="#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="반투명 창이 있는 3D 스테레오 데스크톱: Dolphin의 설정 메뉴와 색 구성표 목록이 앞에 있고, 유리 창들이 뒤로 한 단계씩 물러서며, 시스템 모니터와 배경화면이 가장 깊은 곳에 있습니다 (적청 애너글리프)"></a>

**스테레오 데스크톱:** 데스크톱 자체에 깊이가 있습니다.
사용 중인 것이 화면에 있고 그 메뉴가 앞으로 나옵니다. 여기 Marble의 메뉴와 하위 메뉴처럼 말이죠. 뒤의 창들은 종이 더미처럼 하나씩 뒤로 물러서고, 배경화면이 가장 깊습니다.
3D 프로그램은 Marble의 지구본처럼 창 안에 자체 깊이를 유지합니다.
각각 몇 픽셀씩, 사용자가 선택한 한도 내에서요.

<a href="#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="창 안의 DOOM (2016), 3D로, 아래에 평면 Plasma 패널이 있습니다 (적청 애너글리프)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="별들 앞의 Marble 지구본, 3D로 (적청 애너글리프)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="3D 스테레오 데스크톱: 화면의 패널, 그 앞의 사운드 팝업, 뒤로 물러서는 창들 (적청 애너글리프)"></a>

*적청 안경으로 이들을 3D로 볼 수 있습니다 ([더 보기](#seen-in-3d)).*

**개발 중:** [Flat Headset 개발 APK 및 일치하는 PC 업데이트 지침](https://github.com/Sparky-OS/flat-headset/tree/main/apk)이 제공됩니다; 최종 스테레오 에디션 ISO는 아직 준비 중입니다 ([진행 방향](#where-it-is-going)).

- **[만들기](#create):** 3D로 그리고 딥 컬러(8비트 대신 색상당 16비트)로 그리며, 3D 사진과 비디오를 편집합니다.
- **[과학 및 공학](#science-and-engineering):** Marble의 지구본, KAlgebra의 그래프, Kalzium의 분자를 3D로; 3D 모델과 회로 기판은 진행 중입니다.
- **[보기 및 플레이](#watch-and-play):** 3D 영화, 사진, 게임을 창 또는 전체 화면으로.
- **[개발](#for-developers):** 프로그램을 한 번 3D로 만드세요; 데스크톱이 각 화면에 맞게 조정합니다.
- **[다른 배포판?](docs/other-distributions.md)** 패키징하지 않는 이유와 유지 관리자가 우리의 수정 사항을 채택하는 방법.

**다음 단계: 여러분의 3D 장비에 대해 알려주세요** 그리고 준비되면 가장 먼저 소식을 들으세요.
<br>언어별로 가입하세요: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

### VR도 스테레오 모니터입니다

대부분의 헤드셋은 각 눈에 하나씩, 한 쌍의 작은 화면이고, 나머지는 3D TV처럼 한 화면을 둘로 나눕니다. 그래서 이 하나의 데스크톱이 둘 다 지원합니다.
- **이미 주머니에 있는 3D 화면:** 저렴한 Cardboard 스타일 뷰어가 호환 Android 휴대폰을 스테레오 데스크톱용 화면으로 바꿉니다. 풀 컬러로, 각 눈에 별도의 뷰를 제공합니다. 10월 19일, Daniel은 Redmi Note 7과 2016년 A10 노트북에서 USB 절반 상하 설정을 사용 가능한 것으로 승인했습니다: 데스크톱이 작동하고 마우스가 반응합니다. 비디오는 많이 개선되었지만 여전히 다소 끊깁니다; 첫 가정 Wi-Fi 테스트는 USB에 더 가깝게 느껴지고, Direct Wi-Fi는 더 긴 멈춤이 있습니다. 전체 해상도와 더 많은 기기는 여전히 테스트가 필요합니다 ([측정 및 한계](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)). PC가 그리기를 담당하므로 구형 휴대폰에 또 다른 용도를 제공합니다. [개발 APK, 소스 및 일치하는 PC 업데이트 지침](https://github.com/Sparky-OS/flat-headset/tree/main/apk)이 함께 제공됩니다; 개발 라이브 USB 또는 설치된 PC를 먼저 업데이트하세요. Android 뷰어는 테스트 빌드로 유지됩니다. [첫 테스트](https://github.com/Sparky-OS/flat-headset#the-first-test-12-october-2026)와 [휴대폰의 데스크톱](https://github.com/Sparky-OS/flat-headset#the-desktop-on-the-phone-14-october-2026) 사진.
- **VR 영화:** Bino가 360° 및 180° 영화를 평면 또는 3D로, 어떤 3D 화면에서든 재생하고, 마우스가 시점을 돌립니다.
- **VR 게임:** Half-Life 2와 DOOM (2016)이 VR 모드를 통해 3D 화면에 도달합니다.

<a id="who-builds-it"></a>
## 누가 만듭니다

Brasília의 favela 출신 Daniel, 현재까지 두 명의 인간 기여자: Jeromy Streets는 Plasma용 비디오 배경화면([org.kde.video](https://github.com/Sparky-OS/org.kde.video))을 만들었고 이제 Sparky-OS에서 유지 관리자로 함께하며, Eff (effcol)는 iZ3D의 코드를 [wiz3D](https://github.com/Sparky-OS/wiz3D)로 살려내고 여기서 유지 관리합니다.
Linux의 스테레오는 수년간 자원봉사자를 기다렸습니다: 이전 시도는 리뷰어에게 3D 디스플레이가 없어서 중단되었고, 작업은 커널, Mesa, KWin, FFmpeg, 플레이어 및 웹 표준에 걸쳐 있습니다.
이를 이어갈 다른 개발자가 나서지 않아, 여기서 함께 일하는 다른 파트너는 AI 파트너이며, Daniel이 지시하고 확인하며 [AI 출처](docs/ai-provenance.md)에 명시되어 있습니다.
인간의 손으로 만들어지는 것을 보고 싶다면 언제든 환영합니다: 모든 포크는 공개이고, 모든 작업은 열려 있습니다.
모든 것은 가정용 PC와 2016년 노트북, 두 대의 일반 기계에서 구축되고 테스트됩니다: [하드웨어](docs/hardware.md).

<a id="where-it-is-going"></a>
## 진행 방향

에디션은 작동하는 증거이며, 발견한 것은 공개 표준으로 돌아갑니다.
Daniel은 Milton Ponson과 함께 W3C [절차적 기억 지식 표현 커뮤니티 그룹 (PM-KR)](https://www.w3.org/community/pm-kr/)의 의장입니다.
우리의 보고서 [Linux와 웹의 스테레오 3D](https://www.w3.org/publications/spec-generator/?type=respec&url=https://raw.githubusercontent.com/w3c-cg/pm-kr/main/reports/source/stereo-3d-adoption-report.html)가 개별 제안으로 있으며, 그룹이 논의할 입력 자료입니다: 어떤 기존 사양이 이미 3D를 지원하는지, Linux와 웹이 채택하지 않은 것은 무엇인지, 브라우저에 필요한 것은 무엇인지.
이는 2026년 10월 13일 W3C 미디어 및 엔터테인먼트 관심 그룹에서의 우리 발표 주제이기도 합니다 ([슬라이드](docs/talks/2026-10-13-w3c-me-ig.md)).
W3C 계정으로 그룹 가입은 무료이며, 도움을 환영합니다: 여러분의 디스플레이에서 테스트하고, 보고서를 검토하거나, 사용 사례를 가져오세요.

<a id="create"></a>
## 만들기

**3D로 그림을 그리고, 사진과 비디오를 편집하고, 딥 컬러로 그리세요: 8비트 대신 색상당 16비트.**
- **그리기:** Krita가 16비트 캔버스에 그리고, 각 눈에 16비트인 3D 캔버스에도 그립니다.
- **사진:** digiKam과 Showfoto가 앨범, 라이트 테이블, 슬라이드쇼 및 편집기에서 3D 사진을 보여줍니다; KolourPaint가 3D 사진을 편집하고 3D 표시와 함께 저장합니다.
- **비디오:** Kdenlive에서 클립이 자신의 3D 레이아웃을 알고, 모니터가 3D로 보여줄 수 있으며, 렌더가 3D 표시를 유지합니다.
- **스토리:** [StorySplat](https://storysplat.com) ("3D 스캔을 대화형 투어로 바꾸세요")이 실제 장소의 3D 스캔 안에서 브라우저에서 바로 투어를 만들고, 3D View가 등록된 출력에서 3D로 보여줍니다. Sony 3D 텔레비전에서 나란히 처음 테스트되었습니다.

각 프로그램 전체: [프로그램](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="for-theme-designers-and-customizers"></a>
### 테마 디자이너와 커스터마이저를 위해

**이 데스크톱에서 테마가 무엇이 튀어나오고 무엇이 들어가는지 결정합니다:** [테마 디자인의 새로운 지평](#depth-on-the-desktop).

<a id="science-and-engineering"></a>
## 과학 및 공학

**3D로 연구하고 설계하세요: 지구본, 그래프, 분자가 오늘 3D로 작동하고, 3D 모델과 회로 기판은 진행 중입니다.**
- **학습 및 과학:** Marble의 지구본, KAlgebra의 그래프, Kalzium의 분자와 Kubrick 큐브가 3D 데스크톱에서 기본적으로 3D로.
- **3D 모델 및 회로 기판:** OpenSCAD, KiCad, F3D의 3D 미리보기가 진행 중입니다.
- **책상에서 클라이언트까지, 풀 컬러로:** 엔지니어 책상의 무안경 3D 모니터에서 ([DisplayXR](https://displayxr.org)과 함께, 진행 중), 팀이나 교육 수업을 위한 3D TV나 프로젝터에서, 그리고 모든 직원과 클라이언트의 휴대폰에서 Cardboard 뷰어로 ([Flat Headset](https://github.com/Sparky-OS/flat-headset)) 같은 모델을 깊이 있게. 끝에서 끝까지 개방되어 있어 누구도 한 디스플레이 제조사에 묶이지 않습니다.

각 프로그램 전체: [프로그램](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="watch-and-play"></a>
## 보기 및 플레이

**3D 영화, 사진, 게임이 자체 창이나 전체 화면에서 3D로 표시되고, 데스크톱의 나머지는 그대로 유지됩니다.**
- **화면:** 3D TV, 모니터 또는 프로젝터, 2010년부터 2013년까지의 HDMI 3D 세트 포함, 또는 적청 안경을 쓴 일반 모니터; 각 화면이 동시에 다른 종류의 3D를 보여줄 수 있으며, 무안경 3D 모니터는 DisplayXR 팀과 함께 진행 중입니다.
- **영화:** 3D 비디오가 Haruna, VLC, mpv, Bino, PlasmaTube 등에서 3D로 재생됩니다.
- **사진:** Gwenview, digiKam, KolourPaint가 3D 사진(MPO, JPS, 스테레오 PNG)을 3D로 보여줍니다.
- **게임:** 창 안의 DOOM (2016)과 Half-Life 2, 둘 다 VR 모드를 통해 ([공식](docs/formula.md)).

각 프로그램, 얻는 것과 입증 방법: [프로그램](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="seen-in-3d"></a>
### 3D로 보기

이 페이지의 사진들은 에디션의 Spectacle로 촬영한 스크린샷이며, 양쪽 눈을 모두 유지합니다.
적청 안경으로 여기서 3D로 볼 수 있습니다; MPO 파일은 에디션의 사진 프로그램에서 등록된 출력에서 3D로 열립니다. 각각 적청 버전과 직접 MPO 다운로드가 있는 모든 것: [스크린샷 갤러리](docs/screenshots/README.md). 2014년부터 2016년까지 LG Optimus 3D 휴대폰으로 촬영한 Daniel의 3D 사진, 원본 포함: [사진 갤러리](docs/photos/README.md).

- **스테레오 데스크톱, 반투명** ([MPO](https://raw.githubusercontent.com/Sparky-OS/sparky-stereo-os/main/docs/screenshots/translucent-stereo-desktop.mpo)), 3D TV에서, 2026년 10월 15일. 창들이 유리라서 더미가 비쳐 보입니다. 양안 간 측정: Dolphin, 포커스된 창, 0 px, 그 설정 메뉴 +5 px (앞, 사용자의 팝 한도에서); 긴 색 구성표 목록 0 px, 화면 상단에 닿아 있고 가장자리에 닿는 팝된 것은 화면에 머물기 때문; Thunderbird 뒤 -3 px; 시스템 모니터 위젯과 배경화면 -10 px; 패널 0 px. 두 이메일 주소는 양쪽 눈에서 흐리게 처리되었습니다.
- **스테레오 데스크톱, 메뉴 위의 메뉴** ([MPO](docs/screenshots/stereo-desktop-dialogs.mpo)), 프레임 패킹의 3D TV에서, 2026년 10월 13일. 양안 간 측정: 포커스된 Marble 창 0 px, 그 설정 메뉴 +2 px, Panels 하위 메뉴 +4 px, 뒤의 네 창 -3, -5, -8, -10 px, 위젯과 배경화면 -10 px; 창 안에서 Marble 자체의 3D: 지구 라벨 +12 px, 별들 -13 px. 뒤의 Diolinux 채팅 메시지는 흐리게 처리되었습니다.
- **일반 창 안의 DOOM (2016)** ([MPO](docs/screenshots/doom-2016-in-a-window.mpo)), [KHARVOX](https://github.com/CactusVRStudios/KHARVOX) 기반, CactusVRStudios의 DOOM (2016) VR 변환 모드 (MIT): 게임에는 깊이가 있고 패널과 창 테두리는 양쪽 눈에서 평면 그대로입니다. 양안 간 측정: 가장 가까운 바위 23 px, 먼 산 1 px, 패널 0 px.
- **Marble의 지구본** ([MPO](docs/screenshots/marble-globe.mpo)): 지구는 화면 앞에 (+11 px), 별들은 그 뒤에 (-12 px), 옆 패널은 평면입니다. 이 캡처는 이후 수정 이전의 것입니다; 지금의 Marble은 메뉴 위의 메뉴 그림에서 볼 수 있습니다.
- **스테레오 데스크톱, 팝업** ([MPO](docs/screenshots/stereo-desktop.mpo)), 같은 날. 양안 간 측정: 패널 0 px (화면에), 사운드 팝업 +4 px (앞에), 뒤의 세 창 -3, -7, -10 px, 시스템 모니터 위젯 -10 px, 배경화면과 함께 가장 뒤에.

<a id="depth-on-the-desktop"></a>
## 스테레오 데스크톱: 테마 디자인의 새로운 지평

**처음으로 사용 가능한 데스크톱에서 테마가 무엇이 튀어나오고 무엇이 들어가는지 결정합니다, 외모뿐이 아니라.**
수십 년 동안 그림자, 베벨과 돌출된 버튼은 그럴듯한 모양이었을 뿐입니다; 스테레오 데스크톱에서는 실제이고 부드럽습니다: 몇 픽셀, 사용자가 선택한 한도 내에서 (시스템 설정, "3D Depth").

- **사용하는 것은 튀어나옵니다:** 메뉴, 도구 설명, 알림 및 대화 상자가 사용자 쪽으로 나오고, 작업 중인 창은 화면에 머뭅니다. *구축되었으며 2026년 10월 13일 3D TV에서 확인했습니다 ([맨 위 그림](#seen-in-3d)).*
- **나머지는 뒤로 물러납니다:** 뒤의 창들은 종이 더미처럼 하나씩 뒤로 물러나고, 배경화면이 가장 깊이 들어갑니다. *구축됨.*
- **작은 요소들은 자리를 지킵니다:** 포인터는 그 위에 있는 것의 레벨을 따르고, 그림자는 떨어지는 곳에 놓이며, 슬라이드 위의 웹캠처럼 고정된 창은 모든 것 위로 계속 튀어나옵니다. *구축됨.*
- **배경화면을 3D로:** 배경화면인 3D 사진은 자체 팝과 깊이를 유지하며, 모든 창보다 훨씬 뒤에 있습니다. *구축됨.* 다음은 Jeromy Streets의 비디오 배경화면과 함께 3D 비디오 배경화면입니다. *예정됨.*
- **3D 화면 보호기:** 기본 별밭 화면 보호기와 스테레오 화면 보호기를 실제 3D로. *구축됨.*
- **3D 사진과 아이콘:** 3D 사진은 Dolphin의 미리보기와 사진 뷰어에서 3D로 표시됩니다. *구축됨.* 각 눈에 한 개씩 그린 한 쌍의 아이콘은 에디션 고유의 모습인 Stereo Oxygen의 일부입니다. *예정됨.*
- **실제로 튀어나오고 들어가는 효과:** 닫히는 창은 조각으로 사용자 쪽으로 날아가거나 화면 뒤로 들어가 바닥에 튕길 수 있습니다. *우리 KWin 브랜치에 구축되었으며 다음 패키지에 제공됩니다.* 3D로 부채꼴로 펼쳐지는 창 전환기와 실제 3D의 Desktop Cube도 예정되어 있습니다. *예정됨.*
- **전원을 켠 순간부터 3D:** 부트 스플래시와 로그인 화면을 3D 화면에서 3D로. *예정됨.*

**그리고 이것은 여전히 정상적인 2D 데스크톱입니다.**
일반 화면에서는 아무것도 바뀌지 않습니다: 같은 테마, 같은 레이아웃, 같은 효과를 한 번만 그립니다.
3D는 화면이 표시할 수 있는 곳에서만 나타나거나 적청 안경을 통해 나타나며, 3D를 위해 만든 테마도 완전한 2D 테마입니다.

<a id="the-desktop-cube-what-one-format-makes-possible"></a>자세한 내용: [데스크톱의 깊이](docs/depth-on-the-desktop.md), [테마 디자이너와 커스터마이저를 위해](docs/for-theme-designers.md); 아이디어, 스케치 및 3D 목업은 [테마 이슈](https://github.com/Sparky-OS/sparky-stereo-os/issues/78)에 환영합니다.

<a id="for-developers"></a>
## 개발자를 위해

**프로그램을 한 번 3D로 만드세요: 데스크톱에 양쪽 눈을 주면 모든 화면을 맡습니다.**
이미 있는 화면에서 작업을 작성하고 확인할 수 있습니다.
- [일반 모니터에서 3D 및 XR 개발](docs/develop-3d-on-an-ordinary-monitor.md): 여기에서 시작하세요.
- [웹 페이지에서 스테레오로 보는 3D 장면](docs/web-3d-in-stereo.md): three.js, WebGL 및 WebXR, 모든 브라우저의 적청 안경에서 모든 3D 화면까지.
- [자체 형식](docs/house-formats.md), [스테레오 작업 분배](docs/stereo-labor-division.md): 규격에 연결된 규칙.
- [3D TV 없이 스테레오 테스트](docs/test-stereo-without-a-3d-tv.md), [3D 화면이 있는 가상 머신](docs/stereo-vm.md): 가상 화면 또는 가상 머신에서 3D 출력을 테스트하세요; Stereo KWin이 포함된 준비된 루트 파일 시스템은 [우리 저장소 서버](https://repo.sparkyos.org/bench/kwin-root/)에 있습니다.
- [스킬](skills/README.md): 이 에디션에서 작업하는 사람과 AI 어시스턴트를 위한 지침.

<a id="how-it-works"></a>
## 작동 방식

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**프로그램은 각 그림을 설명하고, 데스크톱은 각 화면에 맞게 조정합니다.** 스테레오에서는 두 보기가 하나의 풀 사이드 바이 사이드 버퍼에서 함께 이동합니다. 제안된 HDR 확장은 같은 작업 분배를 통해 그림의 색상 설명과 복구 정보를 유지합니다.

**세 줄짜리 스테레오 계약입니다.**
- **Stereo KWin** (우리의 스테레오 변경이 있는 KDE Plasma 컴포지터)은 어떤 해상도에서든 풀 사이드 바이 사이드를 사용합니다.
- **프로그램**은 어떤 표준으로든 스테레오를 디코딩하거나 만들고, 어떤 해상도에서든 풀 사이드 바이 사이드를 Stereo KWin에 전달합니다.
- **출력** (끝에서 Stereo KWin의 필터, 화면 종류마다 하나씩)은 각 화면에 필요한 것으로 변환합니다.

왜 풀 사이드 바이 사이드인지, 두 GPU에서 두 3D TV로 하나의 데스크톱을 쓰는 방법과 같은 원리가 HDR로 어떻게 확장되는지: [작동 방식](docs/how-it-works.md). [HDR 선언](docs/stereo-hdr-content.md)은 구현과 범 형식 장치 테스트가 필요한 설계이며; HDR 교환 표현은 검증해야 할 공학 선택으로 남아 있습니다. 기존의 스테레오 및 딥 컬러 테스트는 이 HDR 경로를 검증하지 않습니다.

<a id="stereo-in-the-open-stack-not-in-one-product"></a>
## 단일 제품이 아닌 열린 스택의 스테레오

다른 곳에서 스테레오는 하나의 제품인 한 헤드셋, 한 제조사의 인젝터, 한 제조사의 커널에 묶입니다.
여기에서는 열린 층 (KDE, 커널, 파일 형식)의 속성이므로 사용자가 이미 가진 화면에 도달합니다: [열린 스택의 스테레오](docs/open-stack.md).

<a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>
## 에디션이 스테레오 3D와 딥 컬러를 위해 변경하는 프로그램

영화와 사진에서 지구본과 분자까지, 각 프로그램에 3D가 무엇을 가져다 주는지: [프로그램](docs/programs.md).
각 프로그램이 화면 경로, 비디오, 과학과 공학, 이미지, 시뮬레이터, 시스템과 아직 끝나지 않은 항목별로 어떻게 변경되고 입증되었는지: [프로그램 상세](docs/programs-in-detail.md).

<a id="our-branches-on-kdes-gitlab"></a>
## KDE GitLab의 우리 브랜치

모든 KDE 변경은 [invent.kde.org](https://invent.kde.org/danielcamposramos)의 우리 포크에서 만든 브랜치이며, 업스트림에 제안하기 전에 KDE 자체 CI로 테스트됩니다: [브랜치와 CI 결과](docs/kde-branches.md).

<a id="merged-outside-sparky-stereo"></a>
## Sparky Stereo 외부에서 병합됨

**2026년 10월 20일: IANA가 세 개의 Matroska 깊이 평면 유형을 등록했습니다**, 우리 stereo-layer 규격을 참조하여. 이제 분리된 깊이 트랙에는 왼쪽 눈 평면, 오른쪽 눈 평면, 배경 평면의 식별자가 있습니다. 제안된 여섯 개의 팩 프레임 모드는 전문가 검토 중입니다. [등록 기점과 업스트림 병합](docs/upstream-merges.md#registered-identifiers).

프로그램이 화면으로 가는 길에서 스테레오나 딥 컬러를 망가뜨리면, 수정은 그 프로그램 자체 프로젝트로 갑니다.
HandBrake, mpv, Qt Multimedia 및 PeerTube 같은 프로젝트는 우리 작업에서 온 수정을 병합했습니다; 병합한 유지 관리자와 검토 중인 항목까지, 전체는 [Sparky Stereo 외부에서 병합됨](docs/upstream-merges.md)에 있습니다.
각 조각은 끝났다고 말하기 전에 작동하는 것으로 보여주며, 수치와 적청 애너글리프 및 MPO 그림이 함께 있습니다: [입증](docs/proofs/README.md).
스테레오로 작업하는 사람들이 이에 대해 공개적으로 말한 것과 링크: [사람들의 평가](docs/what-people-said.md).

<a id="documents"></a>
## 문서

[VR 엔진에서 3D 화면으로 가는 공식](docs/formula.md), [실제 TV에서의 첫 KWin 실행](docs/first-runs/kwin-2026-10-01/README.md), 2026년 10월 13일의 [W3C 발표 슬라이드](docs/talks/2026-10-13-w3c-me-ig.md); 모든 페이지는 [docs](docs/)에 있습니다.

<a id="tools"></a>
## 도구

[vkms-stereo-bench](tools/vkms-stereo-bench/README.md)는 가상 화면에서 3D 모드를 점검하고, [hibernate-bench](tools/hibernate-bench/README.md)는 Secure Boot 상태의 절전 복구를 점검합니다; 둘 다 가상 머신에서입니다.

<a id="the-base-three-open-lists"></a>
## 기반: 세 개의 열린 목록

이 에디션 뒤의 연구는 누구나 복제할 수 있는 (CC0) 세 개의 정리된 공개 목록에 있습니다: 스테레오 3D의 [awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy), HDR과 딥 컬러의 [awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr), 가상 현실의 [awesome-vr](https://github.com/danielcamposramos/awesome-vr).

<a id="credit"></a>
## 크레딧

Sparky Stereo OS, Daniel Ramos (Capitain Jack)의 SparkyLinux 에디션 (Paweł "pavroo" Pijanowski 제작).

**패키지 유지 관리자**, 각자 [Sparky-OS](https://github.com/Sparky-OS)에서 자신의 저장소에 대한 전체 권리를 갖습니다:

| | |
| --- | --- |
| <a href="https://github.com/effcol"><img src="https://github.com/effcol.png?size=96" width="72" alt="Eff"></a> | **Eff (effcol)**<br>[wiz3D](https://github.com/effcol/wiz3D)를 유지 관리합니다: iZ3D를 기반으로 DirectX, OpenGL, AMD HD3D 및 NVIDIA 3D Vision을 위한 보편적인 스테레오스코픽 3D 래퍼이며, 모든 시스템을 위한 것입니다; 여기의 [Sparky-OS/wiz3D](https://github.com/Sparky-OS/wiz3D) 패키지도 유지 관리합니다.<br>[![Follow Eff](https://img.shields.io/badge/Follow-effcol-2777AD?style=flat-square&logo=github)](https://github.com/effcol) |
| <a href="https://github.com/halverneus"><img src="https://github.com/halverneus.png?size=96" width="72" alt="Jeromy Streets"></a> | **Jeromy Streets (halverneus)**<br>KDE Plasma용 비디오 배경화면과 잠금 화면인 [org.kde.video](https://github.com/Sparky-OS/org.kde.video)를 만들고 유지 관리합니다.<br>[![Follow Jeromy](https://img.shields.io/badge/Follow-halverneus-2777AD?style=flat-square&logo=github)](https://github.com/halverneus) |

**버전:** Sparky Stereo OS 9 "Mashtabba", Debian 14 "Forky" 기반이며 KDE Plasma만 사용합니다.

이 에디션이 기반으로 삼은 모든 사람, 이름으로: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**특별 감사:**
- **David Fattal**, Leia의 공동 창립자이자 DisplayXR의 유지 관리자, 격려와 시간과 노력, 그리고 그가 만든 3D 화면들에서 우리 데스크톱을 테스트한 것에 대해.
- **Milton Ponson**과 **Christoph Dorn**, W3C PM-KR 그룹에서 Daniel의 대변인, 그 그룹의 모든 구성원, 그리고 W3C의 **Dave Raggett**, **Ian Jacobs**, **Chris Needham**, 이 작업을 위한 문을 열어 준 분들.
- **Tim Berners-Lee**와 층층이 인터넷을 만들어 모두에게 내어 준 모든 사람.
- **Foottroller** 팀, Linux에서 발을 리듬 장치로 쓰는 VR 걷기를 열어 준 것에 대해.
- **Eric Allard**, *Short Circuit*에서 Johnny 5를 살아 있게 만든 공학자; 영화 작가 **S. S. Wilson**과 **Brent Maddock**; 그리고 **El DeBarge**, **Peter Wolf**, **Ina Wolf**, **David Shire**의 음악, 이 에디션을 만드는 동안 여러 번 들려 주었습니다.

**인용:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**스타를 눌러 주세요:** [![GitHub stars](https://img.shields.io/github/stars/Sparky-OS/sparky-stereo-os?style=flat-square&logo=github&label=Stars)](https://github.com/Sparky-OS/sparky-stereo-os/stargazers) ⭐ Sparky Stereo OS가 유용하다면 스타가 다른 사람도 찾는 데 도움이 됩니다.

**후원:** [![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![SparkyLinux 기부](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Daniel 후원은 이 에디션을 지원하고, SparkyLinux 기부는 그 기반이 되는 Paweł의 배포판을 지원합니다.

<a href="https://sourceforge.net/p/sparkyos/"><picture><source media="(prefers-color-scheme: dark)" srcset="https://sourceforge.net/sflogo.php?type=18&amp;group_id=3189517"><img alt="SparkyOS on SourceForge" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3189517" width="200"></picture></a>

<a id="licence"></a>
## 라이선스

문서는 [Creative Commons Attribution 4.0 International 라이선스](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0)로 제공됩니다: Sparky Stereo OS의 출처를 남기면 공유하고 수정할 수 있습니다.

> "정보는 힘입니다. 그러나 모든 힘처럼, 자기만 차지하려는 사람들이 있습니다."
> — Aaron Swartz, [*Guerilla Open Access Manifesto*](https://archive.org/details/GuerillaOpenAccessManifesto) (2008년 7월)

`docs/first-runs/` 아래의 스크립트와 `tools/` 아래의 도구는 코드이며 GNU General Public License, version 2 or later (GPL-2.0-or-later)로 제공됩니다; [LICENSE-GPL-2.0](LICENSE-GPL-2.0)을 보십시오.
