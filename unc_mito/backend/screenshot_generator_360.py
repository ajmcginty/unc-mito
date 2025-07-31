"""
Screenshot generator for creating 360-degree views of mitochondria meshes from the H01 dataset.

Features:
• Generates screenshots at configurable angular intervals
• Enhanced 3D visualization with lighting, shadows, and depth perception
• Outputs numbered screenshots (e.g. 0.png, 45.png, etc.) in the specified directory
"""
from pathlib import Path
import pandas as pd
import sys
import traceback
import numpy as np
from cloudvolume import CloudVolume
import pyvista as pv
import argparse

class ScreenshotGenerator360:
    # Class-level constants
    VOXEL_SIZE_NM = dict(x=8.0, y=8.0, z=33.0)  # 8×8×33 nm for H01
    IMG_SIZE = [1024, 1024]  # screenshot resolution in pixels
    DEFAULT_STEP_DEG = 45  # Default angle step in degrees (8 views for web display)
    
    def __init__(self, mito_src, step_deg=None):
        """Initialize the 360-degree screenshot generator.
        
        Args:
            mito_src (str): URL to the mitochondria source
            step_deg (int, optional): Angle step in degrees. Defaults to DEFAULT_STEP_DEG
        """
        self.mito_src = mito_src
        self.step_deg = step_deg or self.DEFAULT_STEP_DEG
        self.vol = CloudVolume(self.mito_src, use_https=True)

    def print_mesh_stats(self, mesh, vertices):
        """Print detailed mesh statistics for debugging."""
        print("\n=== Mesh Statistics ===")
        print(f"Number of vertices: {len(vertices)}")
        print(f"Number of faces: {len(mesh.faces)}")
        print(f"Vertex bounds:")
        print(f"  X: {vertices[:, 0].min():.2f} to {vertices[:, 0].max():.2f}")
        print(f"  Y: {vertices[:, 1].min():.2f} to {vertices[:, 1].max():.2f}")
        print(f"  Z: {vertices[:, 2].min():.2f} to {vertices[:, 2].max():.2f}")
        print("=====================\n")

    def print_camera_info(self, plotter):
        """Print camera position and orientation information."""
        print("\n=== Camera Information ===")
        print(f"Position: {plotter.camera.position}")
        print(f"Focal Point: {plotter.camera.focal_point}")
        print(f"Up Vector: {plotter.camera.up}")
        print(f"Distance: {plotter.camera.distance}")
        print(f"Azimuth: {plotter.camera.azimuth}")
        print(f"Elevation: {plotter.camera.elevation}")
        print("=========================\n")

    def setup_plotter(self, mesh, vertices):
        """Set up the PyVista plotter with mesh and visualization settings.
        
        Args:
            mesh: CloudVolume mesh object
            vertices: Processed mesh vertices
            
        Returns:
            tuple: (plotter, pvmesh) - Configured plotter and PyVista mesh
        """
        # Format faces for PyVista
        n_triangles = mesh.faces.shape[0]
        faces = np.empty((n_triangles, 4), dtype=np.int64)
        faces[:, 0] = 3
        faces[:, 1:] = mesh.faces
        
        # Create and setup the PyVista plotter
        pv.set_plot_theme('document')
        plotter = pv.Plotter(off_screen=True, window_size=self.IMG_SIZE)
        
        # Create the mesh
        pvmesh = pv.PolyData(vertices, faces)
        
        # Add visualization elements - removed bounding box and axes
        plotter.enable_eye_dome_lighting()
        plotter.enable_depth_peeling()
        
        # Add the main mesh with enhanced visibility
        plotter.add_mesh(
            pvmesh,
            color='red',
            opacity=0.8,
            specular=1.0,
            specular_power=10,
            smooth_shading=True,
            show_edges=True,
            edge_color='black',
            line_width=2,
        )
        
        return plotter, pvmesh

    def generate_screenshots(self, mito_id, output_dir, debug=False):
        """Implementation of screenshot generation - must run on main thread"""
        try:
            # Convert mito_id to uint64 for CloudVolume
            mito_id = np.uint64(mito_id)
            
            # Ensure output directory exists
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Fetch mesh from CloudVolume
            mesh = self.vol.mesh.get(mito_id)
            
            # Keep vertices in voxel space
            vertices = mesh.vertices.copy()
            
            if debug:
                self.print_mesh_stats(mesh, vertices)
            
            # Setup visualization
            plotter, pvmesh = self.setup_plotter(mesh, vertices)
            
            # Calculate physical size
            bounds = pvmesh.bounds
            size = np.array([
                bounds[1] - bounds[0],
                bounds[3] - bounds[2],
                bounds[5] - bounds[4]
            ])
            
            # Scale size by voxel dimensions to get physical size
            physical_size = size * [self.VOXEL_SIZE_NM['x'], 
                                  self.VOXEL_SIZE_NM['y'], 
                                  self.VOXEL_SIZE_NM['z']]
            
            # Use the largest physical dimension for camera distance
            max_physical_size = np.max(physical_size)
            
            # Calculate center
            center = np.mean(vertices, axis=0)
            
            if debug:
                print("\nInitial camera setup:")
                self.print_camera_info(plotter)
            
            # Generate screenshots at specified angles
            angles = range(0, 360, self.step_deg)
            
            for angle in angles:
                # Reset camera for each angle
                plotter.camera_position = 'xy'
                plotter.reset_camera()
                
                # Set up camera
                camera = plotter.camera
                camera.enable_parallel_projection()
                
                # Calculate camera position based on physical size
                # Increased distance significantly while keeping parallel scale the same
                camera_distance = max_physical_size * 0.05  # Increased from 0.018 to 0.05
                
                # Set camera position for this angle
                theta = np.radians(angle)
                camera.position = center + np.array([
                    camera_distance * np.cos(theta),
                    camera_distance * np.sin(theta),
                    0
                ])
                camera.focal_point = center
                camera.up = [0, 0, 1]  # Keep up vector consistent
                
                # Set parallel scale based on physical size
                # Apply z/x ratio scaling to account for anisotropic voxels
                scale = self.VOXEL_SIZE_NM['z'] / self.VOXEL_SIZE_NM['x']
                # Increased scale by 50% to prevent clipping
                plotter.camera.parallel_scale = max_physical_size * 0.014 * scale  # Increased from 0.009375 to 0.014
                
                plotter.render()
                
                frame_file = output_dir / f"{angle}.png"
                plotter.screenshot(str(frame_file))
                
                if debug:
                    print(f"\nRendering angle {angle}°:")
                    self.print_camera_info(plotter)
                    print(f"Saved screenshot to {frame_file}")
            
            plotter.close()
            return True
            
        except Exception as e:
            print(f"Error generating screenshots for mito {mito_id}: {str(e)}")
            if debug:
                traceback.print_exc(file=sys.stdout)
            return False

def main():
    """Script entry point for generating screenshots of a single mitochondrion."""
    parser = argparse.ArgumentParser(description='Generate screenshots for a mitochondrion')
    parser.add_argument('--mito-id', type=str, required=True, help='ID of the mitochondrion')
    parser.add_argument('--output-dir', type=str, required=True, help='Directory to save screenshots')
    parser.add_argument('--mito-url', type=str, required=True, help='URL to the mitochondria source')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    # Convert mito_id to integer, handling float strings
    try:
        mito_id = int(float(args.mito_id))
    except ValueError:
        print(f"Error: Invalid mito ID '{args.mito_id}'. Must be a number.")
        sys.exit(1)

    try:
        # Remove precomputed:// prefix if present
        mito_src = args.mito_url.replace('precomputed://', '')
        
        # Generate screenshots
        generator = ScreenshotGenerator360(mito_src)
        success = generator.generate_screenshots(mito_id, args.output_dir, args.debug)
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()


