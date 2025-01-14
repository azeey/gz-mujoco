# Copyright (C) 2022 Open Source Robotics Foundation
#
# Licensed under the Apache License, version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module to convert MJCF geoms to SDFormat Collision/Visual geometries"""

from ignition.math import Vector2d, Vector3d

import sdformat as sdf
import sdformat_mjcf_utils.sdf_utils as su

VISUAL_NUMBER = 0
COLLISION_NUMBER = 0


def mjcf_geom_to_sdf(geom):
    """
    Converts an MJCF geom to a SDFormat geometry.

    :param mjcf.Element geom: The MJCF geom
    :return: The newly created SDFormat geometry.
    :rtype: sdf.Geometry
    """
    # TODO(ahcorde): we have to adjust the pose of the visual/collision to
    # match the longitudinal axis of the capsule/cylinder and its position
    # Related comment:
    # https://github.com/gazebosim/gz-mujoco/pull/26#discussion_r877558075
    sdf_geometry = sdf.Geometry()
    if geom.type == "box":
        box = sdf.Box()
        box.set_size(su.list_to_vec3d(geom.size) * 2)
        sdf_geometry.set_box_shape(box)
        sdf_geometry.set_type(sdf.GeometryType.BOX)
        # TODO(ahcorde): Add fromto
    elif geom.type == "capsule":
        capsule = sdf.Capsule()
        capsule.set_radius(geom.size[0])
        if geom.fromto is None:
            capsule.set_length(geom.size[1] * 2)
        else:
            v1 = Vector3d(geom.fromto[0], geom.fromto[1], geom.fromto[2])
            v2 = Vector3d(geom.fromto[3], geom.fromto[4], geom.fromto[5])
            length = v1.distance(v2)
            capsule.set_length(length)
        sdf_geometry.set_capsule_shape(capsule)
        sdf_geometry.set_type(sdf.GeometryType.CAPSULE)
    elif geom.type == "cylinder":
        cylinder = sdf.Cylinder()
        cylinder.set_radius(geom.size[0])
        if geom.fromto is None:
            cylinder.set_length(geom.size[1] * 2)
        else:
            v1 = Vector3d(geom.fromto[0], geom.fromto[1], geom.fromto[2])
            v2 = Vector3d(geom.fromto[3], geom.fromto[4], geom.fromto[5])
            length = v1.distance(v2)
            cylinder.set_length(length)
        sdf_geometry.set_cylinder_shape(cylinder)
        sdf_geometry.set_type(sdf.GeometryType.CYLINDER)
    elif geom.type == "ellipsoid":
        ellipsoid = sdf.Ellipsoid()
        ellipsoid.set_radii(su.list_to_vec3d(geom.size))
        sdf_geometry.set_ellipsoid_shape(ellipsoid)
        sdf_geometry.set_type(sdf.GeometryType.ELLIPSOID)
        # TODO(ahcorde): Add fromto
    elif geom.type == "sphere":
        sphere = sdf.Sphere()
        sphere.set_radius(geom.size[0])
        sdf_geometry.set_sphere_shape(sphere)
        sdf_geometry.set_type(sdf.GeometryType.SPHERE)
    elif geom.type == "plane":
        plane = sdf.Plane()
        plane.set_size(Vector2d(geom.size[0] * 2, geom.size[1] * 2))
        sdf_geometry.set_plane_shape(plane)
        sdf_geometry.set_type(sdf.GeometryType.PLANE)
    else:
        raise RuntimeError(
            f"Encountered unsupported shape type {geom.type}")
    return sdf_geometry


def mjcf_visual_to_sdf(geom):
    """
    Converts MJCF geom to a SDFormat visual
    MJCF geom should be part of group `VISUAL_GEOM_GROUP`.

    :param mjcf.Element geom: The MJCF geom.
    :return: The newly created SDFormat visual.
    :rtype: sdformat.Visual
    """
    visual = sdf.Visual()
    if geom.name is not None:
        visual.set_name("visual_" + geom.name)
    else:
        global VISUAL_NUMBER
        visual.set_name("unnamed_visual_" + str(VISUAL_NUMBER))
        VISUAL_NUMBER = VISUAL_NUMBER + 1
    sdf_geometry = mjcf_geom_to_sdf(geom)
    if sdf_geometry is not None:
        visual.set_geometry(sdf_geometry)
    else:
        return None
    return visual


def mjcf_collision_to_sdf(geom):
    """
    Converts MJCF geom to a SDFormat collision
    MJCF geom should be part of group `COLLISION_GEOM_GROUP`.

    :param mjcf.Element geom: The MJCF geom.
    :return: The newly created SDFormat collision.
    :rtype: sdformat.Collision
    """
    col = sdf.Collision()
    if geom.name is not None:
        col.set_name("collision_" + geom.name)
    else:
        global COLLISION_NUMBER
        col.set_name("unnamed_collision_" + str(COLLISION_NUMBER))
        COLLISION_NUMBER = COLLISION_NUMBER + 1
    sdf_geometry = mjcf_geom_to_sdf(geom)
    if sdf_geometry is not None:
        col.set_geometry(sdf_geometry)
    else:
        return None
    return col
