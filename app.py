import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ========== CONFIGURATION CLOUDINARY AVEC SECOURS ==========

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

# Dossier de secours local
UPLOAD_FOLDER = 'temp_uploads'

# Configuration Cloudinary
def configure_cloudinary():
    """Configurer Cloudinary avec valeurs d'environnement ou secours"""
    # Essayer les noms de variables les plus courants
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or os.environ.get('CLOUDINARY_CLOUD')
    api_key = os.environ.get('CLOUDINARY_API_KEY') or os.environ.get('CLOUDINARY_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET') or os.environ.get('CLOUDINARY_SECRET')
    
    # Log pour débogage
    print(f"DEBUG: cloud_name exists = {bool(cloud_name)}")
    print(f"DEBUG: api_key exists = {bool(api_key)}")
    print(f"DEBUG: api_secret exists = {bool(api_secret)}")
    
    if cloud_name and api_key and api_secret:
        try:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
            print("✅ Cloudinary configuré avec succès")
            return True
        except Exception as e:
            print(f"⚠️ Erreur configuration Cloudinary: {e}")
            return False
    else:
        print("⚠️ Variables Cloudinary non trouvées. Utilisation du stockage local.")
        return False

# Initialiser Cloudinary
CLOUDINARY_ENABLED = configure_cloudinary()

# Créer le dossier local de secours
for collection in COLLECTIONS:
    os.makedirs(os.path.join(UPLOAD_FOLDER, collection), exist_ok=True)

# ========== FONCTIONS DE GESTION DES IMAGES ==========

def upload_image(file, collection, public_id=None):
    """Upload une image (Cloudinary ou local selon configuration)"""
    try:
        if CLOUDINARY_ENABLED:
            # Utiliser Cloudinary
            if not public_id:
                name = secure_filename(file.filename)
                public_id = f"rayschic/{collection}/{os.path.splitext(name)[0]}"
            
            result = cloudinary.uploader.upload(
                file,
                folder=f"rayschic/{collection}",
                public_id=public_id,
                overwrite=True,
                resource_type="auto"
            )
            
            return {
                'success': True,
                'storage': 'cloudinary',
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'filename': file.filename,
                'size': result.get('bytes', 0),
                'dimensions': f"{result.get('width', 0)}x{result.get('height', 0)}"
            }
        else:
            # Utiliser stockage local
            name = secure_filename(file.filename)
            upload_path = os.path.join(UPLOAD_FOLDER, collection)
            os.makedirs(upload_path, exist_ok=True)
            
            # Éviter les doublons
            filename = name
            counter = 1
            base_name, ext = os.path.splitext(name)
            
            while os.path.exists(os.path.join(upload_path, filename)):
                filename = f"{base_name}_{counter}{ext}"
                counter += 1
            
            # Sauvegarder le fichier
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            # Obtenir la taille
            size = os.path.getsize(file_path)
            
            # Pour le local, nous servons les fichiers via une route
            return {
                'success': True,
                'storage': 'local',
                'url': f'/temp_uploads/{collection}/{filename}',
                'filename': filename,
                'size': size,
                'collection': collection,
                'public_id': None
            }
            
    except Exception as e:
        print(f"Erreur upload: {e}")
        return {'success': False, 'error': str(e)}

