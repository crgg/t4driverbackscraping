from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from t4alerts_backend.common.decorators import permission_required
from ssl_checker.checker import SSLChecker
import logging

certificates_bp = Blueprint('certificates', __name__)
logger = logging.getLogger(__name__)

@certificates_bp.route('/status', methods=['GET'])
@jwt_required()
@permission_required('view_certificates')
def get_certificates_status():
    """
    Returns the SSL status for all configured domains.
    """
    try:
        checker = SSLChecker()
        domains = checker.get_domains()
        results = []
        
        for domain in domains:
            # We use the new check_domain method that returns a dict
            status = checker.check_domain(domain)
            results.append(status)
            
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error fetching certificates status: {e}")
        return jsonify({"error": "Failed to fetch certificates status"}), 500
