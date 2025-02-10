from cryptography import x509
from cryptography.x509 import Certificate
from cryptography.hazmat.primitives import serialization
import datetime
import cryptography.hazmat.primitives.serialization.pkcs12 as pkcs12

def get_userdata(p12_fname):
    try:    
        with open(p12_fname, "rb") as f:
            p12 = f.read()
        password = None # p12 não está protegido...
        (private_key, user_cert, [ca_cert]) = pkcs12.load_key_and_certificates(p12, password)
        return (private_key, user_cert, ca_cert)
    
    except IOError as e:
        return None

def mkpair(x, y):
    """produz uma byte-string contendo o tuplo '(x,y)' ('x' e 'y' são byte-strings)"""
    len_x = len(x)
    len_x_bytes = len_x.to_bytes(2, "little")
    return len_x_bytes + x + y


def unpair(xy):
    """extrai componentes de um par codificado com 'mkpair'"""
    len_x = int.from_bytes(xy[:2], "little")
    x = xy[2 : len_x + 2]
    y = xy[len_x + 2 :]
    return x, y

def convertCert_to_bytes(obj):
    """Converte o objeto para bytes."""
    if isinstance(obj, Certificate):
        return obj.public_bytes(serialization.Encoding.PEM)
    else:
        return obj

def convert_to_certificate(cert_bytes):
    """Converte bytes de certificado em um objeto Certificate."""
    return x509.load_pem_x509_certificate(cert_bytes)

def get_UID(user_cert: x509.Certificate):
    pseudonym_value = None
    for attribute in user_cert.subject:
        if attribute.oid._name == "pseudonym":
            pseudonym_value = attribute.value
            break
    if pseudonym_value is not None:
        return pseudonym_value
    else:
        return None


def cert_load(fname):
    """lê certificado de ficheiro"""
    with open(fname, "rb") as fcert:
        cert = x509.load_pem_x509_certificate(fcert.read())
    return cert


def cert_validtime(cert, now=None):
    """valida que 'now' se encontra no período
    de validade do certificado."""
    if now is None:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
    if now < cert.not_valid_before_utc or now > cert.not_valid_after_utc:
        raise x509.verification.VerificationError(
            "Certificate is not valid at this time"
        )

def cert_validsignature(cert,signature):
    """verifica a assinatura do certificado"""
    if not cert.is_signature_valid(signature):
        raise x509.verification.VerificationError(
            "Certificate signature is invalid")


def cert_validsubject(cert, attrs=[]):
    """verifica atributos do campo 'subject'. 'attrs'
    é uma lista de pares '(attr,value)' que condiciona
    os valores de 'attr' a 'value'."""
    print(cert.subject)
    for attr in attrs:
        if cert.subject.get_attributes_for_oid(attr[0])[0].value != attr[1]:
            raise x509.verification.VerificationError(
                "Certificate subject does not match expected value"
            )


def cert_validexts(cert, policy=[]):
    """valida extensões do certificado.
    'policy' é uma lista de pares '(ext,pred)' onde 'ext' é o OID de uma extensão e 'pred'
    o predicado responsável por verificar o conteúdo dessa extensão."""
    for check in policy:
        ext = cert.extensions.get_extension_for_oid(check[0]).value
        if not check[1](ext):
            raise x509.verification.VerificationError(
                "Certificate extensions does not match expected value"
            )


def valida_cert(ca_cert, cert, signature=None,nome=None):
    try:
        # obs: pressupõe que a cadeia de certifica só contém 2 níveis
        cert.verify_directly_issued_by(ca_cert)
        #print("Certificado foi assinado pela CA!")
        # verificar período de validade...
        cert_validtime(cert)
        #print("Certificado está no período de validade!")
        # verificar identidade... (e.g.)
        if nome is not None:
            cert_validsubject(cert, [(x509.NameOID.COMMON_NAME, nome)])
            #print("Certificado tem o nome correto!")
        #verificar aplicabilidade... (e.g.)
        if signature is not None:
            cert_validsignature(cert,signature)
        
       
       # verificar aplicabilidade... (e.g.)
        '''
        cert_validexts(
             cert,
             [
                 (
                     x509.ExtensionOID.EXTENDED_KEY_USAGE,
                     lambda e: x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH in e,
                 )
             ],
        )
        '''
        print("Certificate is valid!\n")
        return True
    except:
        print("Certificate is invalid!\n")
        return False