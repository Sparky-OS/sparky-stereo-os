# Thirty years of KDE, in depth

Posted on KDE Discuss on 16 October 2026: https://discuss.kde.org/t/thirty-years-of-kde-in-depth/51031

On 14 October 1996, a student in Tübingen asked the internet for help building a desktop.
In KDE's new documentary he says he really struggled with English when he wrote that email.
I know the feeling.
I am a Brazilian electrical engineer, I have used KDE since the days of Conectiva, and English is not my first language either.

Watching the film, I kept finding our own story inside KDE's.
So this is a thank you, and a short account of what thirty years of KDE made possible.

## A desktop in stereo

Sparky Stereo OS is my edition of SparkyLinux, on KDE Plasma only, with KWin at its heart.
Programs hand KWin their picture once, as two full views, left eye first.
KWin gives every screen what it needs: a 3D TV's HDMI 3D modes, red-cyan glasses on an ordinary monitor, two projectors as one stereo pair, and now a compatible phone in an inexpensive viewer, [tested as a usable stereo desktop over USB](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md).
The panel and the window frames stay at the screen, while a game or a globe gets real depth inside its window.
Turn 3D off and the desktop is the same 2D one, which our tests check pixel by pixel.

## Lessons KDE wrote before we needed them

Kalle says in the film that at the beginning you need people who provide the infrastructure.
We started under KWin, in the kernel, Mesa and Xwayland, because nothing on top stands without them.

KHTML began with the idea of generating code for the whole spec.
Every stereo field we add lists every packing the H.264 and H.265 tables define, never a subset.

KDE 3 needed more, not different.
Nothing we add takes anything away, and when KDE 4 removed icons from the desktop, people missed them until they came back.
We wrote that lesson down before shipping: every path that gives a different result stays a choice for the person using it.

Plasma began with a principle: nothing should just appear and disappear, everything should move in and out.
On a stereo desktop that sentence is literal.
Windows sit on real planes, behind the screen, at it or in front of it, and they move in and out of it.

Plasma also gave the desktop full control of the system tray, so every icon there looks and behaves the same.
3D output works the same way for us: the compositor owns it, so every program gets the same 3D on every screen.

## Does the desktop still matter?

The film asks whether the desktop matters when everything runs in a browser.
For 3D and HDR, it matters more than ever.
A web page cannot know whether it is shown on a 3D TV, a passive monitor or a headset.
The compositor knows.
On 13 October I presented this to W3C's Media and Entertainment Interest Group: 3D and HDR are the same problem, information about each object carried all the way to the compositor, so each display can show it properly.
The minutes are public: https://www.w3.org/2026/10/13-me-minutes.html
On our desktop, that compositor is KWin.

## Nobody left behind

The film ends with KDE as the world's backstop, so that whole groups of people are not left behind.
Stereo left people behind.
Many bought 3D TVs, projectors and glasses, and the software stopped supporting them.
Red-cyan glasses cost almost nothing and work on any screen, even an old phone.
The documentary also mentions that KDE software once ran in Brazil's primary schools.
A school lab seeing in 3D on the computers it already has is something I would love to see in my country.

## How it is built

I build it with AI partners, and I test every piece: captures of both eyes, controls that must fail, and measurements against the specs.
Everything is public, credited by name, and offered back.
In the film, the early rule was that whoever does the work decides what gets done, because writing software is what counts.
That is the standard I ask to be judged by.

## There is probably a part for you

Matthias's first announcement said a desktop can be cut into lots of parts, and that there is probably a part for you.
A stereo desktop is the same.
If you have a 3D TV gathering dust, red-cyan glasses in a drawer, or a program that should show depth, there is a part for you.
The beta tester threads are open: https://github.com/Sparky-OS/sparky-stereo-os/issues/26
The work is at https://invent.kde.org/danielcamposramos and https://github.com/Sparky-OS/sparky-stereo-os

Happy 30th birthday, KDE, and thank you.

Daniel Campos Ramos
