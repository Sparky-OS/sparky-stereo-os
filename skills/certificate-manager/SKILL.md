---
name: certificate-manager
description: Verified ICP-Brasil catalogue work and Ed521 interoperability for Sparky CA, with boundaries between OpenSSL, NSS, Java and KDE. Load sparky-stereo first.
---

# Certificate manager contributions

Load [sparky-stereo](../sparky-stereo/SKILL.md) first. Read the current
Sparky CA design and verification documents before changing trust behavior.
Milestones 1 and 2 were accepted on 2026-10-10. The KDE interface follows them;
acceptance of the verifier does not establish browser or signing integration.

## Preserve the trust boundary

- Package root fingerprints are reviewed inputs. A refresh cannot authorize
  a new root. A trust anchor is authenticated by its pin, not its self-signature.
- Keep expired and revoked certificates visible and excluded from default
  installation. Preserve historical capabilities and provenance.
- Verify HTTPS, the published ZIP hash and each supported certificate chain.
  Never disable TLS checks to compensate for a missing server intermediate.
- Test system/NSS stores, personal imports and tokens only inside isolated
  containers. Use generated public fixtures; never a real personal certificate.
- Keep the same core behind the application, command line and automation.

## Ed521 lessons measured against ITI

Pedro F. Albanese is the reference implementation's author. Preserve his ISC
credit and make contributions with him; do not present the port as independent
invention. ITI's real v7 uses OID 1.3.6.1.4.1.44588.2.1, absent algorithm
parameters, a 66-byte public key, a 132-byte signature and the complete
132-byte SHAKE256 challenge. Verify must not modify its caller's signature.

Use the exact v7 DER fingerprint and an independent arithmetic implementation.
Reject signature/message/key mutations, noncanonical points, identity keys,
invalid scalar bounds and malformed DER. Generated chains supplement the real
root vector; they are not certificates issued by ITI. Neither measured ITI
archive contained a v7-issued certificate when milestone 2 was accepted.

DOC-ICP-01.01 v6.0 section 2's E521 table and sections 2.2/2.3 define parameters
and domain/prehash behavior. No authoritative numeric Ed521ph OID or official
test vector was found in that inspection. Never assign a guessed number.

Go's math/big secret operations remain variable-time. The OpenSSL prototype
is public-only and unaudited. It removes the unsupported marker only after
the pinned real v7 self-signature verifies. Provider loading never changes pins.

## Integration boundaries

An OpenSSL provider does not add an algorithm to NSS, Java or BoringSSL.
Published root-store inclusion does not prove signature capability. Keep
chain mathematics separate from ICP-Brasil document-signature policy compliance.
Check the actual KDE headers, exported API, certificate store and selected
Poppler backend; online documentation alone is not a build or runtime test.

Keep evidence small and record commands, exact results and gaps. External
messages, PR descriptions and contact details stay in private notes, never in
public source or this skill. Publish only after review.
