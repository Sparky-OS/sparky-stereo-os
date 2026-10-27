# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**Crie e explore em 3D na tela que você já tem: pinte, edite fotos e vídeos, estude moléculas e globos, depois assista a filmes e jogue.**
Funciona em uma TV 3D, em qualquer monitor comum com óculos vermelho e ciano baratos e, agora, em um celular Android compatível num visor de baixo custo: uma [área de trabalho estéreo utilizável por USB](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md), testada em hardware mais antigo.
Sparky Stereo OS, a edição de Daniel Ramos do SparkyLinux (de Paweł "pavroo" Pijanowski), é um sistema Linux com uma nova área de trabalho Stereo KDE Plasma.

**Conheça a arquitetura:** [guia ilustrado e mapa do repositório](docs/architectural-synthesis.md), com um [infográfico em tamanho completo e sua versão em texto](docs/architecture-infographic.md), adaptados e verificados a partir da pesquisa de Daniel com Gemini / NotebookLM.

<a href="#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="A área de trabalho estéreo em 3D com janelas translúcidas: o menu Configurações do Dolphin e sua lista de esquemas de cores à frente, as janelas de vidro atrás recuando em sequência, o monitor do sistema e o papel de parede ao fundo (anáglifo vermelho e ciano)"></a>

**Área de trabalho estéreo:** a própria área de trabalho tem profundidade.
O que você está usando fica no plano da tela e seus menus vêm para a frente, como o menu e o submenu do Marble aqui, enquanto as janelas atrás recuam uma após a outra, como papéis numa pilha, com o papel de parede ao fundo.
Um programa 3D mantém sua própria profundidade dentro da janela, como o globo do Marble.
Alguns pixels cada um, dentro dos limites que você escolhe.

<a href="#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) numa janela, em 3D, com o painel plano do Plasma abaixo (anáglifo vermelho e ciano)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="O globo do Marble à frente das estrelas, em 3D (anáglifo vermelho e ciano)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="A área de trabalho estéreo em 3D: o painel no plano da tela, uma janela de som à frente dele e as janelas atrás recuando em sequência (anáglifo vermelho e ciano)"></a>

