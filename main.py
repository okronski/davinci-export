import os
import glob
import time
import subprocess
import sys

path = "/Applications/DaVinci Resolve/DaVinci Resolve.app"
bin = "/Contents/MacOS/Resolve"

print('hi')
print("\n".join(sys.argv))

video_dir = os.path.abspath('./input_data')
video_paths = glob.glob(f'{video_dir}/*.mov')
if not video_paths:
    print("no videos found at the root of ./input_data")
    exit()

if len(sys.argv) > 1 and sys.argv[1] == '--headless':
    print("Starting headless")
    subprocess.Popen([path + bin, "-nogui"])
else:
    os.system(f'open {path}')

print('waiting')
time.sleep(7)

from pydavinci import davinci
print('starting')
resolve = davinci.Resolve()
manager = resolve.project_manager

names = manager.projects
basename = "film_"
suffix = 0
project_name = basename + str(suffix)

while project_name in names:
    suffix = suffix + 1
    project_name = basename + str(suffix)

project = manager.create_project(project_name)
print(f'Created project with name: {project_name}')


items = project.mediapool.import_media(video_paths)
project.mediapool.create_timeline_from_clips("timeline", items)
print(f'Created timeline')

out_dir = os.path.abspath('./out')

# print(project.render_presets)
project.load_render_preset("YouTube - 1080p")
render_settings = {
    "SelectAllFrames": True,
    "TargetDir": out_dir,
    "CustomName": project_name,
    "ExportVideo": True,
    "ExportAudio": True,
}
project.set_render_settings(render_settings)
project.add_renderjob()
print(f'Starting render...')
print(f'Saving to: ./out/{project_name}.mp4')
project.render()

# TODO: check for render status and report if done