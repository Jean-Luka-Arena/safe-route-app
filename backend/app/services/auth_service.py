import datetime
from datetime import timezone

import bcrypt
import jwt

from app.db.database import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.models import Usuario


class EmailYaRegistrado(Exception):
    def __init__(self, email):
        self.email = email
        super().__init__(f"el email '{email}' ya está registrado")


class CredencialesInvalidas(Exception):
    pass


class TokenInvalido(Exception):
    pass


def hashear_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def registrar_usuario(sesion, email, password):
    existente = sesion.query(Usuario).filter_by(email=email).first()
    if existente is not None:
        raise EmailYaRegistrado(email)

    usuario = Usuario(email=email, password_hash=hashear_password(password))
    sesion.add(usuario)
    sesion.commit()
    sesion.refresh(usuario)
    return usuario


def autenticar_usuario(sesion, email, password):
    usuario = sesion.query(Usuario).filter_by(email=email).first()
    if usuario is None or not verificar_password(password, usuario.password_hash):
        raise CredencialesInvalidas()
    return usuario


def crear_token_acceso(usuario):
    expiracion = datetime.datetime.now(timezone.utc) + datetime.timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(usuario.id), "exp": expiracion}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def obtener_usuario_desde_token(sesion, token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise TokenInvalido()

    usuario = sesion.get(Usuario, usuario_id)
    if usuario is None:
        raise TokenInvalido()
    return usuario
