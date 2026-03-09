from passlib.context import CryptContext

password_context = CryptContext(schemes="bcrypt", deprecated="auto")

def get_password_hash(password):
    return password_context.hash(password)

def verify_password(hash_password, password):
    return password_context.verify(password, hash_password)
