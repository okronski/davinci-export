import atexit
import os
import glob
import time
import subprocess
import sys


APP_PATH = "/Applications/DaVinci Resolve/DaVinci Resolve.app"
BIN_PATH = "/Contents/MacOS/Resolve"


def check_davinci_installation():
    """
    Überprüft, ob DaVinci Resolve am angegebenen Anwendungspfad installiert ist.

    Die Funktion prüft, ob der definierte Anwendungspfad existiert.
    Falls DaVinci Resolve nicht gefunden wird, wird eine Fehlermeldung
    ausgegeben und das Programm beendet.

    Args:
        None

    Returns:
        None
    """
    if not os.path.exists(APP_PATH):
        print(f"ERROR: DaVinci Resolve not found at {APP_PATH}")
        # Exit code 1, ohne Erfolg geschlossen
        sys.exit(1)


def get_video_paths():
    """
    Speichert Pfade und filtert diese nach .mov und <= 50 MB

    Erst wird der absolute Pfad des Inputordners gespeichert.
    Und überprueft ob etwas in diesem Ordner existiert.
    Dann wird gefiltert nach .mov datein und nach der Maximalgröße.
    Am Ende werden alle validen Dateien an die Main Function zurückgegeben.

    Args:
        None

    Returns:
        list[str]:
            Liste mit absoluten Dateipfaden zu allen gültigen .mov-Dateien
            im Input-Ordner, deren Dateigröße kleiner oder gleich 50 MB ist.
    """
    # Speichert Pfad von Input Ordner
    input_dir = os.path.abspath('./input_data')
    
    # Wenn Input Ordner nicht existiert, schließt Programm
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory not found: {input_dir}")
        sys.exit(1)
    
    
    MAX_BYTES = 50 * 1024 * 1024    # 50 MB

    video_paths = []
    
    # Prüft anhand von Glob Muster nach Mov Dateien im Input Ordner und speichert Liste
    all_mov_paths = glob.glob(f'{input_dir}/*.mov')

    for path in all_mov_paths:
        if os.path.getsize(path) <= MAX_BYTES:
            # Fügt Pfad zur video_paths Liste an
            video_paths.append(path)

    # Prüft ob video_paths Liste leer
    if not video_paths:
        print(f"ERROR: No videos under 50 MB found in {input_dir}")
        sys.exit(1)
    
    print(f"Found {len(video_paths)} video(s) to process")
    # Gibt Liste zurück (an Main wo die Funktion aufgerufen wurde)
    return video_paths


def start_davinci():
    """
    Startet DaVinci Resolve abhängig von der übergebenen Flag.

    Wird das Script mit dem Argument '--headless' gestartet, wird DaVinci Resolve
    ohne grafische Benutzeroberfläche ausgeführt.
    Dazu wird ein Subprozess mit dem entsprechenden Binary-Pfad und dem '-nogui'-Flag gestartet.
    Beim Beenden des Scripts wird der Subprozess automatisch terminiert.

    Wird das Argument '--headless' nicht übergeben, wird DaVinci Resolve regulär
    mit grafischer Oberfläche gestartet.

    Args:
        None

    Returns:
        None
    """
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
    """
    Wartet, bis der Renderprozess abgeschlossen oder fehlgeschlagen ist.

    Die Funktion fragt in regelmäßigen Abständen den
    Status des angegebenen Render-Jobs über das Projektobjekt ab.
    Sobald der Status "Complete" erreicht ist, wird der Render
    als erfolgreich abgeschlossen betrachtet.
    Tritt der Status "Failed" auf, wird der Render als fehlgeschlagen
    gewertet.

    Args:
        proj:
            Projektobjekt, das Zugriff auf den Render-Status bietet
            (z. B. ein DaVinci-Resolve-Projekt).

        job_id:
            Eindeutige Kennung des Render-Jobs, dessen Status
            überwacht werden soll.

    Returns:
        bool:
            True, wenn der Render erfolgreich abgeschlossen wurde.
            False, wenn der Render fehlgeschlagen ist.
    """
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
    """
    Erzeugt einen eindeutigen Projektnamen.

    Falls der Basisname bereits in der Liste vorhandener Projekte
    existiert, wird schrittweise ein numerischer Suffix angehängt, 
    bis ein eindeutiger Name gefunden ist.

    Args:
        base_name (str):
            Basisname des Projekts, als Ausgangspunkt für die Generierung.

        existing_projects (list[str]):
            Liste mit Namen bereits existierender Projekte, gegen
            die der neue Projektname geprüft wird.

    Returns:
        str:
            Ein eindeutiger Projektname, der noch nicht in der Liste
            der existierenden Projekte enthalten ist.
    """
    project_name = base_name
    suffix = 0
    while project_name in existing_projects:
        suffix += 1
        project_name = f"{base_name}_{suffix}"
    # Gibt einzigartigen Namen wieder zurück
    return project_name


