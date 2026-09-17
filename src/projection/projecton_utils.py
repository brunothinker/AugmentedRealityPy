import os
import struct
import numpy as np
import shutil


"""COLMAP BINARY READING UTILITIES"""


def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character="<"):
    """Reads bytes from the binary file and unpacks them according to the format."""
    data = fid.read(num_bytes)
    return struct.unpack(endian_character + format_char_sequence, data)


def read_cameras_binary(path_to_model_file):
    """Reads the COLMAP cameras.bin file adjusted for the exact byte layout."""
    # Mapping of COLMAP IDs to the number of parameters
    CAMERA_MODEL_NUM_PARAMS = {
        0: 3, 1: 4, 2: 4, 3: 5, 4: 8, 5: 8, 6: 12, 7: 5, 8: 12, 9: 4, 10: 5
    }

    cameras = {}
    with open(path_to_model_file, "rb") as fid:
        num_cameras = read_next_bytes(fid, 8, "Q")[0]
        for _ in range(num_cameras):
            # Official layout: camera_id (int32), model_id (int32), width (uint64), height (uint64)
            camera_properties = read_next_bytes(fid, 24, "iiQQ")
            camera_id = camera_properties[0]
            model_id = camera_properties[1]
            width = camera_properties[2]
            height = camera_properties[3]

            num_params = CAMERA_MODEL_NUM_PARAMS.get(model_id, 4)
            params = read_next_bytes(fid, 8 * num_params, "d" * num_params)

            cameras[camera_id] = {
                "id": camera_id,
                "model_id": model_id,
                "width": width,
                "height": height,
                "params": np.array(params)
            }
    return cameras


def qvec2rotmat(qvec):
    """Converts Quaternion (qw, qx, qy, qz) to a 3x3 Rotation Matrix."""
    qw, qx, qy, qz = qvec
    return np.array([
        [1 - 2 * qy ** 2 - 2 * qz ** 2, 2 * qx * qy - 2 * qz * qw, 2 * qx * qz + 2 * qy * qw],
        [2 * qx * qy + 2 * qz * qw, 1 - 2 * qx ** 2 - 2 * qz ** 2, 2 * qy * qz - 2 * qx * qw],
        [2 * qx * qz - 2 * qy * qw, 2 * qy * qz + 2 * qx * qw, 1 - 2 * qx ** 2 - 2 * qy ** 2]
    ])


def read_images_binary(path_to_model_file):
    """Reads the images.bin file with safe string deserialization."""
    images = {}
    with open(path_to_model_file, "rb") as fid:
        num_images = read_next_bytes(fid, 8, "Q")[0]
        for _ in range(num_images):
            binary_image_properties = read_next_bytes(fid, 64, "idddddddi")
            image_id = binary_image_properties[0]
            qvec = np.array(binary_image_properties[1:5])
            tvec = np.array(binary_image_properties[5:8])
            camera_id = binary_image_properties[8]

            # Reads image name ending with the null byte (\x00)
            image_name_bytes = bytearray()
            while True:
                char = fid.read(1)
                if char == b"\x00" or not char:
                    break
                image_name_bytes.extend(char)
            image_name = image_name_bytes.decode("utf-8")

            # Skips 2D points (8 bytes uint64 + N * 24 bytes)
            num_points2D = read_next_bytes(fid, 8, "Q")[0]
            fid.seek(24 * num_points2D, 1)

            images[image_id] = {
                "id": image_id,
                "qvec": qvec,
                "tvec": tvec,
                "camera_id": camera_id,
                "name": image_name,
                "R": qvec2rotmat(qvec)
            }
    return images


def organize_output_by_camera(output_dir):
    """
    Scans the output folder and moves the rendered files to subfolders
    according to the camera identifier at the end of the name (_1x or _uw).
    """
    print("\nOrganizing rendered images into folders by camera...")

    # Lists all generated files in the output folder
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)

        # Ensures it is a projected image file
        if os.path.isfile(file_path) and filename.startswith("synth_"):
            # Extracts the camera identifier (e.g., '1x' or 'uw' before the extension)
            name_without_ext = os.path.splitext(filename)[0]

            if name_without_ext.endswith("_1x"):
                cam_folder = "camera_1x"
            elif name_without_ext.endswith("_uw"):
                cam_folder = "camera_uw"
            else:
                cam_folder = "camera_others"

            # Creates the specific target directory for the camera
            target_dir = os.path.join(output_dir, cam_folder)
            os.makedirs(target_dir, exist_ok=True)

            # Moves the file to the subfolder
            shutil.move(file_path, os.path.join(target_dir, filename))

    print(" [✓] Images successfully separated into subfolders!")