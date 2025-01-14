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

from ignition.math import Vector3d

from mjcf_to_sdformat.converters.joint import (mjcf_joint_to_sdf,
                                               add_fixed_joint)
from mjcf_to_sdformat.converters.light import mjcf_light_to_sdf
from mjcf_to_sdformat.converters.link import mjcf_body_to_sdf
from mjcf_to_sdformat.converters.sensor import mjcf_camera_sensor_to_sdf

import sdformat_mjcf_utils.sdf_utils as su
from sdformat_mjcf_utils.defaults import MjcfModifiers

import sdformat as sdf


def mjcf_worldbody_to_sdf(mjcf_root, physics, world,
                          export_world_plugins=False):
    """
    Convert a MJCF worldbody to a SDFormat world

    :param mjcf.RootElement mjcf_root: The MJCF root element
    :param mujoco.Physics physics: Mujoco Physics
    :param sdf.World world: SDF World to add the models
    :param boolean export_world_plugins: If this this flag is True then
    system plugin will be exported (SceneBroadcaster, UserCommands, Physics,
    Sensors), otherwise no system plugin will be exported.
    """
    model = sdf.Model()
    if mjcf_root.model is not None:
        model.set_name(mjcf_root.model)
    else:
        model.set_name("model")

    modifiers = MjcfModifiers(mjcf_root)

    model_static = sdf.Model()

    for light in mjcf_root.worldbody.light:
        modifiers.apply_modifiers_to_element(light)
        light_sdf = mjcf_light_to_sdf(light)
        world.add_light(light_sdf)

    link = mjcf_body_to_sdf(mjcf_root.worldbody, physics, modifiers=modifiers)
    model_static.set_name(su.find_unique_name(
        mjcf_root.worldbody, "geom", "static"))

    for camera in mjcf_root.worldbody.camera:
        sensor = mjcf_camera_sensor_to_sdf(camera)
        if sensor is not None:
            link.add_sensor(sensor)

    model_static.add_link(link)
    model_static.set_static(True)
    world.add_model(model_static)

    body = mjcf_root.worldbody.body

    if mjcf_root.option is not None:
        if mjcf_root.option.flag.gravity == "disable":
            world.set_gravity(Vector3d(0, 0, 0))
        elif mjcf_root.option.gravity is not None:
            world.set_gravity(su.list_to_vec3d(mjcf_root.option.gravity))
        if mjcf_root.option.magnetic is not None:
            world.set_magnetic_field(
                su.list_to_vec3d(mjcf_root.option.magnetic))
        if mjcf_root.option.wind is not None:
            world.set_wind_linear_velocity(
                su.list_to_vec3d(mjcf_root.option.wind))

    def iterate_bodies(input_body,
                       model,
                       body_parent_name=None):
        for body in input_body:
            link = mjcf_body_to_sdf(body,
                                    physics,
                                    body_parent_name=body_parent_name,
                                    modifiers=modifiers)
            for camera in body.camera:
                sensor = mjcf_camera_sensor_to_sdf(camera)
                if sensor is not None:
                    link.add_sensor(sensor)

            for joint in body.joint:
                if modifiers is not None:
                    modifiers.apply_modifiers_to_element(joint)
                joint_sdf = mjcf_joint_to_sdf(joint,
                                              body_parent_name,
                                              body.name)
                if joint_sdf is not None:
                    model.add_joint(joint_sdf)
            if len(body.joint) == 0 and body.freejoint is None:
                joint_sdf = add_fixed_joint(body_parent_name, body.name)
                model.add_joint(joint_sdf)

            model.add_link(link)
            iterate_bodies(body.body,
                           model,
                           body.name)
    iterate_bodies(body, model)

    if export_world_plugins:
        plugins = {
            "ignition-gazebo-physics-system":
                "ignition::gazebo::systems::Physics",
            "ignition-gazebo-sensors-system":
                "ignition::gazebo::systems::Sensors",
            "ignition-gazebo-user-commands-system":
                "ignition::gazebo::systems::UserCommands",
            "ignition-gazebo-scene-broadcaster-system":
                "ignition::gazebo::systems::SceneBroadcaster"
        }
        for [key, value] in plugins.items():
            plugin = sdf.Plugin(key, value)
            world.add_plugin(plugin)

    world.add_model(model)
