"""Flask routes for the UNC mitochondria viewer."""

from flask import Blueprint, render_template, jsonify, current_app, request
from pathlib import Path
import subprocess
import sys
from .backend.materialization import MitochondriaMaterialization
from .config import MATERIALIZATION_CSV, SCREENSHOTS_DIR, DEFAULT_SCREENSHOT, MITO_URL
import os

# Initialize materialization data at module level
mito_data = MitochondriaMaterialization(MATERIALIZATION_CSV)

def create_blueprint():
    """Create the Flask blueprint for the mitochondria viewer."""
    bp = Blueprint('mitochondria', __name__)
    
    @bp.route('/')
    def index():
        """Render the main page."""
        return render_template('mitochondria.html')
        
    @bp.route('/get_mitos_for_neuron/<neuron_id>')
    def get_mitos(neuron_id):
        try:
            page = int(request.args.get('page', 1))
            data = mito_data.get_mitochondria_for_neuron(neuron_id, page=page, per_page=8)
            return jsonify(data)
        except Exception as e:
            print(f"Error in get_mitos: {str(e)}")
            return jsonify({'error': str(e)}), 500
        
    @bp.route('/get_neuroglancer_url/<int:mito_id>/<int:neuron_id>')
    def get_ng_url(mito_id, neuron_id):
        try:
            url = mito_data.get_neuroglancer_url(mito_id, neuron_id)
            return jsonify({'url': url})
        except Exception as e:
            print(f"Error in get_ng_url: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    @bp.route('/generate_screenshots/<int:neuron_id>')
    def generate_screenshots(neuron_id):
        try:
            # Get the current page from query parameters
            page = int(request.args.get('page', 1))
            
            # Get mitochondria for this neuron and page
            data = mito_data.get_mitochondria_for_neuron(neuron_id, page=page, per_page=8)
            mitos = data['mitos']
            
            # Set up output directory
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            
            success_count = 0
            fail_count = 0
            
            # Generate screenshots for each mitochondrion on this page
            for mito in mitos:
                mito_id = mito['id']
                output_dir_for_mito = Path(SCREENSHOTS_DIR) / str(mito_id)
                
                # Only generate if screenshots don't exist
                if not output_dir_for_mito.exists():
                    # Get the path to the screenshot generator script
                    script_path = os.path.join(os.path.dirname(__file__), 'backend', 'screenshot_generator_360.py')
                    
                    # Run the script as a separate process
                    try:
                        subprocess.run([
                            sys.executable,
                            script_path,
                            '--mito-id', str(mito_id),
                            '--output-dir', str(output_dir_for_mito),
                            '--mito-url', MITO_URL
                        ], check=True)
                        success_count += 1
                    except subprocess.CalledProcessError:
                        fail_count += 1
            
            return jsonify({
                'success': True,
                'message': f'Generated {success_count} screenshots, {fail_count} failed'
            })
            
        except Exception as e:
            print(f"Error generating screenshots: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp