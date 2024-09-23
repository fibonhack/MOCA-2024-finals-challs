from pwn import process, remote, args, log
import string
import HashTools


def start(io=None):
    if io is not None:
        io.close()
    if args.REMOTE:
        io = remote(args.HOST, args.PORT)
    else:
        io = process(["python3", "chall.py"])
    return io


def submit(io, s, i):
    io.sendlineafter(b"Enter a string to hash:\n", s.encode())
    io.sendlineafter(
        b"Enter an index to insert the string at:\n", str(i).encode())
    io.recvuntil(b"The hash is: ")
    return bytes.fromhex(io.recvline().strip().decode())


io = start()

base = submit(io, "", 0)
log.info(f"base: {base.hex()}")

for flag_length in range(1, 256):
    magic = HashTools.new("sha256")
    s1, sig = magic.extension(
        secret_length=flag_length, original_data=b"",
        append_data=b"", signature=base.hex()
    )
    h1 = submit(io, s1.hex(), flag_length)
    if h1.hex() == sig:
        break
else:
    log.error("flag length not found")
    exit()

log.info(f"flag length: {flag_length}")
flag = b""
while len(flag) < flag_length:
    log.info(f"flag: {flag}")
    i = len(flag) + 1
    for c in string.ascii_letters + string.digits + string.punctuation:
        magic = HashTools.new("sha256")
        test = c.encode()+flag
        s1, sig = magic.extension(
            secret_length=flag_length, original_data=b"",
            append_data=test, signature=base.hex()
        )
        h1 = submit(io, (test+s1[:-i]).hex(),  -i)
        if h1.hex() == sig:
            flag = c.encode() + flag
            break
    else:
        log.error("flag not found")
        exit()
log.success(f"flag: {flag}")
