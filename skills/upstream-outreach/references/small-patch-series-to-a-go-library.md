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

## A command-line tool without tests: proving a crash fix

Written on 2026-11-13 by ORDER 511 (pedroalbanese/edgetk, one `main.go` of 34,000 lines, no test file, no CI), for a nil pointer panic in its certificate commands.

1. **Reproduce on the exact commit, in a container, before reading the fix.** Build the maintainer's current default branch and run the failing command; keep the panic's file and line for each command (`-pkey text` at one line, `-pkey modulus` and `-pkey check` at two others). A line that differs from the one in the brief is a different defect until shown otherwise.
2. **Find every place by reading, not only the one that crashed.** Search the call (`ParseCertificate(`), read each hit, and list the ones on the commands' paths where the error is discarded and the result used. Here five places, of which the real file reached three; the other two needed a second input.
3. **Use the maintainer's own handling.** The same file already had `log.Fatal("Failed to parse certificate:", err)` and `log.Fatal("Failed to parse GOST certificate:", err)`; the fix is those two lines at the places that lacked them, and nothing else.
4. **The fixture is a real public file, unchanged.** Fetch it from its issuer, compare it byte for byte with any copy already held, and write its source and SHA-256 in the test's comment. Inputs that only exist to fail (a truncated certificate, an altered signature) are made by the test from the real file, in `t.TempDir()`, so the repository gains no invented files.
5. **Read how the tree tests before choosing the form.** Scripts beside the command can be ports to other languages, not tests (edgetk's `edgetk-compat*.py` are). With no precedent, a Go command is tested by its own test binary: `TestMain` calls `main()` when an environment variable is set, and each case starts `os.Args[0]` again with the arguments under test. The exit status, `log.Fatal`, `os.Exit` and a panic are then exactly what a person gets, and no second build is needed.
6. **Every changed place has a case that reaches it, and each case is red before.** Run the test with the parent's source file (`git show PARENT:path > path` in a scratch copy) and keep the log: here six cases, six panics, at four different lines. Then the branch: all green.
7. **Controls that already passed stay in the test:** an ordinary input still printed and verified, and a wrong signature still refused. Say in the commit that they pass before and after.
8. **Leave room for the next subject.** If the next pull request will make today's failing input work (the Ed521 root will be read), the error cases move to an input that stays unreadable; make that input in the test (the same certificate with its algorithm OID changed by one octet) when that subject comes, and say so there.

### Traps

- **Symptom:** `go test ./cmd/edgetk/` ends in `[build failed]` after dozens of `non-constant format string in call to fmt.Printf` lines, though `go build` works. **Cause:** `go test` runs a subset of `go vet` first and stops on its findings in the maintainer's own code. **Fix:** `go test -vet=off ./cmd/edgetk/`, said in the commit message and in the pull request; the vet findings are another subject and are not touched. **How found:** the lines name `main.go`, not the test file.
- **Symptom:** the panic is at another line than the one reported (22686 instead of 22719). **Cause:** the reproduction's key file was empty, so `pem.Decode` returned nil and a different unchecked value was used first. **Fix:** give every argument a real file, and list the second defect in the hand-back as its own finding. **How found:** reading the line the trace names.
- **Symptom:** after a build, `go.mod` in the scratch tree differs from upstream's (six requirements lose `// indirect`). **Cause:** `GOFLAGS=-mod=mod` lets the build rewrite `go.mod`. **Fix:** build with the default (`-mod=readonly`) or `-mod=vendor`, and compare the SHA-256 of `go.mod` and `go.sum` before and after. **How found:** `diff` against `git show COMMIT:go.mod`.
- **Symptom:** a case that expects exit status 0 would start failing on a date. **Cause:** the command's status is "the certificate has not expired" (`time.Now().Before(NotAfter)`). **Fix:** compare the output for that command and the status only where the clock does not decide it.
- **Symptom:** sending an unknown certificate down the generic branch gives `certinfo: Unknown public key type`. **Cause:** the printing library refuses key types it does not know, so "do not default to the wrong branch" is not a whole fix. **Fix:** print in the layout of the maintainer's nearest branch (here his GOST one). **How found:** trying the two-line change first and reading its error.
- **Symptom:** `certa, err := parser(...)` inside an inner block compiles and silently makes a second `err`. **Cause:** `:=` declares both names in the inner scope. **Fix:** read the lines after it to see which `err` they now use; here the inner one, with the same behaviour.

## Perks of this part

- ICP-Brasil's v7 root (OID 1.3.6.1.4.1.44588.2.1, 66 octet key, 132 octet signature) and its CRL are small public files that verify in about 30 ms with a correct implementation; see [brazil-certificates](../../brazil-certificates/SKILL.md).
- DOC-ICP-01.01 section 2.2 allows two prehashes for Ed521ph, SHA3-512 and SHAKE256(x, 64); vectors for both are in the e521 series.
- A certificate parser that keeps what it does not understand is enough to read a new algorithm: `smx509.ParseCertificate` (github.com/emmansun/gmsm) reads the v7 root with its algorithms unknown and keeps `RawSubjectPublicKeyInfo`, `RawTBSCertificate` and `Signature`, so `e521.ParsePublicKey` and `PublicKey.Verify` need nothing else.
- ITI serves the roots as PEM at `https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv7.crt` (and `v5` for an RSA one); on 2026-11-13 both were byte-identical to the copies in Sparky CA's catalogue.
