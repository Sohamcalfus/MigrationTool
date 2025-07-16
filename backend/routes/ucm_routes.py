from flask import Blueprint, request, jsonify, current_app
import tempfile
import os
from datetime import datetime
from services.fbdi_generator import FBDIGeneratorService
from services.oracle_ucm_service import upload_to_oracle_fusion_ucm
from utils.file_processor import FileProcessor

ucm_bp = Blueprint('ucm', __name__)

@ucm_bp.route('/generate-and-upload-fbdi', methods=['POST'])
def generate_and_upload_fbdi():
    """Generate FBDI and upload to Oracle Fusion UCM"""
    try:
        raw_file = request.files.get('raw_file')
        fbdi_type = request.form.get('fbdi_type')
        project_name = request.form.get('project_name')
        env_type = request.form.get('env_type')
        upload_to_ucm_flag = request.form.get('upload_to_ucm', 'false').lower() == 'true'

        print(f"✓ Generating FBDI for: {fbdi_type}, Project={project_name}, Env={env_type}")
        
        if not raw_file or not fbdi_type:
            return jsonify({"error": "Missing raw file or FBDI type"}), 400

        # Generate FBDI
        generator_service = FBDIGeneratorService(current_app.config)
        result = generator_service.generate_fbdi(raw_file, fbdi_type, project_name, env_type)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500

        ucm_result = None
        
        # Upload to UCM if requested
        if upload_to_ucm_flag:
            try:
                metadata = {
                    'title': f"{project_name} - {fbdi_type} FBDI Package",
                    'content_id': f"FBDI_{project_name}_{fbdi_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
                
                print("✓ Uploading to Oracle Fusion UCM...")
                ucm_result = upload_to_oracle_fusion_ucm(
                    result["zip_path"], 
                    current_app.config, 
                    metadata
                )
                
                if ucm_result['success']:
                    print(f"✓ Successfully uploaded to UCM: {ucm_result['content_id']}")
                else:
                    print(f"✗ UCM upload failed: {ucm_result['error']}")
                    
            except Exception as e:
                print(f"✗ UCM upload error: {e}")
                ucm_result = {"success": False, "error": str(e)}
        
        # Cleanup temp files
        FileProcessor.cleanup_temp_files(*result["temp_files"])
        
        # Return response
        response_data = {
            "status": "success",
            "filename": result["filename"],
            "metadata": result["metadata"],
            "ucm_upload": ucm_result
        }
        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ucm_bp.route('/upload-to-ucm', methods=['POST'])
def upload_file_to_ucm_endpoint():
    """Standalone endpoint to upload any file to Oracle Fusion UCM"""
    try:
        uploaded_file = request.files.get('file')
        title = request.form.get('title')
        content_id = request.form.get('content_id')
        
        if not uploaded_file:
            return jsonify({"error": "No file provided"}), 400
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.filename}") as tmp_file:
            uploaded_file.save(tmp_file.name)
            
            # Prepare metadata
            metadata = {
                'title': title or uploaded_file.filename,
                'content_id': content_id
            }
            
            # Upload to UCM
            result = upload_to_oracle_fusion_ucm(tmp_file.name, current_app.config, metadata)
            
            # Cleanup
            os.remove(tmp_file.name)
            
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
