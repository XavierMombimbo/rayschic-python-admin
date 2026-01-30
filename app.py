from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
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
    return render_template('admin.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

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
        
        if len(file.read()) > MAX_FILE_SIZE:
            return jsonify({'error': 'Fichier trop volumineux (max 10MB)'}), 400
        
        file.seek(0)  # Revenir au début
        
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
