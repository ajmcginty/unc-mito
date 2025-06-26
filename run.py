from flask import Flask
from unc_mito.routes import create_blueprint
import os

def create_app():
    app = Flask(__name__, 
                template_folder=os.path.join('unc_mito', 'templates'),
                static_folder=os.path.join('unc_mito', 'static'))
    app.register_blueprint(create_blueprint())
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)