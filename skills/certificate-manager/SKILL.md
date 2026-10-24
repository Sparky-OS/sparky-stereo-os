---
metadata:
  requires-packages: gnupg2
name: certificate-manager
description: >-
  Change Sparky CA catalogue, trust-store and Ed521 integration with explicit ownership, rollback and isolated tests.
---

# Certificate manager contributions

## Working recipe

1. Record catalogue revision, root pins, selected groups, trust purposes and target backend (OpenSSL, NSS or Java).
2. Use generated fixtures in isolated stores. Test valid refresh, invalid refresh, revocation, permission denial and ownership-preserving removal.
3. Return store diffs and package tests. A verifier success is separate from browser trust, PDF signing and legal-policy compliance.

Load [sparky-stereo](../sparky-stereo/SKILL.md) first.
Read the current Sparky CA design and verification documents before changing trust behavior.
Milestones 1 and 2 were accepted on 2026-10-10.
The KDE interface follows them; acceptance of the verifier does not establish browser or signing integration.

## Preserve the trust boundary

- Package root fingerprints are reviewed inputs.
  A refresh cannot authorize a new root.
  A trust anchor is authenticated by its pin, not its self-signature.
- Keep expired and revoked certificates visible and excluded from default installation.
  Preserve historical capabilities and provenance.
- Verify HTTPS, the published ZIP hash and each supported certificate chain.
  Never disable TLS checks to compensate for a missing server intermediate.
- Test system/NSS stores, personal imports and tokens only inside isolated containers.
  Use generated public fixtures; never a real personal certificate.
- Keep the same core behind the application, command line and automation.

## Keep the user's choice the only way a group is selected

- A group is chosen only by `install` and `remove`, which write the store's ownership list.
  Automatic updates read that list; they never write it.
- Automatic updates may add a renewed intermediate of a chosen group and remove an owned certificate that expired or was revoked.
  They never add a root, never choose a group and never install an Ed521 certificate.
  A certificate that waits for the user's choice is reported once, not every day.
- A revocation is permanent.
  A failed or unverifiable CRL never turns a known revoked certificate good, and an unknown answer never removes anything.
  A CRL counts only when it names its issuer, verifies against the issuer's key, is complete and has not passed its next update.
- A failed refresh keeps the last verified catalogue and the stores.
  The refreshed catalogue replaces the packaged one only from a root-owned file and only if it still holds everything the package ships.
- The repository job that verifies ITI's bundle holds no write permission.
  A second job opens the pull request.
  A new root arrives only as a reviewed commit; the job opens an issue with the fingerprint instead.
- Test time-dependent steps with libfaketime, never by editing a certificate.
  The timers and the root helper path need a real systemd and root; a container that runs as an ordinary user checks only the unit files.

## Trust purposes are separate decisions

Roots that browsers trust for web sites (TLS) are not trusted to sign PDFs.
Okular and Poppler read the NSS store, which keeps separate trust for TLS and for S/MIME and document signing.
Installing a group gives TLS trust only, so a signed PDF stays untrusted until the user grants the signing purpose on purpose.
GnuPG's trust list for Kleopatra is a third, separate decision.
Say this in the user documentation in plain words.

The KIO certificate manager API is published by a small patch to KIO.
It ships through our kio6 package and our KIO fork after the KDE CI run is green.

## Ed521 lessons measured against ITI

Pedro F.
Albanese is the reference implementation's author.
Preserve his ISC credit and make contributions with him; do not present the port as independent invention.
ITI's real v7 uses OID 1.3.6.1.4.1.44588.2.1, absent algorithm parameters, a 66-byte public key, a 132-byte signature and the complete 132-byte SHAKE256 challenge.
Verify must not modify its caller's signature.

Use the exact v7 DER fingerprint and an independent arithmetic implementation.
Reject signature/message/key mutations, noncanonical points, identity keys, invalid scalar bounds and malformed DER.
Generated chains supplement the real root vector; they are not certificates issued by ITI.
Neither measured ITI archive contained a v7-issued certificate when milestone 2 was accepted.

DOC-ICP-01.01 v6.0 section 2's E521 table and sections 2.2/2.3 define parameters and domain/prehash behavior.
No authoritative numeric Ed521ph OID or official test vector was found in that inspection.
Never assign a guessed number.

Go's math/big secret operations remain variable-time.
The OpenSSL prototype is public-only and unaudited.
It removes the unsupported marker only after the pinned real v7 self-signature verifies.
Provider loading never changes pins.

## Integration boundaries

An OpenSSL provider does not add an algorithm to NSS, Java or BoringSSL.
Published root-store inclusion does not prove signature capability.
Keep chain mathematics separate from ICP-Brasil document-signature policy compliance.
Check the actual KDE headers, exported API, certificate store and selected Poppler backend; online documentation alone is not a build or runtime test.

## Package it, and test what the package does

- A native Debian source package: `debian/` beside the code.
  Name the dependency on the patched KIO in `debian/control` and nowhere else, so one edit changes it.
- Dependencies for the window are listed explicitly, including every QML module; a missing one fails only when the window opens.
- Let `dh_installsystemd` handle the timer only, so installing never runs the update service.
  Never write or remove the switch files from a maintainer script.
- Install in a clean Debian testing container with apt and the recommended packages, then test the installed files, not the build tree: the command name, the desktop entry, the catalogues, the units, a real system store, an A1 import, a token.
- A language ships only when every message is translated; a test fails otherwise and when the catalogue drifts from the sources.
  KDE's translation library needs the locale to exist on the machine, so a test that sets only `LANGUAGE` in a minimal container sees English.
- The privileged helper can be exercised in a container: a system D-Bus, polkit and one rule file written only inside the container.
  Check the refusal with the rule removed, as well as the success.
- A stand-in token is SoftHSM behind p11-kit's proxy, with generated keys; never a physical token or a personal certificate.
- Say what a container cannot show: timers under a running systemd, the package as the main session builds it, the Plasma session, and the owners' review of Brazilian Portuguese and Polish.

Keep evidence small and record commands, exact results and gaps.
External messages, PR descriptions and contact details stay in private notes, never in public source or this skill.
Publish only after review.
