# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇲🇽 [Español](README.es.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**Twórz i odkrywaj w 3D na ekranie, który już masz: maluj, edytuj zdjęcia i filmy, badaj cząsteczki i globusy, a potem oglądaj filmy i graj.**
Powstał z myślą o każdym rodzaju ekranu 3D: telewizorach i projektorach 3D, zestawach VR, wyświetlaczach 3D bez okularów oraz dowolnym monitorze z okularami czerwono-cyjanowymi.
Na zwykłym monitorze 2D ten sam pulpit działa bez żadnych zmian.
Sparky Stereo OS, edycja SparkyLinux autorstwa Daniela Ramosa (twórcą SparkyLinux jest Paweł "pavroo" Pijanowski), to system Linux z nowym pulpitem Stereo KDE Plasma.

**Lżejszy dla Twojego komputera i dla planety:** każdy pakiet trafia do Ciebie bez komentarzy i notatek, których programy nigdy nie czytają, więc ta sama praca wymaga mniej obliczeń, mniej energii i mniej zużycia sprzętu.
[Zmierzone](docs/lean-code-packages.md#why-it-matters) na laptopie z 2016 roku: przygotowanie programu dla kompilatora wymaga o 2 do 4% mniej pracy niż przy tych samych plikach bez usuniętych komentarzy, i nic się nie traci.

<a href="docs/edition-in-detail.pl.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="Pulpit stereoskopowy w 3D z półprzezroczystymi oknami: menu Ustawienia programu Dolphin i lista zestawów barw z przodu, szklane okna za nimi cofające się kolejno, monitor systemu i tapeta najgłębiej (anaglif czerwono-cyjanowy)"></a>

<a href="docs/edition-in-detail.pl.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) w oknie, w 3D, z płaskim panelem Plasma poniżej (anaglif czerwono-cyjanowy)"></a> <a href="docs/edition-in-detail.pl.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Globus w Marble przed gwiazdami, w 3D (anaglif czerwono-cyjanowy)"></a> <a href="docs/edition-in-detail.pl.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="Pulpit stereoskopowy w 3D: panel w płaszczyźnie ekranu, wyskakujące okno dźwięku przed nim i kolejne okna cofające się w głąb (anaglif czerwono-cyjanowy)"></a>

*W okularach czerwono-cyjanowych zobaczysz te obrazy w 3D ([więcej](docs/edition-in-detail.pl.md#seen-in-3d)).*

**Stan: beta 1, dla testerów.** Przetestowano na telewizorach 3D, na zwykłych monitorach z okularami czerwono-cyjanowymi i na telefonie z systemem Android w niedrogich goglach; wyświetlacze bez okularów i samodzielne zestawy są w toku.

**Następny krok: wypróbuj go na swoim komputerze z Windows, z pendrive'a, bez instalowania czegokolwiek:** [jedna strona, dziesięć kroków (po angielsku)](docs/guides/try-on-windows.en.md).
<br>Poproś o plik do pobrania i opowiedz nam o swoim sprzęcie 3D, w swoim języku: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇲🇽](https://github.com/Sparky-OS/sparky-stereo-os/issues/351) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[Nauka i inżynieria](docs/edition-in-detail.pl.md#science-and-engineering):** globus w Marble, wykresy w KAlgebra i cząsteczki w Kalzium w 3D; trwają prace nad modelami 3D i płytkami drukowanymi. Skanowanie jest w planach: nagranie wideo części, terenu lub okazu zamienia się w model 3D.
- <a id="create"></a>**[Twórz](docs/edition-in-detail.pl.md#create):** maluj w 3D i z większą głębią koloru (16 bitów na kolor zamiast 8), edytuj zdjęcia i filmy 3D. Skanowanie jest w planach: nagranie wideo przedmiotu lub miejsca zamienia się w model 3D, po którym można się poruszać.
- <a id="watch-and-play"></a>**[Oglądaj i graj](docs/edition-in-detail.pl.md#watch-and-play):** filmy, zdjęcia i gry 3D, w oknie lub na pełnym ekranie.
- <a id="vr-is-also-a-stereo-monitor"></a>**[VR to także monitor stereoskopowy](docs/edition-in-detail.pl.md#vr-is-also-a-stereo-monitor):** zestaw VR albo telefon w goglach to także ekran 3D dla tego pulpitu.
- <a id="for-developers"></a>**[Programuj](docs/edition-in-detail.pl.md#for-developers):** dodaj 3D do programu raz; pulpit dostosuje je do każdego ekranu.
- **[Inna dystrybucja?](docs/other-distributions.md)** Dlaczego nie przygotowujemy dla niej pakietów i jak jej opiekunowie mogą przejąć nasze poprawki.

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## Pulpit stereoskopowy: nowe możliwości projektowania motywów

**Na tym pulpicie motyw decyduje, co wysuwa się do przodu, a co cofa w głąb:** [nowe możliwości projektowania motywów](docs/edition-in-detail.pl.md#depth-on-the-desktop).

<a id="how-it-works"></a>
## Jak to działa

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Programy opisują każdy obraz; pulpit dostosowuje go do każdego ekranu.** W stereoskopii oba widoki są przesyłane razem w jednym buforze full side by side. Proponowane rozszerzenie HDR zachowuje opis kolorów obrazu i informacje potrzebne do jego rekonstrukcji dzięki temu samemu podziałowi pracy.
[Szczegóły](docs/edition-in-detail.pl.md#how-it-works)

## Więcej o edycji

- <a id="who-builds-it"></a>[Kto to tworzy](docs/edition-in-detail.pl.md#who-builds-it)
- <a id="where-it-is-going"></a>[Dokąd zmierzamy](docs/edition-in-detail.pl.md#where-it-is-going)
- <a id="seen-in-3d"></a>[Zobaczone w 3D](docs/edition-in-detail.pl.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[Dla twórców i osób dostosowujących motywy](docs/edition-in-detail.pl.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[Stereoskopia w otwartym stosie, nie w jednym produkcie](docs/edition-in-detail.pl.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[Programy zmieniane w tej edycji dla stereoskopowego 3D i większej głębi koloru](docs/edition-in-detail.pl.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[Nasze gałęzie na GitLabie KDE](docs/edition-in-detail.pl.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[Włączone do projektów poza Sparky Stereo](docs/edition-in-detail.pl.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[Dokumenty](docs/edition-in-detail.pl.md#documents)
- <a id="tools"></a>[Narzędzia](docs/edition-in-detail.pl.md#tools)
- <a id="the-base-three-open-lists"></a>[Podstawa: trzy otwarte listy](docs/edition-in-detail.pl.md#the-base-three-open-lists)

<a id="credit"></a>
## Autorzy i podziękowania

Sparky Stereo OS, edycja SparkyLinux autorstwa Daniela Ramosa (Capitain Jack); twórcą SparkyLinux jest Paweł "pavroo" Pijanowski.
Wszyscy, na których pracy opiera się ta edycja, wymienieni z nazwiska: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Cytuj:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Wesprzyj:** [![Wesprzyj Daniela](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Przekaż darowiznę na SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Wsparcie Daniela finansuje tę edycję, a darowizna na SparkyLinux wspiera dystrybucję Pawła, na której jest ona oparta.

[Szczegóły](docs/edition-in-detail.pl.md#credit)

<a id="licence"></a>
## Licencja

Dokumenty są udostępniane na [licencji Creative Commons Uznanie autorstwa 4.0 Międzynarodowe](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): możesz je udostępniać i zmieniać, podając Sparky Stereo OS jako autora.
[Szczegóły](docs/edition-in-detail.pl.md#licence)