def process_video(video_path, manager, existing_projects, out_dir):
    """
    Verarbeitet ein einzelnes Video in DaVinci Resolve
    und rendert es mithilfe eines vordefinierten IMF-Presets.

    Die Funktion erstellt auf Basis des Videonamens ein neues Projekt,
    importiert das Video in den Media Pool und erzeugt daraus eine
    Timeline.
    Anschließend wird ein projektspezifischer Output-Ordner angelegt,
    die Render-Einstellungen geladen und ein Render-Job gestartet.
    Während des Renderprozesses wartet die Funktion auf dessen
    Abschluss, misst die gesamte Verarbeitungsdauer und schließt
    danach das Projekt.

    Args:
        video_path (str):
            Absoluter Pfad zur Videodatei, die verarbeitet und
            gerendert werden soll.

        manager:
            Projektmanager-Objekt von DaVinci Resolve, das zum
            Erstellen und Verwalten von Projekten verwendet wird.

        existing_projects (list[str]):
            Liste mit Namen bereits existierender Projekte, um
            eindeutige Projektnamen zu generieren.

        out_dir (str):
            Pfad zum übergeordneten Ausgabeordner, in dem für jedes
            Projekt ein eigener Unterordner angelegt wird.

    Returns:
        None
    """
    start_time = time.time()
    # Splitet Namen und nimmt nur den ersten Teil des Names
    basename = os.path.basename(video_path)
    filename = os.path.splitext(basename)[0]
    
    print(f'\nProcessing: {filename}')
    
    base_project_name = f"{filename}_Film"
    # Übergibt Variablen
    project_name = get_unique_project_name(base_project_name, existing_projects)
    
    # Legt Projekt an
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
        "Codec"
        "SelectAllFrames": True,
        "TargetDir": output_folder,
        "CustomName": filename,
        "ExportVideo": True,
        "ExportAudio": True,
    }
    
    print(project.render_presets)

    project.set_render_settings(render_settings)

    project.set_render_format_and_codec("imf","Kakadu")

    #Fügt Render Job hinzu
    job_id = project.add_renderjob()
    print(f'Starting render to: {output_folder}')
    
    project.render()
    
    wait_for_render(project, job_id)
    # Berechnet die Verarbeitungszeit
    elapsed_time = time.time() - start_time
    print(f"Processed {filename} in {elapsed_time:.2f} seconds")
    
    project.close()

def main():
    """
    Steuert den gesamten Ablauf der automatisierten Videoverarbeitung
    in DaVinci Resolve.

    Die Funktion überprüft zunächst, ob DaVinci Resolve installiert ist
    und liest alle gültigen Videodateien aus dem Input-Ordner ein.
    Anschließend wird der Output-Ordner erstellt und DaVinci Resolve
    gestartet.
    Nach dem Aufbau der Verbindung zur DaVinci-Resolve-API werden alle
    Videos nacheinander verarbeitet und gerendert.
    Zum Abschluss wird DaVinci Resolve ordnungsgemäß beendet.

    Args:
        None

    Returns:
        None
    """
    check_davinci_installation()
    video_paths = get_video_paths()
    
    out_dir = os.path.abspath('./out')
    # Erstelle Output Ordner und wenn es ihn schon gibt, ist okay
    os.makedirs(out_dir, exist_ok=True)
    
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

    #Ausgeführt, wenn das Skript direkt gestartet wird
if __name__ == '__main__':
    main()
