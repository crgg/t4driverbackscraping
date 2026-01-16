from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from t4alerts_backend.common.decorators import permission_required
from ssl_checker.checker import SSLChecker
from t4alerts_backend.certificates.models import SSLCertificate
from t4alerts_backend.common.database import db
import logging

certificates_bp = Blueprint('certificates', __name__)
logger = logging.getLogger(__name__)

@certificates_bp.route('/status', methods=['GET'])
@jwt_required()
@permission_required('view_certificates')
def get_certificates_status():
    """
    Returns the SSL status for all configured domains (static + dynamic).
    """
    try:
        checker = SSLChecker()
        
        # 1. Get Static Domains from Config
        static_domains = checker.get_domains()
        
        # 2. Get Dynamic Domains from DB
        dynamic_certs = SSLCertificate.query.all()
        dynamic_domains = [cert.hostname for cert in dynamic_certs]
        
        # 3. Merge lists (unique)
        all_domains = list(set(static_domains + dynamic_domains))
        
        results = []
        for domain in all_domains:
            # We use the new check_domain method that returns a dict
            status = checker.check_domain(domain)
            results.append(status)
            
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error fetching certificates status: {e}")
        return jsonify({"error": "Failed to fetch certificates status"}), 500

@certificates_bp.route('/check', methods=['POST'])
@jwt_required()
def check_certificate():
    """
    Checks SSL status for a specific domain on demand.
    """
    try:
        data = request.get_json()
        hostname = data.get('hostname')
        
        if not hostname:
            return jsonify({"error": "Hostname is required"}), 400
            
        checker = SSLChecker()
        # Clean domain just in case user pastes full URL
        hostname = checker.clean_domain(hostname)
        
        result = checker.check_domain(hostname)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error checking certificate for {hostname}: {e}")
        return jsonify({"error": str(e)}), 500

@certificates_bp.route('/add', methods=['POST'])
@jwt_required()
def add_certificate():
    """
    Saves a domain to be monitored dynamically.
    """
    try:
        data = request.get_json()
        hostname = data.get('hostname')
        port = data.get('port', 443)
        
        if not hostname:
            return jsonify({"error": "Hostname is required"}), 400

        # Clean domain
        checker = SSLChecker()
        hostname = checker.clean_domain(hostname)

        # Check if already exists
        if SSLCertificate.query.filter_by(hostname=hostname).first():
            return jsonify({"message": "Certificate already monitored"}), 200
            
        new_cert = SSLCertificate(hostname=hostname, port=port)
        db.session.add(new_cert)
        db.session.commit()
        
        return jsonify({"message": "Certificate added successfully", "certificate": new_cert.to_dict()}), 201
    except Exception as e:
        logger.error(f"Error adding certificate {hostname}: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to add certificate"}), 500
