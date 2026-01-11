import atexit
import os
import glob
import time
import subprocess
import sys

#Konstanten
APP_PATH = "/Applications/DaVinci Resolve/DaVinci Resolve.app"
BIN_PATH = "/Contents/MacOS/Resolve"


def check_davinci_installation():
    # Prüfung, ob Pfad existiert
    if not os.path.exists(APP_PATH):
        print(f"ERROR: DaVinci Resolve not found at {APP_PATH}")
        # Exit code 1, weil Programm ohne Erfolg geschlossen
        sys.exit(1)


def get_video_paths():
    # Speichert absoluten Pfad von Input Ordner
    input_dir = os.path.abspath('./input_data')
    
    # Wenn Input Ordner nicht existiert, schließt Programm
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Konstante
    MAX_BYTES = 50 * 1024 * 1024    # 50 MB

    # Leere Liste für valide Pfade zu den einzelnen Videos
    video_paths = []
    
    # Prüft anhand von Glob Muster nach Mov Dateien im Input Ordner und speichert Liste
    all_mov_paths = glob.glob(f'{input_dir}/*.mov')

    for path in all_mov_paths:
        # Prüft Dateigröße
        if os.path.getsize(path) <= MAX_BYTES:
            # Fügt Pfad zur video_paths Liste an
            video_paths.append(path)

    # Prüft ob video_paths Liste leer ist und beendet Programm
    if not video_paths:
        print(f"ERROR: No videos under 50 MB found in {input_dir}")
        sys.exit(1)
    
    print(f"Found {len(video_paths)} video(s) to process")
    # Gibt Liste zurück (an Main wo die Funktion aufgerufen wurde)
    return video_paths


def start_davinci():
    # Prüft ob Headless Flag in den Argumenten
    if '--headless' in sys.argv:
        print("Starting headless mode")
        
        # Starten Subprozess mit den Pfad zur binary und fügen nogui Flag an 
        process = subprocess.Popen([APP_PATH + BIN_PATH, "-nogui"])
        # Wenn Script beendet wird, beende Subprozess
        atexit.register(process.terminate)
        
    else:
        print("Starting DaVinci Resolve")
        os.system(f'open "{APP_PATH}"')


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

# Testet ob es Projektnamen in Existing_projects gibt, setzt ansonssonstten hinten Nummer dran und prüft erneut
def get_unique_project_name(base_name, existing_projects):
    project_name = base_name
    suffix = 0
    while project_name in existing_projects:
        suffix += 1
        project_name = f"{base_name}_{suffix}"
# Gibt einzigartigen Namen wieder zurück
    return project_name


def process_video(video_path, manager, existing_projects, out_dir):
    start_time = time.time()
    
    # Nimmt Basename, splitet den und nimmt nur den ersten Teil des Names (also ohne Dateiendung)
    basename = os.path.basename(video_path)
    filename = os.path.splitext(basename)[0]
    
    print(f'\nProcessing: {filename}')
    
    base_project_name = f"{filename}_IMF"
    # Einzigartigen Namen generieren und übergibt Variablen
    project_name = get_unique_project_name(base_project_name, existing_projects)
    
    # Legt Projekt mit eben generierten Namen an
    project = manager.create_project(project_name)
    print(f'Created project: {project_name}')
    
    # Importiert Videos und erstellt daraus eine Timeline
    items = project.mediapool.import_media([video_path])
    project.mediapool.create_timeline_from_clips("timeline", items)
    print(f'Created timeline')
    
    # Setzt Output Unterorder mit Projektnamen auf und wenn es ihn schon gibt, ist okay
    output_folder = os.path.join(out_dir, project_name)
    os.makedirs(output_folder, exist_ok=True)
    
    # Läd IMF Preset und erstellt Render Settings
    project.load_render_preset("IMF - Netflix")
    render_settings = {
        "SelectAllFrames": True,
        "TargetDir": output_folder,
        "CustomName": filename,
        "ExportVideo": True,
        "ExportAudio": True,
    }
    #Setzt Rendersettings
    project.set_render_settings(render_settings)
    #Fügt Render Job hinzu
    job_id = project.add_renderjob()
    print(f'Starting render to: {output_folder}')
    #Rendert
    project.render()
    
    # Wartet bis fertig gerendert
    wait_for_render(project, job_id)
    
    # Berechnet die Verarbeitungszeit und gibt sie wieder
    elapsed_time = time.time() - start_time
    print(f"Processed {filename} in {elapsed_time:.2f} seconds")
    
    # Projekt Schließen
    project.close()

def main():
    # Checke installation und hole die Videos
    check_davinci_installation()
    video_paths = get_video_paths()
    
    
    out_dir = os.path.abspath('./out')
    # Erstelle Output Ordner und wenn es ihn schon gibt, ist okay
    os.makedirs(out_dir, exist_ok=True)
    
    # Starte DaVinci Resolve
    start_davinci()
    print("Waiting for DaVinci Resolve to start...")
    time.sleep(7)
    
    from pydavinci import davinci
    #Stellt Verbindung zu Davinci her
    resolve = davinci.Resolve()
    manager = resolve.project_manager
    existing_projects = manager.projects
    
    # Verarbeite jedes Video und gibt Variablen an Funktion
    for video_path in video_paths:
        process_video(video_path, manager, existing_projects, out_dir)
    
    print("Done")
    resolve.quit()

if __name__ == '__main__':
    main()
