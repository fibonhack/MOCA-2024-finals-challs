import hashlib

with open("flag.txt", "rb") as f:
    FLAG = f.read().strip()


def hash(s, i):
    msg = FLAG[:i] + s + FLAG[i:]
    return hashlib.sha256(msg).digest()


def main():
    print("Welcome to the hash challenge!")
    while True:
        print("Enter a string to hash:")
        s = bytes.fromhex(input())
        print("Enter an index to insert the string at:")
        i = int(input())
        h = hash(s, i)
        print("The hash is: " + h.hex())


if __name__ == "__main__":
    main()
