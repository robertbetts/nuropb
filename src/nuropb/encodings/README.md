# Serialization and Encryption

Out of the box NuroPb transmits JSON encoded message payloads over the AMQP protocol. There are plans to
support other encodings such as Protocol Buffers and  m.a.y.b.e Avro.

## JSON
JSON encoding is the default encoding for NuroPb. It's a handy human-readable encoding and is
easy to debug, however it's also relatively verbose compares to other binary approaches such as ProtoBuf, 
pickle etc. Take a look [nuropb/interface.py](#nuropb.interface) for type specifications on message
structure as this is describes what is being encoded.

## Encrypted Payloads
This is the first extension to the NuroPb payload serialisation, and ahead of Protocol Buffers other 
serialisation formats. After a serialised payload produces a byte stream, it can then be encrypted. 

It is good practice to transmit any network traffic over TLS, however this only ensures a level of protection 
over the network between point a and point b. As the payload is passed through Gateways, Message Brokers and 
other network and application infrastructure, it is possible for the payload to be inspected or modified, but 
most commonly it can be logged. This is entirely out of the control of the NuroPb protocol and the application 
owner or developer.

In  exceeding the requirements of Data Privacy and Data Protection, it is important to ensure that the 
visibility and integrity of data be accounted for at all times. This is the primary purpose of the encrypted 
payload capability. 

NuroPb uses hybrid asymmetric and symmetric key approach to encrypt request and response payloads. 


### High Level Overview

Where Nuropb enabled service, requires encryption for one or any of its methods is started, it instantiates
a cryptographic private key. The public key is shared with all other services and service mesh consumers. A 
message sender will encrypy the message payload with a Fernet symmetric key. The symmetric key is then 
encrypted with the public key of the receiver and is sent as part of the encrypted payload. The message 
receiver will then decrypt the symmetric key with its private key in order to decrypt the payload. 

A response message is encrypted with the symmetric key from the request and the encrypted payload sent back 
to the sender. On receipt of the response, the original sender will decrypt the response message with the 
symmetric key used to encrypt the original message payload and continue processing the response.

### Encryption Algorithms

* The encryption algorithm uses RSA private and public keys. The RSA algorithm is used to encrypt the symmetric
key after it was used to encrypt the message payload. 
* The Fernet algorithm is used for the symmetric key generation and payload encryption. 

```{note}
The recipe for this approach is prompted by an article from Igor Filatov on Medium.com. The 
article can be found here: https://medium.com/@igorfilatov/hybrid-encryption-in-python-3e408c73970c
```








