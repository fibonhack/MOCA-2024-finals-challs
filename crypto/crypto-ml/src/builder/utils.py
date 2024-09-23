
import torch
from torch import nn
import os

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Unary(nn.Module):
    def __init__(self):
        super(Unary, self).__init__()

        self.body = nn.Sequential(
            nn.Linear(1, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        out = self.body(x)
        return out


class Unary128(nn.Module):
    def __init__(self):
        super(Unary128, self).__init__()

        self.body = nn.Sequential(
            nn.Linear(128, 128),
            nn.Sigmoid(),
        )

    def forward(self, x):
        out = self.body(x)
        return out


class MixColumns4(nn.Module):
    def __init__(self):
        super(MixColumns4, self).__init__()

        self.body = nn.Sequential(
            nn.Linear(8*4 * 4, 8*3*4 * 4),  # 4 gmul 1
            nn.Sigmoid(),
            nn.Linear(8*3*4 * 4, 8*3*4 * 4),  # 4 gmul 2
            nn.Sigmoid(),
            # here we have 9 8 bit:
            # gmul(a, 1), gmul(a, 2), gmul(a, 3),
            # gmul(b, 1), gmul(b, 2), gmul(b, 3),
            # gmul(c, 1), gmul(c, 2), gmul(c, 3),
            # gmul(d, 1), gmul(d, 2), gmul(d, 3)
            nn.Linear(8*3*4 * 4, 8*2*8 * 4),  # 8 xor 1:
            nn.Sigmoid(),
            nn.Linear(8*2*8 * 4, 8*2*8 * 4),  # 8 xor 2
            nn.Sigmoid(),
            # here we have 8 8 bit:
            # gmul(c, 1) ^ gmul(d, 1),   gmul(d, 1) ^ gmul(a, 1),
            # gmul(a, 1) ^ gmul(b, 1),   gmul(b, 1) ^ gmul(c, 1),
            # gmul(a, 2) ^ gmul(b, 3),   gmul(b, 2) ^ gmul(c, 3),
            # gmul(c, 2) ^ gmul(d, 3),   gmul(d, 2) ^ gmul(a, 3)
            nn.Linear(8*2*8 * 4, 8*4*4 * 4),  # 4 xor 1
            nn.Sigmoid(),
            nn.Linear(8*4*4 * 4, 8*4 * 4),  # 4 xor 2
            nn.Sigmoid(),
            # here we have 4 8 bit:
            # gmul(a, 2) ^ gmul(b, 3) ^ gmul(c, 1) ^ gmul(d, 1),
            # gmul(a, 1) ^ gmul(b, 2) ^ gmul(c, 3) ^ gmul(d, 1),
            # gmul(a, 1) ^ gmul(b, 1) ^ gmul(c, 2) ^ gmul(d, 3),
            # gmul(a, 3) ^ gmul(b, 1) ^ gmul(c, 1) ^ gmul(d, 2)
        )

    def forward(self, x):
        out = self.body(x)
        return out


class ShiftRows(nn.Module):
    def __init__(self):
        super(ShiftRows, self).__init__()

        self.body = nn.Sequential(
            nn.Linear(8*16, 8*16),
        )

    def forward(self, x):
        out = self.body(x)
        return out


class OneHot16(nn.Module):
    def __init__(self):
        super(OneHot16, self).__init__()
        self.body = nn.Sequential(
            nn.Linear(8*16, 256*16),
        )

    def forward(self, x):
        o = self.body(x)
        return o


class ReverseOneHot16(nn.Module):
    def __init__(self):
        super(ReverseOneHot16, self).__init__()
        self.body = nn.Sequential(
            nn.Linear(256*16, 8*16),
        )

    def forward(self, x):
        x = self.body(x)
        return x


class SboxOneHot16(nn.Module):
    def __init__(self):
        super(SboxOneHot16, self).__init__()
        self.body = nn.Sequential(
            nn.Linear(256*16, 256*16),
        )

    def forward(self, x):
        x = self.body(x)
        return x


class ArgMax16(torch.nn.Module):
    def __init__(self):
        super(ArgMax16, self).__init__()

    def forward(self, x) -> torch.Tensor:
        # find the highest value every 256 values
        pred = torch.argmax(x.view(-1, 256), dim=1)
        return torch.zeros_like(x).view(-1, 256).scatter_(1, pred.unsqueeze(1), 1.).view(x.shape)


class Sbox16(nn.Module):
    def __init__(self):
        super(Sbox16, self).__init__()

        self.body = nn.Sequential(
            OneHot16(),
            ArgMax16(),
            SboxOneHot16(),
            ReverseOneHot16(),
        )

    def forward(self, x):
        out = self.body(x)
        return out


class AES_O(nn.Module):
    def __init__(self, key):
        super(AES_O, self).__init__()
        key_expaded = get_expanded_key(key)
        self.key_layers = []
        for k in key_expaded:
            self.key_layers.append(get_xor_layer(k))
        self.Sbox = get_sbox()
        self.ShiftRows = get_shiftrows()
        self.MixColumns = get_mixcolumns()

        self.body = []
        self.body.append(nn.Linear(16*8, 16*8))
        self.body.append(nn.Sigmoid())
        for i in range(1, len(self.key_layers)-1):
            # Sbox
            self.body.append(nn.Linear(8*16, 256*16))
            self.body.append(ArgMax16())
            self.body.append(nn.Linear(256*16, 256*16))
            self.body.append(nn.Linear(256*16, 8*16))
            # ShiftRows
            self.body.append(nn.Linear(8*16, 8*16))
            # MixColumns
            self.body.append(nn.Linear(8*4 * 4, 8*3*4 * 4))
            self.body.append(nn.Sigmoid())
            self.body.append(nn.Linear(8*3*4 * 4, 8*3*4 * 4))
            self.body.append(nn.Sigmoid())
            self.body.append(nn.Linear(8*3*4 * 4, 8*2*8 * 4))
            self.body.append(nn.Sigmoid())
            self.body.append(nn.Linear(8*2*8 * 4, 8*2*8 * 4))
            self.body.append(nn.Sigmoid())
            self.body.append(nn.Linear(8*2*8 * 4, 8*4*4 * 4))
            self.body.append(nn.Sigmoid())
            self.body.append(nn.Linear(8*4*4 * 4, 8*4 * 4))
            self.body.append(nn.Sigmoid())
            # AddRoundKey
            self.body.append(nn.Linear(8*16, 256*16))
            self.body.append(nn.Sigmoid())
        # Sbox
        self.body.append(nn.Linear(8*16, 256*16))
        self.body.append(ArgMax16())
        self.body.append(nn.Linear(256*16, 256*16))
        self.body.append(nn.Linear(256*16, 8*16))
        # ShiftRows
        self.body.append(nn.Linear(8*16, 8*16))
        # AddRoundKey
        self.body.append(nn.Linear(8*16, 256*16))
        self.body = nn.Sequential(*self.body)

        # load weights
        self.body[0].weight.data = self.key_layers[0].body[0].weight.clone()
        self.body[0].bias.data = self.key_layers[0].body[0].bias.clone()
        for i in range(len(self.key_layers)-2):
            # Sbox
            self.body[2 + 19 *
                      i].weight.data = self.Sbox.body[0].body[0].weight.clone()
            self.body[2 + 19*i].bias.data = self.Sbox.body[0].body[0].bias.clone()
            assert isinstance(self.body[2 + 19*i+1], ArgMax16)
            self.body[2 + 19*i +
                      2].weight.data = self.Sbox.body[2].body[0].weight.clone()
            self.body[2 + 19*i +
                      2].bias.data = self.Sbox.body[2].body[0].bias.clone()
            self.body[2 + 19*i +
                      3].weight.data = self.Sbox.body[3].body[0].weight.clone()
            self.body[2 + 19*i +
                      3].bias.data = self.Sbox.body[3].body[0].bias.clone()
            # ShiftRows
            self.body[2 + 19*i +
                      4].weight.data = self.ShiftRows.body[0].weight.clone()
            self.body[2 + 19*i+4].bias.data = self.ShiftRows.body[0].bias.clone()
            # MixColumns
            self.body[2 + 19*i +
                      5].weight.data = self.MixColumns.body[0].weight.clone()
            self.body[2 + 19*i+5].bias.data = self.MixColumns.body[0].bias.clone()
            assert isinstance(self.body[2 + 19*i+6], nn.Sigmoid)
            self.body[2 + 19*i +
                      7].weight.data = self.MixColumns.body[2].weight.clone()
            self.body[2 + 19*i+7].bias.data = self.MixColumns.body[2].bias.clone()
            assert isinstance(self.body[2 + 19*i+8], nn.Sigmoid)
            self.body[2 + 19*i +
                      9].weight.data = self.MixColumns.body[4].weight.clone()
            self.body[2 + 19*i+9].bias.data = self.MixColumns.body[4].bias.clone()
            assert isinstance(self.body[2 + 19*i+10], nn.Sigmoid)
            self.body[2 + 19*i +
                      11].weight.data = self.MixColumns.body[6].weight.clone()
            self.body[2 + 19*i+11].bias.data = self.MixColumns.body[6].bias.clone()
            assert isinstance(self.body[2 + 19*i+12], nn.Sigmoid)
            self.body[2 + 19*i +
                      13].weight.data = self.MixColumns.body[8].weight.clone()
            self.body[2 + 19*i+13].bias.data = self.MixColumns.body[8].bias.clone()
            assert isinstance(self.body[2 + 19*i+14], nn.Sigmoid)
            self.body[2 + 19*i +
                      15].weight.data = self.MixColumns.body[10].weight.clone()
            self.body[2 + 19*i +
                      15].bias.data = self.MixColumns.body[10].bias.clone()
            assert isinstance(self.body[2 + 19*i+16], nn.Sigmoid)
            # AddRoundKey
            self.body[2 + 19*i+17].weight.data = self.key_layers[i +
                                                                 1].body[0].weight.clone()
            self.body[2 + 19*i+17].bias.data = self.key_layers[i +
                                                               1].body[0].bias.clone()
            assert isinstance(self.body[2 + 19*i+18], nn.Sigmoid)
        i += 1
        # Sbox
        self.body[2 + 19*i].weight.data = self.Sbox.body[0].body[0].weight.clone()
        self.body[2 + 19*i].bias.data = self.Sbox.body[0].body[0].bias.clone()
        self.body[2 + 19*i+2].weight.data = self.Sbox.body[2].body[0].weight.clone()
        self.body[2 + 19*i+2].bias.data = self.Sbox.body[2].body[0].bias.clone()
        self.body[2 + 19*i+3].weight.data = self.Sbox.body[3].body[0].weight.clone()
        self.body[2 + 19*i+3].bias.data = self.Sbox.body[3].body[0].bias.clone()
        # ShiftRows
        self.body[2 + 19*i+4].weight.data = self.ShiftRows.body[0].weight.clone()
        self.body[2 + 19*i+4].bias.data = self.ShiftRows.body[0].bias.clone()
        # AddRoundKey
        self.body[2 + 19*i +
                  5].weight.data = self.key_layers[-1].body[0].weight.clone()
        self.body[2 + 19*i+5].bias.data = self.key_layers[-1].body[0].bias.clone()

    def forward(self, x):
        out = x.reshape(-1, 4, 4, 8).transpose(1, 2).reshape(-1, 16*8)
        for i in range(len(self.body)):
            out = self.body[i](out)
            # if (i-2) % 19 in [3,4,15,17] :
            #     print(f"after sbox B {(i-1)//19} {(i-2) % 19}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
        out = out.reshape(-1, 4, 4, 8).transpose(1, 2).reshape(-1, 16*8)
        return out


class AES(nn.Module):
    def __init__(self, key):
        super(AES, self).__init__()
        key_expaded = get_expanded_key(key)
        self.key_layers = []
        for k in key_expaded:
            self.key_layers.append(get_xor_layer(k))
        self.Sbox = get_sbox()
        self.ShiftRows = get_shiftrows()
        self.MixColumns = get_mixcolumns()

    def forward(self, x):
        out = x.reshape(-1, 4, 4, 8).transpose(1, 2).reshape(-1, 16*8)
        out = self.key_layers[0](out)
        for i in range(1, len(self.key_layers)-1):
            # print(f"after addroundkey {i-1}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
            out = self.Sbox(out)
            # print(f"after sbox {i}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
            out = self.ShiftRows(out)
            # print(f"after shiftrows {i}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
            out = self.MixColumns(out)
            # print(f"after mixcolumns {i}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
            out = self.key_layers[i](out)

        out = self.Sbox(out)
        # print(f"after sbox {i}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
        out = self.ShiftRows(out)
        # print(f"after shiftrows {i}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
        out = self.key_layers[-1](out)
        # print(f"after addroundkey {i}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
        out = out.reshape(-1, 4, 4, 8).transpose(1, 2).reshape(-1, 16*8)
        # print(f"after reshape {i}", " ".join([hex(a)[2:] for a in lin_to_list(out[0])]))
        return out


def bin_tuple(i0, i1, i2, i3):
    b0 = torch.tensor([float(a)
                      for a in bin(i0)[2:].rjust(8, "0")], dtype=torch.float32)
    b0 = b0.to(device)

    b1 = torch.tensor([float(a)
                      for a in bin(i1)[2:].rjust(8, "0")], dtype=torch.float32)
    b1 = b1.to(device)

    b2 = torch.tensor([float(a)
                      for a in bin(i2)[2:].rjust(8, "0")], dtype=torch.float32)
    b2 = b2.to(device)

    b3 = torch.tensor([float(a)
                      for a in bin(i3)[2:].rjust(8, "0")], dtype=torch.float32)
    b3 = b3.to(device)

    return (b0, b1, b2, b3)


def bin_list(Is):
    ret = []
    for i in Is:
        b0 = torch.tensor([float(a) for a in bin(
            i)[2:].rjust(8, "0")], dtype=torch.float32)
        b0 = b0.to(device)
        ret = ret + [b0]
    return ret


def noise_to_int(bits):
    bits = [round(float(b)) for b in bits]
    bits = "".join([str(b) if b in [0, 1] else "0" if b <
                   1/10**5 else "1" for b in bits])
    return int(bits, 2)


def lin_to_tuple(t):
    a = (t[:8], t[8:16], t[16:24], t[24:])
    return tuple([noise_to_int(b) for b in a])


def lin_to_list(t):
    res = []
    for i in range(len(t)//8):
        res += [noise_to_int(t[i*8:i*8+8])]
    return res


def get_not():
    model_not = Unary().to(device)
    model_not.body[0].weight.data = torch.tensor([[-10000000.0]])
    model_not.body[0].bias.data = torch.tensor([5000000.0])
    model_not.eval()

    a = model_not(torch.tensor([0.0]))
    b = model_not(torch.tensor([1.0]))
    assert int(a[0]) == 1
    assert int(b[0]) == 0
    return model_not


def get_nop():

    model_nop = Unary().to(device)
    model_nop.body[0].weight.data = torch.tensor([[10000000.0]])
    model_nop.body[0].bias.data = torch.tensor([-5000000.0])

    model_nop.eval()

    a = model_nop(torch.tensor([0.0]))
    b = model_nop(torch.tensor([1.0]))
    assert int(a[0]) == 0
    assert int(b[0]) == 1
    return model_nop


def get_sbox():
    model_sbox = Sbox16().to(device)
    w = torch.load("sbox16.pt")
    for k in w:
        w[k] = w[k].to_dense()
    model_sbox.load_state_dict(w)
    model_sbox.eval()
    a = bin_list([0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    b = model_sbox(torch.cat(a))
    b = lin_to_list(b)
    assert b == [0x63, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
                 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76, 0xca]
    return model_sbox


def get_mixcolumns():
    model_mixcolumns = MixColumns4().to(device)
    w = torch.load("mixcolumns4.pt")
    for k in w:
        w[k] = w[k].to_dense()
    model_mixcolumns.load_state_dict(w)
    model_mixcolumns.eval()
    a = bin_list([0xdb, 0xdb, 0xdb, 0x7c, 0x13, 0x13, 0x13, 0x63,
                 0x53, 0x53, 0x53, 0x63, 0x45, 0x45, 0x45, 0x63])
    b = model_mixcolumns(torch.cat(a))
    b = lin_to_list(b)
    assert b == [0x8e, 0x8e, 0x8e, 0x5d, 0x4d, 0x4d, 0x4d,
                 0x7c, 0xa1, 0xa1, 0xa1, 0x7c, 0xbc, 0xbc, 0xbc, 0x42]
    return model_mixcolumns


def get_shiftrows():
    model_shiftrows = ShiftRows().to(device)
    model_shiftrows.load_state_dict(torch.load("shiftrows.pt"))
    model_shiftrows.eval()
    a = bin_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    b = model_shiftrows(torch.cat(a))
    b = lin_to_list(b)
    assert b == [1, 2, 3, 4, 6, 7, 8, 5, 11, 12, 9, 10, 16, 13, 14, 15]
    return model_shiftrows


def get_expanded_key(key):
    from aeskeyschedule import key_schedule
    # n bit aes key schedule
    expanded_key = key_schedule(key)
    return expanded_key


def get_xor_layer(round_key):
    key = int.from_bytes(round_key, byteorder='big')

    model_xor = Unary128().to(device)
    model_nop = get_nop()
    model_not = get_not()
    w = model_xor.body[0].weight.clone()
    wb = model_xor.body[0].bias.clone()
    # print(w.shape)
    for i in range(4):
        for j in range(4):
            for k in range(8):
                a = 128-((i+j*4)*8 + k)-1
                b = (i+j*4)*8+k
                c = (i*4+j)*8+k
                if (key >> a) & 1 == 0:
                    w[c, c] = model_nop.body[0].weight.clone()
                    wb[c] = model_nop.body[0].bias.clone()
                else:
                    w[c, c] = model_not.body[0].weight.clone()
                    wb[c] = model_not.body[0].bias.clone()
    model_xor.body[0].weight = nn.Parameter(w)
    model_xor.body[0].bias = nn.Parameter(wb)
    model_xor.eval()

    a = bin_list([0xff]*8+[0x00]*8)
    b = model_xor(torch.cat(a))
    b = lin_to_list(b)
    res = []

    v = [_ for _ in round_key]
    for i in range(4):
        for j in range(4):
            if i > 1:
                res += [v[i+j*4]]
            else:
                res += [0xff ^ (v[i+j*4])]
    assert b == res
    return model_xor


def get_aes_model(key):
    model_o = AES_O(key).to(device)
    model_o.eval()

    model = AES(key).to(device)
    model.eval()

    for i in range(10):
        # print(i)
        inp = os.urandom(16)

        x = torch.cat(bin_list(inp)).reshape(1, 16*8).to(device)
        with torch.no_grad():
            out = model(x)
            out_o = model_o(x)
        out = out_o
        out = bytes([a for a in lin_to_list(out[0])])

        from Crypto.Cipher import AES as AES2
        aes = AES2.new(key, AES2.MODE_ECB)
        res = aes.encrypt(inp)

        assert out == res, (out, res)

    return model_o


if __name__ == "__main__":
    get_aes_model(b'128 bits key!!!!')
    get_aes_model(b'192 bits key!!!!12345678')
    get_aes_model(b'256 bits key!!!!1234567890123456')
    print("AES model test passed")
