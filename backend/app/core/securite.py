"""Hachage des mots de passe et gestion des tokens JWT."""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from backend.app.core.config import obtenir_parametres
from backend.app.modules.auth.schemas import TokenPayload


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    return bcrypt.hashpw(
        mot_de_passe.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    """Verifie un mot de passe contre son hash."""
    return bcrypt.checkpw(
        mot_de_passe.encode("utf-8"), mot_de_passe_hash.encode("utf-8")
    )


def creer_token_acces(email: str, role: str, utilisateur_id: int) -> str:
    """Genere un token JWT."""
    parametres = obtenir_parametres()
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=parametres.jwt_expiration_minutes
    )
    payload = {
        "sub": email,
        "role": role,
        "uid": utilisateur_id,
        "exp": expiration,
    }
    return jwt.encode(payload, parametres.jwt_secret, algorithm=parametres.jwt_algorithm)


def decoder_token(token: str) -> TokenPayload | None:
    """Decode et valide un token JWT."""
    parametres = obtenir_parametres()
    try:
        donnees = jwt.decode(
            token, parametres.jwt_secret, algorithms=[parametres.jwt_algorithm]
        )
        return TokenPayload(
            sub=donnees["sub"],
            role=donnees["role"],
            uid=int(donnees["uid"]),
        )
    except (JWTError, KeyError, ValueError):
        return None
