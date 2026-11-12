#!/usr/bin/env python3
"""Run fitter jobs, each in its own container, PAR at a time, and wait for all of them (milestone 2).

m2run.py BINARY JOBFILE [PAR]
JOBFILE: one job per line, "OUTPREFIX TILE.ppm [name=value ...]"; a job whose OUTPREFIX.script exists is skipped.
Every job's output goes to OUTPREFIX.out; the binary is run from a copy named by its SHA-256 (in SCRATCH/bin), so a
rebuild while jobs run changes nothing. Prints one line per finished job and the total time.

The environment names the rest, and the runner stops when one is missing:
  P2P_SCRATCH   the folder every path of the jobs lies in (mounted read-write; the containers run as you)
  P2P_IMAGE     a local image with nothing but a shell (the fitter is one static program)
  P2P_PRIOR     the prior (prior.py's prior.txt)
  P2P_FONTINDEX the font index's candidates.tsv (for seeds and Text), or empty
  P2P_NAME      a prefix for the containers' names, so you stop only your own
  DOCKER_HOST   as usual
The machine's font folders are mounted read-only, as the font index reads them in place."""
import hashlib, os, shutil, subprocess, sys, time

def need(k):
    v = os.environ.get(k)
    if v is None:
        sys.exit('%s is not set: see the first lines of this file' % k)
    return v

S, image, prior, fontindex, prefix = need('P2P_SCRATCH'), need('P2P_IMAGE'), need('P2P_PRIOR'), need('P2P_FONTINDEX'), need('P2P_NAME')
binary, jobfile = sys.argv[1], sys.argv[2]
par = int(sys.argv[3]) if len(sys.argv) > 3 else 8
digest = hashlib.sha256(open(binary, 'rb').read()).hexdigest()[:16]
os.makedirs(S + '/bin', exist_ok=True)
run_bin = '%s/bin/p2p-%s' % (S, digest)
if not os.path.exists(run_bin):
    shutil.copy2(binary, run_bin)
jobs = []
for line in open(jobfile):
    p = line.split()
    if not p or p[0].startswith('#'):
        continue
    if os.path.exists(p[0] + '.script'):
        continue
    jobs.append(p)
print('%d jobs, %d at a time, binary %s' % (len(jobs), par, digest), flush=True)
t0 = time.time()
running = []
k = 0


def start(job):
    global k
    k += 1
    out, tile, extra = job[0], job[1], job[2:]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    name = '%s-%d-%d' % (prefix, os.getpid(), k)
    cmd = ['docker', 'run', '--rm', '--name', name, '--network', 'none', '--ulimit', 'core=0', '--cpus', '1',
           '--user', '%d:%d' % (os.getuid(), os.getgid()), '-e', 'HOME=' + S,
           '-e', 'WZ_FONTMAP=', '-e', 'WZ_FONTINDEX=' + fontindex, '-e', 'WZ_GLYPHINDEX=',
           '-v', '/usr/share/fonts:/usr/share/fonts:ro', '-v', '/usr/local/share/fonts:/usr/local/share/fonts:ro',
           '-v', '%s:%s' % (S, S), '-w', S, image, run_bin, 'fit', tile, prior, out] + extra
    f = open(out + '.out', 'w')
    return (subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT), f, job, time.time())


while jobs or running:
    while jobs and len(running) < par:
        running.append(start(jobs.pop(0)))
    time.sleep(1)
    still = []
    for pr, f, job, ts in running:
        if pr.poll() is None:
            still.append((pr, f, job, ts))
            continue
        f.close()
        print('%s %s exit %d, %.0f s' % (time.strftime('%H:%M:%S'), job[0], pr.returncode, time.time() - ts), flush=True)
    running = still
print('all done in %.0f s' % (time.time() - t0), flush=True)
