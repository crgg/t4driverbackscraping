import socket
import ssl as ssl_lib
import idna
import logging
import pytz
import os
import select
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
        """
        Safely retrieves SSL certificate for a hostname.
        Returns None on any error to prevent worker crashes.
        Tries standard library ssl first (more reliable), falls back to OpenSSL if needed.
        """
        sock = None
        sock_ssl = None
        try:
            # Validate hostname
            if not hostname or not isinstance(hostname, str):
                logger.warning(f"Invalid hostname provided: {hostname}")
                return None
            
            # Try using Python's standard ssl library first (more reliable)
            try:
                return self._get_certificate_stdlib(hostname)
            except Exception as stdlib_error:
                logger.debug(f"Standard library SSL failed for {hostname}, trying OpenSSL: {stdlib_error}")
                # Fall back to OpenSSL method
                pass
                
            hostname_idna = idna.encode(hostname)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Use shorter timeout for initial connection (5 seconds)
            sock.settimeout(5)
            # Set socket options for better reliability
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sock.connect((hostname, self.port))
            peername = sock.getpeername()
            
            # Set longer timeout for SSL operations (10 seconds)
            sock.settimeout(10)
            
            ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
            ctx.check_hostname = False
            ctx.verify_mode = SSL.VERIFY_NONE
            
            # Allow legacy connections if needed (OpenSSL 3+)
            try:
                ctx.set_options(SSL.OP_LEGACY_SERVER_CONNECT)
            except AttributeError:
                pass

            sock_ssl = SSL.Connection(ctx, sock)
            sock_ssl.set_connect_state()
            sock_ssl.set_tlsext_host_name(hostname_idna)
            
            # Perform handshake - socket timeout will handle it
            # If handshake takes too long, socket timeout will raise
            sock_ssl.do_handshake()
            
            cert = sock_ssl.get_peer_certificate()
            crypto_cert = cert.to_cryptography()
            sock_ssl.close()
            sock.close()

            return HostInfo(cert=crypto_cert, peername=peername, hostname=hostname)
        except (socket.timeout, TimeoutError) as e:
            logger.warning(f"SSL Connection Timeout for {hostname} after 15s: {e}")
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except (socket.gaierror, socket.herror) as e:
            logger.warning(f"DNS Resolution Failed for {hostname}: {e}")
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except (ConnectionRefusedError, ConnectionResetError) as e:
            logger.warning(f"Connection Refused/Reset for {hostname}: {e}")
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except OSError as e:
            # Catch network unreachable, no route to host, etc.
            error_code = getattr(e, 'errno', None)
            if error_code in (101, 111, 113):  # Network unreachable, Connection refused, No route to host
                logger.warning(f"Network Error for {hostname} (errno {error_code}): {e}")
            else:
                logger.warning(f"OS Error for {hostname}: {e}")
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except SSL.SysCallError as e:
            logger.warning(f"SSL Connection Failed for {hostname}: Server rejected connection (ECONNRESET/SysCallError): {e}")
            if sock_ssl:
                try:
                    sock_ssl.close()
                except:
                    pass
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except SSL.WantReadError:
            logger.warning(f"SSL Connection Timeout for {hostname} (WantReadError).")
            if sock_ssl:
                try:
                    sock_ssl.close()
                except:
                    pass
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except KeyboardInterrupt:
            # Don't catch keyboard interrupts, let them propagate
            raise
        except SystemExit:
            # Don't catch system exits, let them propagate
            raise
        except BaseException as e:
            # Catch all other exceptions including SystemExit-like errors
            logger.exception(f"ERROR EN GET CERTIFICATE para {hostname}: {type(e).__name__}: {e}")
            if sock_ssl:
                try:
                    sock_ssl.close()
                except:
                    pass
            if sock:
                try:
                    sock.close()
                except:
                    pass
            # Always return None instead of raising - this prevents worker crashes
            return None
    
    def _get_certificate_stdlib(self, hostname):
        """
        Alternative method using Python's standard ssl library.
        More reliable for network issues.
        """
        sock = None
        try:
            # Create socket with timeout
            sock = socket.create_connection((hostname, self.port), timeout=8)
            peername = sock.getpeername()
            
            # Wrap with SSL context
            context = ssl_lib.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl_lib.CERT_NONE
            
            # Create SSL socket
            ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
            
            # Get certificate
            cert_der = ssl_sock.getpeercert(binary_form=True)
            crypto_cert = x509.load_der_x509_certificate(cert_der)
            
            ssl_sock.close()
            
            return HostInfo(cert=crypto_cert, peername=peername, hostname=hostname)
        except Exception as e:
            if sock:
                try:
                    sock.close()
                except:
                    pass
            raise  # Re-raise to trigger fallback to OpenSSL method
            logger.warning(f"SSL Connection Timeout for {hostname} after 15s: {e}")
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except (socket.gaierror, socket.herror) as e:
            logger.warning(f"DNS Resolution Failed for {hostname}: {e}")
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except (ConnectionRefusedError, ConnectionResetError) as e:
            logger.warning(f"Connection Refused/Reset for {hostname}: {e}")
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except OSError as e:
            # Catch network unreachable, no route to host, etc.
            error_code = getattr(e, 'errno', None)
            if error_code in (101, 111, 113):  # Network unreachable, Connection refused, No route to host
                logger.warning(f"Network Error for {hostname} (errno {error_code}): {e}")
            else:
                logger.warning(f"OS Error for {hostname}: {e}")
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except SSL.SysCallError as e:
            logger.warning(f"SSL Connection Failed for {hostname}: Server rejected connection (ECONNRESET/SysCallError): {e}")
            if sock_ssl:
                try:
                    sock_ssl.close()
                except:
                    pass
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except SSL.WantReadError:
            logger.warning(f"SSL Connection Timeout for {hostname} (WantReadError).")
            if sock_ssl:
                try:
                    sock_ssl.close()
                except:
                    pass
            if sock:
                try:
                    sock.close()
                except:
                    pass
            return None
        except KeyboardInterrupt:
            # Don't catch keyboard interrupts, let them propagate
            raise
        except SystemExit:
            # Don't catch system exits, let them propagate
            raise
        except BaseException as e:
            # Catch all other exceptions including SystemExit-like errors
            logger.exception(f"ERROR EN GET CERTIFICATE para {hostname}: {type(e).__name__}: {e}")
            if sock_ssl:
                try:
                    sock_ssl.close()
                except:
                    pass
            if sock:
                try:
                    sock.close()
                except:
                    pass
            # Always return None instead of raising - this prevents worker crashes
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
        try:
            hostinfo = self.get_certificate(hostname)
        except Exception as e:
            logger.error(f"Unexpected error in check_domain for {hostname}: {type(e).__name__}: {e}")
            return {
                "hostname": hostname,
                "status": "ERROR",
                "days_left": 0,
                "expires": "Unknown",
                "issuer": "Unknown",
                "color": "gray",
                "error": f"Connection failed: {str(e)}"
            }
        
        if not hostinfo:
            return {
                "hostname": hostname,
                "status": "ERROR",
                "days_left": 0,
                "expires": "Unknown",
                "issuer": "Unknown",
                "color": "gray",
                "error": "Unable to connect to host or retrieve certificate"
            }

        try:
            notafter_dt = hostinfo.cert.not_valid_after_utc
            now_utc = datetime.now(pytz.UTC)
            days_left = (notafter_dt - now_utc).days
            
            # Format required: YYYY-MM-DD - HH:MM:SS
            not_after_str = notafter_dt.strftime("%Y-%m-%d - %H:%M:%S")
            issuer = self.get_issuer(hostinfo.cert)

            logger.info(f"{hostname} - Days Left: {days_left}, Expires: {not_after_str}")

            if days_left <= 3:
                severity = "CRITICAL"
                color = "red"
            elif days_left < 8:
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

        # Solo enviar alerta si quedan <= 3 días
        if result["days_left"] <= 3:
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
