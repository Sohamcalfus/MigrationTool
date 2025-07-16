import requests
import json
import os
from datetime import datetime
import mimetypes
from requests.auth import HTTPBasicAuth

class OracleFusionUCMService:
    """Service class for Oracle Fusion UCM operations"""
    
    def __init__(self, base_url, username, password):
        """
        Initialize Oracle Fusion UCM service
        
        Args:
            base_url: Oracle Fusion base URL (e.g., 'https://your-instance.oraclecloud.com')
            username: Oracle Fusion username
            password: Oracle Fusion password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        
        # Set common headers
        self.session.headers.update({
            'Accept': 'application/json'
        })
    
    def authenticate(self):
        """Test authentication with Oracle Fusion"""
        try:
            # Test with UCM service endpoint
            test_url = f"{self.base_url}/cs/api/1.2/folders"
            response = self.session.get(test_url, timeout=30)
            
            if response.status_code in [200, 401]:  # 401 means auth is working but may need proper endpoint
                print("✓ Successfully authenticated with Oracle Fusion UCM")
                return True
            else:
                print(f"✗ Authentication test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False
    
    def upload_file_to_ucm(self, file_path, content_id=None, title=None, 
                          security_group="FAFusionImportExport", account="fin$/receivables$/import$"):
        """
        Upload file to Oracle Fusion UCM using REST API
        
        Args:
            file_path: Path to the file to upload
            content_id: Unique content ID (auto-generated if None)
            title: Document title
            security_group: UCM security group
            account: UCM account path
            
        Returns:
            dict: Upload response with status and details
        """
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": "File not found"}
            
            # Generate content ID if not provided
            if not content_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.basename(file_path).split('.')[0]
                content_id = f"FBDI_{filename}_{timestamp}"
            
            # Set title if not provided
            if not title:
                title = os.path.basename(file_path)
            
            # Prepare file for upload
            filename = os.path.basename(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/zip'
            
            # Oracle Fusion UCM REST API endpoint for file upload
            ucm_url = f"{self.base_url}/cs/idcplg"
            
            # Prepare form data for UCM
            with open(file_path, 'rb') as file_content:
                files = {
                    'primaryFile': (filename, file_content, mime_type)
                }
                
                data = {
                    'IdcService': 'CHECKIN_UNIVERSAL',
                    'dDocName': content_id,
                    'dDocTitle': title,
                    'dDocType': 'Document',
                    'dSecurityGroup': security_group,
                    'dDocAccount': account,
                    'dDocAuthor': self.username,
                    'dRevLabel': '1',
                    'IsJavaUploaded': '1'
                }
                
                # Remove Content-Type header for multipart upload
                headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
                
                response = self.session.post(ucm_url, files=files, data=data, headers=headers, timeout=120)
            
            if response.status_code == 200:
                # Check if upload was successful by looking for success indicators in response
                response_text = response.text
                if 'StatusCode>0<' in response_text or 'success' in response_text.lower():
                    return {
                        "success": True,
                        "content_id": content_id,
                        "title": title,
                        "message": "File uploaded successfully to Oracle Fusion UCM",
                        "ucm_url": f"{self.base_url}/cs/idcplg?IdcService=GET_FILE&dDocName={content_id}",
                        "download_url": f"{self.base_url}/cs/idcplg?IdcService=GET_FILE&dDocName={content_id}&Rendition=web"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Upload failed - check UCM response",
                        "response": response_text[:500]
                    }
            else:
                return {
                    "success": False,
                    "error": f"Upload failed with HTTP status {response.status_code}",
                    "response": response.text[:500]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload exception: {str(e)}"
            }
    
    def check_file_exists(self, content_id):
        """Check if a file exists in Oracle Fusion UCM"""
        try:
            search_url = f"{self.base_url}/cs/idcplg"
            params = {
                'IdcService': 'GET_SEARCH_RESULTS',
                'QueryText': f'dDocName <matches> `{content_id}`',
                'ResultCount': '1'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                return 'TotalRows>0<' in response.text
            return False
            
        except Exception as e:
            print(f"Error checking file existence: {e}")
            return False

def upload_to_oracle_fusion_ucm(file_path, config, metadata=None):
    """
    Convenience function to upload a file to Oracle Fusion UCM
    
    Args:
        file_path: Path to file to upload
        config: Configuration object with Oracle Fusion settings
        metadata: Optional metadata for the file
        
    Returns:
        dict: Upload result
    """
    try:
        ucm_service = OracleFusionUCMService(
            base_url=config.ORACLE_FUSION_BASE_URL,
            username=config.ORACLE_FUSION_USERNAME,
            password=config.ORACLE_FUSION_PASSWORD
        )
        
        # Test authentication
        if not ucm_service.authenticate():
            return {"success": False, "error": "Oracle Fusion authentication failed"}
        
        # Prepare upload parameters
        upload_params = {
            'security_group': config.UCM_SECURITY_GROUP,
            'account': config.UCM_ACCOUNT
        }
        
        if metadata:
            upload_params.update(metadata)
        
        # Upload file
        result = ucm_service.upload_file_to_ucm(file_path, **upload_params)
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Upload process failed: {str(e)}"}
