# Spatial Roaming Network

**For people building and linking spatial worlds:** a proposal for finding places, moving between them and receiving their content near the visitor.
**Status:** a proposal combining established techniques, named by Daniel Campos Ramos on 28 October 2026.
This page records the idea for discussion; it does not report an implemented or measured SRN path in Sparky Stereo OS.

## What it means

Spatial Roaming Network (SRN) applies a cellular model to the spatial web, including both physical places and places inside virtual worlds.
A cell is an area in which a visitor can discover services, content, people and doors to other places.
A network is a set of cells managed by a publisher, with connections to cells managed by other publishers.
The proposal has three parts: finding, moving and delivering.

## Finding

Real cells describe physical places and can use an existing geographic index such as H3.
Virtual cells describe logical places inside a world, such as a game hub or a square with no location on Earth.
They can have local coordinates, but need no latitude or longitude.
Each cell needs an address that identifies its network and its place within that network.

Inside a virtual world, an "irradiator" would act like a phone tower, announcing the services, content, people and doors available within its range.
Its range is a region defined by the world, and its announcements travel over the network.
It is a software role, with no radio transmitter required.
The proposed protocol would let a client discover both real and virtual cells while keeping their coordinate systems distinct.

## Moving

As the visitor moves, handover would change which cell serves the visit, with the aim of keeping its services available.
Roaming would let a visitor enter a spatial network run by another publisher, whether the destination is real or virtual.
A door could lead from a physical place into a virtual square, or from one publisher's world into another's.

The destination would keep control of its content and access rules.
The protocol would need to agree what identity and session state can cross, with the visitor's consent, and what happens when access is refused or a connection fails.
Continuity across a boundary is a requirement to design and test.
Finding a door alone does not provide it.

## Delivering

A person in Brazil visiting another spatial network should be able to receive that world's content from an edge server near them, where the publisher permits it and the service is available.
In this design, the world would keep its address and publisher while its delivery location could change.
This follows content delivery networks (CDNs), including delivery across cooperating CDNs.
Theoretically, a nearby edge could reduce content loading delay; that benefit still needs measuring with actual visitors, networks and worlds.
Cached assets and a live world's changing state have different needs, so edge delivery does not by itself move the simulation or keep a shared session consistent.

## Why it fits stereo and the spatial web

Finding a world and moving into it should serve current 2D and 3D devices as well as headsets.
The same place can be presented in 2D or with two eye views, according to the client and display.
SRN would concern discovery, movement and delivery; the renderer still produces the views.
In Sparky Stereo OS, those views follow the [presentation contract](how-it-works.md): declared full side by side, left eye first, each eye at its own resolution, with Stereo KWin adapting them for the display.

## Part of the answer

The proposal is to combine handover and roaming across independent publishers, logical cells for places with no geographic location, one protocol for real and virtual cells, and edge delivery.
The sources below already establish parts of that design, including independent map services, virtual regions, travel between grids, cellular mobility and delivery across networks.
SRN claims to invent none of those techniques.
The proposed combination still needs a protocol, interoperable implementations and measurements.

SRN is part of the answer to linking worlds.
It does not settle world formats, rendering, identity, permissions, privacy or shared simulation.
[Dynamic Procedural Foveated Rendering](dynamic-procedural-foveated-rendering.md) is a separate proposal for how a world could draw detail while its images load.
Daniel's [Web of Worlds input](https://github.com/w3c-cg/pm-kr/tree/main/talks/2026-10-30-tpac-web-of-worlds) puts SRN in its discussion context.
A useful next step is to compare these requirements with existing discovery and world-linking protocols, then test a crossing between two independent publishers.

## Sources

- Open AR Cloud, [OSCP Spatial Service Discovery](https://github.com/OpenArCloud/oscp-spatial-service-discovery/blob/e86a0e54f8155264d247b9e6e1dfc0a6e0598136/README.md) and [`@oarc/ssd-access`](https://github.com/OpenArCloud/ssd-access/blob/531b6ac0b6d68d846c3293ca287ff608fb5367d1/lib/README.md), provide nearby service discovery using H3 and regional servers, with service records shared between providers.
- Sagar Bharadwaj, Anthony Rowe and Srinivasan Seshan, [Uniting the World by Dividing it: Federated Maps to Enable Spatial Applications](https://arxiv.org/html/2507.11437v1), HotOS 2025, propose independently managed physical maps and services, including switching localization services along a journey.
- Sagar Bharadwaj, Ziyong Ma, Ivan Liang, Michael Farb, Anthony Rowe and Srinivasan Seshan, [OpenFLAME: A Federated Spatial Naming Infrastructure](https://doi.org/10.4230/OASIcs.NINeS.2026.20), NINeS 2026, implement discovery through DNS and services across independently managed maps.
- Josh Millar, Ryan Gibb, Roy Ang, Hamed Haddadi and Anil Madhavapeddy, [An Architecture for Spatial Networking](https://arxiv.org/html/2507.22687v3), describe Bifröst, which uses physical containment and connectivity to scope names, services and policies while linking spaces.
- Gokul Kartha, [Geospatial Resource Discovery, draft-kartha-grd-01](https://datatracker.ietf.org/doc/html/draft-kartha-grd-01), describes physical cells, resource lookup and local filtering by viewing volume.
  It is an expired individual Internet-Draft, with no IETF endorsement, and defines no protocol or implementation.
- Web3D Consortium, [X3D 4.0, clause 22.4.1, ProximitySensor](https://www.web3d.org/documents/specifications/19775-1/V4.0/Part01/components/environmentalSensor.html#ProximitySensor), defines events for entering, leaving and moving within a box in a scene.
- Jean-Sébastien Boulanger, Jörg Kienzle and Clark Verbrugge, [Comparing Interest Management Algorithms for Massively Multiplayer Games](https://doi.org/10.1145/1230040.1230069), NetGames 2006, compare ways to send players relevant state changes, including filtering by tiles and visibility.
- Martin Woolley, Bluetooth SIG, [Advertising works, part 1](https://www.bluetooth.com/blog/advertising-works-part-1/), explains nearby discovery through advertising packets and scanning, including beacons.
- 3GPP, [TS 23.501 V15.5.0, clause 4.2.4](https://www.etsi.org/deliver/etsi_ts/123500_123599/123501/15.05.00_60/ts_123501v150500p.pdf), specifies home and visited network architectures for roaming.
  [TS 23.502 V15.9.0, clause 4.9.1](https://www.etsi.org/deliver/etsi_ts/123500_123599/123502/15.09.00_60/ts_123502v150900p.pdf) specifies handover procedures between radio access nodes.
- Larry Peterson, Bruce Davie and Rob van Brandenburg, [RFC 7336, Framework for Content Distribution Network Interconnection](https://www.rfc-editor.org/rfc/rfc7336.html), describes request routing, content delivery and policy exchange across CDNs.
- Crista Lopes's Hypergrid already supports travel between OpenSimulator grids, as recorded by the [OpenSimulator Community Conference](https://conference.opensimulator.org/conference-organizing-committee/).
  Travel between independent virtual worlds is a precedent to build on.

The name records Daniel Campos Ramos's proposal of 28 October 2026.
In Portuguese: Rede de Roaming Espacial.
