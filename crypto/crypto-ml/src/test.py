from onnxruntime import InferenceSession
import numpy as np


def bin_list(Is):
    ret = []
    for i in Is:
        b0 = np.array([float(a) for a in bin(
            i)[2:].rjust(8, "0")], dtype=np.float32)
        ret = ret + [b0]
    return ret


def noise_to_int(bits):
    bits = [round(float(b)) for b in bits]
    bits = "".join([str(b) if b in [0, 1] else "0" if b <
                   1/10**5 else "1" for b in bits])
    return int(bits, 2)


def lin_to_list(t):
    res = []
    for i in range(len(t)//8):
        res += [noise_to_int(t[i*8:i*8+8])]
    return res


sess = InferenceSession("model.onnx")

inp = b"0123456789abcdef"

inps = [inp[i:i+16] for i in range(0, len(inp), 16)]

inp = []
for i in inps:
    inp += bin_list(i)

x = np.concatenate(inp).reshape(-1, 16*8)

outs = sess.run(None, {"input": x})[0]
out = []
for o in outs:
    out += lin_to_list(o)
out = bytes(out)
print(out)

x = x.reshape(-1)
x = bytes(lin_to_list(x))

if x == b"0123456789abcdef":
    assert out == b"'\xc2IbS\x0c\xf9\xc2\x90\xbf\xb7)U{\x1f\xa3"
    print("Correct!")
