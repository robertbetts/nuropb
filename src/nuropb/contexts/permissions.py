from typing import Dict, Any


def authorise_from_token(token) -> Dict[str, Any] | None:
    """ Receives a JWT bearer token and returns the user claims if the token is valid
    :param token:
    :return: claims: Dict[str, Any] or None
    """
    raise NotImplementedError()


def authorise_from_user(credentials: Dict[str, Any]) -> Dict[str, Any] | None:
    """ Receives a users credentials and returns the user claims if the credentials are valid

    :param credentials: Dict[str, Any]
    :return: claims: Dict[str, Any] or None
    """
    raise NotImplementedError()
