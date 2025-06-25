#!/usr/bin/env python3
"""
Screenshot one mitochondrion mesh (segment_id == 2) from the H01 dataset.

• Expects a CSV like 36750893213_mito_materialization.csv
• Outputs screenshots/2/0.png in the project directory
"""

# ─── 0.  pip install requirements ───────────────────────────────────────────────────
# pip install cloud-volume pillow pandas numpy pyvista

# ─── 1.  Imports & constants ───────────────────────────────────────────────────────
from pathlib import Path
import pandas as pd
import sys
import traceback
import os
import numpy as np
import time
from cloudvolume import CloudVolume
import pyvista as pv

print("Starting script...")

CSV_FILE  = Path("/Users/ajmcginty/Downloads/36750893213_mito_materialization.csv")
MITO_SRC  = "https://rhoana.rc.fas.harvard.edu/ng/h01_mito/36750893213"  # Remove precomputed:// for CloudVolume
TARGET_ID = np.uint64(10)  # Convert to uint64
OUT_PNG = Path("unc_mito/static/screenshots") / str(TARGET_ID) / "0.png"

VOXEL_SIZE_NM = dict(x=8.0, y=8.0, z=33.0)   # 8×8×33 nm for H01
IMG_SIZE = [1024, 1024]      # screenshot resolution in pixels

try:
    # Create output directories if they don't exist
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nCreated output directory: {OUT_PNG.parent}")

    # ─── 2.  Load CSV & compute centre voxel coord ─────────────────────────────────────
    print(f"\nReading CSV file: {CSV_FILE}")
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")
        
    df = pd.read_csv(CSV_FILE)
    print(f"Found {len(df)} rows in CSV")
    
    row = df.loc[df["segment_id"] == int(TARGET_ID)]
    if row.empty:
        raise ValueError(f"segment_id {TARGET_ID} not found in {CSV_FILE.name}")
    
    print(f"\nFound mito {TARGET_ID} data:")
    print(row.to_dict('records')[0])

    # ─── 3.  Fetch mesh using CloudVolume ─────────────────────────────────────────────
    print("\nConnecting to CloudVolume...")
    vol = CloudVolume(MITO_SRC, use_https=True)
    
    print(f"Fetching mesh for segment {TARGET_ID}...")
    mesh = vol.mesh.get(TARGET_ID)  # Get the mesh object
    
    # ─── 4.  Render with PyVista ─────────────────────────────────────────────────────
    print("\nCreating PyVista mesh...")
    vertices = mesh.vertices * [VOXEL_SIZE_NM['x'], VOXEL_SIZE_NM['y'], VOXEL_SIZE_NM['z']]  # Scale to nm
    
    # Debug print mesh information
    print(f"Mesh info:")
    print(f"  Vertices shape: {mesh.vertices.shape}")
    print(f"  Faces shape: {mesh.faces.shape}")
    print(f"  First few faces: {mesh.faces[:9]}")
    
    # Correctly format faces for PyVista
    n_triangles = mesh.faces.shape[0]  # Number of triangles is the first dimension of faces
    faces = np.empty((n_triangles, 4), dtype=np.int64)
    faces[:, 0] = 3  # Number of points per face
    faces[:, 1:] = mesh.faces  # Faces are already in the correct shape
    
    print(f"  Processed faces shape: {faces.shape}")
    print(f"  First few processed faces: {faces[:3]}")
    
    # Create and setup the PyVista plotter
    print("Setting up PyVista renderer...")
    pv.set_plot_theme('document')
    plotter = pv.Plotter(off_screen=True, window_size=IMG_SIZE)
    
    # Add the mesh to the scene
    pvmesh = pv.PolyData(vertices, faces)
    plotter.add_mesh(pvmesh, color='red', opacity=0.8)
    
    # Center camera on mesh and set parallel projection
    plotter.camera.enable_parallel_projection()
    plotter.camera_position = 'xy'
    plotter.reset_camera()
    
    # Take screenshot
    print("Taking screenshot...")
    plotter.screenshot(str(OUT_PNG))
    
    print(f"\n✅  Successfully wrote {OUT_PNG.resolve()}")

except Exception as e:
    print(f"\n❌  Error: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
