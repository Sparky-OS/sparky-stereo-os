# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**Twórz i odkrywaj w 3D na ekranie, który już masz: maluj, edytuj zdjęcia i filmy, badaj cząsteczki i globusy, a potem oglądaj filmy i graj.**
Sprawdzi się telewizor 3D, zwykły monitor z tanimi okularami czerwono-cyjanowymi, a teraz także zgodny telefon z systemem Android w niedrogich goglach: [pulpit stereoskopowy, z którego można korzystać przez USB](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md), przetestowany na starszym sprzęcie.
Sparky Stereo OS, edycja SparkyLinux autorstwa Daniela Ramosa (twórcą SparkyLinux jest Paweł "pavroo" Pijanowski), to system Linux z nowym pulpitem Stereo KDE Plasma.

**Poznaj architekturę:** [ilustrowany przewodnik i mapa repozytorium](docs/architectural-synthesis.md), z [infografiką w pełnym rozmiarze i wersją tekstową](docs/architecture-infographic.md), opracowane i sprawdzone na podstawie badań Daniela z Gemini / NotebookLM.

<a href="#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="Pulpit stereoskopowy w 3D z półprzezroczystymi oknami: menu Ustawienia programu Dolphin i lista zestawów barw z przodu, szklane okna za nimi cofające się kolejno, monitor systemu i tapeta najgłębiej (anaglif czerwono-cyjanowy)"></a>

**Pulpit stereoskopowy:** sam pulpit ma głębię.
To, z czego korzystasz, znajduje się w płaszczyźnie ekranu, a jego menu wysuwają się do przodu, jak tutaj menu i podmenu programu Marble; okna za nim cofają się jedno po drugim, jak kartki w stosie, z tapetą najgłębiej.
Program 3D zachowuje własną głębię wewnątrz swojego okna, jak globus w Marble.
Każdy element o kilka pikseli, w wybranych przez Ciebie granicach.

<a href="#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) w oknie, w 3D, z płaskim panelem Plasma poniżej (anaglif czerwono-cyjanowy)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Globus w Marble przed gwiazdami, w 3D (anaglif czerwono-cyjanowy)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="Pulpit stereoskopowy w 3D: panel w płaszczyźnie ekranu, wyskakujące okno dźwięku przed nim i kolejne okna cofające się w głąb (anaglif czerwono-cyjanowy)"></a>

