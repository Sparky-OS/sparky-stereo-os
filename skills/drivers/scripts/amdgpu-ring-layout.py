#!/usr/bin/env python3
# amdgpu-ring-layout.py DEVCOREDUMP: decodes the gfx ring an amdgpu devcoredump holds (Southern Islands PM4) and says what is
# on it between 0 and Wptr: which packets, and whether a job's INDIRECT_BUFFER and an EVENT_WRITE_EOP fence (with its
# sequence number) are there. A ring that holds only the CP's init, the clear state, ring tests and NOP padding has
# nothing left that can write the timed-out fence.
# Packet format: type-3 header bits 31:30 = 3, count 29:16 (body = count + 1 dwords), opcode 15:8; type-2 0x80000000 is
# a one-dword NOP (gfx_v6_0 ring funcs .nop). Opcodes from the kernel's drivers/gpu/drm/amd/amdgpu/sid.h.
import re
import sys

OPS = {0x10: 'NOP', 0x11: 'SET_BASE', 0x12: 'CLEAR_STATE', 0x15: 'DISPATCH_DIRECT', 0x22: 'COND_EXEC',
       0x33: 'INDIRECT_BUFFER_CONST', 0x37: 'WRITE_DATA', 0x3C: 'WAIT_REG_MEM', 0x3F: 'INDIRECT_BUFFER',
       0x40: 'COPY_DATA', 0x42: 'PFP_SYNC_ME', 0x43: 'SURFACE_SYNC', 0x44: 'ME_INITIALIZE', 0x46: 'EVENT_WRITE',
       0x47: 'EVENT_WRITE_EOP', 0x4A: 'PREAMBLE_CNTL', 0x68: 'SET_CONFIG_REG', 0x69: 'SET_CONTEXT_REG',
       0x76: 'SET_SH_REG', 0x8B: 'SWITCH_BUFFER'}


def main():
    text = open(sys.argv[1], encoding='utf-8', errors='replace').read()
    m = re.search(r'Rptr: (0x[0-9a-f]+) Wptr: (0x[0-9a-f]+)', text)
    if not m or 'ring name: gfx' not in text:
        sys.exit('amdgpu-ring-layout: no gfx ring section (Rptr/Wptr) in this file')
    rptr, wptr = int(m.group(1), 16), int(m.group(2), 16)
    ring = {}
    for line in text.splitlines():
        f = line.split()
        if len(f) == 2 and f[0].startswith('0x') and f[1].startswith('0x'):
            ring[int(f[0], 16) // 4] = int(f[1], 16)
    if not ring:
        sys.exit('amdgpu-ring-layout: the ring contents are empty')
    n = max(ring) + 1
    for k in ('pasid', 'vmid', 'time'):
        mm = re.search(rf'^{k}: (.*)$', text, re.M)
        if mm:
            print(f'{k}: {mm.group(1)}')
    print(f'Rptr 0x{rptr:x} Wptr 0x{wptr:x} (dwords), ring {n} dwords')
    i, nops, found = 0, 0, {'INDIRECT_BUFFER': 0, 'EVENT_WRITE_EOP': 0}
    seqs = []
    while i < min(wptr, n) if wptr else 0:
        d = ring.get(i, 0)
        if d == 0x80000000:
            nops += 1
            i += 1
            continue
        if nops:
            print(f'  0x{i - nops:04x}  NOP x{nops}')
            nops = 0
        if d >> 30 == 3:
            count, op = (d >> 16) & 0x3FFF, (d >> 8) & 0xFF
            name = OPS.get(op, f'op 0x{op:02x}')
            body = [ring.get(i + 1 + j, 0) for j in range(count + 1)]
            extra = ''
            if name == 'SET_CONFIG_REG' and len(body) >= 2:
                extra = f' reg 0x{body[0]:x} = 0x{body[1]:x}'
            if name == 'EVENT_WRITE_EOP' and len(body) >= 4:
                extra = f' writes seq {body[3]}'
                seqs.append(body[3])
            if name in found:
                found[name] += 1
            print(f'  0x{i:04x}  {name} ({count + 1} dwords){extra}')
            i += count + 2
        else:
            print(f'  0x{i:04x}  data 0x{d:08x}')
            i += 1
    if nops:
        print(f'  0x{i - nops:04x}  NOP x{nops}')
    print(f'INDIRECT_BUFFER packets before Wptr: {found["INDIRECT_BUFFER"]}; EVENT_WRITE_EOP: {found["EVENT_WRITE_EOP"]}'
          + (f' (seq {", ".join(map(str, seqs))})' if seqs else ''))
    if not found['EVENT_WRITE_EOP']:
        print('verdict: no fence packet on the ring; the timed-out fence cannot be written by the GPU')


if __name__ == '__main__':
    main()
