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
        dynamic_domains_map = {cert.hostname: cert.id for cert in dynamic_certs}
        
        # 3. Merge lists (unique)
        all_domains = list(set(static_domains + list(dynamic_domains_map.keys())))
        
        results = []
        for domain in all_domains:
            # We use the new check_domain method that returns a dict
            status = checker.check_domain(domain)
            
            # Add certificate ID and is_dynamic flag
            is_dynamic = domain in dynamic_domains_map
            status['id'] = dynamic_domains_map.get(domain, None)
            status['is_dynamic'] = is_dynamic
            
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

@certificates_bp.route('/<int:cert_id>', methods=['DELETE'])
@jwt_required()
def delete_certificate(cert_id):
    """
    Deletes a certificate from the database by ID.
    Only dynamic certificates can be deleted.
    """
    try:
        cert = SSLCertificate.query.get(cert_id)
        
        if not cert:
            return jsonify({"error": "Certificate not found"}), 404
        
        hostname = cert.hostname
        db.session.delete(cert)
        db.session.commit()
        
        logger.info(f"Certificate deleted: {hostname} (ID: {cert_id})")
        return jsonify({"message": "Certificate deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting certificate {cert_id}: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete certificate"}), 500

@certificates_bp.route('/<int:cert_id>', methods=['PUT'])
@jwt_required()
def update_certificate(cert_id):
    """
    Updates a certificate's hostname.
    """
    try:
        cert = SSLCertificate.query.get(cert_id)
        
        if not cert:
            return jsonify({"error": "Certificate not found"}), 404
        
        data = request.get_json()
        new_hostname = data.get('hostname')
        
        if not new_hostname:
            return jsonify({"error": "Hostname is required"}), 400
        
        # Clean domain
        checker = SSLChecker()
        new_hostname = checker.clean_domain(new_hostname)
        
        # Check if new hostname already exists (excluding current certificate)
        existing = SSLCertificate.query.filter(
            SSLCertificate.hostname == new_hostname,
            SSLCertificate.id != cert_id
        ).first()
        
        if existing:
            return jsonify({"error": "A certificate with this hostname already exists"}), 409
        
        old_hostname = cert.hostname
        cert.hostname = new_hostname
        db.session.commit()
        
        logger.info(f"Certificate updated: {old_hostname} → {new_hostname} (ID: {cert_id})")
        return jsonify({
            "message": "Certificate updated successfully",
            "certificate": cert.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error updating certificate {cert_id}: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update certificate"}), 500
