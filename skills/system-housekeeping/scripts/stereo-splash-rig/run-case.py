#!/usr/bin/python3 -I
# One boot of the rig (ORDER 639): QEMU with KVM under your own user, no display, the guest's console in a file, its
# frames written to OUTDIR through a 9p share; with --fw, OVMF and a standard VGA give the guest the firmware's
# framebuffer (efifb), and the screen is read through QMP screendump just before the GPU's driver appears.
#   run-case.py OUTDIR TAG INITRD 'KERNEL ARGS' [--fw[=WxH]]   (the firmware's framebuffer, 1024x768 by default: a laptop's
#   with its television connected)
import json, os, socket, subprocess, sys, time

out, tag, initrd, args = sys.argv[1:5]
fwarg = [a for a in sys.argv[5:] if a.startswith('--fw')]
fw = bool(fwarg)
fwres = fwarg[0].split('=', 1)[1].split('x') if fwarg and '=' in fwarg[0] else ['1024', '768']
kver = os.environ['KVER']
out = os.path.abspath(out)
os.makedirs(out, exist_ok=True)
qmp_path = os.path.join(out, tag + '.qmp')
serial = os.path.join(out, tag + '.serial')
for p in (qmp_path, serial):
    if os.path.exists(p):
        os.unlink(p)
cmd = ['qemu-system-x86_64', '-name', os.environ.get('PREFIX', 'rig') + '-' + tag, '-machine', 'q35,accel=kvm', '-cpu', 'host', '-smp', '2', '-m', '2G',
       '-kernel', '/boot/vmlinuz-' + kver, '-initrd', initrd,
       # no console= in the restart and shutdown cases, as on a laptop: plymouthd's shutdown modes take tty63 for themselves
       # and count a console= tty as one more console, which forces the text splash
       '-append', '%srdinit=/init quiet splash plymouth.debug=stream:/run/ply.log rig.tag=%s %s' % (
           '' if 'rig.mode=reboot' in args or 'rig.mode=shutdown' in args else 'console=tty1 ', tag, args),
       '-display', 'none', '-qmp', 'unix:%s,server=on,wait=off' % qmp_path, '-serial', 'file:' + serial,
       '-monitor', 'none', '-nic', 'none',
       '-virtfs', 'local,path=%s,mount_tag=out,security_model=none,id=out' % out]
if fw:
    vars_copy = os.path.join(out, tag + '.ovmf-vars.fd')
    with open('/usr/share/OVMF/OVMF_VARS_4M.fd', 'rb') as src, open(vars_copy, 'wb') as dst:
        dst.write(src.read())
    cmd += ['-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
            '-drive', 'if=pflash,format=raw,file=' + vars_copy, '-device', 'VGA,xres=%s,yres=%s,edid=on' % tuple(fwres)]
else:
    cmd += ['-vga', 'none']
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
    shot = False
    endshot = False
    while time.time() - t0 < 150 and vm.poll() is None:
        text = open(serial, errors='replace').read() if os.path.exists(serial) else ''
        if fw and not shot and 'FB-PHASE-END' in text:
            r = qmp('screendump', filename=os.path.join(out, '%s-fb.png' % tag), format='png')
            if 'error' in r:
                print(r)
            shot = True
        # the firmware's framebuffer again when the frames are read: a frame-buffer display still there beside the
        # GPU's screens (rig.unbindfb=0) shows what the splash draws on it then
        if fw and not endshot and 'RIG: ---- frames 1' in text:
            r = qmp('screendump', filename=os.path.join(out, '%s-fbend.png' % tag), format='png')
            if 'error' in r:
                print(r)
            endshot = True
        if 'RIG: DONE' in text:
            break
        time.sleep(0.2)
    t0 = time.time()
    while time.time() - t0 < 30 and vm.poll() is None:
        time.sleep(0.5)
finally:
    if vm.poll() is None:
        vm.terminate()
        try:
            vm.wait(10)
        except subprocess.TimeoutExpired:
            vm.kill()
    if fw and os.path.exists(os.path.join(out, tag + '.ovmf-vars.fd')):
        os.unlink(os.path.join(out, tag + '.ovmf-vars.fd'))
    if os.path.exists(qmp_path):
        os.unlink(qmp_path)
print(open(serial, errors='replace').read())
