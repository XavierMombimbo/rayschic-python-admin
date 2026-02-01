import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ========== CONFIGURATION CLOUDINARY ==========
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dvjgsq4zl'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '514262723866384'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', '9BIyeJyzZHYPDaH26lFxwYDb5dc'),
    secure=True
)

# Configuration
COLLECTIONS = ['hero', 'costumes', 'chemises', 'pantalons', 'vestes', 'tenues', 'accessoires']

# Titres des collections
COLLECTION_TITLES = {
    'hero': 'Image Principale',
    'costumes': 'Costumes sur Mesure',
    'chemises': 'Chemises sur Mesure',
    'pantalons': 'Pantalons sur Mesure',
    'vestes': 'Vestes & Blazers',
    'tenues': 'Tenues Spécifiques',
    'accessoires': 'Accessoires Masculins'
}

# ========== CRÉER UN COMPTE CLOUDINARY GRATUIT ==========
"""
ÉTAPES POUR CLOUDINARY (GRATUIT) :
1. Allez sur https://cloudinary.com
2. Créez un compte gratuit
3. Dans le Dashboard, notez :
   - Cloud Name
   - API Key
   - API Secret
4. Sur Render, ajoutez ces variables d'environnement
"""

# ========== FONCTIONS CLOUDINARY ==========

def upload_to_cloudinary(file, collection, public_id=None):
    """Upload une image vers Cloudinary"""
    try:
        # Déterminer le public_id
        if not public_id:
            name = secure_filename(file.filename)
            public_id = f"rayschic/{collection}/{os.path.splitext(name)[0]}"
        
        # Upload vers Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder=f"rayschic/{collection}",
            public_id=public_id,
            overwrite=True,
            resource_type="auto"
        )
        
        return {
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'filename': file.filename,
            'size': result.get('bytes', 0),
            'format': result.get('format', ''),
            'dimensions': f"{result.get('width', 0)}x{result.get('height', 0)}"
        }
    except Exception as e:
        print(f"Erreur Cloudinary upload: {e}")
        return {'success': False, 'error': str(e)}

def delete_from_cloudinary(public_id):
    """Supprime une image de Cloudinary"""
    try:
        result = cloudinary.uploader.destroy(public_id)
        return {'success': True, 'result': result}
    except Exception as e:
        print(f"Erreur Cloudinary delete: {e}")
        return {'success': False, 'error': str(e)}

def list_cloudinary_images():
    """Liste toutes les images de Cloudinary"""
    collections_data = {}
    total_images = 0
    
    for collection in COLLECTIONS:
        try:
            # Rechercher les images dans le dossier
            result = cloudinary.api.resources(
                type="upload",
                prefix=f"rayschic/{collection}/",
                max_results=100
            )
            
            images = []
            for resource in result.get('resources', []):
                images.append({
                    'filename': os.path.basename(resource['public_id']),
                    'url': resource['secure_url'],
                    'size': resource.get('bytes', 0),
                    'public_id': resource['public_id'],
                    'dimensions': f"{resource.get('width', 0)}x{resource.get('height', 0)}",
                    'format': resource.get('format', ''),
                    'uploaded_at': resource.get('created_at', '')
                })
            
            collections_data[collection] = {
                'title': COLLECTION_TITLES.get(collection, collection),
                'images': images,
                'count': len(images)
            }
            total_images += len(images)
            
        except Exception as e:
            print(f"Erreur listing {collection}: {e}")
            collections_data[collection] = {
                'title': COLLECTION_TITLES.get(collection, collection),
                'images': [],
                'count': 0
            }
    
    return {
        'collections': collections_data,
        'stats': {
            'total_images': total_images,
            'collections_count': len(collections_data),
            'last_updated': datetime.now().isoformat()
        }
    }

# ========== ROUTES API ==========

@app.route('/api/scan', methods=['GET'])
def api_scan():
    """API: Scanner toutes les images depuis Cloudinary"""
    try:
        data = list_cloudinary_images()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API: Uploader une image vers Cloudinary"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        if 'collection' not in request.form:
            return jsonify({'error': 'Collection non spécifiée'}), 400
        
        file = request.files['file']
        collection = request.form['collection']
        
        if collection not in COLLECTIONS:
            return jsonify({'error': f'Collection invalide: {collection}'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Upload vers Cloudinary
        result = upload_to_cloudinary(file, collection)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Image uploadée avec succès',
                'image': {
                    'filename': result['filename'],
                    'url': result['url'],
                    'size': result['size'],
                    'collection': collection,
                    'public_id': result['public_id']
                }
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def api_delete():
    """API: Supprimer une image de Cloudinary"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        collection = data.get('collection')
        filename = data.get('filename')
        
        if not collection or not filename:
            return jsonify({'error': 'Collection et nom de fichier requis'}), 400
        
        # Construire le public_id
        name = secure_filename(filename)
        public_id = f"rayschic/{collection}/{os.path.splitext(name)[0]}"
        
        # Supprimer de Cloudinary
        result = delete_from_cloudinary(public_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Image supprimée avec succès'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-json', methods=['GET'])
def api_generate_json():
    """API: Générer le JSON pour GitHub"""
    try:
        data = list_cloudinary_images()
        
        # Formater pour GitHub
        github_data = {
            'last_updated': datetime.now().isoformat(),
            'hero': {
                'url': data['collections']['hero']['images'][0]['url'] if data['collections']['hero']['images'] else ''
            },
            'collections': {}
        }
        
        for key, collection in data['collections'].items():
            if key == 'hero':
                continue
            
            github_data['collections'][key] = {
                'title': collection['title'],
                'images': collection['images'],
                'count': collection['count']
            }
        
        # Téléchargement
        response = jsonify(github_data)
        response.headers.add('Content-Disposition', 'attachment; filename=rayschic-images.json')
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """API: Vérifier la santé"""
    return jsonify({
        'status': 'online',
        'storage': 'cloudinary',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/test-cloudinary', methods=['GET'])
def test_cloudinary():
    """Tester la connexion Cloudinary"""
    try:
        # Tester avec une requête simple
        result = cloudinary.api.ping()
        return jsonify({
            'success': True,
            'cloudinary': 'connected',
            'response': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'cloudinary': 'disconnected',
            'error': str(e)
        }), 500

@app.route('/')
def index():
    return jsonify({
        'name': 'Rayschic Cloudinary API',
        'version': '2.0.0',
        'storage': 'Cloudinary (Permanent)',
        'endpoints': {
            '/api/scan': 'GET - Scanner images Cloudinary',
            '/api/upload': 'POST - Uploader vers Cloudinary',
            '/api/delete': 'POST - Supprimer de Cloudinary',
            '/api/generate-json': 'GET - Générer JSON GitHub',
            '/api/test-cloudinary': 'GET - Tester Cloudinary'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
