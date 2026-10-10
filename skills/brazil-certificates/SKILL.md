---
name: brazil-certificates
description: Brazil's digital certificates (ICP-Brasil) on Linux: the roots and how to verify them, the E-521 root (v7), browsers and tokens, and the court signer PJeOffice. Load it for work on sparky-ca, signing tools or the edition for Brazil's legal, financial and government users.
---

# ICP-Brasil certificates on Linux

Written on 2026-10-10 from measurements; public material only.

## Where the certificates come from

- ITI publishes the current certificate authorities as one ZIP with its SHA-512 next to it (`acraiz.icpbrasil.gov.br/credenciadas/CertificadosAC-ICP-Brasil/ACcompactado.zip` and `hashsha512.txt`; 180 certificates on 2026-10-10), and the complete history including expired ones as `ACcompactadox.zip` with `hashsha512x.txt`.
- There is no machine-readable index or API; the hash protects against corruption, not against a hostile server, so **pin the roots' SHA-256 fingerprints** in the package and check every certificate's chain against them.
- ITI's HTTPS server does not send its intermediate certificate, so strict clients fail (curl error 60) on a stock Debian, and Debian ships no ICP-Brasil root. Complete the chain properly (the issuer from the AIA, verified to a trusted root); never switch TLS verification off.

## The roots

v1 and v2 expired; v3, v8 and v9 revoked (ITI's root page); v4 to v7 and v10 to v13 valid as of 2026-10-10.
v6 signs with Ed448, which OpenSSL handles.

## v7: EdDSA over E-521

- v7's key and signature carry OID `1.3.6.1.4.1.44588.2.1` (an arc registered by Kryptus Information Security), with a 66-byte key: EdDSA over the curve E-521, permitted by ITI's algorithm standard DOC-ICP-01.01 (v6.0) alongside Ed448 and Brainpool.
- OpenSSL, NSS and GnuTLS do not implement it, so no ordinary Linux program validates a v7 chain today.
- **Verified construction** (v7's own self-signature checks out): PureEdDSA as in RFC 8032, with the curve E-521 (p = 2^521 − 1, d = −376014, the base point with y = 12, order 2^519 − 337554763258501705789107630418782636071904961214051226618635150085779108655765), points encoded as 66 bytes of y in little-endian with the low bit of x in the top bit, the domain string `"SigEd521" || 0x00 || 0x00`, and k = SHAKE256(dom || R || A || message) read over its **full 132 bytes**, little-endian, reduced mod the order.
- Pedro Albanese's [e521](https://github.com/pedroalbanese/e521) (ISC) has the right curve and encoding; its Go `Sign` and `Verify` used only the first 66 bytes of the hash, which is why they did not interoperate with ITI's root. ITI's current bundle has no certificate issued by v7, so the root's self-signature is the one real test vector.

## Browsers, tokens and signers

- Firefox and Waterfox keep certificates in each profile's NSS database (`certutil`, or the `Certificates.Install` policy); Chromium in `~/.local/share/pki/nssdb`, with an existing `~/.pki/nssdb` taking priority. Debian's system store is `/usr/local/share/ca-certificates/` plus `update-ca-certificates`.
- A3 tokens and smart cards: `pcscd`, `libccid` and `opensc`, the PKCS#11 module registered in each NSS database (`modutil`). Proprietary middleware (SafeSign, SafeNet) is fetched on the user's machine, never mirrored; a community OpenSC driver for the G&D StarSign token exists ([starsign-driver](https://github.com/DiegoRibeirodeSouza/starsign-driver), LGPL-2.1).
- **PJeOffice Pro** (CNJ, built by TRF3; 2.5.16u on 2026-10-10): a ZIP with its own Java (Azul Zulu 8u382), a self-patching updater writing into its own folder, and no published checksum. A distribution fetches it on the user's machine and checks it against a pinned hash.
