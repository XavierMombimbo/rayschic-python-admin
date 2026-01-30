from flask import Flask, jsonify, send_from_directory
import os

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Collections
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

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rayschic Admin - EN LIGNE</title>
        <style>
            body { 
                background: #1a1a2e; 
                color: white; 
                font-family: sans-serif; 
                padding: 40px; 
                text-align: center; 
                margin: 0;
            }
            h1 { 
                color: #d4af37; 
                font-size: 2.5rem; 
                margin-bottom: 10px;
            }
            .btn { 
                background: #d4af37; 
                color: #1a1a2e; 
                padding: 12px 24px; 
                border-radius: 8px; 
                text-decoration: none; 
                display: inline-block; 
                margin: 10px; 
                font-weight: bold;
                font-size: 1.1rem;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
            }
            .card { 
                background: #2d3047; 
                padding: 30px; 
                border-radius: 15px; 
                margin: 30px 0; 
                border: 2px solid #d4af37;
            }
            .success { 
                color: #4CAF50; 
                font-weight: bold;
                font-size: 1.2rem;
            }
            code {
                background: rgba(0,0,0,0.3);
                padding: 4px 8px;
                border-radius: 4px;
                color: #d4af37;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ RAYSCHIC ADMIN PYTHON</h1>
            <p class="success">SYSTÈME EN LIGNE ET FONCTIONNEL</p>
            
            <div class="card">
                <h2>🎯 Votre API est opérationnelle</h2>
                <p>Le système Python a été déployé avec succès sur Render.com</p>
                
                <div style="margin: 25px 0;">
                    <a class="btn" href="/api/scan">
                        📡 Tester l'API maintenant
                    </a>
                    <a class="btn" href="https://rayschic-couture.github.io" target="_blank">
                        🌐 Voir le site principal
                    </a>
                </div>
                
                <div style="text-align: left; background: #1a1a2e; padding: 20px; border-radius: 10px; margin-top: 20px;">
                    <h3>🔗 Votre URL API :</h3>
                    <p><code id="api-url">Chargement...</code></p>
                    
                    <h3>📋 Endpoints disponibles :</h3>
                    <ul>
                        <li><code>GET /api/scan</code> - Scanner les images</li>
                        <li><code>POST /api/upload</code> - Uploader une image</li>
                        <li><code>GET /api/generate-json</code> - Générer JSON</li>
                        <li><code>GET /uploads/[collection]/[image]</code> - Accéder aux images</li>
                    </ul>
                </div>
            </div>
            
            <div style="color: #666; margin-top: 40px;">
                <p><strong>Prochaine étape :</strong> Mettre à jour votre site principal pour utiliser cette API</p>
                <p>URL de votre service : <code>https://rayschic-python-admin.onrender.com</code></p>
            </div>
        </div>
        
        <script>
            // Afficher l'URL actuelle
            document.getElementById('api-url').textContent = window.location.origin;
            
            // Tester automatiquement l'API
            fetch('/api/scan')
                .then(response => response.json())
                .then(data => {
                    console.log('✅ API fonctionnelle :', data);
                    // Ajouter un badge de confirmation
                    const title = document.querySelector('h1');
                    title.innerHTML = '✅ RAYSCHIC ADMIN PYTHON <span style="color:#4CAF50; font-size:1rem;">(API OK)</span>';
                })
                .catch(error => {
                    console.log('⚠️ Test API :', error);
                });
        </script>
    </body>
    </html>
    '''

@app.route('/api/scan')
def scan():
    """Scanner toutes les images"""
    result = {
        'collections': {},
        'stats': {'total_images': 0, 'collections_count': len(COLLECTIONS)}
    }
    
    for folder, title in COLLECTIONS.items():
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        images = []
        
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    filepath = os.path.join(folder_path, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        images.append({
                            'filename': filename,
                            'url': f'/uploads/{folder}/{filename}',
                            'size': stat.st_size
                        })
        
        result['collections'][folder] = {
            'title': title,
            'images': images,
            'count': len(images)
        }
        result['stats']['total_images'] += len(images)
    
    return jsonify(result)

@app.route('/uploads/<path:path>')
def serve_uploads(path):
    """Servir les images uploadées"""
    return send_from_directory(UPLOAD_FOLDER, path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

