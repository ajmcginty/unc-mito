"""Module for generating mitochondria screenshots using CloudVolume and PyVista."""

from pathlib import Path
import numpy as np
from cloudvolume import CloudVolume
import pyvista as pv

class ScreenshotGenerator:
    def __init__(self):
        """Initialize the screenshot generator."""
        self.mito_src = "https://rhoana.rc.fas.harvard.edu/ng/h01_mito/36750893213"
        self.voxel_size_nm = dict(x=8.0, y=8.0, z=33.0)  # 8×8×33 nm for H01
        self.img_size = [1024, 1024]  # screenshot resolution in pixels
        
        # Initialize CloudVolume
        self.vol = CloudVolume(self.mito_src, use_https=True)
        
    def generate_screenshots(self, mito_id, mito_data, output_dir):
        """Generate screenshots for a mitochondrion.
        
        Args:
            mito_id: ID of the mitochondrion
            mito_data: Dictionary containing mitochondrion data including bounds
            output_dir: Directory to save screenshots
        """
        # Convert mito_id to uint64 for CloudVolume
        mito_id = np.uint64(mito_id)
        
        # Ensure output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Fetch mesh from CloudVolume
        mesh = self.vol.mesh.get(mito_id)
        
        # Scale vertices to nanometers
        vertices = mesh.vertices * [self.voxel_size_nm['x'], 
                                  self.voxel_size_nm['y'], 
                                  self.voxel_size_nm['z']]
        
        # Format faces for PyVista
        n_triangles = mesh.faces.shape[0]
        faces = np.empty((n_triangles, 4), dtype=np.int64)
        faces[:, 0] = 3  # Number of points per face
        faces[:, 1:] = mesh.faces
        
        # Create and setup the PyVista plotter
        pv.set_plot_theme('document')
        plotter = pv.Plotter(off_screen=True, window_size=self.img_size)
        
        # Create the mesh and add to scene
        pvmesh = pv.PolyData(vertices, faces)
        plotter.add_mesh(pvmesh, color='red', opacity=0.8)
        
        # Set up camera
        plotter.camera.enable_parallel_projection()
        
        # Take screenshots from different angles
        views = {
            '0': 'xy',   # top view
            '1': 'xz',   # front view
            '2': 'yz'    # side view
        }
        
        for view_id, camera_pos in views.items():
            # Set camera position for this view
            plotter.camera_position = camera_pos
            plotter.reset_camera()
            
            # Save screenshot
            output_file = output_dir / f"{view_id}.png"
            plotter.screenshot(str(output_file))
    
    def generate_all_screenshots(self, materialization, output_dir):
        """Generate screenshots for all mitochondria in the materialization.
        
        Args:
            materialization: MitochondriaMaterialization instance
            output_dir (str): Directory to save screenshots
        """
        success_count = 0
        fail_count = 0
        
        for _, row in materialization.df.iterrows():
            bounds = {
                'min_x': float(row['min_x']),
                'max_x': float(row['max_x']),
                'min_y': float(row['min_y']),
                'max_y': float(row['max_y']),
                'min_z': float(row['min_z']),
                'max_z': float(row['max_z'])
            }
            
            success = self.generate_screenshots(
                row['segment_id'],
                bounds,
                output_dir
            )
            
            if success:
                success_count += 1
                print(f"Successfully generated screenshots for mito {row['segment_id']}")
            else:
                fail_count += 1
                print(f"Failed to generate screenshots for mito {row['segment_id']}")
                
        print(f"\nFinal results:")
        print(f"Successes: {success_count}")
        print(f"Failures: {fail_count}")
        return success_count, fail_count 