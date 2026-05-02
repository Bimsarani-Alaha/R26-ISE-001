import os
from xml.dom import minidom

# CONFIG
EXPECTED_KPTS = 17
out_dir = './out'

if not os.path.exists(out_dir):

    os.makedirs(out_dir)

file = minidom.parse('Anno150.xml')
images = file.getElementsByTagName('image')

for image in images:

    width = int(image.getAttribute('width'))
    height = int(image.getAttribute('height'))
    name = image.getAttribute('name')

    elem = image.getElementsByTagName('points')
    bbox = image.getElementsByTagName('box')[0]

    xtl = float(bbox.getAttribute('xtl'))
    ytl = float(bbox.getAttribute('ytl'))
    xbr = float(bbox.getAttribute('xbr'))
    ybr = float(bbox.getAttribute('ybr'))

    w = xbr - xtl
    h = ybr - ytl

    label_path = os.path.join(out_dir, name[:-4] + '.txt')

    with open(label_path, 'w') as label_file:

        for e in elem:

            # ✅ Write class + bbox
            label_file.write(
                f"0 {(xtl + w/2)/width} {(ytl + h/2)/height} {w/width} {h/height} "
            )

            # ✅ Read points safely
            raw_points = e.getAttribute('points').strip()

            if raw_points == "":
                points = []
            else:
                points = [p for p in raw_points.split(';') if p.strip() != ""]

            # ✅ Ensure EXACTLY 17 keypoints
            if len(points) < EXPECTED_KPTS:
                points += ["0,0"] * (EXPECTED_KPTS - len(points))
            elif len(points) > EXPECTED_KPTS:
                points = points[:EXPECTED_KPTS]

            # ✅ Write keypoints (x, y, visibility)
            for i, p in enumerate(points):
                try:
                    x_str, y_str = p.split(',')
                    x_raw = float(x_str)
                    y_raw = float(y_str)
                except:
                    x_raw, y_raw = 0.0, 0.0

                # Normalize
                x = x_raw / width
                y = y_raw / height

                # Visibility
                v = 0 if (x_raw == 0 and y_raw == 0) else 2

                label_file.write(f"{x} {y} {v}")

                if i < EXPECTED_KPTS - 1:
                    label_file.write(' ')
                else:
                    label_file.write('\n')