def delete_image(collection, filename):
    """Supprimer une image"""
    try:
        if CLOUDINARY_ENABLED:
            # Supprimer de Cloudinary
            name = secure_filename(filename)
            name_without_ext = os.path.splitext(name)[0]
            public_id = f"rayschic/{collection}/{name_without_ext}"
            
            result = cloudinary.uploader.destroy(public_id)
            return {'success': True, 'storage': 'cloudinary'}
        else:
            # Supprimer du local
            safe_filename = secure_filename(filename)
            file_path = os.path.join(UPLOAD_FOLDER, collection, safe_filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return {'success': True, 'storage': 'local'}
            else:
                return {'success': False, 'error': 'Fichier non trouvé'}
                
    except Exception as e:
        print(f"Erreur delete: {e}")
        return {'success': False, 'error': str(e)}

def list_images():
    """Lister toutes les images"""
    collections_data = {}
    total_images = 0
    
    if CLOUDINARY_ENABLED:
        # Lister depuis Cloudinary
        for collection in COLLECTIONS:
            try:
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
                        'uploaded_at': resource.get('created_at', '')
                    })
                
                collections_data[collection] = {
                    'title': COLLECTION_TITLES.get(collection, collection),
                    'images': images,
                    'count': len(images),
                    'storage': 'cloudinary'
                }
                total_images += len(images)
                
            except Exception as e:
                print(f"Erreur listing {collection}: {e}")
                collections_data[collection] = {
                    'title': COLLECTION_TITLES.get(collection, collection),
                    'images': [],
                    'count': 0,
                    'storage': 'error'
                }
    else:
        # Lister depuis le local
        for collection in COLLECTIONS:
            collection_path = os.path.join(UPLOAD_FOLDER, collection)
            images = []
            
            if os.path.exists(collection_path):
                for filename in os.listdir(collection_path):
                    filepath = os.path.join(collection_path, filename)
                    if os.path.isfile(filepath):
                        try:
                            size = os.path.getsize(filepath)
                            images.append({
                                'filename': filename,
                                'url': f'/temp_uploads/{collection}/{filename}',
                                'size': size,
                                'public_id': None,
                                'uploaded_at': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                            })
                        except:
                            continue
            
            collections_data[collection] = {
                'title': COLLECTION_TITLES.get(collection, collection),
                'images': images,
                'count': len(images),
                'storage': 'local'
            }
            total_images += len(images)
    
    return {
        'collections': collections_data,
        'stats': {
            'total_images': total_images,
            'collections_count': len(collections_data),
            'storage': 'cloudinary' if CLOUDINARY_ENABLED else 'local',
            'last_updated': datetime.now().isoformat()
        }
    }

# ========== ROUTES API ==========

@app.route('/api/scan', methods=['GET'])
def api_scan():
    """API: Scanner toutes les images"""
    try:
        data = list_images()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API: Uploader une image"""
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
        
        # Vérifier la taille (max 10MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            return jsonify({'error': 'Fichier trop volumineux (max 10MB)'}), 400
        
        # Vérifier l'extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' in file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                return jsonify({'error': 'Type de fichier non autorisé. Utilisez: PNG, JPG, JPEG, GIF, WebP'}), 400
        
        # Upload l'image
        result = upload_image(file, collection)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Image uploadée avec succès',
                'storage': result['storage'],
                'image': {
                    'filename': result['filename'],
                    'url': result['url'],
                    'size': result['size'],
                    'collection': collection,
                    'public_id': result.get('public_id'),
                    'dimensions': result.get('dimensions', '')
                }
            })
        else:
            return jsonify({'error': result['error']}), 500
            
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
        
        # Supprimer l'image
        result = delete_image(collection, filename)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Image supprimée avec succès',
                'storage': result['storage']
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-json', methods=['GET'])
def api_generate_json():
    """API: Générer le JSON pour GitHub"""
    try:
        data = list_images()
        
        # Formater pour GitHub
        github_data = {
            'last_updated': datetime.now().isoformat(),
            'storage': 'cloudinary' if CLOUDINARY_ENABLED else 'local',
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
        'storage': 'cloudinary' if CLOUDINARY_ENABLED else 'local',
        'cloudinary_enabled': CLOUDINARY_ENABLED,
        'timestamp': datetime.now().isoformat(),
        'message': 'Système fonctionnel' + (' avec Cloudinary' if CLOUDINARY_ENABLED else ' en local')
    })

@app.route('/api/test-cloudinary', methods=['GET'])
def test_cloudinary():
    """Tester la connexion Cloudinary"""
    if not CLOUDINARY_ENABLED:
        return jsonify({
            'success': False,
            'cloudinary': 'disabled',
            'message': 'Cloudinary non configuré. Stockage local utilisé.'
        })
    
    try:
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

# ========== ROUTES POUR FICHIERS LOCAUX ==========

@app.route('/temp_uploads/<collection>/<filename>')
def serve_temp_file(collection, filename):
    """Servir les fichiers uploadés localement"""
    if not CLOUDINARY_ENABLED:
        try:
            return send_from_directory(os.path.join(UPLOAD_FOLDER, collection), filename)
        except:
            return jsonify({'error': 'Fichier non trouvé'}), 404
    else:
        return jsonify({'error': 'Utilisez les URLs Cloudinary'}), 400

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir les fichiers statiques"""
    try:
        return send_from_directory(app.static_folder, filename)
    except:
        return jsonify({'error': 'Fichier non trouvé'}), 404

