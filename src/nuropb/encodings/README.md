# NuroPb Protocol Encodings
This directory contains the encoding definitions for the NuroPb protocol.

Out of the box NuroPb transmits JSON encoded messages payloads over the AMQP protocol. There are plans to
support other encodings such as Protocol Buffers and  m a y b e Avro.

## JSON
The JSON encoding is the default encoding for NuroPb. It is the most human-readable encoding and is the
easiest to debug. It is also the most verbose encoding and is not the most efficient encoding. Take a look
src/nuropb/interface.py for information on the structure of messages as this translates directly to the
JSON encoding.

## Encrypted Payloads
This is the first extension to the NuroPb payload serialisation ahead of the introduction of Protocol Buffers
other serialisation formats. After the JSON or other serialised payload produces a byte stream, this byte stream
is then encrypted. 

It is good practice to transmit any network data over TLS, however this only ensures a level of data protection 
over the network. As the payload is passed through Gateways, Message Brokers and other network infrastructure, 
it is possible for the payload to be intercepted, read or modifies, but most commonly it can be logged. This 
is entirely out of the control of the NuroPb protocol and the application owner or developer.

In  exceeding the requirements of Data Privacy and Data Protection, it is important to ensure that the 
visibility and integrity of data payload can be accounted for at all times. This is the primary purpose of the 
Encrypted Payload Extension. 

The Encrypted Payload Extension encrypts the payload uses hybrid asymmetric and symmetric keys to produce
encryption level data obfuscation of the payload in transit. 

### High Level Overview

When a Nuropb service is started, it retrieves or generates a public and private key pair. The public key is then 
shared with all other services on the service mesh. A message sender will encrypy the message payload with a 
Fernet symmetric key. The symmetric key is then encrypted with the public key of the receiver and is sent with 
the message payload. The message receiver will then decrypt the symmetric key with its private key and then decrypt 
the message payload with the decrypted symmetric key. 

A response message is then encrypted with the same symmetric key and sent back to the sender. On receipt of the 
response, the original sender will then decrypt the response message with the symmetric key used to encrypt the 
original message payload.

### Encryption Algorithms

The encryption algorithm uses RSA 2048 bit private and public keys. The RSA algorithm is used to encrypt the symmetric
key after it was used to encrypt the message payload. The Fernet algorithm is used for the symmetric key generation
and payload encryption. The recipe for this approach is prompted by an article from Igor Filatov on Medium.com. The 
article can be found here: https://medium.com/@igorfilatov/hybrid-encryption-in-python-3e408c73970c








