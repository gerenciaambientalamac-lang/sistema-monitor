from pathlib import Path
import ipaddress, socket, datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT=Path(__file__).resolve().parent
TLS=ROOT/'tls'; TLS.mkdir(exist_ok=True)
name=socket.gethostname()
ips={'127.0.0.1'}
try:
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); ips.add(s.getsockname()[0]); s.close()
except Exception: pass
for info in socket.getaddrinfo(name,None,socket.AF_INET): ips.add(info[4][0])
key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,name)])
b=x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=5)).not_valid_after(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=30))
san=[x509.DNSName('localhost')]+[x509.IPAddress(ipaddress.ip_address(x)) for x in sorted(ips)]
b=b.add_extension(x509.SubjectAlternativeName(san),critical=False).sign(key,hashes.SHA256())
(TLS/'key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.TraditionalOpenSSL,serialization.NoEncryption()))
(TLS/'cert.pem').write_bytes(b.public_bytes(serialization.Encoding.PEM))
print('Certificado D06 creado en:',TLS)
print('SAN IP:',', '.join(sorted(ips)))
