# A series of small patches to one maintainer's Go library, one subject at a time

Written on 2026-11-10 by ORDER 493 (pedroalbanese/e521, a Go library of EdDSA over the curve E-521 for ICP-Brasil), after its maintainer answered an offer with "send them, so we can review and integrate together".
Load it with [upstream-outreach](../SKILL.md) when a maintainer has said yes to several fixes and tests, and for the independent-vector method of any signature or hash library.

## Recipe

1. **Fresh upstream first.** `git fetch` the maintainer's repository, read `git log` for the file and its open issues and pull requests (search-upstream-first); a fix they already made is dropped and credited. Read their commit titles (e521: short English imperatives, one line), their layout (a flat package, no tests, no CI, no `go.mod`) and their licence header, and follow them.
2. **Our own earlier work is a lead, not a patch.** Lanes' earlier fixes live in other workspaces and sometimes in forks with a different layout; rewrite each fix against their current main and prove it there. Never copy a file out of a workspace the brief does not name.
3. **One subject, one branch, one commit**, in a straight line (0, a, b, c, d, e), because they review and merge in order and the next subject is sent only after the previous one settles. A branch that needs the fix before it adds a test that depends on it (the real-certificate tests need the hash fix) is based on the fix, and says so. A prerequisite the project lacks (here `go.mod` and `go.sum`, so that `go test ./...` can run) is its own first commit, never folded into a fix.
4. **Red and green are shown, not claimed.** For a fix: run the new test on the parent commit (it fails, with the message that names the defect) and on the branch (it passes). Restore only the source file of the parent (`git show PARENT:file.go > file.go`) and keep the tests; put the file back afterwards and check `git status`. For tests that only pin behaviour that already worked, say so in the commit message ("only the challenge cut to 66 octets fails on the previous code") and prove each is able to fail by a mutation: change one line of the source (drop the `S < L` check, ignore `phflag`, shorten the hash) and watch the named vector fail.
5. **Commit message in their style**: a title under 72 characters, a body that says what the defect was, which clause says what it must do, what the test checks and that it fails before; the `Assisted-by:` trailer of the edition (no `Signed-off-by`); the author is Daniel's identity as configured.
6. **The pull-request text** in the maintainer's language and Daniel's voice (one sentence per line, no dash in the middle of a sentence): what, why, how it was tested, the one limit. AI use was said once in the thread and is not repeated in every text.
7. **Run their CI's commands**; when they have none, state the ones our fork runs (`go vet ./...`, `go test ./...`, and `-race` in a container) and do not add a workflow to their repository.
8. **Findings found on the way** (a different defect than the subject) go in the hand-back as one line each with the failing evidence, not into the commit: one finding at a time.

## The independent-vector method

A vector is independent only if the code under test did not produce it.

- Write (or take) a second implementation in another language from the standard's text, sharing no code with the library (here a 150 line affine Python oracle from RFC 8032 section 5.2 and ITI's DOC-ICP-01.01 section 2). Check the oracle itself against the standard's own vectors first (RFC 8032 section 7.4 and 7.5 for Ed448, which the same generic code runs).
- Derive keys from public test seeds that are printed in the file and named "never for real use"; never a real key.
- Ship the generator beside the vectors (`testdata/make_vectors.py`, `testdata/oracle.py`) and make it deterministic, so rerunning it gives the same bytes (`cmp`).
- For a library's own signer, verify the library's signature with the oracle, then pin it as a known answer; the test then checks Sign against the second implementation, not against Verify.
- Real-world vectors are the best independent ones: a public certificate and its CRL signed by the real key (fetch them from the issuer, compare the SHA-256 with the issuer's published value, keep the bytes unchanged in `testdata`).
- Each negative vector names the clause it breaks. A vector that is only a policy (small-order keys, torsion in R: RFC 8032 allows both checks) is left out, not pinned.
- When the library has no API for a variant (Ed521ph here), test the variant through the library's internals in the test file only, and say it.

## Traps

- **Symptom:** `go test ./...` says "go.mod file not found" or `crypto/internal/boring: C source files not allowed when not using cgo`. **Cause:** the repository has no module file; the host toolchain has no cgo for this build. **Fix:** commit a minimal `go.mod`/`go.sum` first (`go mod tidy` with `GOPROXY=off GOFLAGS=-mod=mod` against the local module cache works offline) and run host tests with `CGO_ENABLED=0`; `-race` needs cgo, so run it in the `golang` image with the module cache mounted read-only and `--network none`.
- **Symptom:** a signature verifies once and the same buffer fails the second time, though nothing else changed. **Cause:** `append(sig[:n], more...)` writes into the spare capacity of the caller's slice, so it overwrote the second half of the signature. **Fix:** build the hash input in a new buffer (`make([]byte, 0, total)`). **How found:** a test that verifies twice and compares the bytes; read every `append` whose first argument is a sub-slice of a parameter.
- **Symptom:** a library signs and verifies its own signatures but rejects a real certificate's. **Cause:** `H(x) = SHAKE256(dom5||x, 132)` was computed and then cut to the first 66 octets; both sides did the same, so a round trip passed. **Fix:** use all 132 octets as one little-endian integer. **How found:** the independent oracle and the issuer's own signature; a round-trip test cannot find this kind of bug.
- **Symptom:** a test that prints with `fmt.Printf` shows nothing. **Cause:** `go test` hides the output of passing tests of a package list. **Fix:** `-v`.
- **Symptom:** `python3 -c "import oracle"` leaves a `__pycache__` in a committed folder. **Fix:** `PYTHONDONTWRITEBYTECODE=1` and `sys.dont_write_bytecode = True` in the generator; check `git status` before every commit.
- **Symptom:** a `ParsePublicKey` fails on the real certificate's key ("sequence truncated"). **Cause:** the real AlgorithmIdentifier has no parameters and the library's struct requires them. **Fix:** a separate subject; here the test decodes the key bytes itself and the finding is reported on its own.

## Perks of this part

- ICP-Brasil's v7 root (OID 1.3.6.1.4.1.44588.2.1, 66 octet key, 132 octet signature) and its CRL are small public files that verify in about 30 ms with a correct implementation; see [brazil-certificates](../../brazil-certificates/SKILL.md).
- DOC-ICP-01.01 section 2.2 allows two prehashes for Ed521ph, SHA3-512 and SHAKE256(x, 64); vectors for both are in the e521 series.
