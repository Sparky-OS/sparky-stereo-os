# Sparky Stereo OS beta 1: experimente e desenvolva em 3D

Com esta beta, você tem o desktop inteiro em 3D na tela que já usa e programas com imagem 3D estéreo para experimentar.
Você pode testar tudo pelo pendrive e depois instalar ao lado do Windows.

Sparky Stereo OS, edição de Daniel Ramos do SparkyLinux (de Paweł "pavroo" Pijanowski).

## Baixe e confira a imagem

O arquivo é sparky-stereo-os-9-mashtabba-beta1-x86_64.iso; o link de download vai para quem testa a beta: peça na [issue de testes em português](https://github.com/Sparky-OS/sparky-stereo-os/issues/25).
Ele tem cerca de 5,2 GB, então use um pendrive de pelo menos 8 GB.

SHA-256: `3564fc23315117bb552543235e889e5a398c9cf13e41ec0cceb6086ff43a25ab`.
SHA-512: `cd7c3da5ae699b951471a4c9d6e7443f5a8944fd7eb3a0f2f7d311c96275689be1e056c0ea96296f4ffd75ba4c3b21a5d79c499bb8a34e43b7d89784a35bd377`.

No Windows, confira o SHA-256 com `certutil -hashfile <file> SHA256` e compare o resultado com o valor acima.
No Linux, use `sha256sum <file>` e compare o resultado com o mesmo valor.
Se também quiser conferir o SHA-512, no Linux use `sha512sum <file>` e compare com o valor informado.

## Experimente pelo pendrive

O pendrive inicia uma sessão ao vivo para você conhecer o sistema sem instalar nada no disco.
Use um dispositivo de pelo menos 8 GB, pois a gravação apaga tudo que estiver nele.

No Windows, use o Rufus e escolha “Write in DD Image mode” quando ele perguntar como gravar a imagem.
Nesse modo o pendrive vira uma cópia exata da imagem, igual ao `dd`, que foi testado em todos os firmwares da beta.
O próprio Rufus não foi executado nos testes, e o modo ISO dele não foi testado, então use o modo DD.

Com Ventoy, instale o Ventoy no pendrive com suporte ao Secure Boot e copie a ISO para ele.
O Ventoy foi testado em BIOS, UEFI e UEFI com Secure Boot.
Com o Secure Boot ligado, o Ventoy pode pedir que você autorize a chave dele na primeira inicialização.
Essa chave é separada da chave do Sparky Stereo OS, explicada adiante.

![Mensagem de bloqueio do Ventoy na primeira inicialização com Secure Boot](images/beta1/ventoy-sb-violation.png)

No Linux, grave a imagem no dispositivo inteiro, não em uma partição, com um comando como `sudo dd if=sparky-stereo-os-9-mashtabba-beta1-x86_64.iso of=/dev/sdX bs=4M status=progress oflag=sync`.
Troque `/dev/sdX` pelo dispositivo do seu pendrive e confira duas vezes com `lsblk` antes de iniciar, porque a gravação apaga o dispositivo escolhido.

## Inicie a sessão ao vivo

No menu do pendrive, escolha `Sparky Stereo OS (live)` para iniciar em inglês ou `Sparky Stereo OS (live, Deutsch)` para iniciar em alemão.
Também há a opção `Sparky Stereo OS with Debian's signed kernel`, que inicia com o kernel assinado do Debian, sem os recursos estéreo do kernel da edição.
Para instalar ao lado de um Windows em modo UEFI, inicie o pendrive pela opção UEFI.
Na etapa de idioma do instalador, escolha Português.

## Instale ao lado do Windows

No Windows, abra o Gerenciamento de Disco, clique com o botão direito na unidade C: e escolha “Diminuir volume”.
Deixe pelo menos 30 GB como espaço livre sem formatar.
Desative também a Inicialização rápida (Fast Startup) nas opções de energia do Windows.

Na sessão ao vivo, abra o Sparky Installer pelo ícone na área de trabalho.
Na etapa “Partições”, escolha “Substituir uma partição” e clique no espaço livre na barra “Atual”.
A barra “Depois” mostra a nova partição do Sparky Stereo OS no espaço livre.
Esse é o caminho testado: o instalador cria uma partição ext4 para o Sparky Stereo OS e usa a partição EFI compartilhada com o Windows.
“Instalar lado a lado” reduz uma partição dentro do instalador; reduzir o Windows antes, pelo próprio Windows, foi o caminho testado e mais seguro.
Não escolha “Formatar o disco” em um disco compartilhado, porque essa opção apaga o Windows.
O processo funciona sem conexão de rede, preserva o carregador de fallback do Windows e adiciona o Windows Boot Manager ao menu de inicialização.

![Substituição do espaço livre por uma partição para o Sparky Stereo OS](images/beta1/installer-replace-free-space.jpg)

## Autorize a chave para o Secure Boot

Com o Secure Boot ligado, a sessão pode iniciar com o kernel assinado do Debian antes de você cadastrar a chave da edição.
Para iniciar com o kernel estéreo da edição, cadastre uma vez a chave do Sparky Stereo OS no computador.

No menu do pendrive, escolha `Enrol the Sparky Stereo OS key`, depois `Enroll key from disk` e selecione `EFI/boot/sparky-stereo-secureboot-2026.der`.
Confirme a inclusão da chave e reinicie.

![Arquivo da chave do Sparky Stereo OS selecionado no MokManager](images/beta1/mok-disk-5-file.png)

Você também pode pedir o cadastro pela sessão ao vivo com `sudo mokutil --import /usr/lib/sparkybackup/stereo/secureboot/sparky-stereo-secureboot-2026.der`.
Defina uma senha de uso único, reinicie e escolha “Enroll MOK”, “Continue” e “Yes” no MokManager.
Informe a senha escolhida e reinicie quando o MokManager pedir.
Na primeira tela do MokManager, pressione uma tecla assim que ela aparecer, pois ela fecha após cerca de 10 segundos.

## Use o desktop 3D na sua tela

Abra “System Settings” e “Display Configuration”.
Cada tela tem dois controles, “Anaglyph” e “Other stereo formats”, ambos desligados por padrão.

![Controles Anaglyph e Other stereo formats na configuração de tela](images/beta1/display-settings.jpg)

Ative o controle desejado e clique em “Apply”.
Com “Anaglyph” ligado, a lista “Resolução” passa a mostrar também `(anaglyph, modern screens)` e `(anaglyph, CRT)`.
Use óculos de lentes vermelha e ciano para ver o desktop em 3D no monitor comum.

![Desktop em 3D anaglífico vermelho e ciano](images/beta1/anaglyph-desktop.jpg)

Com “Other stereo formats” ligado, a lista “Taxa de atualização” mostra formatos como lado a lado, cima e baixo, linhas, colunas, checkerboard e frame sequential.
Se a sua TV 3D anunciar modos HDMI 3D, eles também aparecem nessa lista.
Esses modos nunca são escolhidos automaticamente; ao selecionar um, a própria TV muda para 3D.
Depois de cada alteração, aparece “Manter a configuração da tela?” e a configuração volta sozinha em 10 segundos se você não a confirmar.

## Comece a desenvolver em 3D

O formato interno do desktop é uma imagem lado a lado completa, com o olho esquerdo primeiro, entregue na resolução de origem e declarada uma vez ao compositor.
Os programas não escolhem anáglifo ou formatos próprios de cada tela; o KWin transforma a imagem para cada saída.

- Fotos e vídeos estéreo podem chegar em formatos como MPO, JPS, PNG `sTER`, H.264, H.265 e `StereoMode` do Matroska; o sistema converte a entrada para o formato interno. [Veja os formatos da casa.](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/house-formats.md)
- O desktop já oferece prévias 3D de fotos no Dolphin, visualização de fotos estéreo no Gwenview, captura dos dois olhos no Spectacle e reprodução de vídeos 3D no mpv e no Bino. [Veja como o formato estéreo passa pelos programas e pelo desktop.](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/house-formats.md)
- Para gerar os dois olhos, programas podem usar OpenGL quad buffer, uma janela EGL multiview ou uma swapchain Vulkan com duas camadas; a Mesa junta as imagens lado a lado e declara o conteúdo estéreo. [Veja como começar em um monitor comum.](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/develop-3d-on-an-ordinary-monitor.md)
- Outra opção é desenhar as duas vistas lado a lado na própria superfície e declará-las com `kde-stereo-content-v1`; a biblioteca compartilhada atende Wayland e X11. [Veja o protocolo e o fluxo de desenvolvimento.](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/develop-3d-on-an-ordinary-monitor.md)
- Para conferir o resultado sem uma TV 3D, escolha “Anaglyph” para o monitor comum e use óculos vermelho e ciano. [Veja o guia de desenvolvimento em monitor comum](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/develop-3d-on-an-ordinary-monitor.md) e [o roteiro de testes estéreo sem TV 3D](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/test-stereo-without-a-3d-tv.md).

As [skills para quem contribui](https://github.com/Sparky-OS/sparky-stereo-os/tree/main/skills) reúnem orientações para diferentes partes do sistema.

## Conte o que aconteceu

Abra a [issue #25, em português](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) para relatar o resultado.
Inclua o modelo do computador, da placa de vídeo e da tela, os passos que você seguiu, o que esperava ver e o que apareceu.
Se puder, anexe capturas de tela ou fotos que ajudem a mostrar o problema.

## O que esta beta ainda não faz tão bem

Computadores com UEFI de 32 bits, em geral tablets Atom mais antigos, não iniciam esta imagem.
O MokManager fecha a tela inicial de confirmação após cerca de 10 segundos se você não pressionar uma tecla.
Os slides do instalador aparecem em inglês mesmo quando o instalador está em português, alemão ou outro idioma.
Os menus do GRUB ainda mostram a imagem azul do átomo do SparkyLinux.
As Configurações Rápidas ainda oferecem Breeze e Breeze Dark, e a Central de Boas-vindas do KDE abre junto com o Sparky Welcome no primeiro acesso.
O repositório próprio da edição ainda não está online, então o apt avisa que essa fonte está inacessível, enquanto as atualizações do Debian, do SparkyLinux e do deb-multimedia funcionam.
O pendrive ao vivo é mais lento do que o sistema instalado.
