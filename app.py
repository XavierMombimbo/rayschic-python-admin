from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dossiers des collections
COLLECTIONS = {
    'costumes': 'Costumes sur Mesure',
    'chemises': 'Chemises sur Mesure', 
    'pantalons': 'Pantalons sur Mesure',
    'vestes': 'Vestes & Blazers',
    'tenues': 'Tenues Spécifiques',
    'accessoires': 'Accessoires Masculins',
    'hero': 'Image Principale'
}

# Créer les dossiers
for folder in COLLECTIONS.keys():
    os.makedirs(os.path.join(UPLOAD_FOLDER, folder), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rayschic Admin</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                background: #1a1a2e;
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 40px;
                text-align: center;
                margin: 0;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #d4af37;
                font-size: 3rem;
                margin-bottom: 10px;
                background: linear-gradient(90deg, #d4af37, #ffd700);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .subtitle {
                color: #aaa;
                font-size: 1.2rem;
                margin-bottom: 40px;
            }
            .card {
                background: linear-gradient(145deg, #2d3047, #1a1a2e);
                padding: 40px;
                border-radius: 20px;
                margin: 40px 0;
                border: 2px solid rgba(212, 175, 55, 0.3);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                text-align: left;
            }
            .btn {
                background: linear-gradient(135deg, #d4af37, #b8941f);
                color: #1a1a2e;
                padding: 15px 30px;
                border-radius: 10px;
                text-decoration: none;
                display: inline-block;
                margin: 10px;
                font-weight: bold;
                font-size: 1.1rem;
                border: none;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);
            }
            .btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(212, 175, 55, 0.3);
                background: linear-gradient(135deg, #ffd700, #d4af37);
            }
            .status-badge {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: bold;
                margin-left: 15px;
            }
            .api-list {
                list-style: none;
                padding: 0;
                margin: 25px 0;
            }
            .api-list li {
                padding: 15px;
                margin: 10px 0;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                border-left: 4px solid #d4af37;
                transition: background 0.3s;
            }
            .api-list li:hover {
                background: rgba(212, 175, 55, 0.1);
            }
            .api-list code {
                background: rgba(0, 0, 0, 0.3);
                padding: 4px 8px;
                border-radius: 4px;
                color: #d4af37;
                font-family: monospace;
            }
            .url-display {
                background: rgba(0, 0, 0, 0.3);
                padding: 15px;
                border-radius: 10px;
                margin: 30px 0;
                border: 1px solid rgba(212, 175, 55, 0.2);
                font-family: monospace;
                word-break: break-all;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature {
                background: rgba(212, 175, 55, 0.1);
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                border: 1px solid rgba(212, 175, 55, 0.2);
            }
            .feature i {
                font-size: 2.5rem;
                color: #d4af37;
                margin-bottom: 15px;
            }
            .logo {
                font-size: 2.8rem;
                font-weight: bold;
                color: #d4af37;
                margin-bottom: 20px;
                display: inline-block;
            }
            .logo span {
                color: white;
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        <div class="container">
            <div class="logo">RAY<span>SCHIC</span></div>
            <h1>Python Image Admin</h1>
            <p class="subtitle">Système de gestion d'images avancé - Déployé sur Render</p>
            
            <div class="card">
                <h2 style="color: #d4af37; margin-top: 0;">
                    <i class="fas fa-rocket"></i> Statut du système
                    <span class="status-badge">EN LIGNE ✅</span>
                </h2>
                <p>Votre API Python fonctionne parfaitement. Tous les services sont opérationnels.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="/api/scan" class="btn">
                        <i class="fas fa-search"></i> Tester l'API Maintenant
                    </a>
                    <a href="https://rayschic-couture.github.io" target="_blank" class="btn">
                        <i class="fas fa-external-link-alt"></i> Voir le Site Principal
                    </a>
                </div>
                
                <div class="features">
                    <div class="feature">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <h3>Upload Direct</h3>
                        <p>Uploader des images sans passer par GitHub</p>
                    </div>
                    <div class="feature">
                        <i class="fas fa-sync-alt"></i>
                        <h3>Redimensionnement Auto</h3>
                        <p>Images optimisées automatiquement</p>
                    </div>
                    <div class="feature">
                        <i class="fas fa-code"></i>
                        <h3>JSON Automatique</h3>
                        <p>Génération automatique pour GitHub</p>
                    </div>
                </div>
                
                <h3 style="color: #d4af37; margin-top: 40px;">
                    <i class="fas fa-plug"></i> Points d'accès API
                </h3>
                <ul class="api-list">
                    <li>
                        <strong><a href="/api/scan" style="color: #d4af37; text-decoration: none;">GET /api/scan</a></strong>
                        <p style="margin: 8px 0 0 0; color: #aaa; font-size: 0.9rem;">
                            Scanner toutes les images uploadées
                        </p>
                    </li>
                    <li>
                        <strong><code>POST /api/upload</code></strong>
                        <p style="margin: 8px 0 0 0; color: #aaa; font-size: 0.9rem;">
                            Uploader une nouvelle image (multipart/form-data)
                        </p>
                    </li>
                    <li>
                        <strong><a href="/api/generate-json" style="color: #d4af37; text-decoration: none;">GET /api/generate-json</a></strong>
                        <p style="margin: 8px 0 0 0; color: #aaa; font-size: 0.9rem;">
                            Générer le fichier images.json pour GitHub
                        </p>
                    </li>
                </ul>
                
                <div class="url-display">
                    <strong>URL de votre API :</strong><br>
                    <span id="api-url">Chargement...</span>
                </div>
                
                <div style="background: rgba(76, 175, 80, 0.1); padding: 20px; border-radius: 10px; border-left: 4px solid #4CAF50; margin-top: 30px;">
                    <h4 style="color: #4CAF50; margin-top: 0;">
                        <i class="fas fa-check-circle"></i> Prochaine étape
                    </h4>
                    <p>Interface d'administration complète disponible dans <code>/admin</code> (bientôt)</p>
                    <a href="/admin" class="btn" style="background: rgba(76, 175, 80, 0.2); color: #4CAF50; margin-top: 10px;">
                        <i class="fas fa-cogs"></i> Accéder à l'Admin
                    </a>
                </div>
            </div>
            
            <div style="color: #666; margin-top: 40px; font-size: 0.9rem;">
                <p>
                    <i class="fas fa-info-circle"></i> 
                    Système développé pour Rayschic Couture • Déployé sur Render.com • 
                    <a href="https://github.com/XavierMombimbo/rayschic-python-admin" style="color: #666;">Code source</a>
                </p>
            </div>
        </div>
        
        <script>
            // Afficher l'URL actuelle
            document.getElementById('api-url').textContent = window.location.origin;
            
            // Tester automatiquement l'API
            async function testAPI() {
                try {
                    const response = await fetch('/api/scan');
                    const data = await response.json();
                    console.log('✅ API fonctionnelle:', data);
                    
                    // Mettre à jour le badge si l'API répond
                    const badge = document.querySelector('.status-badge');
                    badge.innerHTML = 'API OK <i class="fas fa-check"></i>';
                    badge.style.background = '#4CAF50';
                    
                } catch (error) {
                    console.warn('⚠️ API temporairement indisponible:', error);
                }
            }
            
            // Tester au chargement
            document.addEventListener('DOMContentLoaded', testAPI);
            
            // Raccourcis clavier
            document.addEventListener('keydown', function(e) {
                // Ctrl+I pour info API
                if (e.ctrlKey && e.key === 'i') {
                    e.preventDefault();
                    testAPI();
                }
                // Ctrl+T pour test
                if (e.ctrlKey && e.key === 't') {
                    e.preventDefault();
                    window.open('/api/scan', '_blank');
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/admin')
def admin():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Interface</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                background: #1a1a2e;
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 40px;
                text-align: center;
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                max-width: 600px;
                padding: 40px;
                background: linear-gradient(145deg, #2d3047, #1a1a2e);
                border-radius: 20px;
                border: 2px solid rgba(212, 175, 55, 0.3);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
            }
            h1 {
                color: #d4af37;
                font-size: 2.5rem;
                margin-bottom: 20px;
            }
            .loading-icon {
                font-size: 4rem;
                color: #d4af37;
                margin-bottom: 30px;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.1); opacity: 0.7; }
                100% { transform: scale(1); opacity: 1; }
            }
            .message {
                background: rgba(212, 175, 55, 0.1);
                padding: 25px;
                border-radius: 15px;
                margin: 30px 0;
                border-left: 4px solid #d4af37;
                text-align: left;
            }
            .btn {
                background: linear-gradient(135deg, #d4af37, #b8941f);
                color: #1a1a2e;
                padding: 15px 30px;
                border-radius: 10px;
                text-decoration: none;
                display: inline-block;
                margin: 10px;
                font-weight: bold;
                font-size: 1.1rem;
                border: none;
                cursor: pointer;
                transition: all 0.3s;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(212, 175, 55, 0.3);
            }
            .progress {
                width: 100%;
                height: 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                margin: 30px 0;
                overflow: hidden;
            }
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #d4af37, #ffd700);
                width: 75%;
                border-radius: 5px;
                animation: loading 2s ease-in-out infinite;
            }
            @keyframes loading {
                0% { transform: translateX(-100%); }
                50% { transform: translateX(0%); }
                100% { transform: translateX(100%); }
            }
            .links {
                margin-top: 40px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            .links a {
                color: #d4af37;
                text-decoration: none;
                padding: 12px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            .links a:hover {
                background: rgba(212, 175, 55, 0.1);
                transform: translateX(5px);
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        <div class="container">
            <div class="loading-icon">
                <i class="fas fa-cogs"></i>
            </div>
            
            <h1>Interface Admin</h1>
            <p>En cours de finalisation...</p>
            
            <div class="progress">
                <div class="progress-bar"></div>
            </div>
            
            <div class="message">
                <h3><i class="fas fa-info-circle"></i> Information</h3>
                <p>L'interface d'administration complète est en cours de déploiement. En attendant, vous pouvez utiliser les fonctionnalités API directement.</p>
                <p><strong>Prochain déploiement :</strong> Interface drag & drop, gestion visuelle, prévisualisation en direct.</p>
            </div>
            
            <div class="links">
                <a href="/api/scan">
                    <i class="fas fa-search"></i> Scanner les images
                </a>
                <a href="/">
                    <i class="fas fa-home"></i> Retour à l'accueil
                </a>
                <a href="https://github.com/XavierMombimbo/rayschic-python-admin" target="_blank">
                    <i class="fab fa-github"></i> Voir le code source
                </a>
            </div>
            
            <div style="margin-top: 40px; color: #666; font-size: 0.9rem;">
                <p><i class="fas fa-sync-alt"></i> Mise à jour automatique dans <span id="countdown">30</span> secondes</p>
            </div>
        </div>
        
        <script>
            // Compte à rebours
            let seconds = 30;
            const countdownElement = document.getElementById('countdown');
            
            const countdown = setInterval(() => {
                seconds--;
                countdownElement.textContent = seconds;
                
                if (seconds <= 0) {
                    clearInterval(countdown);
                    window.location.reload();
                }
            }, 1000);
            
            // Vérifier si l'admin est prêt
            setTimeout(() => {
                fetch('/api/scan')
                    .then(response => response.json())
                    .then(data => {
                        console.log('API status:', data);
                        // Si l'API fonctionne, on pourrait rediriger vers une interface plus avancée
                    })
                    .catch(error => {
                        console.log('API check:', error);
                    });
            }, 5000);
        </script>
    </body>
    </html>
    '''

@app.route('/api/scan', methods=['GET'])
def scan_images():
    """Scanner tous les dossiers et lister les images"""
    result = {
        'collections': {},
        'stats': {
            'total_images': 0,
            'collections_count': 0
        }
    }
    
    for folder, title in COLLECTIONS.items():
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        images = []
        
        if os.path.exists(folder_path):
            # Lire les fichiers JPG
            for filename in sorted(os.listdir(folder_path)):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    filepath = os.path.join(folder_path, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        images.append({
                            'filename': filename,
                            'url': f'/uploads/{folder}/{filename}',
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
        
        if images or folder == 'hero':  # Toujours inclure hero même vide
            result['collections'][folder] = {
                'title': title,
                'images': images,
                'count': len(images)
            }
            result['stats']['total_images'] += len(images)
    
    result['stats']['collections_count'] = len(result['collections'])
    return jsonify(result)

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Uploader une nouvelle image"""
    try:
        # Vérifier le fichier
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier'}), 400
        
        file = request.files['file']
        collection = request.form.get('collection', '').strip().lower()
        
        if not file or file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Format non supporté. Utilisez JPG, PNG ou WebP'}), 400
        
        # Vérifier la taille
        file.seek(0, 2)  # Aller à la fin
        file_size = file.tell()
        file.seek(0)  # Retourner au début
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'Fichier trop volumineux (max 10MB)'}), 400
        
        # Valider la collection
        if collection not in COLLECTIONS:
            return jsonify({'error': f'Collection invalide. Options: {", ".join(COLLECTIONS.keys())}'}), 400
        
        # Déterminer le nom de fichier
        if collection == 'hero':
            filename = 'hero.jpg'
        else:
            # Compter les images existantes
            folder_path = os.path.join(UPLOAD_FOLDER, collection)
            existing = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            next_num = len(existing) + 1
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f'{next_num}.{ext}'
        
        # Sauvegarder le fichier
        filename = secure_filename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, collection, filename)
        
        # Remplacer si existe déjà
        if os.path.exists(filepath):
            os.remove(filepath)
        
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Image uploadée: {filename}',
            'image': {
                'filename': filename,
                'url': f'/uploads/{collection}/{filename}',
                'collection': collection
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/replace', methods=['POST'])
def replace_image():
    """Remplacer une image existante"""
    try:
        collection = request.form.get('collection', '')
        filename = request.form.get('filename', '')
        
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier'}), 400
        
        file = request.files['file']
        
        # Validation
        if collection not in COLLECTIONS:
            return jsonify({'error': 'Collection invalide'}), 400
        
        old_path = os.path.join(UPLOAD_FOLDER, collection, filename)
        if not os.path.exists(old_path):
            return jsonify({'error': 'Image originale non trouvée'}), 404
        
        # Supprimer l'ancienne
        os.remove(old_path)
        
        # Sauvegarder la nouvelle
        file.save(old_path)
        
        return jsonify({
            'success': True,
            'message': f'Image remplacée: {filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_image():
    """Supprimer une image"""
    try:
        data = request.json
        collection = data.get('collection', '')
        filename = data.get('filename', '')
        
        if not collection or not filename:
            return jsonify({'error': 'Paramètres manquants'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, collection, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            
            # Réorganiser les numéros si nécessaire
            if collection != 'hero':
                folder_path = os.path.join(UPLOAD_FOLDER, collection)
                images = sorted([
                    f for f in os.listdir(folder_path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
                ])
                
                # Renommer pour avoir une séquence continue
                for i, old_name in enumerate(images, 1):
                    ext = old_name.rsplit('.', 1)[1].lower()
                    new_name = f'{i}.{ext}'
                    if old_name != new_name:
                        old_path = os.path.join(folder_path, old_name)
                        new_path = os.path.join(folder_path, new_name)
                        os.rename(old_path, new_path)
        
        return jsonify({
            'success': True,
            'message': f'Image supprimée: {filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-json', methods=['GET'])
def generate_json():
    """Générer le fichier images.json pour GitHub"""
    try:
        scan_result = scan_images().get_json()
        
        data = {
            "last_updated": datetime.now().isoformat(),
            "hero": {},
            "collections": {}
        }
        
        # Image hero
        if 'hero' in scan_result['collections'] and scan_result['collections']['hero']['images']:
            hero_images = scan_result['collections']['hero']['images']
            if hero_images:
                data['hero'] = {
                    'url': hero_images[0]['url'],
                    'filename': hero_images[0]['filename']
                }
        
        # Collections
        for collection_key, collection_data in scan_result['collections'].items():
            if collection_key == 'hero':
                continue
                
            images_list = []
            for img in collection_data['images']:
                images_list.append({
                    'url': img['url'],
                    'filename': img['filename'],
                    'number': img['filename'].split('.')[0]
                })
            
            data['collections'][collection_key] = {
                'title': collection_data['title'],
                'images': images_list,
                'count': len(images_list)
            }
        
        # Sauvegarder localement
        os.makedirs('static', exist_ok=True)
        json_path = os.path.join('static', 'images.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Retourner pour téléchargement
        response = jsonify(data)
        response.headers.add('Content-Disposition', 'attachment; filename=images.json')
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Servir les images uploadées"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir les fichiers statiques"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