*W okularach czerwono-cyjanowych zobaczysz te obrazy w 3D ([więcej](#seen-in-3d)).*

**W trakcie prac:** dostępne są [rozwojowy APK Flat Headset i odpowiednie instrukcje aktualizacji komputera](https://github.com/Sparky-OS/flat-headset/tree/main/apk), a rozwojowy obraz ISO dla testerów uruchamia się już na nowych komputerach z włączonym Secure Boot, starszych komputerach z BIOS i maszynach z 32-bitowym UEFI; ostateczny obraz ISO edycji stereoskopowej jest nadal przygotowywany ([dokąd zmierzamy](#where-it-is-going)).

- **[Twórz](#create):** maluj w 3D i z większą głębią koloru (16 bitów na kolor zamiast 8), edytuj zdjęcia i filmy 3D.
- **[Nauka i inżynieria](#science-and-engineering):** globus w Marble, wykresy w KAlgebra i cząsteczki w Kalzium w 3D; trwają prace nad modelami 3D i płytkami drukowanymi.
- **[Oglądaj i graj](#watch-and-play):** filmy, zdjęcia i gry 3D, w oknie lub na pełnym ekranie.
- **[Programuj](#for-developers):** dodaj 3D do programu raz; pulpit dostosuje je do każdego ekranu.
- **[Inna dystrybucja?](docs/other-distributions.md)** Dlaczego nie przygotowujemy dla niej pakietów i jak jej opiekunowie mogą przejąć nasze poprawki.

**Następny krok: opowiedz nam o swoim sprzęcie 3D**, a jako jedna z pierwszych osób dowiesz się, gdy system będzie gotowy.
<br>Zgłoś się w swoim języku: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

<a id="vr-is-also-a-stereo-monitor"></a>
### VR to także monitor stereoskopowy

**Czy twoje gogle VR zbierają kurz w szafie?**
Sparky Stereo OS zamienia je z powrotem w ekran 3D: graj w gry 3D, oglądaj filmy 3D, edytuj treści 3D, pisz e-maile i koduj na całym pulpicie w 3D oraz graj w gry PCVR przez SteamVR tam, gdzie twoje gogle działają w Linuksie.
Zgodny telefon z Androidem w niedrogich goglach już dziś działa; samodzielne zestawy, takie jak Quest, są następne, jeszcze nieprzetestowane.

Większość gogli ma parę małych ekranów, po jednym dla każdego oka, a pozostałe dzielą jeden ekran na dwie części, podobnie jak telewizor 3D, więc ten sam pulpit obsługuje oba rozwiązania.
- **Ekran 3D, który już masz w kieszeni:** niedrogie gogle typu Cardboard zamieniają zgodny telefon z systemem Android w ekran pulpitu stereoskopowego, w pełnym kolorze, z osobnym widokiem dla każdego oka. 19 października Daniel uznał konfigurację USB z obrazami jeden nad drugim, każdy o połowie wysokości, na Redmi Note 7 i laptopie A10 z 2016 roku za nadającą się do użytku: pulpit działa, a mysz reaguje sprawnie. Wideo znacznie się poprawiło, ale wciąż nie jest całkiem płynne; pierwszy test przez domowe Wi-Fi daje wrażenia bliższe USB, natomiast Direct Wi-Fi ma dłuższe zacięcia. Pełna rozdzielczość i kolejne urządzenia nadal wymagają testów ([pomiary i ograniczenia](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)). Obraz rysuje komputer, dzięki czemu starszy telefon zyskuje nowe zastosowanie. [Rozwojowy APK, kod źródłowy i odpowiednie instrukcje aktualizacji komputera](https://github.com/Sparky-OS/flat-headset/tree/main/apk) są dostępne razem; najpierw zaktualizuj rozwojowy system live na USB lub system zainstalowany na komputerze. Aplikacja do wyświetlania obrazu w systemie Android pozostaje wersją testową. Zdjęcia z [pierwszego testu](https://github.com/Sparky-OS/flat-headset#the-first-test-12-october-2026) i [pulpitu na telefonie](https://github.com/Sparky-OS/flat-headset#the-desktop-on-the-phone-14-october-2026).
- **Filmy VR:** Bino odtwarza filmy 360° i 180°, płaskie lub w 3D, na dowolnym ekranie 3D, a mysz obraca widok.
- **Gry VR:** Half-Life 2 i DOOM (2016) trafiają na ekran 3D dzięki swoim trybom VR.

<a id="who-builds-it"></a>
## Kto to tworzy

Tworzy go Daniel, z faweli w Brasílii; dotąd pomagają mu dwie osoby: Jeromy Streets, którego tapeta wideo dla środowiska Plasma ([org.kde.video](https://github.com/Sparky-OS/org.kde.video)) jest teraz w Sparky-OS pod jego opieką, oraz Eff (effcol), który rozwija kod iZ3D jako [wiz3D](https://github.com/Sparky-OS/wiz3D) i opiekuje się nim tutaj.
Stereoskopia w systemie Linux czekała latami na ochotników: wcześniejsze próby utknęły, bo recenzenci nie mieli ekranu 3D, a praca obejmuje jądro, Mesa, KWin, FFmpeg, odtwarzacze i standardy internetowe.
Nie zgłosił się żaden inny programista, który podjąłby się tego zadania, więc pozostali pracujący tu partnerzy to AI, kierowane i sprawdzane przez Daniela oraz wymienione w [informacjach o udziale AI](docs/ai-provenance.md).
Jeśli wolisz, żeby tworzyli to ludzie, zapraszamy: każdy fork jest publiczny i każde zadanie jest otwarte.
Całość powstaje i jest testowana na dwóch zwykłych maszynach, domowym komputerze i laptopie z 2016 roku: [sprzęt](docs/hardware.md).
Na tym laptopie każdy scenariusz pulpitu utrzymuje 24 kl./s w 2D i 3D: [zmierzony koszt stereoskopii w KWin](docs/measurements/kwin-stereo-cost-a10-2026-10-23.md).

<a id="where-it-is-going"></a>
## Dokąd zmierzamy

Edycja jest działającym dowodem, a to, co dzięki niej odkrywamy, wraca do otwartych standardów.
Daniel wraz z Miltonem Ponsonem przewodniczy grupie W3C [Procedural Memory Knowledge Representation Community Group (PM-KR)](https://www.w3.org/community/pm-kr/).
Nasz raport [Stereoskopowe 3D w systemie Linux i w sieci](https://www.w3.org/publications/spec-generator/?type=respec&url=https://raw.githubusercontent.com/w3c-cg/pm-kr/main/reports/source/stereo-3d-adoption-report.html) jest tam indywidualną propozycją, materiałem do dyskusji w grupie: które istniejące specyfikacje już przenoszą 3D, czego Linux i sieć nigdy nie przyjęły oraz czego potrzebowałaby przeglądarka.
To także temat naszego wystąpienia w Media and Entertainment Interest Group W3C 13 października 2026 roku ([slajdy](docs/talks/2026-10-13-w3c-me-ig.md)).
Dołączenie do grupy jest bezpłatne z kontem W3C, a pomoc jest mile widziana: przetestuj na swoim ekranie, przejrzyj raport lub przedstaw swój przypadek użycia.

<a id="create"></a>
## Twórz

**Maluj, edytuj zdjęcia i filmy w 3D, maluj z większą głębią koloru: 16 bitów na kolor zamiast 8.**
- **Malowanie:** Krita pozwala malować na 16-bitowym płótnie oraz na płótnie 3D z 16 bitami dla każdego oka.
- **Zdjęcia:** digiKam i Showfoto pokazują zdjęcia 3D w albumie, podświetlarce, pokazie obrazów i edytorze; KolourPaint edytuje obraz 3D i zapisuje go z oznaczeniem 3D.
- **Wideo:** w Kdenlive klip zna swój układ 3D, monitory mogą go pokazać w 3D, a renderowanie zachowuje oznaczenie 3D.
- **Opowieści:** [StorySplat](https://storysplat.com) ("Zamień swoje skany 3D w interaktywne wycieczki") tworzy wycieczki wewnątrz skanów 3D rzeczywistych miejsc, bezpośrednio w przeglądarce, a jego 3D View pokazuje je w 3D na dowolnym z zarejestrowanych wyjść; pierwszy test odbył się w układzie obok siebie na telewizorze Sony 3D.

Pełny opis każdego programu: [Programy](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="for-theme-designers-and-customizers"></a>
### Dla twórców i osób dostosowujących motywy

**Na tym pulpicie motyw decyduje, co wysuwa się do przodu, a co cofa w głąb:** [nowe możliwości projektowania motywów](#depth-on-the-desktop).

<a id="science-and-engineering"></a>
## Nauka i inżynieria

**Badaj i projektuj w 3D: globus, wykresy i cząsteczki już działają w 3D, a prace nad modelami 3D i płytkami drukowanymi trwają.**
- **Nauka i edukacja:** globus w Marble, wykresy w KAlgebra, cząsteczki w Kalzium i kostka w Kubrick, domyślnie w 3D na pulpicie 3D.
- **Modele 3D i płytki drukowane:** trwają prace nad podglądami 3D w OpenSCAD, KiCad i F3D.
- **Od biurka do klienta, w pełnym kolorze:** ten sam model z głębią na monitorze 3D bez okularów na biurku inżyniera (z [DisplayXR](https://displayxr.org), prace trwają), na telewizorze 3D lub projektorze dla zespołu czy grupy szkoleniowej oraz na własnym telefonie każdego pracownika i klienta w kartonowych goglach ([Flat Headset](https://github.com/Sparky-OS/flat-headset)). Wszystko jest otwarte od początku do końca, więc nikt nie jest związany z jednym producentem ekranów.

Pełny opis każdego programu: [Programy](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="watch-and-play"></a>
## Oglądaj i graj

**Filmy, zdjęcia i gry 3D są wyświetlane w 3D we własnym oknie lub na pełnym ekranie, a reszta pulpitu pozostaje bez zmian.**
- **Ekrany:** telewizor, monitor lub projektor 3D, także urządzenia HDMI 3D z lat 2010 do 2013, albo zwykły monitor z okularami czerwono-cyjanowymi; każdy ekran może jednocześnie wyświetlać inny rodzaj 3D, a prace nad monitorami 3D bez okularów trwają wspólnie z zespołem DisplayXR.
- **Filmy:** filmy 3D są odtwarzane w 3D w Haruna, VLC, mpv, Bino, PlasmaTube i innych programach.
- **Zdjęcia:** Gwenview, digiKam i KolourPaint pokazują zdjęcia 3D (MPO, JPS i stereoskopowe PNG) w 3D.
- **Gry:** DOOM (2016) w oknie i Half-Life 2, oba przez tryb VR ([sposób](docs/formula.md)).
- **Jądro dostrojone do grania:** edycja korzysta z jądra Linux 7.3 z naszymi poprawkami stereoskopowymi. Nowy planista zadań podniósł najniższą liczbę klatek na sekundę w grze z 4 do 29 kl./s na starszym procesorze w teście przeprowadzonym przez samego autora ([liczby](https://lore.kernel.org/all/20260511113104.563854162@infradead.org/)), a karty AMD z małą ilością pamięci wideo mogą utrzymywać pamięć gry na karcie ([zmiana](https://pixelcluster.dev/VRAM-Mgmt-fixed/)).

Każdy program, co zyskuje i jak to sprawdzono: [Programy](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="seen-in-3d"></a>
### Zobaczone w 3D

Obrazy na tej stronie to zrzuty ekranu wykonane programem Spectacle z tej edycji, który zachowuje obraz dla obu oczu.
Okulary czerwono-cyjanowe pozwalają zobaczyć je tutaj w 3D; pliki MPO otwierają się w 3D w programach do zdjęć z tej edycji, na dowolnym z zarejestrowanych wyjść. Wszystkie obrazy, każdy z wersją czerwono-cyjanową i bezpośrednim pobieraniem MPO: [galeria zrzutów ekranu](docs/screenshots/README.md). Własne zdjęcia 3D Daniela z telefonu LG Optimus 3D z lat 2014 do 2016, wraz z oryginałami: [galeria zdjęć](docs/photos/README.md).

- **Pulpit stereoskopowy, półprzezroczysty** ([MPO](https://raw.githubusercontent.com/Sparky-OS/sparky-stereo-os/main/docs/screenshots/translucent-stereo-desktop.mpo)), na telewizorze 3D, 15 października 2026 roku. Okna są szklane, więc widać przez nie cały stos. Pomiar między oczami: Dolphin, aktywne okno, 0 px, a jego menu Ustawienia +5 px (z przodu, na wybranej przez użytkownika granicy wysunięcia); długa lista zestawów barw 0 px, bo dotyka góry ekranu, a wysunięty element dotykający krawędzi pozostaje w płaszczyźnie ekranu; Thunderbird z tyłu -3 px; widżet monitora systemu i tapeta -10 px; panel 0 px. Oba adresy e-mail są rozmyte w obrazach dla obu oczu.
- **Pulpit stereoskopowy, menu nad menu** ([MPO](docs/screenshots/stereo-desktop-dialogs.mpo)), na telewizorze 3D w trybie frame packing, 13 października 2026 roku. Pomiar między oczami: aktywne okno Marble 0 px, jego menu Ustawienia +2 px i podmenu Panele +4 px, cztery okna z tyłu -3, -5, -8 i -10 px, widżety i tapeta -10 px; wewnątrz okna własne 3D programu Marble: etykiety Ziemi +12 px, gwiazd -13 px. Wiadomości na czacie Diolinux z tyłu są rozmyte.
- **DOOM (2016) w zwykłym oknie** ([MPO](docs/screenshots/doom-2016-in-a-window.mpo)), na podstawie [KHARVOX](https://github.com/CactusVRStudios/KHARVOX), moda CactusVRStudios przekształcającego DOOM (2016) w grę VR (MIT): gra ma głębię, a panel i rama okna pozostają płaskie w obrazach dla obu oczu. Pomiar między oczami: obrazy najbliższej skały przesunięte względem siebie o 23 px, dalekie góry 1 px, panel 0 px.
- **Globus w Marble** ([MPO](docs/screenshots/marble-globe.mpo)): Ziemia przed ekranem (+11 px), gwiazdy za nim (-12 px), panel boczny płaski. Ten zrzut powstał przed późniejszymi poprawkami; obraz z menu nad menu pokazuje obecny stan Marble.
- **Pulpit stereoskopowy, wyskakujące okno** ([MPO](docs/screenshots/stereo-desktop.mpo)), tego samego dnia. Pomiar między oczami: panel 0 px (w płaszczyźnie ekranu), wyskakujące okno dźwięku +4 px (z przodu), trzy okna z tyłu -3, -7 i -10 px, a widżet monitora systemu -10 px, w głębi wraz z tapetą.

<a id="depth-on-the-desktop"></a>
<a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## Pulpit stereoskopowy: nowe możliwości projektowania motywów

**Po raz pierwszy motyw decyduje, co wysuwa się do przodu, a co cofa w głąb, nie tylko o wyglądzie elementów.**
Przez dziesięciolecia cienie, ścięcia krawędzi i wypukłe przyciski tylko udawały głębię; na pulpicie stereoskopowym jest ona rzeczywista i subtelna: kilka pikseli, w wybranych przez Ciebie granicach (Ustawienia systemowe, "Głębia 3D").

- **To, czego używasz, wysuwa się do przodu:** menu, podpowiedzi, powiadomienia i okna dialogowe wychodzą w Twoją stronę, a okno, w którym pracujesz, pozostaje w płaszczyźnie ekranu. *Gotowe i pokazane na telewizorze 3D 13 października 2026 roku ([obraz na górze](#seen-in-3d)).*
- **Reszta cofa się w głąb:** okna z tyłu cofają się jedno po drugim, jak kartki w stosie, a tapeta znajduje się najgłębiej. *Gotowe.*
- **Drobne elementy zachowują swoje miejsce:** wskaźnik przyjmuje poziom tego, nad czym się znajduje, cień leży na powierzchni, na którą pada, a przypięte okno, na przykład kamera nad slajdami, pozostaje przed wszystkim. *Gotowe.*
- **Tapety w 3D:** zdjęcie 3D w tle zachowuje własne wysunięcia i głębię, daleko za wszystkimi oknami. *Gotowe.* Następne będą tła wideo 3D, z tapetą wideo, którą tworzy Jeromy Streets. *W planach.*
- **Wygaszacze ekranu w 3D:** klasyczne pole gwiazd i wygaszacze stereoskopowe, w prawdziwym 3D. *Gotowe.*
- **Obrazy i ikony w 3D:** zdjęcia 3D są wyświetlane w 3D w podglądach programu Dolphin i przeglądarkach obrazów. *Gotowe.* Ikony rysowane parami, po jednej dla każdego oka, są częścią Stereo Oxygen, własnego wyglądu tej edycji. *W planach.*
- **Efekty, które naprawdę wysuwają się i cofają:** zamykane okno może polecieć ku Tobie w kawałkach albo zanurkować za ekran i odbić się od podłogi. *Gotowe w naszej gałęzi KWin, trafią do następnego pakietu.* Przełączniki okien rozkładające się w wachlarz w 3D oraz Sześcian pulpitu w prawdziwym 3D. *W planach.*
- **3D od chwili włączenia:** ekran startowy i ekran logowania korzystają z trybu 3D zapisanego dla głównego ekranu. *Gotowe.*

**I nadal jest to zwykły pulpit 2D.**
Na zwykłym ekranie nic się nie zmienia: ten sam motyw, układ i efekty, rysowane tylko raz.
3D pojawia się tylko tam, gdzie ekran może je pokazać, albo przez okulary czerwono-cyjanowe, a motyw zaprojektowany dla 3D jest także pełnym motywem 2D.

<a id="the-desktop-cube-what-one-format-makes-possible"></a>Szczegóły: [Głębia pulpitu](docs/depth-on-the-desktop.md) i [Dla twórców i osób dostosowujących motywy](docs/for-theme-designers.md); pomysły, szkice i makiety 3D są mile widziane w [zgłoszeniu dotyczącym motywów](https://github.com/Sparky-OS/sparky-stereo-os/issues/78).

<a id="for-developers"></a>
## Dla programistów

**Dodaj 3D do programu raz: przekaż pulpitowi obrazy dla obu oczu, a on zadba o każdy ekran.**
Możesz pisać i sprawdzać kod na ekranie, który już masz.
- [Twórz 3D i XR na zwykłym monitorze](docs/develop-3d-on-an-ordinary-monitor.md): zacznij tutaj.
- [Twoja scena 3D w stereoskopii, ze strony internetowej](docs/web-3d-in-stereo.md): three.js, WebGL i WebXR, od czerwono-cyjanowych okularów w dowolnej przeglądarce po wszystkie ekrany 3D.
- [Formaty wewnętrzne](docs/house-formats.md) i [Podział pracy przy stereoskopii](docs/stereo-labor-division.md): zasady powiązane ze specyfikacjami.
- [Testuj stereoskopię bez telewizora 3D](docs/test-stereo-without-a-3d-tv.md) i [Maszyna wirtualna z ekranem 3D](docs/stereo-vm.md): testuj wyjście 3D na ekranie wirtualnym lub w maszynie wirtualnej; gotowy główny system plików ze Stereo KWin znajduje się na [naszym serwerze repozytorium](https://repo.sparkyos.org/bench/kwin-root/).
- [Skills](skills/README.md): instrukcje dla ludzi i asystentów AI pracujących nad edycją.

<a id="how-it-works"></a>
## Jak to działa

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Programy opisują każdy obraz; pulpit dostosowuje go do każdego ekranu.** W stereoskopii oba widoki są przesyłane razem w jednym buforze full side by side. Proponowane rozszerzenie HDR zachowuje opis kolorów obrazu i informacje potrzebne do jego rekonstrukcji dzięki temu samemu podziałowi pracy.

**Kontrakt stereoskopowy w trzech punktach.**
- **Stereo KWin** (kompozytor KDE Plasma z naszymi zmianami stereoskopowymi) używa full side by side w dowolnej rozdzielczości.
- **Programy** dekodują lub generują stereoskopię w dowolnym standardzie i przekazują obraz full side by side, w dowolnej rozdzielczości, do Stereo KWin.
- **Wyjścia** (końcowe filtry Stereo KWin, po jednym na każdy rodzaj ekranu) przekształcają go w to, czego potrzebuje dany ekran.

Dlaczego full side by side, jeden pulpit na dwóch telewizorach 3D z dwóch GPU i jak ta sama zasada obejmuje HDR: [Jak to działa](docs/how-it-works.md). [Deklaracja HDR](docs/stereo-hdr-content.md) jest projektem oczekującym na implementację i testy urządzeń z różnymi formatami; reprezentacja wymiany danych HDR pozostaje wyborem inżynierskim wymagającym sprawdzenia. Istniejące testy stereoskopii i większej głębi koloru nie potwierdzają działania tej ścieżki HDR.

<a id="stereo-in-the-open-stack-not-in-one-product"></a>
## Stereoskopia w otwartym stosie, nie w jednym produkcie

Gdzie indziej stereoskopia jest związana z jednym produktem: jednymi goglami, narzędziem do wstrzykiwania kodu jednego producenta, jądrem jednego producenta.
Tutaj jest właściwością otwartych warstw (KDE, jądra, formatów plików), więc dociera na ekran, który już masz: [Stereoskopia w otwartym stosie](docs/open-stack.md).

<a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>
## Programy zmieniane w tej edycji dla stereoskopowego 3D i większej głębi koloru

Co 3D wnosi do każdego programu, od filmów i zdjęć po globusy i cząsteczki: [Programy](docs/programs.md).
Jak zmieniono i sprawdzono każdy z nich, według obszarów (droga obrazu do ekranu, wideo, nauka i inżynieria, obrazy, symulatory, system i to, co jeszcze nie jest gotowe): [Programy szczegółowo](docs/programs-in-detail.md).

<a id="our-branches-on-kdes-gitlab"></a>
## Nasze gałęzie na GitLabie KDE

Każda zmiana w KDE jest gałęzią naszego forka na [invent.kde.org](https://invent.kde.org/danielcamposramos), testowaną przez własne CI KDE przed zaproponowaniem jej projektowi źródłowemu: [gałęzie i wyniki ich CI](docs/kde-branches.md).

<a id="merged-outside-sparky-stereo"></a>
## Włączone do projektów poza Sparky Stereo

**26 października 2026 roku IANA przypisała wartości StereoMode 15 do 20 w Matroska** układom łączącym obraz z głębią w jednej klatce, po przypisaniu 20 października typów płaszczyzn 3 do 5 dla osobnych ścieżek głębi lewego oka, prawego oka i tła.
Obie rejestracje wskazują naszą specyfikację stereo-layer.
[Aktualny rejestr](https://www.iana.org/assignments/matroska) oraz [rejestracja i poprawki przyjęte przez projekty źródłowe](docs/upstream-merges.md#registered-identifiers).

Gdy program gubi stereoskopię lub większą głębię koloru w drodze do ekranu, poprawka trafia do projektu tego programu.
Projekty takie jak HandBrake, mpv, Qt Multimedia i PeerTube włączyły poprawki z naszych prac; każda z nich, wraz z opiekunem, który ją przyjął, oraz poprawki w trakcie przeglądu są opisane w [Włączone do projektów poza Sparky Stereo](docs/upstream-merges.md).
Działanie każdej części jest pokazywane, zanim uznamy ją za gotową, z liczbami i obrazem w anaglifie oraz MPO: [Dowody działania](docs/proofs/README.md).
Co publicznie powiedziały o tym osoby zajmujące się stereoskopią, wraz z odnośnikami: [Co mówią inni](docs/what-people-said.md).

<a id="documents"></a>
## Dokumenty

[Sposób przeniesienia obrazu z silnika VR na ekran 3D](docs/formula.md), [pierwsze uruchomienia KWin na prawdziwych telewizorach](docs/first-runs/kwin-2026-10-01/README.md) i [slajdy z wystąpienia w W3C](docs/talks/2026-10-13-w3c-me-ig.md) z 13 października 2026 roku; wszystkie strony są w [docs](docs/).

<a id="tools"></a>
## Narzędzia

[vkms-stereo-bench](tools/vkms-stereo-bench/README.md) sprawdza tryby 3D na wirtualnym ekranie, a [hibernate-bench](tools/hibernate-bench/README.md) sprawdza hibernację przy włączonym Secure Boot, oba w maszynie wirtualnej.

<a id="the-base-three-open-lists"></a>
## Podstawa: trzy otwarte listy

Badania stojące za tą edycją są publiczne, w trzech starannie dobieranych listach, które każdy może kopiować (CC0): [awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy) dla stereoskopowego 3D, [awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr) dla HDR i większej głębi koloru oraz [awesome-vr](https://github.com/danielcamposramos/awesome-vr) dla rzeczywistości wirtualnej.

<a id="credit"></a>
## Autorzy i podziękowania

Sparky Stereo OS, edycja SparkyLinux autorstwa Daniela Ramosa (Capitain Jack); twórcą SparkyLinux jest Paweł "pavroo" Pijanowski.

**Opiekunowie pakietów**, każdy z pełnymi uprawnieniami do własnego repozytorium w [Sparky-OS](https://github.com/Sparky-OS):

| | |
| --- | --- |
| <a href="https://github.com/effcol"><img src="https://github.com/effcol.png?size=96" width="72" alt="Eff"></a> | **Eff (effcol)**<br>Opiekuje się [wiz3D](https://github.com/effcol/wiz3D), uniwersalną warstwą stereoskopowego 3D dla DirectX, OpenGL, AMD HD3D i NVIDIA 3D Vision, opartą na iZ3D, dla wszystkich systemów, oraz jej pakietem tutaj, [Sparky-OS/wiz3D](https://github.com/Sparky-OS/wiz3D).<br>[![Obserwuj Eff](https://img.shields.io/badge/Follow-effcol-2777AD?style=flat-square&logo=github)](https://github.com/effcol) |
| <a href="https://github.com/halverneus"><img src="https://github.com/halverneus.png?size=96" width="72" alt="Jeromy Streets"></a> | **Jeromy Streets (halverneus)**<br>Stworzył i rozwija [org.kde.video](https://github.com/Sparky-OS/org.kde.video), tapetę wideo i ekran blokady dla KDE Plasma.<br>[![Obserwuj Jeromy](https://img.shields.io/badge/Follow-halverneus-2777AD?style=flat-square&logo=github)](https://github.com/halverneus) |

**Wersja:** Sparky Stereo OS 9 "Mashtabba", na bazie Debian 14 "Forky", wyłącznie KDE Plasma.

Wszyscy, na których pracy opiera się ta edycja, wymienieni z nazwiska: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Szczególne podziękowania:**
- **David Fattal**, współzałożyciel Leia i opiekun DisplayXR, za zachętę, czas i wysiłek oraz testowanie naszego pulpitu na ekranach 3D, które buduje.
- **Milton Ponson** i **Christoph Dorn**, wsparcie Daniela w grupie W3C PM-KR, wszyscy członkowie tej grupy oraz **Dave Raggett**, **Ian Jacobs** i **Chris Needham** z W3C, którzy otworzyli drzwi dla tej pracy.
- **Tim Berners-Lee** i wszyscy, którzy zbudowali Internet, warstwa po warstwie, i oddali go innym.
- Zespół **Foottroller**, za otwarcie drogi do chodzenia własnymi stopami w VR w systemie Linux.
- **Eric Allard**, inżynier, dzięki któremu Johnny 5 ożył w *Short Circuit*; scenarzyści filmu, **S. S. Wilson** i **Brent Maddock**; oraz jego muzyka, której autorami są **El DeBarge**, **Peter Wolf**, **Ina Wolf** i **David Shire**, odtwarzana wielokrotnie podczas tworzenia tej edycji.

**Cytuj:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Daj gwiazdkę:** [![Gwiazdki GitHub](https://img.shields.io/github/stars/Sparky-OS/sparky-stereo-os?style=flat-square&logo=github&label=Stars)](https://github.com/Sparky-OS/sparky-stereo-os/stargazers) ⭐ Jeśli Sparky Stereo OS Ci się przydaje, gwiazdka pomaga innym go znaleźć.

**Wesprzyj:** [![Wesprzyj Daniela](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Przekaż darowiznę na SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Wsparcie Daniela finansuje tę edycję, a darowizna na SparkyLinux wspiera dystrybucję Pawła, na której jest ona oparta.

<a href="https://sourceforge.net/p/sparkyos/"><picture><source media="(prefers-color-scheme: dark)" srcset="https://sourceforge.net/sflogo.php?type=18&amp;group_id=3189517"><img alt="SparkyOS na SourceForge" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3189517" width="200"></picture></a>

<a id="licence"></a>
## Licencja

Dokumenty są udostępniane na [licencji Creative Commons Uznanie autorstwa 4.0 Międzynarodowe](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): możesz je udostępniać i zmieniać, podając Sparky Stereo OS jako autora.

> "Informacja to władza. Ale jak w przypadku każdej władzy, są tacy, którzy chcą zatrzymać ją dla siebie."
> — Aaron Swartz, [*Guerilla Open Access Manifesto*](https://archive.org/details/GuerillaOpenAccessManifesto) (lipiec 2008)

Skrypty w `docs/first-runs/` i narzędzia w `tools/` są kodem objętym licencją GNU General Public License w wersji 2 lub późniejszej (GPL-2.0-or-later); zobacz [LICENSE-GPL-2.0](LICENSE-GPL-2.0).
