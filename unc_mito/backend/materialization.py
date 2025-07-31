"""Handle mitochondria materialization table format and processing."""

import pandas as pd
import numpy as np
import requests
from ..config import MITO_URL, NEURON_URL, DEFAULT_SCREENSHOT
import os

class MitochondriaMaterialization:
    def __init__(self, csv_path):
        """Initialize with mitochondria CSV data.
        
        Args:
            csv_path (str): Path to CSV containing mitochondria data
        """
        self.df = pd.read_csv(csv_path)
        # Convert segment_id to integer
        self.df['segment_id'] = self.df['segment_id'].astype(int)
        
        # Make sure URLs have the precomputed:// prefix
        self.mito_url = MITO_URL if MITO_URL.startswith('precomputed://') else f"precomputed://{MITO_URL}"
        self.neuron_url = NEURON_URL if NEURON_URL.startswith('precomputed://') else f"precomputed://{NEURON_URL}"
        
    def validate_bounds(self, volume_bounds, scale_factor=32):
        """Check if mitochondria are completely outside volume bounds.
        Only warns about mitochondria that are entirely outside the volume.
        
        Args:
            volume_bounds (dict): Dictionary containing x_min, x_max, y_min, y_max, z_min, z_max
            scale_factor (int): Factor to divide coordinates by (default 32 for nm to voxels)
        
        Returns:
            tuple: (bool, list) - (whether all mitochondria overlap volume, list of completely out-of-bounds IDs)
        """
        print("Volume bounds (in voxels):")
        print(f"X: {volume_bounds['x_min']} to {volume_bounds['x_max']}")
        print(f"Y: {volume_bounds['y_min']} to {volume_bounds['y_max']}")
        print(f"Z: {volume_bounds['z_min']} to {volume_bounds['z_max']}")
        
        completely_outside = []
        for idx, row in self.df.iterrows():
            # Convert coordinates from nm to voxels
            scaled_coords = {
                'min_x': row['min_x'] / scale_factor,
                'max_x': row['max_x'] / scale_factor,
                'min_y': row['min_y'] / scale_factor,
                'max_y': row['max_y'] / scale_factor,
                'min_z': row['min_z'] / scale_factor,
                'max_z': row['max_z'] / scale_factor,
            }
            
            # Check if mitochondrion is completely outside the volume
            if (scaled_coords['min_x'] > volume_bounds['x_max'] or
                scaled_coords['max_x'] < volume_bounds['x_min'] or
                scaled_coords['min_y'] > volume_bounds['y_max'] or
                scaled_coords['max_y'] < volume_bounds['y_min'] or
                scaled_coords['min_z'] > volume_bounds['z_max'] or
                scaled_coords['max_z'] < volume_bounds['z_min']):
                completely_outside.append(row['segment_id'])
                if len(completely_outside) <= 5:  # Show first 5 examples
                    print(f"\nMitochondrion {row['segment_id']} completely outside volume:")
                    print(f"X: {scaled_coords['min_x']:.1f} to {scaled_coords['max_x']:.1f}")
                    print(f"Y: {scaled_coords['min_y']:.1f} to {scaled_coords['max_y']:.1f}")
                    print(f"Z: {scaled_coords['min_z']:.1f} to {scaled_coords['max_z']:.1f}")
        
        if completely_outside:
            print(f"\nFound {len(completely_outside)} mitochondria completely outside the volume")
            print("These will be excluded from visualization")
        else:
            print("\nAll mitochondria overlap with the volume")
            
        return len(completely_outside) == 0, completely_outside
    
    def get_mitochondria_for_neuron(self, neuron_id, page=1, per_page=8):
        """Get mitochondria segments for a given neuron with pagination.
        
        Args:
            neuron_id: ID of the neuron
            page: Page number (1-based)
            per_page: Number of items per page
        """
        mitos = self.df[self.df['neuron_id'] == int(neuron_id)]
        total_mitos = len(mitos)
        total_pages = (total_mitos + per_page - 1) // per_page
        
        # Calculate slice indices
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get mitos for current page
        page_mitos = mitos.iloc[start_idx:end_idx]
        
        # For each mitochondrion, prepare the view URLs
        mito_data = []
        for _, mito in page_mitos.iterrows():
            # Calculate center point
            center_x = (mito['min_x'] + mito['max_x']) / 2
            center_y = (mito['min_y'] + mito['max_y']) / 2
            center_z = (mito['min_z'] + mito['max_z']) / 2
            
            # Check if screenshots exist, otherwise use a placeholder
            screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                        'static', 'screenshots', str(mito['segment_id']))
            
            if os.path.exists(screenshot_dir) and any(f.endswith('.png') for f in os.listdir(screenshot_dir)):
                screenshots = [
                    f'/static/screenshots/{mito["segment_id"]}/0.png',
                    f'/static/screenshots/{mito["segment_id"]}/45.png',
                    f'/static/screenshots/{mito["segment_id"]}/90.png',
                    f'/static/screenshots/{mito["segment_id"]}/135.png',
                    f'/static/screenshots/{mito["segment_id"]}/180.png',
                    f'/static/screenshots/{mito["segment_id"]}/225.png',
                    f'/static/screenshots/{mito["segment_id"]}/270.png',
                    f'/static/screenshots/{mito["segment_id"]}/315.png'
                ]
            else:
                # Use a single placeholder image for all views
                screenshots = [DEFAULT_SCREENSHOT] * 8
            
            mito_data.append({
                'id': mito['segment_id'],
                'bounds': {
                    'min_x': mito['min_x'],
                    'min_y': mito['min_y'],
                    'min_z': mito['min_z'],
                    'max_x': mito['max_x'],
                    'max_y': mito['max_y'],
                    'max_z': mito['max_z']
                },

                'screenshots': screenshots
            })
            
        return {
            'mitos': mito_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_mitos': total_mitos
        }
    

    def get_volume_bounds_from_precomputed(self, precomputed_url):
        if precomputed_url.startswith('precomputed://'):
            precomputed_url = precomputed_url[len('precomputed://'):]
        
        info_url = precomputed_url.rstrip('/') + '/info'
        response = requests.get(info_url)
        info = response.json()

        scale = info['scales'][0]  # Use highest resolution
        voxel_offset = scale.get('voxel_offset', [0, 0, 0])
        size = scale['size']
        
        return {
            'x_min': voxel_offset[0],
            'x_max': voxel_offset[0] + size[0],
            'y_min': voxel_offset[1],
            'y_max': voxel_offset[1] + size[1],
            'z_min': voxel_offset[2],
            'z_max': voxel_offset[2] + size[2]
        }
        
