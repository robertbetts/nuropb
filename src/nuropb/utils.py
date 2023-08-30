import re


def obfuscate_credentials(url_with_credentials: str) -> str:
    """obfuscate_secret: obfuscate the password in the AMQP url
    :param url_with_credentials:
    :return: str
    """
    pattern = r"(:.*?@)"
    result = re.sub(
        pattern,
        lambda match: ":" + "x" * (len(match.group(0)) - 2) + "@",
        url_with_credentials,
    )
    return result
