import tkinter as tk
import zmq
import pmt
import numpy as np

buttonid2dir = [
    "up_left", "up", "up_right",
    "left", "nothing", "right",
    "down_left", "down", "down_right"
]

W2 = [1, 1, 1, 0]
W1 = [1, 0]

def make_packet(n):
    return W2*4 + W1*n + W2*4 + W1*n + W2*4

dir2seq = {
    "up_left": make_packet(28),
    "up": make_packet(10),
    "up_right": make_packet(34),
    "left": make_packet(58),
    "nothing": [],
    "right": make_packet(64),
    "down_left": make_packet(52),
    "down": make_packet(40),
    "down_right": make_packet(46)
}

IP = "localhost"
PORT = 5555

def send_message(socket, message):
    message = np.array(message, dtype=np.uint64).tolist()
    tags = pmt.make_dict()

    pdu = pmt.serialize_str(
        pmt.cons(
            tags,
            pmt.init_u8vector(
                len(message),
                message
            )
        )
    )
    socket.send(pdu)

# Event handler for button click
def on_button_click(socket, button_id):
    print(f"{buttonid2dir[button_id]} clicked")
    send_message(socket, dir2seq[buttonid2dir[button_id]])


def create_gui(socket):
    root = tk.Tk()
    root.title("RF car controller")

    for i in range(3):
        for j in range(3):
            button_id = i * 3 + j
            print(buttonid2dir[button_id])
            button = tk.Button(root, text=buttonid2dir[button_id],
                               command=lambda id=button_id: on_button_click(socket, id))
            button.grid(row=i, column=j, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.XPUB)
    socket.bind(f"tcp://{IP}:{PORT}")

    import time
    time.sleep(1)

    create_gui(socket)
