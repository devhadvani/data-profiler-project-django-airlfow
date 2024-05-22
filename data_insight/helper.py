from cryptography.fernet import Fernet
import base64

# Provide a proper Fernet key (32 bytes)

SECRET_KEY = Fernet.generate_key() 

# Create an instance of the Fernet cipher
cipher_suite = Fernet(SECRET_KEY)

def encrypt_data(data):
    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data

def decrypt_data(encrypted_data):
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
    print("disde",decrypted_data)
    return decrypted_data
