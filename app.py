import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import hashlib

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Créer les dossiers s'ils n'existent pas
COLLECTIONS = ['hero', 'costumes', 'chemises', 'pantalons', 'vestes', 'tenues', 'accessoires']
for collection in COLLECTIONS:
    os.makedirs(os.path.join(UPLOAD_FOLDER, collection), exist_ok=True)

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def scan_uploads():
    """Scanner tous les dossiers d'upload"""
    collections = {}
    total_images = 0
    
    for collection in COLLECTIONS:
        collection_path = os.path.join(UPLOAD_FOLDER, collection)
        images = []
        
        if os.path.exists(collection_path):
            for filename in os.listdir(collection_path):
                if allowed_file(filename):
                    filepath = os.path.join(collection_path, filename)
                    if os.path.isfile(filepath):
                        try:
                            size = os.path.getsize(filepath)
                            images.append({
                                'filename': filename,
                                'url': f'/uploads/{collection}/{filename}',
                                'size': size,
                                'uploaded_at': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                            })
                        except:
                            continue
        
        collections[collection] = {
            'title': COLLECTION_TITLES.get(collection, collection),
            'images': images,
            'count': len(images)
        }
        total_images += len(images)
    
    return {
        'collections': collections,
        'stats': {
            'total_images': total_images,
            'collections_count': len(collections),
            'last_updated': datetime.now().isoformat()
        }
    }

@app.route('/api/scan', methods=['GET'])
def api_scan():
    """API: Scanner toutes les images"""
    try:
        data = scan_uploads()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API: Uploader une image"""
    try:
        # Vérifier si les champs sont présents
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        if 'collection' not in request.form:
            return jsonify({'error': 'Collection non spécifiée'}), 400
        
        file = request.files['file']
        collection = request.form['collection']
        
        # Vérifier la collection
        if collection not in COLLECTIONS:
            return jsonify({'error': f'Collection invalide. Options: {", ".join(COLLECTIONS)}'}), 400
        
        # Vérifier le fichier
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Type de fichier non autorisé. Types autorisés: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Sécuriser le nom de fichier
        original_filename = secure_filename(file.filename)
        filename = original_filename
        
        # Vérifier si le fichier existe déjà, ajouter un suffixe si nécessaire
        counter = 1
        name, ext = os.path.splitext(original_filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], collection)
        
        while os.path.exists(os.path.join(upload_path, filename)):
            filename = f"{name}_{counter}{ext}"
            counter += 1
        
        # Sauvegarder le fichier
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Obtenir les informations du fichier
        size = os.path.getsize(file_path)
        
        # Réponse
        image_data = {
            'filename': filename,
            'url': f'/uploads/{collection}/{filename}',
            'size': size,
            'uploaded_at': datetime.now().isoformat(),
            'collection': collection
        }
        
        return jsonify({
            'success': True,
            'message': 'Fichier uploadé avec succès',
            'image': image_data
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def api_delete():
    """API: Supprimer une image"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        collection = data.get('collection')
        filename = data.get('filename')
        
        if not collection or not filename:
            return jsonify({'error': 'Collection et nom de fichier requis'}), 400
        
        # Vérifier la collection
        if collection not in COLLECTIONS:
            return jsonify({'error': 'Collection invalide'}), 400
        
        # Sécuriser le nom de fichier
        safe_filename = secure_filename(filename)
        
        # Chemin du fichier
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], collection, safe_filename)
        
        # Vérifier si le fichier existe
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        # Supprimer le fichier
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'Fichier supprimé avec succès'
        })
        
    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-json', methods=['GET'])
def api_generate_json():
    """API: Générer le JSON pour GitHub"""
    try:
        data = scan_uploads()
        
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
        
        # Créer la réponse
        response = jsonify(github_data)
        response.headers.add('Content-Disposition', 'attachment; filename=images.json')
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """API: Vérifier la santé du serveur"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'collections': COLLECTIONS,
        'upload_folder': UPLOAD_FOLDER
    })

@app.route('/api/clear-cache', methods=['POST'])
def api_clear_cache():
    """API: Nettoyer le cache (placeholder)"""
    return jsonify({
        'success': True,
        'message': 'Cache nettoyé (fonctionnalité de placeholder)'
    })

@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    """API: Optimiser les images (placeholder)"""
    return jsonify({
        'success': True,
        'message': 'Optimisation (fonctionnalité de placeholder)',
        'optimized': 0
    })

# Servir les fichiers uploadés
@app.route('/uploads/<collection>/<filename>')
def serve_uploaded_file(collection, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, collection), filename)

# Route pour l'admin
@app.route('/admin')
def serve_admin():
    return send_from_directory('static', 'admin.html')

# Route racine
@app.route('/')
def index():
    return jsonify({
        'name': 'Rayschic Image Admin API',
        'version': '1.0.0',
        'endpoints': {
            '/api/scan': 'GET - Scanner les images',
            '/api/upload': 'POST - Uploader une image',
            '/api/delete': 'POST - Supprimer une image',
            '/api/generate-json': 'GET - Générer JSON pour GitHub',
            '/api/health': 'GET - Vérifier la santé du serveur'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