*Óculos vermelho e ciano mostram essas imagens em 3D ([mais](#seen-in-3d)).*

**Em desenvolvimento:** o [APK de desenvolvimento do Flat Headset e as instruções correspondentes para atualizar o PC](https://github.com/Sparky-OS/flat-headset/tree/main/apk) estão disponíveis, e uma ISO de desenvolvimento para testadores já inicia em PCs novos com Secure Boot ativado, em PCs mais antigos com BIOS e em máquinas com UEFI de 32 bits; a ISO final da edição estéreo ainda está sendo preparada ([para onde vamos](#where-it-is-going)).

- **[Criar](#create):** pinte em 3D e com maior profundidade de cor (16 bits por cor em vez de 8), e edite fotos e vídeos 3D.
- **[Ciência e engenharia](#science-and-engineering):** o globo do Marble, os gráficos do KAlgebra e as moléculas do Kalzium em 3D; modelos 3D e placas de circuito estão em desenvolvimento.
- **[Assistir e jogar](#watch-and-play):** filmes, fotos e jogos 3D, numa janela ou em tela cheia.
- **[Desenvolver](#for-developers):** torne seu programa 3D uma vez; a área de trabalho o adapta a cada tela.
- **[Outra distribuição?](docs/other-distributions.md)** Por que não fazemos pacotes para ela e como seus mantenedores podem adotar nossas correções.

**Próximo passo: conte sobre seu equipamento 3D** e receba a notícia assim que estiver pronto.
<br>Inscreva-se no seu idioma: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

<a id="vr-is-also-a-stereo-monitor"></a>
### VR também é um monitor estéreo

A maioria dos headsets tem um par de telas pequenas, uma para cada olho, e os demais dividem uma tela em duas, assim como uma TV 3D, então esta mesma área de trabalho atende aos dois.
- **A tela 3D que já está no seu bolso:** um visor barato do tipo Cardboard transforma um celular Android compatível numa tela para a área de trabalho estéreo, em cores, com uma imagem separada para cada olho. Em 19 de outubro, Daniel considerou utilizável a configuração USB com imagens acima e abaixo, cada uma com metade da altura, num Redmi Note 7 e num notebook A10 de 2016: a área de trabalho funciona e o mouse responde bem. O vídeo melhorou bastante, mas ainda tem algumas interrupções; o primeiro teste no Wi-Fi doméstico parece mais próximo do USB, enquanto o Direct Wi-Fi tem pausas mais longas. A resolução completa e mais dispositivos ainda precisam de testes ([medições e limites](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)). O PC faz a renderização, dando outro uso a um celular mais antigo. O [APK de desenvolvimento, o código-fonte e as instruções correspondentes para atualizar o PC](https://github.com/Sparky-OS/flat-headset/tree/main/apk) estão disponíveis juntos; atualize primeiro o pendrive de desenvolvimento ou o PC instalado. O visualizador Android continua sendo uma versão de teste. Fotos do [primeiro teste](https://github.com/Sparky-OS/flat-headset#the-first-test-12-october-2026) e da [área de trabalho no celular](https://github.com/Sparky-OS/flat-headset#the-desktop-on-the-phone-14-october-2026).
- **Filmes em VR:** Bino reproduz filmes de 360° e 180°, planos ou em 3D, em qualquer tela 3D, e o mouse gira a vista.
- **Jogos em VR:** Half-Life 2 e DOOM (2016) chegam a uma tela 3D por seus modos VR.

<a id="who-builds-it"></a>
## Quem constrói

Daniel, de uma favela em Brasília, com dois colaboradores humanos até agora: Jeromy Streets, cujo papel de parede de vídeo para Plasma ([org.kde.video](https://github.com/Sparky-OS/org.kde.video)) agora está na Sparky-OS com ele como mantenedor, e Eff (effcol), que mantém vivo o código do iZ3D como [wiz3D](https://github.com/Sparky-OS/wiz3D) e cuida dele aqui.
O estéreo no Linux esperou anos por voluntários: tentativas anteriores pararam porque os revisores não tinham uma tela 3D, e o trabalho envolve o kernel, Mesa, KWin, FFmpeg, os reprodutores e os padrões da web.
Nenhum outro desenvolvedor se apresentou para levar isso adiante, então os demais parceiros que trabalham aqui são de IA, orientados e verificados por Daniel e identificados em [Proveniência de IA](docs/ai-provenance.md).
Se você prefere ver isso construído por mãos humanas, será mais que bem-vindo: todos os forks são públicos e todas as tarefas estão abertas.
Tudo é construído e testado em duas máquinas comuns, um PC doméstico e um notebook de 2016: [o hardware](docs/hardware.md).
Nesse notebook, todos os cenários da área de trabalho mantêm 24 fps em 2D e 3D: [quanto o estéreo custa ao KWin, com medições](docs/measurements/kwin-stereo-cost-a10-2026-10-23.md).

<a id="where-it-is-going"></a>
## Para onde vamos

A edição é a prova em funcionamento, e o que ela descobre volta para os padrões abertos.
Daniel preside o [Procedural Memory Knowledge Representation Community Group (PM-KR)](https://www.w3.org/community/pm-kr/) do W3C com Milton Ponson.
Nosso relatório [Estéreo 3D no Linux e na Web](https://www.w3.org/publications/spec-generator/?type=respec&url=https://raw.githubusercontent.com/w3c-cg/pm-kr/main/reports/source/stereo-3d-adoption-report.html) está lá como uma proposta individual, material para discussão no grupo: quais especificações estabelecidas já comportam 3D, o que o Linux e a web nunca adotaram e do que um navegador precisaria.
Também é o assunto da nossa apresentação no Media and Entertainment Interest Group do W3C em 13 de outubro de 2026 ([slides](docs/talks/2026-10-13-w3c-me-ig.md)).
Participar do grupo é gratuito com uma conta W3C, e toda ajuda é bem-vinda: teste na sua tela, revise o relatório ou traga seu caso de uso.

<a id="create"></a>
## Criar

**Pinte, edite fotos e vídeos em 3D e pinte com maior profundidade de cor: 16 bits por cor em vez de 8.**
- **Pintura:** Krita pinta numa tela de 16 bits e numa tela 3D com 16 bits em cada olho.
- **Fotos:** digiKam e Showfoto mostram fotos 3D no álbum, na Mesa de Luz, na Apresentação de slides e no editor; KolourPaint edita uma imagem 3D e a salva com sua marca 3D.
- **Vídeo:** no Kdenlive, um clipe conhece sua disposição 3D, os monitores podem mostrá-lo em 3D e a renderização mantém a marca 3D.
- **Histórias:** [StorySplat](https://storysplat.com) ("Transforme suas digitalizações 3D em passeios interativos") cria passeios dentro de digitalizações 3D de lugares reais, direto no navegador, e seu 3D View os mostra em 3D em qualquer uma das saídas registradas, com o primeiro teste lado a lado numa televisão Sony 3D.

Cada programa em detalhe: [Programas](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="for-theme-designers-and-customizers"></a>
### Para quem cria e personaliza temas

**Nesta área de trabalho, um tema decide o que vem para a frente e o que vai para o fundo:** [novas fronteiras para o design de temas](#depth-on-the-desktop).

<a id="science-and-engineering"></a>
## Ciência e engenharia

**Estude e projete em 3D: um globo, gráficos e moléculas já funcionam em 3D, e modelos 3D e placas de circuito estão em desenvolvimento.**
- **Aprendizado e ciência:** o globo do Marble, os gráficos do KAlgebra, as moléculas do Kalzium e o cubo do Kubrick, em 3D por padrão numa área de trabalho 3D.
- **Modelos 3D e placas de circuito:** prévias 3D no OpenSCAD, KiCad e F3D estão em desenvolvimento.
- **Da mesa ao cliente, em cores:** o mesmo modelo com profundidade num monitor 3D sem óculos na mesa do engenheiro (com [DisplayXR](https://displayxr.org), em desenvolvimento), numa TV 3D ou num projetor para uma equipe ou uma turma em treinamento, e no próprio celular de cada trabalhador e cliente num visor de papelão ([Flat Headset](https://github.com/Sparky-OS/flat-headset)). É aberto de ponta a ponta, então ninguém fica preso a um fabricante de telas.

Cada programa em detalhe: [Programas](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="watch-and-play"></a>
## Assistir e jogar

**Filmes, fotos e jogos 3D aparecem em 3D na própria janela ou em tela cheia, e o restante da área de trabalho fica como está.**
- **Telas:** uma TV, monitor ou projetor 3D, incluindo os aparelhos HDMI 3D de 2010 a 2013, ou qualquer monitor comum com óculos vermelho e ciano; cada tela pode mostrar um tipo diferente de 3D ao mesmo tempo, e monitores 3D sem óculos estão em desenvolvimento com a equipe DisplayXR.
- **Filmes:** vídeos 3D são reproduzidos em 3D no Haruna, VLC, mpv, Bino, PlasmaTube e outros.
- **Fotos:** Gwenview, digiKam e KolourPaint mostram fotos 3D (MPO, JPS e PNG estéreo) em 3D.
- **Jogos:** DOOM (2016) numa janela e Half-Life 2, ambos por um modo VR ([a fórmula](docs/formula.md)).
- **Um kernel ajustado para jogar:** a edição usa Linux 7.3 com nossos patches estéreo. Seu novo escalonador elevou a menor taxa de quadros de um jogo de 4 para 29 fps numa CPU mais antiga no teste do próprio autor ([os números](https://lore.kernel.org/all/20260511113104.563854162@infradead.org/)), e permite que placas AMD com pouca memória de vídeo mantenham a memória de um jogo na placa ([a mudança](https://pixelcluster.dev/VRAM-Mgmt-fixed/)).

Cada programa, o que ele ganha e como foi comprovado: [Programas](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

<a id="seen-in-3d"></a>
### Visto em 3D

As imagens desta página são capturas de tela feitas com o Spectacle da edição, que preserva os dois olhos.
Óculos vermelho e ciano as mostram em 3D aqui; os arquivos MPO abrem em 3D nos programas de fotos da edição, em qualquer uma das saídas registradas. Todas elas, cada uma com sua versão vermelho e ciano e um download direto em MPO: [a galeria de capturas de tela](docs/screenshots/README.md). As próprias fotos 3D de Daniel, feitas com um celular LG Optimus 3D de 2014 a 2016, com os originais: [a galeria de fotos](docs/photos/README.md).

- **Área de trabalho estéreo, translúcida** ([MPO](https://raw.githubusercontent.com/Sparky-OS/sparky-stereo-os/main/docs/screenshots/translucent-stereo-desktop.mpo)), na TV 3D, em 15 de outubro de 2026. As janelas são de vidro, então é possível ver a pilha através delas. Medido entre os olhos: Dolphin, a janela em foco, 0 px, e seu menu Configurações +5 px (à frente, no limite de avanço escolhido pelo usuário); a longa lista de esquemas de cores 0 px, porque toca o topo da tela e um elemento avançado que toca a borda fica no plano da tela; Thunderbird atrás -3 px; o widget do monitor do sistema e o papel de parede -10 px; o painel 0 px. Os dois endereços de e-mail estão desfocados nos dois olhos.
- **Área de trabalho estéreo, um menu sobre outro** ([MPO](docs/screenshots/stereo-desktop-dialogs.mpo)), numa TV 3D em frame packing, em 13 de outubro de 2026. Medido entre os olhos: a janela do Marble em foco 0 px, seu menu Configurações +2 px e o submenu Painéis +4 px, as quatro janelas atrás -3, -5, -8 e -10 px, os widgets e o papel de parede -10 px; dentro da janela, o próprio 3D do Marble: os rótulos da Terra +12 px, os das estrelas -13 px. As mensagens no chat Diolinux atrás estão desfocadas.
- **DOOM (2016) numa janela comum** ([MPO](docs/screenshots/doom-2016-in-a-window.mpo)), baseado em [KHARVOX](https://github.com/CactusVRStudios/KHARVOX), o mod de conversão de DOOM (2016) para VR da CactusVRStudios (MIT): o jogo tem profundidade enquanto o painel e a moldura da janela ficam planos nos dois olhos. Medido entre os olhos: a rocha mais próxima com 23 px de separação, as montanhas distantes 1 px, o painel 0 px.
- **O globo do Marble** ([MPO](docs/screenshots/marble-globe.mpo)): a Terra à frente da tela (+11 px) e as estrelas atrás dela (-12 px), com o painel lateral plano. Esta captura é anterior às correções feitas desde então; a imagem do menu sobre outro menu mostra o Marble de hoje.
- **Área de trabalho estéreo, uma janela suspensa** ([MPO](docs/screenshots/stereo-desktop.mpo)), no mesmo dia. Medido entre os olhos: o painel 0 px (no plano da tela), a janela de som +4 px (à frente), as três janelas atrás -3, -7 e -10 px, e o widget do monitor do sistema -10 px, ao fundo com o papel de parede.

<a id="depth-on-the-desktop"></a>
<a id="the-stereo-desktop-new-frontiers-for-theme-design"></a>
## A área de trabalho estéreo: novas fronteiras para o design de temas

**Pela primeira vez, um tema decide o que vem para a frente e o que vai para o fundo, além da aparência das coisas.**
Por décadas, sombras, chanfros e botões em relevo apenas davam essa impressão; na área de trabalho estéreo isso é real e suave: alguns pixels, dentro dos limites que você escolhe (Configurações do sistema, "Profundidade 3D").

- **O que você usa vem para a frente:** menus, dicas, notificações e caixas de diálogo avançam na sua direção, e a janela em que você trabalha fica no plano da tela. *Implementado e visto numa TV 3D em 13 de outubro de 2026 ([a imagem no topo](#seen-in-3d)).*
- **O restante recua:** as janelas atrás recuam uma após a outra, como papéis numa pilha, e o papel de parede fica ao fundo. *Implementado.*
- **Os pequenos elementos mantêm seu lugar:** o ponteiro assume o nível do que está sob ele, uma sombra fica sobre aquilo em que incide, e uma janela fixada, como uma webcam sobre seus slides, continua à frente de tudo. *Implementado.*
- **Papéis de parede em 3D:** uma foto 3D como fundo mantém seus próprios avanços e recuos, bem atrás de todas as janelas. *Implementado.* Os fundos de vídeo 3D vêm a seguir, com o papel de parede de vídeo de Jeromy Streets. *Em breve.*
- **Protetores de tela em 3D:** o clássico campo de estrelas e os protetores estéreo, em 3D real. *Implementado.*
- **Imagens e ícones em 3D:** fotos 3D aparecem em 3D nas prévias do Dolphin e nos visualizadores de imagens. *Implementado.* Ícones desenhados em pares, um para cada olho, fazem parte do Stereo Oxygen, o visual próprio da edição. *Em breve.*
- **Efeitos que realmente avançam e recuam:** uma janela sendo fechada pode voar em pedaços na sua direção ou mergulhar atrás da tela e quicar num chão. *Implementado na nossa branch do KWin, chegando no próximo pacote.* Alternadores de janelas que se abrem em leque em 3D e o Cubo da área de trabalho em 3D real. *Em breve.*
- **3D desde que você liga:** a tela de inicialização e a tela de login seguem o modo 3D salvo para sua tela principal. *Implementado.*

**E continua sendo uma área de trabalho 2D normal.**
Numa tela comum, nada muda: o mesmo tema, a mesma disposição, os mesmos efeitos, desenhados uma vez.
O 3D aparece apenas onde uma tela pode mostrá-lo ou através de óculos vermelho e ciano, e um tema feito para 3D também é um tema 2D completo.

<a id="the-desktop-cube-what-one-format-makes-possible"></a>Os detalhes: [Profundidade na área de trabalho](docs/depth-on-the-desktop.md) e [Para quem cria e personaliza temas](docs/for-theme-designers.md); ideias, esboços e maquetes 3D são bem-vindos na [issue de temas](https://github.com/Sparky-OS/sparky-stereo-os/issues/78).

<a id="for-developers"></a>
## Para desenvolvedores

**Torne um programa 3D uma vez: entregue as imagens dos dois olhos à área de trabalho, e ela cuida de cada tela.**
Você pode desenvolver e verificar o trabalho na tela que já tem.
- [Desenvolva 3D e XR num monitor comum](docs/develop-3d-on-an-ordinary-monitor.md): comece aqui.
- [Sua cena 3D em estéreo, a partir de uma página web](docs/web-3d-in-stereo.md): three.js, WebGL e WebXR, dos óculos vermelho e ciano em qualquer navegador a todas as telas 3D.
- [Formatos da edição](docs/house-formats.md) e [Divisão do trabalho estéreo](docs/stereo-labor-division.md): as regras, vinculadas às especificações.
- [Teste estéreo sem uma TV 3D](docs/test-stereo-without-a-3d-tv.md) e [Uma máquina virtual com tela 3D](docs/stereo-vm.md): teste a saída 3D numa tela virtual ou numa máquina virtual; um sistema de arquivos raiz pronto com Stereo KWin está no [nosso servidor de repositório](https://repo.sparkyos.org/bench/kwin-root/).
- [Skills](skills/README.md): instruções para pessoas e assistentes de IA que trabalham na edição.

<a id="how-it-works"></a>
## Como funciona

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Os programas descrevem cada imagem; a área de trabalho a adapta a cada tela.** No estéreo, as duas vistas viajam juntas num único buffer no formato full side by side. A extensão HDR proposta preserva a descrição de cor da imagem e as informações de reconstrução por meio dessa mesma divisão do trabalho.

**O contrato estéreo em três linhas.**
- **Stereo KWin** (o compositor do KDE Plasma, com nossas mudanças estéreo) usa full side by side, em qualquer resolução.
- **Os programas** decodificam ou geram estéreo em qualquer padrão e entregam full side by side, em qualquer resolução, ao Stereo KWin.
- **As saídas** (os filtros do Stereo KWin no final, um por tipo de tela) convertem esse formato no que cada tela precisa.

Por que full side by side, uma área de trabalho em duas TVs 3D a partir de duas GPUs e como o mesmo princípio se estende ao HDR: [Como funciona](docs/how-it-works.md). A [declaração HDR](docs/stereo-hdr-content.md) é um projeto que aguarda implementação e testes em dispositivos com diferentes formatos; a representação de intercâmbio HDR continua sendo uma escolha de engenharia a validar. Os testes existentes de estéreo e de profundidade de cor não validam esse caminho HDR.

<a id="stereo-in-the-open-stack-not-in-one-product"></a>
## Estéreo nas camadas abertas, não num único produto

Em outros lugares, o estéreo fica preso a um produto: um headset, um injetor de um fabricante, um kernel de um fabricante.
Aqui, ele é uma propriedade das camadas abertas (KDE, o kernel, os formatos de arquivo), então chega à tela que você já tem: [Estéreo nas camadas abertas](docs/open-stack.md).

<a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>
## Programas que a edição modifica para estéreo 3D e maior profundidade de cor

O que o 3D traz a cada programa, de filmes e fotos a globos e moléculas: [Programas](docs/programs.md).
Como cada um foi modificado e verificado, por área (o caminho até a tela, vídeo, ciência e engenharia, imagens, simuladores, o sistema e o que ainda não está pronto): [Programas em detalhe](docs/programs-in-detail.md).

<a id="our-branches-on-kdes-gitlab"></a>
## Nossas branches no GitLab do KDE

Cada mudança no KDE é uma branch do nosso fork no [invent.kde.org](https://invent.kde.org/danielcamposramos), testada pela própria CI do KDE antes de ser proposta ao projeto original: [as branches e seus resultados de CI](docs/kde-branches.md).

<a id="merged-outside-sparky-stereo"></a>
## Incorporado fora do Sparky Stereo

**26 de outubro de 2026: a IANA atribuiu os valores StereoMode 15 a 20 do Matroska** aos quadros que empacotam imagem e profundidade, após atribuir os tipos de planos 3 a 5 em 20 de outubro às trilhas de profundidade separadas do olho esquerdo, do olho direito e do fundo.
Os dois registros citam nossa especificação stereo-layer.
[Registro atual](https://www.iana.org/assignments/matroska) e [marco do registro e contribuições incorporadas aos projetos originais](docs/upstream-merges.md#registered-identifiers).

Quando um programa quebra o estéreo ou a profundidade de cor no caminho até a tela, a correção vai para o projeto do próprio programa.
Projetos como HandBrake, mpv, Qt Multimedia e PeerTube incorporaram correções do nosso trabalho; cada uma, com o mantenedor que a incorporou e o que está em revisão, está em [Incorporado fora do Sparky Stereo](docs/upstream-merges.md).
Cada parte é mostrada em funcionamento antes de ser considerada pronta, com os números e uma imagem em anáglifo e MPO: [Comprovações](docs/proofs/README.md).
O que pessoas que trabalham com estéreo disseram sobre o projeto, em público e com links: [O que disseram](docs/what-people-said.md).

<a id="documents"></a>
## Documentos

[A fórmula do motor VR para a tela 3D](docs/formula.md), [as primeiras execuções do KWin em TVs reais](docs/first-runs/kwin-2026-10-01/README.md) e [os slides da apresentação no W3C](docs/talks/2026-10-13-w3c-me-ig.md) de 13 de outubro de 2026; todas as páginas estão em [docs](docs/).

<a id="tools"></a>
## Ferramentas

[vkms-stereo-bench](tools/vkms-stereo-bench/README.md) verifica modos 3D numa tela virtual, e [hibernate-bench](tools/hibernate-bench/README.md) verifica a hibernação com Secure Boot, ambos numa máquina virtual.

<a id="the-base-three-open-lists"></a>
## A base: três listas abertas

A pesquisa por trás desta edição é pública, em três listas com curadoria que qualquer pessoa pode copiar (CC0): [awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy) para estéreo 3D, [awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr) para HDR e maior profundidade de cor, e [awesome-vr](https://github.com/danielcamposramos/awesome-vr) para realidade virtual.

<a id="credit"></a>
## Créditos

Sparky Stereo OS, a edição de Daniel Ramos (Capitain Jack) do SparkyLinux (de Paweł "pavroo" Pijanowski).

**Mantenedores de pacotes**, cada um com plenos direitos sobre seu próprio repositório na [Sparky-OS](https://github.com/Sparky-OS):

| | |
| --- | --- |
| <a href="https://github.com/effcol"><img src="https://github.com/effcol.png?size=96" width="72" alt="Eff"></a> | **Eff (effcol)**<br>Mantém [wiz3D](https://github.com/effcol/wiz3D), o wrapper universal de 3D estereoscópico para DirectX, OpenGL, AMD HD3D e NVIDIA 3D Vision, baseado no iZ3D, para todos os sistemas, e seu pacote aqui, [Sparky-OS/wiz3D](https://github.com/Sparky-OS/wiz3D).<br>[![Siga Eff](https://img.shields.io/badge/Follow-effcol-2777AD?style=flat-square&logo=github)](https://github.com/effcol) |
| <a href="https://github.com/halverneus"><img src="https://github.com/halverneus.png?size=96" width="72" alt="Jeromy Streets"></a> | **Jeromy Streets (halverneus)**<br>Criou e mantém [org.kde.video](https://github.com/Sparky-OS/org.kde.video), o papel de parede de vídeo e a tela de bloqueio para KDE Plasma.<br>[![Siga Jeromy](https://img.shields.io/badge/Follow-halverneus-2777AD?style=flat-square&logo=github)](https://github.com/halverneus) |

**Versão:** Sparky Stereo OS 9 "Mashtabba", baseado em Debian 14 "Forky", somente KDE Plasma.

Todas as pessoas em cujo trabalho esta edição se apoia, pelo nome: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Agradecimentos especiais:**
- **David Fattal**, cofundador da Leia e mantenedor do DisplayXR, pelo incentivo, tempo e esforço, e por testar nossa área de trabalho nas telas 3D que ele constrói.
- **Milton Ponson** e **Christoph Dorn**, os braços de Daniel no grupo PM-KR do W3C, todos os membros desse grupo, e **Dave Raggett**, **Ian Jacobs** e **Chris Needham**, do W3C, que abriram suas portas a este trabalho.
- **Tim Berners-Lee** e todas as pessoas que construíram a Internet, camada por camada, e a entregaram a todos.
- A equipe **Foottroller**, por abrir caminho para andar em VR com os próprios pés no Linux.
- **Eric Allard**, o engenheiro que deu vida a Johnny 5 em *Short Circuit*; os roteiristas do filme, **S. S. Wilson** e **Brent Maddock**; e sua música, de **El DeBarge**, **Peter Wolf**, **Ina Wolf** e **David Shire**, ouvida muitas vezes durante a construção desta edição.

**Cite:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Dê uma estrela:** [![Estrelas no GitHub](https://img.shields.io/github/stars/Sparky-OS/sparky-stereo-os?style=flat-square&logo=github&label=Stars)](https://github.com/Sparky-OS/sparky-stereo-os/stargazers) ⭐ Se o Sparky Stereo OS é útil para você, uma estrela ajuda outras pessoas a encontrá-lo.

**Apoie:** [![Patrocine Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Doe para o SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Patrocinar Daniel financia esta edição, e uma doação ao SparkyLinux apoia a distribuição de Paweł, a base sobre a qual ela é construída.

<a href="https://sourceforge.net/p/sparkyos/"><picture><source media="(prefers-color-scheme: dark)" srcset="https://sourceforge.net/sflogo.php?type=18&amp;group_id=3189517"><img alt="SparkyOS no SourceForge" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3189517" width="200"></picture></a>

<a id="licence"></a>
## Licença

Os documentos estão sob a [licença Creative Commons Atribuição 4.0 Internacional](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): compartilhe e adapte, dando crédito ao Sparky Stereo OS.

> "Informação é poder. Mas, como todo poder, há quem queira guardá-lo para si."
> — Aaron Swartz, [*Guerilla Open Access Manifesto*](https://archive.org/details/GuerillaOpenAccessManifesto) (julho de 2008)

Os scripts em `docs/first-runs/` e as ferramentas em `tools/` são código e estão sob a GNU General Public License, versão 2 ou posterior (GPL-2.0-or-later); veja [LICENSE-GPL-2.0](LICENSE-GPL-2.0).
