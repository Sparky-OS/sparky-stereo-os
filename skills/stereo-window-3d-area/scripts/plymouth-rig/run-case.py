#!/usr/bin/python3 -I
# One guest boot of the rig: QEMU with a virtio-vga that takes stereo modes, the splash's screen read through QMP
# (screendump), the guest's console in a file. usage: run-case.py OUTDIR TAG INITRD 'KERNEL ARGS' [SHOTS]
import json, os, socket, subprocess, sys, time

out, tag, initrd, args = sys.argv[1:5]
shots = int(sys.argv[5]) if len(sys.argv) > 5 else 2
kver = os.environ['KVER']
os.makedirs(out, exist_ok=True)
qmp_path = os.path.join(out, tag + '.qmp')
serial = os.path.join(out, tag + '.serial')
for p in (qmp_path, serial):
    if os.path.exists(p):
        os.unlink(p)
cmd = ['qemu-system-x86_64', '-name', 'plymouth-rig-' + tag, '-machine', 'q35,accel=kvm', '-cpu', 'host', '-smp', '2', '-m', '3G',
       '-kernel', '/boot/vmlinuz-' + kver, '-initrd', initrd,
       '-append', 'console=ttyS0 rdinit=/init loglevel=3 plymouth.debug=stream:/run/ply.log ' + args,
       '-device', 'virtio-vga,xres=1920,yres=1080,stereo=on,max_hostmem=1G', '-display', 'none',
       '-qmp', 'unix:%s,server=on,wait=off' % qmp_path, '-serial', 'file:' + serial, '-monitor', 'none', '-nic', 'none']
vm = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=open(os.path.join(out, tag + '.qemu.log'), 'w'))
try:
    for _ in range(100):
        if os.path.exists(qmp_path):
            break
        time.sleep(0.1)
    s = socket.socket(socket.AF_UNIX)
    s.connect(qmp_path)
    f = s.makefile('rw')
    f.readline()
    def qmp(name, **a):
        f.write(json.dumps({'execute': name, 'arguments': a}) + '\n')
        f.flush()
        while True:
            m = json.loads(f.readline())
            if 'return' in m or 'error' in m:
                return m
    qmp('qmp_capabilities')
    t0 = time.time()
    while time.time() - t0 < 120:
        text = open(serial, errors='replace').read() if os.path.exists(serial) else ''
        if 'SPLASH-UP' in text:
            break
        time.sleep(0.3)
    else:
        print('no splash within 120 s'); 
    time.sleep(4)
    for i in range(shots):
        r = qmp('screendump', filename=os.path.abspath(os.path.join(out, '%s-%d.png' % (tag, i + 1))), format='png')
        if 'error' in r:
            print(r)
        time.sleep(0.5)
    t0 = time.time()
    while time.time() - t0 < 60 and vm.poll() is None:
        time.sleep(0.5)
finally:
    if vm.poll() is None:
        vm.terminate()
        try:
            vm.wait(10)
        except subprocess.TimeoutExpired:
            vm.kill()
print(open(serial, errors='replace').read())
