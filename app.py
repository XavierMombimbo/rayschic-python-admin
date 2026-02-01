import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template_string
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
    cloud_name=os.getenv('dvjgsq4zl', ''),
    api_key=os.getenv('514262723866384', ''),
    api_secret=os.getenv('9BIyeJyzZHYPDaH26lFxwYDb5dc', ''),
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
                max_results=100,
                tags=True
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
        
        # Vérifier la taille du fichier (max 10MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({'error': 'Fichier trop volumineux (max 10MB)'}), 400
        
        # Vérifier l'extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' in file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                return jsonify({'error': f'Extension non autorisée. Utilisez: {", ".join(allowed_extensions)}'}), 400
        
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
                    'public_id': result['public_id'],
                    'dimensions': result['dimensions']
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
        name_without_ext = os.path.splitext(name)[0]
        public_id = f"rayschic/{collection}/{name_without_ext}"
        
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
        'timestamp': datetime.now().isoformat(),
        'cloudinary_configured': bool(os.getenv('CLOUDINARY_CLOUD_NAME'))
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

# ========== ROUTES POUR LES FICHIERS STATIQUES ==========

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir les fichiers statiques"""
    try:
        return send_from_directory(app.static_folder, filename)
    except:
        return jsonify({'error': 'Fichier non trouvé'}), 404

@app.route('/admin')
def serve_admin():
    """Rediriger vers l'interface admin"""
    try:
        return send_from_directory(app.static_folder, 'admin.html')
    except:
        # Fallback: Interface admin intégrée
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Rayschic - Fallback</title>
            <style>
                body { background: #1a1a2e; color: white; padding: 40px; text-align: center; }
                h1 { color: #d4af37; }
                .btn { background: #d4af37; color: #1a1a2e; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; margin: 10px; }
            </style>
        </head>
        <body>
            <h1>Interface Admin - Mode Secours</h1>
            <p>L'interface principale n'est pas disponible.</p>
            <p><a href="/" class="btn">Retour à l'API</a></p>
        </body>
        </html>
        ''')

# ========== PAGE D'ACCUEIL AVEC LIENS ==========

@app.route('/')
def index():
    """Page d'accueil avec interface complète"""
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rayschic Image Management</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
            body { background: #1a1a2e; color: #f8f9fa; min-height: 100vh; }
            .container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
            
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { color: #d4af37; font-size: 2.8rem; margin-bottom: 10px; }
            .header p { color: #aaa; font-size: 1.2rem; }
            
            .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; }
            
            .card { background: #2d3047; border-radius: 12px; padding: 25px; border-left: 5px solid #d4af37; transition: transform 0.3s; }
            .card:hover { transform: translateY(-5px); }
            
            .card h2 { color: #d4af37; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
            
            .btn { display: inline-block; background: #d4af37; color: #1a1a2e; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px; transition: all 0.3s; border: none; cursor: pointer; }
            .btn:hover { background: #b8941f; transform: translateY(-2px); }
            
            .btn-secondary { background: #2d3047; color: #d4af37; border: 2px solid #d4af37; }
            
            .endpoint { background: #1a1a2e; padding: 12px; border-radius: 6px; margin: 8px 0; font-family: monospace; font-size: 0.9rem; }
            
            .status { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 0.9rem; margin-left: 10px; }
            .status.online { background: #28a745; }
            .status.offline { background: #dc3545; }
            
            .instructions { background: rgba(212, 175, 55, 0.1); padding: 20px; border-radius: 10px; margin-top: 30px; border-left: 4px solid #d4af37; }
            
            @media (max-width: 768px) {
                .container { padding: 20px 15px; }
                .header h1 { font-size: 2rem; }
                .card-grid { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Rayschic Image Management</h1>
                <p>Système de gestion d'images avec stockage Cloudinary permanent</p>
                <div style="margin-top: 15px;">
                    <span class="status online" id="apiStatus">En ligne</span>
                    <span class="status" id="cloudinaryStatus" style="background: #6c757d;">Cloudinary ?</span>
                </div>
            </div>
            
            <div class="card-grid">
                <div class="card">
                    <h2><i class="fas fa-tv"></i> Interface Complète</h2>
                    <p>Interface d'administration responsive avec drag & drop, gestion des collections et prévisualisation.</p>
                    <a href="/static/admin.html" class="btn" id="adminBtn">
                        <i class="fas fa-external-link-alt"></i> Ouvrir l'Admin
                    </a>
                    <a href="/admin" class="btn btn-secondary">
                        <i class="fas fa-link"></i> Alternative
                    </a>
                </div>
                
                <div class="card">
                    <h2><i class="fas fa-cloud-upload-alt"></i> Upload Rapide</h2>
                    <p>Uploader directement vers une collection spécifique :</p>
                    <div style="margin: 15px 0;">
                        <select id="quickCollection" style="width: 100%; padding: 10px; background: #1a1a2e; color: white; border: 2px solid #d4af37; border-radius: 6px; margin-bottom: 10px;">
                            <option value="hero">Image Hero</option>
                            <option value="costumes">Costumes</option>
                            <option value="chemises">Chemises</option>
                            <option value="pantalons">Pantalons</option>
                            <option value="vestes">Vestes</option>
                            <option value="tenues">Tenues</option>
                            <option value="accessoires">Accessoires</option>
                        </select>
                        <input type="file" id="quickUpload" multiple accept="image/*" style="display: none;">
                        <button onclick="document.getElementById('quickUpload').click()" class="btn" style="width: 100%;">
                            <i class="fas fa-upload"></i> Sélectionner des images
                        </button>
                    </div>
                </div>
                
                <div class="card">
                    <h2><i class="fas fa-code"></i> API Endpoints</h2>
                    <p>Accédez directement aux endpoints :</p>
                    <div class="endpoint">GET <strong>/api/scan</strong> - Lister les images</div>
                    <div class="endpoint">POST <strong>/api/upload</strong> - Uploader</div>
                    <div class="endpoint">POST <strong>/api/delete</strong> - Supprimer</div>
                    <div class="endpoint">GET <strong>/api/generate-json</strong> - JSON GitHub</div>
                    <div class="endpoint">GET <strong>/api/health</strong> - Santé système</div>
                </div>
            </div>
            
            <div class="instructions">
                <h3 style="color: #d4af37; margin-bottom: 15px;">
                    <i class="fas fa-info-circle"></i> Instructions
                </h3>
                <ol style="margin-left: 20px; line-height: 1.8;">
                    <li><strong>Cloudinary requis</strong> : Ajoutez vos credentials dans les variables d'environnement Render</li>
                    <li><strong>Interface Admin</strong> : Accédez à <code>/static/admin.html</code> pour la gestion complète</li>
                    <li><strong>Stockage permanent</strong> : Les images sont stockées sur Cloudinary (25GB gratuit)</li>
                    <li><strong>Mise à jour site</strong> : Générez le JSON et uploadez-le sur GitHub</li>
                </ol>
            </div>
        </div>
        
        <script>
        // Vérifier le statut
        async function checkStatus() {
            try {
                // Vérifier API
                const apiResponse = await fetch('/api/health');
                const apiData = await apiResponse.json();
                
                document.getElementById('apiStatus').textContent = 'API ✓';
                
                // Vérifier Cloudinary
                const cloudinaryResponse = await fetch('/api/test-cloudinary');
                const cloudinaryData = await cloudinaryResponse.json();
                
                const cloudinaryStatus = document.getElementById('cloudinaryStatus');
                if (cloudinaryData.success) {
                    cloudinaryStatus.textContent = 'Cloudinary ✓';
                    cloudinaryStatus.style.background = '#28a745';
                } else {
                    cloudinaryStatus.textContent = 'Cloudinary ✗';
                    cloudinaryStatus.style.background = '#dc3545';
                }
                
            } catch (error) {
                console.error('Status check failed:', error);
            }
        }
        
        // Quick upload
        document.getElementById('quickUpload').addEventListener('change', async function(e) {
            const files = Array.from(e.target.files);
            const collection = document.getElementById('quickCollection').value;
            
            if (files.length === 0) return;
            
            alert(`Upload de ${files.length} image(s) vers ${collection}...`);
            
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('collection', collection);
                
                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        console.log('Upload réussi:', result);
                    } else {
                        console.error('Upload échoué:', result);
                    }
                } catch (error) {
                    console.error('Erreur réseau:', error);
                }
            }
            
            alert('Upload terminé ! Actualisez l\'admin pour voir les images.');
            this.value = '';
        });
        
        // Vérifier si admin.html existe
        async function checkAdmin() {
            try {
                const response = await fetch('/static/admin.html', { method: 'HEAD' });
                const adminBtn = document.getElementById('adminBtn');
                
                if (!response.ok) {
                    adminBtn.innerHTML = '<i class="fas fa-warning"></i> Admin non installé';
                    adminBtn.style.background = '#dc3545';
                    adminBtn.href = '#';
                    adminBtn.onclick = () => alert('Téléchargez admin.html et placez-le dans le dossier static/');
                }
            } catch (error) {
                console.log('Admin check skipped');
            }
        }
        
        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            checkStatus();
            checkAdmin();
        });
        </script>
        
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </body>
    </html>
    '''

# ========== GESTION DES ERREURS ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Route non trouvée', 'available_routes': {
        '/': 'Page d\'accueil',
        '/admin': 'Interface admin',
        '/static/admin.html': 'Admin complet',
        '/api/scan': 'Scanner images',
        '/api/upload': 'Uploader image',
        '/api/delete': 'Supprimer image',
        '/api/health': 'Santé système'
    }}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur interne du serveur', 'message': str(error)}), 500

# ========== POINT D'ENTRÉE ==========

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
