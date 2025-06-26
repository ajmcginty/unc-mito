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
        
        # Initialize CloudVolume
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
        
        # Add visualization elements
        plotter.add_axes()
        plotter.add_bounding_box(color='gray', opacity=0.3)
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
        
        # Add center point marker
        center = np.array([pvmesh.center])
        plotter.add_points(center, color='blue', point_size=20, render_points_as_spheres=True)
        
        # Add a shadow plane for better depth perception
        bounds = pvmesh.bounds
        grid = pv.Plane(
            center=(center[0][0], center[0][1], bounds[4] - 100),
            direction=(0, 0, 1),
            i_size=(bounds[1] - bounds[0]) * 1.5,
            j_size=(bounds[3] - bounds[2]) * 1.5
        )
        plotter.add_mesh(grid, color='lightgray', opacity=0.3)
        
        # Set up camera
        plotter.camera.enable_parallel_projection()
        plotter.camera_position = 'xy'
        plotter.reset_camera()
        
        return plotter, pvmesh

    def generate_screenshots(self, mito_id, output_dir, debug=False):
        """Generate 360-degree screenshots for a mitochondrion.
        
        Args:
            mito_id: ID of the mitochondrion
            output_dir: Directory to save screenshots
            debug (bool): Whether to print debug information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert mito_id to uint64 for CloudVolume
            mito_id = np.uint64(mito_id)
            
            # Ensure output directory exists
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Fetch and process mesh
            mesh = self.vol.mesh.get(mito_id)
            vertices = mesh.vertices * [self.VOXEL_SIZE_NM['x'], 
                                      self.VOXEL_SIZE_NM['y'], 
                                      self.VOXEL_SIZE_NM['z']]
            
            if debug:
                self.print_mesh_stats(mesh, vertices)
            
            # Setup visualization
            plotter, _ = self.setup_plotter(mesh, vertices)
            
            if debug:
                print("\nInitial camera setup:")
                self.print_camera_info(plotter)
            
            # Generate screenshots at specified angles
            angles = range(0, 360, self.step_deg)
            
            for angle in angles:
                plotter.camera.azimuth = angle
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
    try:
        # Get the project root directory (2 levels up from this script)
        project_root = Path(__file__).parent.parent.parent
        
        # Configuration with absolute paths
        csv_file = project_root / "data" / "36750893213_mito_materialization.csv"
        mito_src = "https://rhoana.rc.fas.harvard.edu/ng/h01_mito/36750893213"
        target_id = 115
        output_dir = project_root / "unc_mito" / "static" / "screenshots" / str(target_id)
        
        print(f"Using CSV file: {csv_file}")
        print(f"Output directory: {output_dir}")
        
        # Validate inputs
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
            
        df = pd.read_csv(csv_file)
        if target_id not in df["segment_id"].values:
            raise ValueError(f"segment_id {target_id} not found in {csv_file.name}")
        
        # Generate screenshots
        generator = ScreenshotGenerator360(mito_src, step_deg=30)
        success = generator.generate_screenshots(target_id, output_dir, debug=True)
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
