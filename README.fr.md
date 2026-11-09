# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**Créez et explorez en 3D sur l'écran que vous avez déjà : peinture, retouche de photos et de vidéos, étude de molécules et de globes, puis films et jeux.**
Il est conçu pour tous les types d'écrans 3D : téléviseurs et projecteurs 3D, casques VR, écrans 3D sans lunettes et n'importe quel écran avec des lunettes rouge-cyan.
Sur un écran 2D ordinaire, le même bureau fonctionne sans aucun changement.
Sparky Stereo OS, l'édition de Daniel Ramos de SparkyLinux (par Paweł « pavroo » Pijanowski), est un système Linux doté d'un nouveau bureau KDE Plasma stéréo.

**Plus léger pour votre machine et pour la planète :** chaque paquet est livré sans les commentaires et les notes que les programmes ne lisent jamais, donc le même travail demande moins de calcul, moins d'énergie et moins d'usure.
[Mesuré](docs/lean-code-packages.md#why-it-matters) : lire les en-têtes C++ demande 2 à 4 % de travail en moins que sous Debian, sans rien perdre.

<a href="docs/edition-in-detail.fr.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="Le bureau stéréo en 3D avec des fenêtres translucides : le menu Réglages de Dolphin et sa liste de jeux de couleurs en avant, les fenêtres vitrines derrière en gradation, le moniteur système et le fond d'écran au plus profond (anaglyphe rouge-cyan)"></a>

<a href="docs/edition-in-detail.fr.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) dans une fenêtre, en 3D, avec le panneau Plasma plat en dessous (anaglyphe rouge-cyan)"></a> <a href="docs/edition-in-detail.fr.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Le globe de Marble devant les étoiles, en 3D (anaglyphe rouge-cyan)"></a> <a href="docs/edition-in-detail.fr.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="Le bureau stéréo en 3D : le panneau à l'écran, un pop-up du son en avant, et les fenêtres derrière en gradation (anaglyphe rouge-cyan)"></a>

*Des lunettes rouge-cyan les montrent en 3D ([plus](docs/edition-in-detail.fr.md#seen-in-3d)).*

**État : bêta 1, pour les testeurs.** Testé sur des téléviseurs 3D, sur des écrans ordinaires avec des lunettes rouge-cyan et sur un téléphone Android dans une visionneuse peu coûteuse ; les écrans sans lunettes et les casques autonomes sont en cours.

**Étape suivante : essayez-le sur votre PC Windows, depuis une clé USB, sans rien installer :** [une page, dix étapes (en anglais)](docs/guides/try-on-windows.en.md).
<br>Demandez le téléchargement et parlez-nous de votre matériel 3D, dans votre langue : [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[Science et ingénierie](docs/edition-in-detail.fr.md#science-and-engineering) :** le globe de Marble, les tracés de KAlgebra et les molécules de Kalzium en 3D ; les modèles 3D et les circuits imprimés sont en cours.
- <a id="create"></a>**[Créer](docs/edition-in-detail.fr.md#create) :** peindre en 3D et en couleurs profondes (16 bits par couleur au lieu de 8), et retoucher des photos et des vidéos 3D.
- <a id="watch-and-play"></a>**[Regarder et jouer](docs/edition-in-detail.fr.md#watch-and-play) :** des films, des photos et des jeux 3D, dans une fenêtre ou en plein écran.
- <a id="vr-is-also-a-stereo-monitor"></a>**[La VR est aussi un écran stéréo](docs/edition-in-detail.fr.md#vr-is-also-a-stereo-monitor):** un casque, ou un téléphone dans une visionneuse, est aussi un écran 3D pour ce bureau.
- <a id="for-developers"></a>**[Développer](docs/edition-in-detail.fr.md#for-developers) :** rendez votre programme 3D une seule fois ; le bureau l'adapte à chaque écran.
- **[Une autre distribution ?](docs/other-distributions.md)** Pourquoi nous n'empaqueterons pas pour elle, et comment ses mainteneurs peuvent adopter nos corrections.

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## Le bureau stéréo : de nouvelles frontières pour la conception des thèmes

**Sur ce bureau, un thème décide de ce qui ressort et de ce qui plonge :** [de nouvelles frontières pour la conception des thèmes](docs/edition-in-detail.fr.md#depth-on-the-desktop).

<a id="how-it-works"></a>
## Comment cela fonctionne

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Les programmes décrivent chaque image ; le bureau l'adapte à chaque écran.** En stéréo, les deux vues voyagent ensemble dans un seul tampon côte à côte complet. L'extension HDR proposée préserve la description des couleurs de l'image et les informations de reconstruction à travers ce même partage du travail.
[En détail](docs/edition-in-detail.fr.md#how-it-works)

## En savoir plus sur l'édition

- <a id="who-builds-it"></a>[Qui le construit](docs/edition-in-detail.fr.md#who-builds-it)
- <a id="where-it-is-going"></a>[Où cela va](docs/edition-in-detail.fr.md#where-it-is-going)
- <a id="seen-in-3d"></a>[Vus en 3D](docs/edition-in-detail.fr.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[Pour les concepteurs et les personnalisateurs de thèmes](docs/edition-in-detail.fr.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[La stéréo dans la pile ouverte, pas dans un seul produit](docs/edition-in-detail.fr.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[Programmes que l'édition modifie pour la 3D stéréo et les couleurs profondes](docs/edition-in-detail.fr.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[Nos branches sur le GitLab de KDE](docs/edition-in-detail.fr.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[Contributions fusionnées hors de Sparky Stereo](docs/edition-in-detail.fr.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[Documents](docs/edition-in-detail.fr.md#documents)
- <a id="tools"></a>[Outils](docs/edition-in-detail.fr.md#tools)
- <a id="the-base-three-open-lists"></a>[La base : trois listes ouvertes](docs/edition-in-detail.fr.md#the-base-three-open-lists)

<a id="credit"></a>
## Crédits

Sparky Stereo OS, l'édition de Daniel Ramos (Capitain Jack) de SparkyLinux (par Paweł « pavroo » Pijanowski).
Tout ce sur quoi s'appuie cette édition, par nom : [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Citez le :** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Sponsor Daniel :** [![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donnez à SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Sponsoriser Daniel finance cette édition, et un don à SparkyLinux soutient la distribution de Paweł, la base sur laquelle elle est construite.

[En détail](docs/edition-in-detail.fr.md#credit)

<a id="licence"></a>
## Licence

Les documents sont sous licence [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0) : partagez-les et adaptez-les, en donnant le crédit à Sparky Stereo OS.
[En détail](docs/edition-in-detail.fr.md#licence)
