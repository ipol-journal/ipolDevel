import json

def is_json(myjson):
    """
    verify if string is in json format
    """
    try:
        json_object = json.loads(myjson)
        del json_object
    except Exception as e:
        print("is_json e:%s" % e)
        return False
    return True

def generate_ssh_keys():
    """
    Generates public and private ssh keys.
    """
    from cryptography.hazmat.primitives import serialization as crypto_serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = Ed25519PrivateKey.generate()
    privkey = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.OpenSSH,
        crypto_serialization.NoEncryption()
    )
    pubkey = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )
    return pubkey, privkey
