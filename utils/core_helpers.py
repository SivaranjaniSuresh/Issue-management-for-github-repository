from jose import JWTError, jwt


def decode_token(token, SECRET_KEY, ALGORITHM):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        return None