@app.route('/admin')
def serve_admin():
    """Interface admin"""
    try:
        return send_from_directory(app.static_folder, 'admin.html')
    except:
        # Fallback si admin.html n'existe pas
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Rayschic - Fallback</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { background:#1a1a2e; color:white; font-family:sans-serif; padding:40px; }
                h1 { color:#d4af37; }
                .btn { background:#d4af37; color:#1a1a2e; padding:12px 24px; border-radius:8px; text-decoration:none; display:inline-block; margin:10px; }
                .status { padding:5px 10px; border-radius:4px; }
                .online { background:#28a745; }
                .offline { background:#dc3545; }
            </style>
        </head>
        <body>
            <h1>Admin Rayschic - Mode Secours</h1>
            <p>Statut: <span class="status online" id="status">En ligne</span></p>
            <p><a href="/" class="btn">Accueil</a></p>
            <p><a href="/api/scan" class="btn">Voir les images</a></p>
            <p>Upload direct:</p>
            <form id="uploadForm">
                <select name="collection" style="padding:10px; margin:5px;">
                    <option value="hero">Hero</option>
                    <option value="costumes">Costumes</option>
                    <option value="chemises">Chemises</option>
                    <option value="pantalons">Pantalons</option>
                    <option value="vestes">Vestes</option>
                    <option value="tenues">Tenues</option>
                    <option value="accessoires">Accessoires</option>
                </select><br>
                <input type="file" name="file" style="margin:5px;"><br>
                <button type="submit" class="btn">Uploader</button>
            </form>
            <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                alert(result.success ? 'Upload réussi!' : 'Erreur: ' + result.error);
            };
            </script>
        </body>
        </html>
        '''

@app.route('/')
def index():
    """Page d'accueil"""
    storage_type = 'Cloudinary' if CLOUDINARY_ENABLED else 'Local (temporaire)'
    storage_color = '#28a745' if CLOUDINARY_ENABLED else '#ffc107'
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rayschic Image System</title>
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', sans-serif; }}
            body {{ background:#1a1a2e; color:#f8f9fa; min-height:100vh; padding:20px; }}
            .container {{ max-width:1000px; margin:0 auto; }}
            .header {{ text-align:center; margin-bottom:40px; }}
            h1 {{ color:#d4af37; font-size:2.5rem; margin-bottom:10px; }}
            .storage-badge {{ display:inline-block; background:{storage_color}; color:white; padding:5px 15px; border-radius:20px; font-size:0.9rem; margin-bottom:20px; }}
            .card {{ background:#2d3047; padding:25px; border-radius:12px; margin-bottom:20px; border-left:5px solid #d4af37; }}
            .btn {{ background:#d4af37; color:#1a1a2e; padding:12px 24px; border-radius:8px; text-decoration:none; display:inline-block; margin:10px 5px; font-weight:bold; transition:all 0.3s; }}
            .btn:hover {{ background:#b8941f; transform:translateY(-2px); }}
            .btn-secondary {{ background:#2d3047; color:#d4af37; border:2px solid #d4af37; }}
            .btn-secondary:hover {{ background:#d4af37; color:#1a1a2e; }}
            .endpoint {{ background:#1a1a2e; padding:10px; border-radius:6px; margin:5px 0; font-family:monospace; }}
            .warning {{ background:rgba(220,53,69,0.2); border-left:4px solid #dc3545; }}
            .info {{ background:rgba(13,110,253,0.2); border-left:4px solid #0d6efd; }}
            @media (max-width:768px) {{ .container {{ padding:10px; }} h1 {{ font-size:2rem; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Rayschic Image System</h1>
                <div class="storage-badge">Stockage: {storage_type}</div>
                <p>Gestion complète des images pour le site web</p>
            </div>
            
            <div class="card">
                <h2>📱 Interface Admin Complète</h2>
                <p>Interface responsive avec drag & drop, prévisualisation et gestion des collections.</p>
                <a href="/admin" class="btn">Ouvrir l'Admin</a>
                <a href="/static/admin.html" class="btn-secondary">Admin Direct</a>
            </div>
            
            <div class="card">
                <h2>⚡ API Endpoints</h2>
                <p>Endpoints REST pour intégration :</p>
                <div class="endpoint">GET <strong>/api/scan</strong> - Lister toutes les images</div>
                <div class="endpoint">POST <strong>/api/upload</strong> - Uploader une image</div>
                <div class="endpoint">POST <strong>/api/delete</strong> - Supprimer une image</div>
                <div class="endpoint">GET <strong>/api/generate-json</strong> - Générer JSON pour GitHub</div>
                <div class="endpoint">GET <strong>/api/health</strong> - Vérifier le statut</div>
                <div class="endpoint">GET <strong>/api/test-cloudinary</strong> - Tester Cloudinary</div>
                <a href="/api/health" class="btn">Vérifier santé</a>
            </div>
            
            {"".join(f'''
            <div class="card warning">
                <h2>⚠️ Stockage Local Temporaire</h2>
                <p><strong>Les images seront perdues au redémarrage!</strong></p>
                <p>Pour activer Cloudinary (stockage permanent) :</p>
                <ol>
                    <li>Créez un compte gratuit sur <a href="https://cloudinary.com" style="color:#d4af37;">cloudinary.com</a></li>
                    <li>Récupérez vos credentials (cloud_name, api_key, api_secret)</li>
                    <li>Ajoutez-les dans les variables d'environnement sur Render</li>
                    <li>Redémarrez le service</li>
                </ol>
            </div>
            ''' if not CLOUDINARY_ENABLED else "")}
            
            <div class="card info">
                <h2>📦 Collections disponibles</h2>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin-top:15px;">
                    <div style="background:#1a1a2e; padding:10px; border-radius:6px;">• Hero (Image principale)</div>
                    <div style="background:#1a1a2e; padding:10px; border-radius:6px;">• Costumes sur Mesure</div>
                    <div style="background:#1a1a2e; padding:10px; border-radius:6px;">• Chemises sur Mesure</div>
                    <div style="background:#1a1a2e; padding:10px; border-radius:6px;">• Pantalons sur Mesure</div>
                    <div style="background:#1a1a2e; padding:10px; border-radius:6px;">• Vestes & Blazers</div>
                    <div style="background:#1a1a2e; padding:10px; border-radius:6px;">• Tenues Spécifiques</div>
                    <div style="background:#1a1a2e; padding:10px; border-radius:6px;">• Accessoires Masculins</div>
                </div>
            </div>
        </div>
        
        <script>
        // Vérifier le statut automatiquement
        fetch('/api/health')
            .then(r => r.json())
            .then(data => console.log('Système:', data));
        </script>
    </body>
    </html>
    '''

# ========== GESTION DES ERREURS ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Route non trouvée', 'available_routes': {
        '/': 'Page d\'accueil',
        '/admin': 'Interface admin',
        '/api/scan': 'Scanner images',
        '/api/upload': 'Uploader image (POST)',
        '/api/delete': 'Supprimer image (POST)',
        '/api/health': 'Santé système'
    }}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur interne du serveur', 'message': str(error)}), 500

# ========== POINT D'ENTRÉE ==========

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Démarrage sur le port {port}")
    print(f"📦 Cloudinary activé: {CLOUDINARY_ENABLED}")
    print(f"📁 Stockage de secours: {UPLOAD_FOLDER}")
    app.run(host='0.0.0.0', port=port, debug=False)
