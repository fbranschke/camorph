import copy

import numpy as np
import os
import warnings
from camorph.lib.model.Camera import Camera
from camorph.lib.model.FileHandler import FileHandler
from camorph.lib.utils import math_utils
from pyquaternion import Quaternion


class LLFF(FileHandler):
    def __init__(self):
        pass

    def crucial_properties(self) -> list[(str, type)]:
        return ['focal_length_px', 'resolution', 'near_far_bounds']

    def name(self):
        return "llff"

    def file_number(self):
        return 1

    def read_file(self, input_path: str, **kwargs):
        data = np.load(input_path)
        cams = []

        for c in data:
            cam = Camera()
            cam.focal_length_px = [c[14],c[14]]
            cam.resolution = [c[9],c[4]]
            c_mat = c[:-2].reshape([3,5])[:,:-1]
            t = c_mat[:,-1]
            rm = c_mat[:,:-1]
            s = [np.linalg.norm(rm[:,x]) for x in range(0,3)]
            rm = np.asarray([[rm[0,0]/s[0],rm[0,1]/s[1],rm[0,2]/s[2]],
                  [rm[1,0]/s[0],rm[1,1]/s[1],rm[1,2]/s[2]],
                  [rm[2,0]/s[0],rm[2,1]/s[1],rm[2,2]/s[2]]])
            cam.t = t
            cam.r = math_utils.rotation_matrix_to_quaternion(rm)
            cam.near_far_bounds = [c[15],c[16]]
            cams.append(cam)
        return self.coordinate_from(cams)

    def write_file(self, camera_array: list[Camera], output_path: str, file_type=None):
        cams = self.coordinate_into(camera_array)
        warnings.warn("LLFF relies on sorted image order. Cameras will be sorted after images when writing LLFF")
        cams = sorted(cams, key=lambda x : (os.path.basename(x.source_image),x.source_image))
        data = []
        for c in cams:
            r = c.r.rotation_matrix.copy()
            r = np.append(r,c.t[...,None],axis=1)
            r = np.append(r,[[c.resolution[1]],[c.resolution[0]],[c.focal_length_px[0]]],axis=1)
            r = np.append(r,c.near_far_bounds)
            data.append(r)
        data = np.asarray(data, dtype='float64')
        np.save(output_path,data)


    def coordinate_into(self, camera_array: list[Camera]):
        cam_arr = copy.deepcopy(camera_array)
        for cam in cam_arr:
            cam.t, cam.r = math_utils.convert_coordinate_systems(['-x', '-z', 'y'], cam.t, cam.r, cdir=[0, 0, -1],
                                                                 cup=[-1, 0, 0],transpose=True)
        return cam_arr

    def coordinate_from(self, camera_array: list[Camera]):
        cam_arr = copy.deepcopy(camera_array)
        for cam in cam_arr:
            cam.t, cam.r = math_utils.convert_coordinate_systems(['-x', '-z', 'y'], cam.t, cam.r, cdir=[0, 0, -1],
                                                                 cup=[-1, 0, 0])
        return cam_arr
