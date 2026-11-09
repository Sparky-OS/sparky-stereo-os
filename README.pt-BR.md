# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**Crie e explore em 3D na tela que você já tem: pinte, edite fotos e vídeos, estude moléculas e globos, depois assista a filmes e jogue.**
Ele é feito para todo tipo de tela 3D: TVs e projetores 3D, headsets de VR, telas 3D sem óculos e qualquer monitor com óculos vermelho e ciano.
Num monitor 2D comum, a mesma área de trabalho funciona sem nenhuma mudança.
Sparky Stereo OS, a edição de Daniel Ramos do SparkyLinux (de Paweł "pavroo" Pijanowski), é um sistema Linux com uma nova área de trabalho Stereo KDE Plasma.

**Mais leve para a sua máquina e para o planeta:** todo pacote vem sem os comentários e anotações que os programas nunca leem, então o mesmo trabalho exige menos processamento, menos energia e menos desgaste.
[Medido](docs/lean-code-packages.md#why-it-matters): ler os cabeçalhos C++ dá de 2 a 4% menos trabalho do que no Debian, sem perder nada.

<a href="docs/edition-in-detail.pt-BR.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="A área de trabalho estéreo em 3D com janelas translúcidas: o menu Configurações do Dolphin e sua lista de esquemas de cores à frente, as janelas de vidro atrás recuando em sequência, o monitor do sistema e o papel de parede ao fundo (anáglifo vermelho e ciano)"></a>

<a href="docs/edition-in-detail.pt-BR.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) numa janela, em 3D, com o painel plano do Plasma abaixo (anáglifo vermelho e ciano)"></a> <a href="docs/edition-in-detail.pt-BR.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="O globo do Marble à frente das estrelas, em 3D (anáglifo vermelho e ciano)"></a> <a href="docs/edition-in-detail.pt-BR.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="A área de trabalho estéreo em 3D: o painel no plano da tela, uma janela de som à frente dele e as janelas atrás recuando em sequência (anáglifo vermelho e ciano)"></a>

*Óculos vermelho e ciano mostram essas imagens em 3D ([mais](docs/edition-in-detail.pt-BR.md#seen-in-3d)).*

**Situação: beta 1, para testadores.** Testado em TVs 3D, em monitores comuns com óculos vermelho e ciano e em um celular Android num visor de baixo custo; as telas sem óculos e os headsets autônomos estão em desenvolvimento.

**Próximo passo: experimente no seu PC com Windows, pelo pendrive, sem instalar nada:** [uma página, dez passos](docs/guides/try-on-windows.pt-BR.md).
<br>Peça o download e conte sobre seu equipamento 3D, no seu idioma: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[Ciência e engenharia](docs/edition-in-detail.pt-BR.md#science-and-engineering):** o globo do Marble, os gráficos do KAlgebra e as moléculas do Kalzium em 3D; modelos 3D e placas de circuito estão em desenvolvimento.
- <a id="create"></a>**[Criar](docs/edition-in-detail.pt-BR.md#create):** pinte em 3D e com maior profundidade de cor (16 bits por cor em vez de 8), e edite fotos e vídeos 3D.
- <a id="watch-and-play"></a>**[Assistir e jogar](docs/edition-in-detail.pt-BR.md#watch-and-play):** filmes, fotos e jogos 3D, numa janela ou em tela cheia.
- <a id="vr-is-also-a-stereo-monitor"></a>**[VR também é um monitor estéreo](docs/edition-in-detail.pt-BR.md#vr-is-also-a-stereo-monitor):** um headset, ou um celular num visor, também é uma tela 3D para esta área de trabalho.
- <a id="for-developers"></a>**[Desenvolver](docs/edition-in-detail.pt-BR.md#for-developers):** torne seu programa 3D uma vez; a área de trabalho o adapta a cada tela.
- **[Outra distribuição?](docs/other-distributions.md)** Por que não fazemos pacotes para ela e como seus mantenedores podem adotar nossas correções.

<a id="depth-on-the-desktop"></a><a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## A área de trabalho estéreo: novas fronteiras para o design de temas

**Nesta área de trabalho, um tema decide o que vem para a frente e o que vai para o fundo:** [novas fronteiras para o design de temas](docs/edition-in-detail.pt-BR.md#depth-on-the-desktop).

<a id="how-it-works"></a>
## Como funciona

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Os programas descrevem cada imagem; a área de trabalho a adapta a cada tela.** No estéreo, as duas vistas viajam juntas num único buffer no formato full side by side. A extensão HDR proposta preserva a descrição de cor da imagem e as informações de reconstrução por meio dessa mesma divisão do trabalho.
[Em detalhe](docs/edition-in-detail.pt-BR.md#how-it-works)

## Mais sobre a edição

- <a id="who-builds-it"></a>[Quem constrói](docs/edition-in-detail.pt-BR.md#who-builds-it)
- <a id="where-it-is-going"></a>[Para onde vamos](docs/edition-in-detail.pt-BR.md#where-it-is-going)
- <a id="seen-in-3d"></a>[Visto em 3D](docs/edition-in-detail.pt-BR.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[Para quem cria e personaliza temas](docs/edition-in-detail.pt-BR.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[Estéreo nas camadas abertas, não num único produto](docs/edition-in-detail.pt-BR.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[Programas que a edição modifica para estéreo 3D e maior profundidade de cor](docs/edition-in-detail.pt-BR.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[Nossas branches no GitLab do KDE](docs/edition-in-detail.pt-BR.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[Incorporado fora do Sparky Stereo](docs/edition-in-detail.pt-BR.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[Documentos](docs/edition-in-detail.pt-BR.md#documents)
- <a id="tools"></a>[Ferramentas](docs/edition-in-detail.pt-BR.md#tools)
- <a id="the-base-three-open-lists"></a>[A base: três listas abertas](docs/edition-in-detail.pt-BR.md#the-base-three-open-lists)

<a id="credit"></a>
## Créditos

Sparky Stereo OS, a edição de Daniel Ramos (Capitain Jack) do SparkyLinux (de Paweł "pavroo" Pijanowski).
Todas as pessoas em cujo trabalho esta edição se apoia, pelo nome: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Cite:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Apoie:** [![Patrocine Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Doe para o SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Patrocinar Daniel financia esta edição, e uma doação ao SparkyLinux apoia a distribuição de Paweł, a base sobre a qual ela é construída.

[Em detalhe](docs/edition-in-detail.pt-BR.md#credit)

<a id="licence"></a>
## Licença

Os documentos estão sob a [licença Creative Commons Atribuição 4.0 Internacional](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): compartilhe e adapte, dando crédito ao Sparky Stereo OS.
[Em detalhe](docs/edition-in-detail.pt-BR.md#licence)
