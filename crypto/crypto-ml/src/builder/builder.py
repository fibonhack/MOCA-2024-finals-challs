
import os
import zipfile
import numpy as np
from onnxruntime import InferenceSession
from utils import get_aes_model, bin_list, lin_to_list
import torch
from Crypto.Util.Padding import pad

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


flag = b'pwnx{they_told_me_1_could_not_do_aes_with_ml_so_1_did_it_anyway}'
key = flag[:32]

model = get_aes_model(key)

inp = b"here the last piece of the flag and the rest is in the key :) " + \
    flag[32:]

inp = pad(inp, 16)

inps = [inp[i:i+16] for i in range(0, len(inp), 16)]

inp = []
for i in inps:
    inp += bin_list(i)

x = torch.cat(inp).reshape(-1, 16*8).to(device)

outs = model(x)
out = []
for o in outs:
    out += lin_to_list(o)
out = bytes(out)
print(out)

x = torch.cat(bin_list([0]*16)).reshape(-1, 16*8).to(device)
x.requires_grad = True
model(x)

path = input("Enter path to save model: ")

if not path.endswith('.onnx'):
    raise ValueError("Path must end with .onnx")

torch.onnx.export(model, x, path, dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}},
                  input_names=['input'], output_names=['output'])

print("Tmp model saved to", path)

sess = InferenceSession(path)
inp = [x.cpu() for x in inp]
x = np.concatenate(inp).reshape(-1, 16*8)

ys = sess.run(None, {"input": x})[0]
y = []
for o in ys:
    y += lin_to_list(o)
y = bytes(y)
print(y)

assert y == out
print("Model exported correctly")

# zip the model
with zipfile.ZipFile('model.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(path)
print("Model zipped")

os.remove(path)

print("Removed tmp model")

with open('ciphertext', 'wb') as f:
    f.write(out)

print("Done")
