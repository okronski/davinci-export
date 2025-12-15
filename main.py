import os
import glob
import time

print('hi')

path = "/Applications/DaVinci Resolve/DaVinci Resolve.app"
os.system(f'open "{path}"')
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

video_dir = os.path.abspath('./videos')
video_paths = glob.glob(f'{video_dir}/*.mp4')
if video_paths is None:
    print("no videos found in ./videos")
    exit()
items = project.mediapool.import_media(video_paths)
project.mediapool.create_timeline_from_clips("timeline", items)

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
project.render()