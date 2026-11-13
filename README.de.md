# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇲🇽 [Español](README.es.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**Gestalten und entdecken Sie in 3D auf dem Bildschirm, den Sie schon haben: malen, Fotos und Videos bearbeiten, Moleküle und Globen erkunden, dann Filme ansehen und spielen.**
Es ist für jede Art von 3D-Bildschirm gemacht: 3D-Fernseher und 3D-Projektoren, VR-Headsets, brillenlose 3D-Displays und jeden Monitor mit einer Rot-Cyan-Brille.
Auf einem gewöhnlichen 2D-Monitor funktioniert derselbe Desktop ohne jede Änderung.
Sparky Stereo OS, Daniel Ramos' Edition von SparkyLinux (von Paweł "pavroo" Pijanowski), ist ein Linux-System mit einem neuen Stereo-KDE-Plasma-Desktop.

**Leichter für Ihren Rechner und für den Planeten:** Jedes Paket kommt ohne die Kommentare und Notizen, die Programme nie lesen; dieselbe Arbeit braucht so weniger Rechenleistung, weniger Energie und weniger Verschleiß.
[Gemessen](docs/lean-code-packages.md#why-it-matters) auf einem Laptop von 2016: Das Vorbereiten eines Programms für den Compiler kostet 2 bis 4 % weniger Arbeit als mit denselben Dateien ohne entfernte Kommentare, und es geht nichts verloren.

<a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="Der Stereo-Desktop in 3D mit durchscheinenden Fenstern: vorn das Einstellungsmenü von Dolphin mit der Liste der Farbschemata, dahinter treten die Glasfenster stufenweise zurück, am tiefsten liegen die Systemüberwachung und das Hintergrundbild (Rot-Cyan-Anaglyphe)"></a>

<a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) in einem Fenster, in 3D, darunter die flache Plasma-Leiste (Rot-Cyan-Anaglyphe)"></a> <a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Marbles Globus vor den Sternen, in 3D (Rot-Cyan-Anaglyphe)"></a> <a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="Der Stereo-Desktop in 3D: die Leiste auf der Bildschirmebene, davor ein Lautstärke-Fenster, dahinter die zurücktretenden Fenster (Rot-Cyan-Anaglyphe)"></a>

*Mit einer Rot-Cyan-Brille erscheinen diese Bilder in 3D ([mehr](docs/edition-in-detail.md#seen-in-3d)).*

**Stand: Beta 1, für Tester.** Getestet auf 3D-Fernsehern, auf gewöhnlichen Monitoren mit Rot-Cyan-Brille und auf einem Android-Telefon in einem preiswerten Betrachter; brillenlose Displays und eigenständige Headsets sind in Arbeit.

**Nächster Schritt: Probieren Sie es auf Ihrem Windows-PC vom USB-Stick aus, ohne etwas zu installieren:** [eine Seite, zehn Schritte](docs/guides/try-on-windows.de.md).
<br>Fragen Sie nach dem Download und erzählen Sie uns von Ihrer 3D-Ausrüstung, in Ihrer Sprache: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇲🇽](https://github.com/Sparky-OS/sparky-stereo-os/issues/351) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[Wissenschaft und Technik](docs/edition-in-detail.md#science-and-engineering):** Marbles Globus, die Graphen von KAlgebra und die Moleküle von Kalzium in 3D; 3D-Modelle und Leiterplatten sind in Arbeit. Das Scannen ist geplant: Aus einem Video eines Bauteils, eines Geländes oder einer Probe wird ein 3D-Modell.
- <a id="create"></a>**[Gestalten](docs/edition-in-detail.md#create):** in 3D und in hoher Farbtiefe malen (16 Bit je Farbe statt 8) und 3D-Fotos und 3D-Videos bearbeiten. Das Scannen ist geplant: Aus einem Video eines Gegenstands oder eines Ortes wird ein 3D-Modell, in dem man sich bewegen kann.
- <a id="watch-and-play"></a>**[Ansehen und Spielen](docs/edition-in-detail.md#watch-and-play):** 3D-Filme, 3D-Fotos und Spiele, im Fenster oder im Vollbild.
- <a id="vr-is-also-a-stereo-monitor"></a>**[VR ist auch ein Stereo-Monitor](docs/edition-in-detail.md#vr-is-also-a-stereo-monitor):** Ein Headset, oder ein Telefon in einem Betrachter, ist für diesen Desktop ebenfalls ein 3D-Bildschirm.
- <a id="for-developers"></a>**[Entwickeln](docs/edition-in-detail.md#for-developers):** Machen Sie Ihr Programm einmal 3D-fähig; der Desktop passt es an jeden Bildschirm an.
- **[Eine andere Distribution?](docs/other-distributions.md)** Warum wir nicht für sie paketieren und wie ihre Betreuer unsere Korrekturen übernehmen können.

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## Der Stereo-Desktop: Neuland für das Theme-Design

**Auf diesem Desktop entscheidet ein Theme, was hervortritt und was zurücktritt:** [Neuland für das Theme-Design](docs/edition-in-detail.md#depth-on-the-desktop).

<a id="how-it-works"></a>
## So funktioniert es

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Programme beschreiben jedes Bild; der Desktop passt es an jeden Bildschirm an.** Für Stereo reisen beide Ansichten gemeinsam in einem Puffer, vollständig nebeneinander (Full Side by Side). Die vorgeschlagene HDR-Erweiterung bewahrt die Farbbeschreibung und die Rekonstruktionsdaten des Bildes über dieselbe Arbeitsteilung.
[Im Detail (auf Englisch)](docs/edition-in-detail.md#how-it-works)

## Mehr über die Edition

- <a id="who-builds-it"></a>[Wer es baut](docs/edition-in-detail.md#who-builds-it)
- <a id="where-it-is-going"></a>[Wohin es geht](docs/edition-in-detail.md#where-it-is-going)
- <a id="seen-in-3d"></a>[In 3D gesehen](docs/edition-in-detail.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[Für Theme-Designer und alle, die ihren Desktop anpassen](docs/edition-in-detail.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[Stereo im offenen Stack, nicht in einem einzelnen Produkt](docs/edition-in-detail.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[Programme, die die Edition für Stereo-3D und hohe Farbtiefe ändert](docs/edition-in-detail.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[Unsere Zweige in KDEs GitLab](docs/edition-in-detail.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[Außerhalb von Sparky Stereo übernommen](docs/edition-in-detail.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[Dokumente](docs/edition-in-detail.md#documents)
- <a id="tools"></a>[Werkzeuge](docs/edition-in-detail.md#tools)
- <a id="the-base-three-open-lists"></a>[Die Grundlage: drei offene Listen](docs/edition-in-detail.md#the-base-three-open-lists)

<a id="credit"></a>
## Mitwirkende und Dank

Sparky Stereo OS, Daniel Ramos' (Capitain Jack) Edition von SparkyLinux (von Paweł "pavroo" Pijanowski).
Alle, auf deren Arbeit diese Edition aufbaut, mit Namen: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Zitieren:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Unterstützen:** [![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donate to SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Wer Daniel sponsert, finanziert diese Edition, und eine Spende an SparkyLinux unterstützt Pawełs Distribution, die Basis, auf der sie aufbaut.

[Im Detail (auf Englisch)](docs/edition-in-detail.md#credit)

<a id="licence"></a>
## Lizenz

Die Dokumente stehen unter der Lizenz [Creative Commons Namensnennung 4.0 International](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): Teilen und bearbeiten Sie sie, mit Nennung von Sparky Stereo OS.
[Im Detail (auf Englisch)](docs/edition-in-detail.md#licence)
