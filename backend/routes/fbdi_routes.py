from flask import Blueprint, request, jsonify, send_file, current_app
import io
from services.fbdi_generator import FBDIGeneratorService
from services.preview_service import PreviewService
from utils.file_processor import FileProcessor

fbdi_bp = Blueprint('fbdi', __name__)

@fbdi_bp.route('/preview-mappings', methods=['POST'])
def preview_mappings():
    """Generate mapping preview for uploaded file"""
    try:
        raw_file = request.files.get('raw_file')
        fbdi_type = request.form.get('fbdi_type')

        if not raw_file or not fbdi_type:
            return jsonify({"error": "Missing raw file or FBDI type"}), 400

        preview_service = PreviewService(current_app.config)
        result = preview_service.generate_preview(raw_file, fbdi_type)
        
        if result["success"]:
            return jsonify({
                "status": "success", 
                "mappings": result["mappings"],
                "stats": result["stats"]
            })
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@fbdi_bp.route('/generate-fbdi-from-type', methods=['POST'])
def generate_fbdi_from_type():
    """Generate FBDI file from uploaded data"""
    try:
        raw_file = request.files.get('raw_file')
        fbdi_type = request.form.get('fbdi_type')
        project_name = request.form.get('project_name')
        env_type = request.form.get('env_type')

        print(f"✓ Generating FBDI for: {fbdi_type}, Project={project_name}, Env={env_type}")

        if not raw_file or not fbdi_type:
            return jsonify({"error": "Missing raw file or FBDI type"}), 400

        generator_service = FBDIGeneratorService(current_app.config)
        result = generator_service.generate_fbdi(raw_file, fbdi_type, project_name, env_type)
        
        if result["success"]:
            # Read ZIP file and return as download
            with open(result["zip_path"], 'rb') as zip_file:
                zip_buffer = io.BytesIO(zip_file.read())
            
            # Cleanup temp files
            FileProcessor.cleanup_temp_files(*result["temp_files"])
            
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=result["filename"]
            )
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
