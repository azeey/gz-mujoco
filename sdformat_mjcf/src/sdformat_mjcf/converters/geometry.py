# Copyright (C) 2022 Open Source Robotics Foundation

# Licensed under the Apache License, version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#       http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module to convert SDFormat Collision/Visual geometries to MJCF geoms"""

import sdformat as sdf
import sdformat_mjcf.sdf_utils as su

GeometryType = sdf.Geometry.GeometryType

COLLISION_GEOM_GROUP = 3
VISUAL_GEOM_GROUP = 0


def add_geometry(body, name, pose, sdf_geom):
    """
    Converts an SDFormat geometry to an MJCF geom and add it to the given body.

    :param mjcf.Element body: The MJCF body to which the geom is added
    :param str name: Name of the geom (obtained from the name of the SDFormat
            Collision or Visual)
    :param sdformat.Pose3d pose: Resolved pose of the geom (obtained from the
            pose of the SDFormat Collision or Visual)
    :return: The newly created MJCF geom
    """

    if sdf_geom is None:
        return

    geom = body.add(
        "geom",
        name=name,
        pos=su.vec3d_to_list(pose.pos()),
        euler=su.quat_to_euler_list(pose.rot()),
    )

    if sdf_geom.box_shape():
        box_shape = sdf_geom.box_shape()
        geom.type = "box"
        geom.size = su.vec3d_to_list(box_shape.size() / 2.0)
    elif sdf_geom.capsule_shape():
        capsule_shape = sdf_geom.capsule_shape()
        geom.type = "capsule"
        geom.size = [capsule_shape.radius(), capsule_shape.length() / 2.0]
    elif sdf_geom.cylinder_shape():
        cylinder_shape = sdf_geom.cylinder_shape()
        geom.type = "cylinder"
        geom.size = [cylinder_shape.radius(), cylinder_shape.length() / 2.0]
    elif sdf_geom.ellipsoid_shape():
        ellipsoid_shape = sdf_geom.ellipsoid_shape()
        geom.type = "ellipsoid"
        geom.size = su.vec3d_to_list(ellipsoid_shape.radii())
    elif sdf_geom.plane_shape():
        plane_shape = sdf_geom.plane_shape()
        geom.type = "plane"
        # The third element of size defines the spacing between square grid
        # lines for rendering.
        # TODO (azeey) Consider making this configurable
        geom.size = su.vec2d_to_list(plane_shape.size() / 2.0) + [0]
    elif sdf_geom.sphere_shape():
        sphere_shape = sdf_geom.sphere_shape()
        geom.type = "sphere"
        geom.size = [sphere_shape.radius()]
    elif sdf_geom.mesh_shape():
        raise RuntimeError("Meshes are not yet supported")
    else:
        raise RuntimeError(f"Encountered unsupported shape type {sdf_geom.type()}")

    return geom


def add_collision(body, col, pose_resolver=su.pose_resolver):
    sem_pose = col.semantic_pose()
    pose = pose_resolver(sem_pose)
    geom = add_geometry(body, col.name(), pose, col.geometry())
    geom.group = COLLISION_GEOM_GROUP
    return geom
