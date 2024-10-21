import pytesseract
from flask import Flask, request, jsonify, render_template, send_from_directory
import cv2
import numpy as np
from PIL import Image
import os

app = Flask(__name__)

# Ruta de Tesseract en tu sistema
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Directorio para guardar las imágenes subidas temporalmente
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_multipliers(image):
    # Convertir la imagen a escala de grises
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Aumentar el contraste de la imagen
    contrast_image = cv2.convertScaleAbs(gray_image, alpha=2.0, beta=0)

    # Aplicar un umbral simple en lugar de adaptativo
    _, thresh_image = cv2.threshold(contrast_image, 150, 255, cv2.THRESH_BINARY)

    # Extraer el texto con pytesseract y psm 11
    text = pytesseract.image_to_string(thresh_image, config='--psm 11')
    print(f'Texto extraído por Tesseract: {text}')  # Esto te mostrará el texto capturado

    # Filtrar los multiplicadores (números decimales que contienen 'x')
    multipliers = [word for word in text.split() if 'x' in word and word.replace('x', '').replace('.', '', 1).isdigit()]
    
    return multipliers

@app.route('/')
def index():
    return '''
        <div style="display: flex; justify-content: center; align-items: center; height: 100vh; text-align: center;">
            <div>
                <h1>OCR de Multiplicadores en Aviator</h1>
                <form method="POST" action="/upload" enctype="multipart/form-data" style="border: 1px solid #ccc; padding: 20px; width: 300px; margin: 0 auto;">
                    <label for="image">Subir imagen de los multiplicadores:</label><br>
                    <input type="file" name="image" style="margin-top: 10px;"><br><br>
                    <input type="submit" value="Subir Imagen" style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer;">
                </form>
            </div>
        </div>
    '''

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return '''
            <div style="text-align: center; margin-top: 20px;">
                <h3 style="color: red;">No se subió ninguna imagen</h3>
                <a href="/">Volver a la página de subida</a>
            </div>
        ''', 400
    
    file = request.files['image']
    if file.filename == '':
        return '''
            <div style="text-align: center; margin-top: 20px;">
                <h3 style="color: red;">No se seleccionó ninguna imagen</h3>
                <a href="/">Volver a la página de subida</a>
            </div>
        ''', 400

    # Guardamos la imagen subida
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Convertimos la imagen a un formato compatible
    image = Image.open(file_path).convert('RGB')
    image_np = np.array(image)
    
    # Extraemos los multiplicadores de la imagen
    multipliers = extract_multipliers(image_np)
    
    # Mostrar la imagen subida en la respuesta con el texto alineado a la izquierda
    response_html = f'''
        <div style="text-align: left; margin-left: 20px;">
            <h1>Resultados de los Multiplicadores</h1>
            <p>Multiplicadores detectados:</p>
            <ul>
                {''.join([f'<li>{mult}</li>' for mult in multipliers])}
            </ul>
            <h3>Imagen subida:</h3>
            <img src="/uploads/{file.filename}" alt="Imagen subida" style="max-width: 100%;">
            <br><br>
            <a href="/">Volver a subir otra imagen</a>
        </div>
    '''
    
    return response_html

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
