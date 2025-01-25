import wave
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from pydub import AudioSegment
from cryptography.fernet import Fernet


def generate_key():
    """
    Generate a new encryption key.
    :return: Encryption key as a string
    """
    return Fernet.generate_key().decode()


def encrypt_message(secret_message, key):
    """
    Encrypt a secret message using the provided key.
    :param secret_message: The secret message to encrypt
    :param key: The encryption key
    :return: Encrypted message as bytes
    """
    cipher_suite = Fernet(key.encode())
    return cipher_suite.encrypt(secret_message.encode())


def decrypt_message(encrypted_message, key):
    """
    Decrypt an encrypted message using the provided key.
    :param encrypted_message: The encrypted message as bytes
    :param key: The encryption key
    :return: Decrypted message as a string
    """
    cipher_suite = Fernet(key.encode())
    return cipher_suite.decrypt(encrypted_message).decode()


def convert_to_wav(input_audio_path):
    if input_audio_path.lower().endswith('.wav'):
        return input_audio_path

    audio = AudioSegment.from_file(input_audio_path)
    wav_path = os.path.splitext(input_audio_path)[0] + "_converted.wav"
    audio.export(wav_path, format="wav")
    return wav_path


def encode_audio(input_audio_path, secret_message, key):
    wav_path = convert_to_wav(input_audio_path)

    with wave.open(wav_path, 'rb') as audio:
        params = audio.getparams()
        frames = audio.readframes(params.nframes)

        audio_data = np.frombuffer(frames, dtype=np.int16)

    encrypted_message = encrypt_message(secret_message, key)
    secret_message_binary = ''.join(format(byte, '08b') for byte in encrypted_message) + '00000000'

    if len(secret_message_binary) > len(audio_data):
        raise ValueError("The secret message is too large to encode in this audio file.")

    encoded_audio_data = audio_data.copy()
    for i, bit in enumerate(secret_message_binary):
        encoded_audio_data[i] = (encoded_audio_data[i] & ~1) | int(bit)

    output_audio_path = os.path.splitext(wav_path)[0] + "_encoded.wav"
    with wave.open(output_audio_path, 'wb') as encoded_audio:
        encoded_audio.setparams(params)
        encoded_audio.writeframes(encoded_audio_data.tobytes())

    return output_audio_path


def decode_audio(encoded_audio_path, key):
    wav_path = convert_to_wav(encoded_audio_path)

    with wave.open(wav_path, 'rb') as audio:
        frames = audio.readframes(audio.getnframes())
        audio_data = np.frombuffer(frames, dtype=np.int16)

    bits = [str(sample & 1) for sample in audio_data]

    message_bytes = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    encrypted_message = b''
    for byte in message_bytes:
        char = chr(int(''.join(byte), 2))
        if char == '\x00':
            break
        encrypted_message += bytes([int(''.join(byte), 2)])

    return decrypt_message(encrypted_message, key)


def select_input_file(entry):
    file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3 *.flac *.ogg *.aac *.m4a")])
    entry.delete(0, tk.END)
    entry.insert(0, file_path)


def encode_message_ui(input_entry, message_entry, key_entry):
    input_path = input_entry.get()
    secret_message = message_entry.get()
    key = key_entry.get()

    if not key:
        messagebox.showerror("Error", "Encryption key is required.")
        return

    try:
        output_path = encode_audio(input_path, secret_message, key)
        messagebox.showinfo("Success", f"Message encoded successfully into {output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def decode_message_ui(input_entry, key_entry, message_label):
    input_path = input_entry.get()
    key = key_entry.get()

    if not key:
        messagebox.showerror("Error", "Encryption key is required.")
        return

    try:
        decoded_message = decode_audio(input_path, key)
        message_label.config(text=f"Decoded message: {decoded_message}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def create_gui():
    root = tk.Tk()
    root.title("Audio Steganography with Encryption")

    tab_control = tk.Frame(root)
    tab_control.pack(pady=10, padx=10)

    encode_frame = tk.Frame(tab_control)
    encode_frame.pack(side=tk.LEFT, padx=20)

    decode_frame = tk.Frame(tab_control)
    decode_frame.pack(side=tk.RIGHT, padx=20)

    # Encoding Section
    tk.Label(encode_frame, text="Encoding", font=("Arial", 14)).pack()

    tk.Label(encode_frame, text="Input Audio File:").pack(anchor="w")
    input_entry = tk.Entry(encode_frame, width=40)
    input_entry.pack()
    tk.Button(encode_frame, text="Browse", command=lambda: select_input_file(input_entry)).pack()

    tk.Label(encode_frame, text="Secret Message:").pack(anchor="w")
    message_entry = tk.Entry(encode_frame, width=40)
    message_entry.pack()

    tk.Label(encode_frame, text="Encryption Key:").pack(anchor="w")
    key_entry = tk.Entry(encode_frame, width=40)
    key_entry.pack()

    tk.Button(encode_frame, text="Encode Message",
              command=lambda: encode_message_ui(input_entry, message_entry, key_entry)).pack(pady=10)

    # Decoding Section
    tk.Label(decode_frame, text="Decoding", font=("Arial", 14)).pack()

    tk.Label(decode_frame, text="Encoded Audio File:").pack(anchor="w")
    decode_input_entry = tk.Entry(decode_frame, width=40)
    decode_input_entry.pack()
    tk.Button(decode_frame, text="Browse", command=lambda: select_input_file(decode_input_entry)).pack()

    tk.Label(decode_frame, text="Encryption Key:").pack(anchor="w")
    decode_key_entry = tk.Entry(decode_frame, width=40)
    decode_key_entry.pack()

    message_label = tk.Label(decode_frame, text="Decoded message will appear here.")
    message_label.pack(pady=10)

    tk.Button(decode_frame, text="Decode Message",
              command=lambda: decode_message_ui(decode_input_entry, decode_key_entry, message_label)).pack()

    root.mainloop()


if __name__ == "__main__":
    print(generate_key())
    create_gui()
