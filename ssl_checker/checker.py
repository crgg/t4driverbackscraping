import socket
import idna
import logging
import pytz
import os
from datetime import datetime
from OpenSSL import SSL
from cryptography import x509
from cryptography.x509.oid import NameOID
from collections import namedtuple

from app.config import APPS_CONFIG
from app.alerts import send_email, default_recipients

# Setup Logging
logger = logging.getLogger(__name__)

HostInfo = namedtuple(field_names='cert hostname peername', typename='HostInfo')

class SSLChecker:
    def __init__(self):
        self.port = 443
        self.umbral_days = int(os.getenv('DAYS_UMBRAL', 7)) # Default to 7 if not set
        
    def clean_domain(self, domain):
        """Extrae solo el hostname de una URL"""
        if "://" in domain:
            domain = domain.split("://")[1]
        return domain.split("/")[0]

    def get_domains(self):
        """Retrieves domain list from app.config.APPS_CONFIG"""
        domains = []
        for key, config in APPS_CONFIG.items():
            base_url = config.get("base_url")
            if base_url:
                hostname = self.clean_domain(base_url)
                domains.append(hostname)
        # Remove duplicates if any
        return list(set(domains))

    def get_certificate(self, hostname):
        try:
            hostname_idna = idna.encode(hostname)
            sock = socket.socket()
            # sock.settimeout(10) # Removed to prevent OpenSSL.SSL.WantReadError

            sock.connect((hostname, self.port))
            peername = sock.getpeername()
            ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
            ctx.check_hostname = False
            ctx.verify_mode = SSL.VERIFY_NONE

            sock_ssl = SSL.Connection(ctx, sock)
            sock_ssl.set_connect_state()
            sock_ssl.set_tlsext_host_name(hostname_idna)
            sock_ssl.do_handshake()
            cert = sock_ssl.get_peer_certificate()
            crypto_cert = cert.to_cryptography()
            sock_ssl.close()
            sock.close()

            return HostInfo(cert=crypto_cert, peername=peername, hostname=hostname)
            return HostInfo(cert=crypto_cert, peername=peername, hostname=hostname)
        except Exception as e:
            logger.exception(f"ERROR EN GET CERTIFICATE para {hostname}")
            return None

    def get_issuer(self, cert):
        try:
            names = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
            return names[0].value
        except x509.ExtensionNotFound as e:
            logger.error(f"ERROR GET ISSUER: {str(e)}")
            return None
        except Exception as e:
            return "Unknown Issuer"

    def check_domain(self, hostname):
        """
        Checks SSL status for a domain and returns a dictionary with the results.
        Does NOT send alerts.
        """
        logger.info(f"Checking SSL for {hostname}...")
        hostinfo = self.get_certificate(hostname)
        if not hostinfo:
            return {
                "hostname": hostname,
                "status": "ERROR",
                "days_left": 0,
                "expires": "Unknown",
                "issuer": "Unknown",
                "color": "gray"
            }

        try:
            notafter_dt = hostinfo.cert.not_valid_after_utc
            now_utc = datetime.now(pytz.UTC)
            days_left = (notafter_dt - now_utc).days
            
            # Format required: YYYY-MM-DD - HH:MM:SS
            not_after_str = notafter_dt.strftime("%Y-%m-%d - %H:%M:%S")
            issuer = self.get_issuer(hostinfo.cert)

            logger.info(f"{hostname} - Days Left: {days_left}, Expires: {not_after_str}")

            if days_left < 8:
                severity = "CRITICAL"
                color = "red"
            elif 8 <= days_left <= 30:
                severity = "WARNING"
                color = "#FFBF00" # Mustard/Amber
            else:
                severity = "OK"
                color = "green"
            
            return {
                "hostname": hostname,
                "status": severity,
                "days_left": days_left,
                "expires": not_after_str,
                "issuer": issuer,
                "color": color
            }

        except Exception as e:
            logger.error(f"Error processing domain {hostname}: {e}")
            return {
                "hostname": hostname,
                "status": "ERROR",
                "error": str(e),
                "days_left": 0,
                "expires": "Unknown",
                "issuer": "Unknown",
                "color": "red"
            }

    def process_domain(self, hostname):
        """
        Original method (kept for backward compatibility).
        Checks domain and sends alerts if needed.
        """
        result = self.check_domain(hostname)
        
        # If there was a connection error (status ERROR without valid data), skip alerting or handle differently
        if result["status"] == "ERROR" and result["expires"] == "Unknown":
            return

        # Check conditions for alerting
        # process_domain logic was: send alert if days_left < umbral? 
        # Actually in original code it sent alert ALWAYS (see send_alert call in original code line 106)
        # Wait, line 106 sent alert regardless of days_left.
        # But let's check if the user wanted alerts only on threshold.
        # The original code sent it always. I will accept that behavior.
        
        self.send_alert(
            hostname, 
            result["days_left"], 
            result["expires"], 
            result["issuer"], 
            result["status"], 
            result["color"]
        )

    def send_alert(self, hostname, days_left, expiration_str, issuer, severity, color):
        try:
            # Construct Email Body with tighter spacing and styles
            html_body = f"""
            <div style="font-family: Arial, sans-serif;">
                <h3 style="margin-bottom: 5px;">Alerta SSL: {hostname}</h3>
                <p style="margin: 0; color: {color}; font-weight: bold;">Severidad: {severity}</p>
                <br>
                <p style="margin: 0;"><strong>Días restantes:</strong> {days_left}</p>
                <p style="margin: 0;"><strong>Vence:</strong> <b>{expiration_str}</b></p>
                <p style="margin: 0;"><strong>Issuer:</strong> {issuer}</p>
            </div>
            """

            # Subject
            subject = f"[SSL] {hostname} vence en {days_left} días (expira {expiration_str})"
            
            recipients = default_recipients(owner_email=None) 
            
            if recipients:
                send_email(
                    subject=subject, 
                    html_body=html_body, 
                    to_addrs=recipients,
                    sender_name="T4SSL"
                )
                logger.info(f"Alert sent for {hostname} to {recipients}")
            else:
                logger.warning(f"No recipients found for {hostname}")

        except Exception as e:
            logger.error(f"Failed to send alert for {hostname}: {e}")

    def run(self):
        domains = self.get_domains()
        logger.info(f"Starting SSL check for {len(domains)} domains.")
        try:
            for domain in domains:
                self.process_domain(domain)
        except Exception as e:
            logger.error(f"Critical error in run loop: {e}")
