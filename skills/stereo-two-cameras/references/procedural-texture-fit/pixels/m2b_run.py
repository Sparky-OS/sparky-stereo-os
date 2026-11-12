#!/usr/bin/env python3
"""Run p2p commands, each in its own container, PAR at a time, and wait for all (milestone 2b).

m2b_run.py BINARY JOBFILE [PAR]
JOBFILE: one job per line, "OUTFILE ARG..." (the arguments after the binary); a job whose OUTFILE exists is skipped;
the job's output goes to OUTFILE.out. The binary runs from a copy named by its SHA-256 (a rebuild while jobs run
changes nothing). Containers are named ppx-508-2b-*; core files off; no network."""
import hashlib, os, shutil, subprocess, sys, time

S = os.environ['P2P_SCRATCH']  # the scratch folder: fits, pictures, the font index under m1e/ix
W = os.environ['P2P_WORK']  # the work folder that holds docker.sock (DOCKER_HOST)
binary, jobfile = sys.argv[1], sys.argv[2]
par = int(sys.argv[3]) if len(sys.argv) > 3 else 8
digest = hashlib.sha256(open(binary, 'rb').read()).hexdigest()[:16]
os.makedirs(S + '/m2b/bin', exist_ok=True)
run_bin = '%s/m2b/bin/p2p-%s' % (S, digest)
if not os.path.exists(run_bin):
    shutil.copy2(binary, run_bin)
env = dict(os.environ, DOCKER_HOST='unix://%s/docker.sock' % W)
ix = S + '/m1e/ix'
jobs = []
for line in open(jobfile):
    p = line.split()
    if not p or p[0].startswith('#'):
        continue
    if os.path.exists(p[0]):
        continue
    jobs.append(p)
print('%d jobs, %d at a time, binary %s' % (len(jobs), par, digest), flush=True)
t0 = time.time()
running = []
k = 0


def start(job):
    global k
    k += 1
    out, args = job[0], job[1:]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    name = 'ppx-508-2b-%d-%d' % (os.getpid(), k)
    cmd = ['docker', 'run', '--rm', '--name', name, '--network', 'none', '--ulimit', 'core=0', '--cpus', '1',
           '--user', '%d:%d' % (os.getuid(), os.getgid()), '-e', 'HOME=' + S,
           '-e', 'WZ_FONTMAP=', '-e', 'WZ_FONTINDEX=%s/candidates.tsv' % ix, '-e', 'WZ_GLYPHINDEX=',
           '-v', '/usr/share/fonts:/usr/share/fonts:ro', '-v', '/usr/local/share/fonts:/usr/local/share/fonts:ro',
           '-v', '/usr/share/texmf:/usr/share/texmf:ro', '-v', '%s:%s' % (S, S), '-v', '%s:%s:ro' % (W, W), '-w', S,
           'ppx-508-base:forky', run_bin] + args
    f = open(out + '.out', 'w')
    return (subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, env=env), f, job, time.time())


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
print('all done in %.0f s' % (time.time() - t0))
