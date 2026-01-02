import atexit
import os
import glob
import time
import subprocess
import sys

APP_PATH = "/Applications/DaVinci Resolve/DaVinci Resolve.app"
BIN_PATH = "/Contents/MacOS/Resolve"


def check_davinci_installation():
    if not os.path.exists(APP_PATH):
        print(f"ERROR: DaVinci Resolve not found at {APP_PATH}")
        sys.exit(1)


def get_video_paths():
    input_dir = os.path.abspath('./input_data')
    
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory not found: {input_dir}")
        sys.exit(1)
    
    MAX_BYTES = 50 * 1024 * 1024    # 50 MB
    video_paths = []
    
    for path in glob.glob(f'{input_dir}/*.mov'):
        if os.path.getsize(path) <= MAX_BYTES:
            video_paths.append(path)

    if not video_paths:
        print(f"ERROR: No videos under 50 MB found in {input_dir}")
        sys.exit(1)
    
    print(f"Found {len(video_paths)} video(s) to process")
    return video_paths



def start_davinci():
    if '--headless' in sys.argv:
        print("Starting headless mode")
        process = subprocess.Popen([APP_PATH + BIN_PATH, "-nogui"])
        atexit.register(process.terminate)
        return process

    print("Starting DaVinci Resolve")
    os.system(f'open "{APP_PATH}"')
    return None


def wait_for_render(proj, job_id):
    while True:
        st = proj.render_status(job_id)
        status = st.get("JobStatus")
        
        if status == "Complete":
            print("Render finished")
            return True
        elif status == "Failed":
            print("ERROR: Render failed")
            return False
        
        time.sleep(1)


def get_unique_project_name(base_name, existing_projects):
    project_name = base_name
    suffix = 0
    while project_name in existing_projects:
        suffix += 1
        project_name = f"{base_name}_{suffix}"
    return project_name


def check_available_presets(project):
    presets = project.render_presets
    print("\nAvailable Render Presets")
    for preset in presets:
        print(f"  - {preset}")
    print("=" * 35 + "\n")


def process_video(video_path, manager, existing_projects, out_dir):
    start_time = time.time()
    
    # Get filename without extension
    basename = os.path.basename(video_path)
    filename = os.path.splitext(basename)[0]
    
    print(f'\nProcessing: {filename}')
    
    # Create unique project name
    base_project_name = f"{filename}_IMF"
    project_name = get_unique_project_name(base_project_name, existing_projects)
    
    # Create project
    project = manager.create_project(project_name)
    print(f'Created project: {project_name}')
    
    # Import video
    items = project.mediapool.import_media([video_path])
    project.mediapool.create_timeline_from_clips("timeline", items)
    print(f'Created timeline')
    
    # Setup output folder
    output_folder = os.path.join(out_dir, project_name)
    os.makedirs(output_folder, exist_ok=True)
    
    # Load IMF preset and configure render settings
    project.load_render_preset("IMF - Netflix")
    render_settings = {
        "SelectAllFrames": True,
        "TargetDir": output_folder,
        "CustomName": filename,
        "ExportVideo": True,
        "ExportAudio": True,
    }
    project.set_render_settings(render_settings)
    job_id = project.add_renderjob()
    print(f'Starting render to: {output_folder}')
    project.render()
    
    # Wait for completion
    wait_for_render(project, job_id)
    
    # Calculate and print execution time
    elapsed_time = time.time() - start_time
    print(f"Processed {filename} in {elapsed_time:.2f} seconds")
    
    # Close project
    project.close()

def main():
    # Check installation and get videos
    check_davinci_installation()
    video_paths = get_video_paths()
    
    # Create output directory
    out_dir = os.path.abspath('./out')
    os.makedirs(out_dir, exist_ok=True)
    
    # Start DaVinci Resolve
    proccess = start_davinci()
    print("Waiting for DaVinci Resolve to start...")
    time.sleep(7)
    
    # Connect to Resolve
    from pydavinci import davinci
    resolve = davinci.Resolve()
    manager = resolve.project_manager
    existing_projects = manager.projects
    
    # Process each video
    for video_path in video_paths:
        process_video(video_path, manager, existing_projects, out_dir)
    
    print("Done")
    resolve.quit()

if __name__ == '__main__':
    main()
