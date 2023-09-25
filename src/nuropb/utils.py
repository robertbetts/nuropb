import re
from typing import Any, Dict


def obfuscate_credentials(url_with_credentials: str | Dict[str, Any]) -> str:
    """obfuscate_secret: obfuscate the password in the AMQP url
    :param url_with_credentials:
    :return: str
    """
    if isinstance(url_with_credentials, dict):
        return "tls-amqp://{username}:@{host}:{port}/{vhost}".format(**url_with_credentials)

    pattern = r"(:.*?@)"
    result = re.sub(
        pattern,
        lambda match: ":" + "x" * (len(match.group(0)) - 2) + "@",
        url_with_credentials,
    )
    return result
