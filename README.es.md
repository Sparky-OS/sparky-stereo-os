# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇲🇽 [Español](README.es.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**Crear y explorar en 3D en la pantalla que ya tiene: pintar, editar fotos y vídeo, estudiar moléculas y globos terráqueos, y después ver películas y jugar.**
Está hecho para todo tipo de pantalla 3D: televisores y proyectores 3D, cascos de realidad virtual, pantallas 3D sin gafas y cualquier monitor con gafas rojo-cian.
En un monitor 2D común, el mismo escritorio funciona sin ningún cambio.
Sparky Stereo OS, la edición de Daniel Ramos de SparkyLinux (de Paweł "pavroo" Pijanowski), es un sistema Linux con un nuevo escritorio Stereo KDE Plasma.

**Más ligero para su equipo y para el planeta:** cada paquete llega sin los comentarios y las notas que los programas nunca leen, de modo que el mismo trabajo requiere menos procesamiento, menos energía y menos desgaste.
[Medido](docs/lean-code-packages.md#why-it-matters) en un portátil de 2016: preparar un programa para el compilador requiere entre un 2 y un 4 % menos de trabajo que con los mismos archivos sin quitarles los comentarios, y no se pierde nada.

<a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="El escritorio estéreo en 3D con ventanas translúcidas: delante, el menú Preferencias de Dolphin con su lista de esquemas de color; detrás, las ventanas de cristal que retroceden una tras otra, y al fondo el monitor del sistema y el fondo de pantalla (anaglifo rojo-cian)"></a>

<a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) en una ventana, en 3D, con el panel plano de Plasma debajo (anaglifo rojo-cian)"></a> <a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="El globo de Marble delante de las estrellas, en 3D (anaglifo rojo-cian)"></a> <a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="El escritorio estéreo en 3D: el panel en el plano de la pantalla, una ventana emergente de sonido delante de él y las ventanas de detrás que retroceden una tras otra (anaglifo rojo-cian)"></a>

*Con gafas rojo-cian, estas imágenes se ven en 3D ([más](docs/edition-in-detail.md#seen-in-3d)).*

**Estado: beta 1, para probadores.** Probado en televisores 3D, en monitores comunes con gafas rojo-cian y en un teléfono Android en un visor económico; las pantallas sin gafas y los cascos autónomos están en desarrollo.

**Siguiente paso: pruébelo en su PC con Windows desde una memoria USB, sin instalar nada:** [una página, diez pasos](docs/guides/try-on-windows.es.md).
<br>Pida la descarga y cuéntenos qué equipo 3D tiene, en su idioma: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇲🇽](https://github.com/Sparky-OS/sparky-stereo-os/issues/351) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[Ciencia e ingeniería](docs/edition-in-detail.md#science-and-engineering):** el globo de Marble, las gráficas de KAlgebra y las moléculas de Kalzium en 3D; los modelos 3D y las placas de circuito están en desarrollo. El escaneo 3D está previsto: un vídeo de una pieza, de un sitio o de un espécimen se convierte en un modelo 3D.
- <a id="create"></a>**[Crear](docs/edition-in-detail.md#create):** pintar en 3D y en color profundo (16 bits por color en lugar de 8), y editar fotos y vídeo en 3D. El escaneo 3D está previsto: un vídeo de un objeto o de un lugar se convierte en un modelo 3D que puede recorrer.
- <a id="watch-and-play"></a>**[Ver y jugar](docs/edition-in-detail.md#watch-and-play):** películas, fotos y juegos en 3D, en una ventana o a pantalla completa.
- <a id="vr-is-also-a-stereo-monitor"></a>**[La realidad virtual también es un monitor estéreo](docs/edition-in-detail.md#vr-is-also-a-stereo-monitor):** un casco, o un teléfono en un visor, es también una pantalla 3D para este escritorio.
- <a id="for-developers"></a>**[Desarrollar](docs/edition-in-detail.md#for-developers):** haga que su programa sea 3D una sola vez; el escritorio lo adapta a cada pantalla.
- **[¿Otra distribución?](docs/other-distributions.md)** Por qué no hacemos paquetes para ella y cómo sus mantenedores pueden adoptar nuestras correcciones.

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## El escritorio estéreo: nuevas fronteras para el diseño de temas

**En este escritorio, un tema decide qué emerge y qué se hunde:** [nuevas fronteras para el diseño de temas](docs/edition-in-detail.md#depth-on-the-desktop).

<a id="how-it-works"></a>
## Cómo funciona

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Los programas describen cada imagen; el escritorio la adapta a cada pantalla.** Para el estéreo, las dos vistas viajan juntas en un único búfer lado a lado completo (full side by side). La extensión HDR propuesta conserva la descripción del color de la imagen y la información para reconstruirla mediante esa misma división del trabajo.
[En detalle (en inglés)](docs/edition-in-detail.md#how-it-works)

<a id="more-about-the-edition"></a>
## Más sobre la edición

- <a id="who-builds-it"></a>[Quién la construye](docs/edition-in-detail.md#who-builds-it)
- <a id="where-it-is-going"></a>[Hacia dónde va](docs/edition-in-detail.md#where-it-is-going)
- <a id="seen-in-3d"></a>[Visto en 3D](docs/edition-in-detail.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[Para quienes diseñan y personalizan temas](docs/edition-in-detail.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[Estéreo en las capas abiertas, no en un solo producto](docs/edition-in-detail.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[Programas que la edición modifica para el 3D estéreo y el color profundo](docs/edition-in-detail.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[Nuestras ramas en el GitLab de KDE](docs/edition-in-detail.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[Integrado fuera de Sparky Stereo](docs/edition-in-detail.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[Documentos](docs/edition-in-detail.md#documents)
- <a id="tools"></a>[Herramientas](docs/edition-in-detail.md#tools)
- <a id="the-base-three-open-lists"></a>[La base: tres listas abiertas](docs/edition-in-detail.md#the-base-three-open-lists)

<a id="credit"></a>
## Créditos

Sparky Stereo OS, la edición de Daniel Ramos (Capitain Jack) de SparkyLinux (de Paweł "pavroo" Pijanowski).
Todas las personas en cuyo trabajo se apoya esta edición, por su nombre: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Cítelo:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Apóyelo:** [![Patrocinar a Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donar a SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Patrocinar a Daniel financia esta edición, y una donación a SparkyLinux apoya la distribución de Paweł, la base sobre la que está construida.

[En detalle (en inglés)](docs/edition-in-detail.md#credit)

<a id="licence"></a>
## Licencia

Los documentos están bajo la [licencia Creative Commons Atribución 4.0 Internacional](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): compártalos y adáptelos, dando crédito a Sparky Stereo OS.
[En detalle (en inglés)](docs/edition-in-detail.md#licence)
