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

import unittest
from numpy.testing import assert_allclose
from math import pi, sqrt

import sdformat as sdf
from ignition.math import Color, Inertiald, Pose3d, MassMatrix3d, Vector3d
from dm_control import mjcf

from sdformat_to_mjcf.converters.link import add_link
from sdformat_to_mjcf.converters.root import add_root
from tests import helpers


class LinkTest(helpers.TestCase):
    test_pose = Pose3d(1, 2, 3, pi / 2, pi / 3, pi / 4)
    expected_pos = [1.0, 2.0, 3.0]
    expected_euler = [90.0, 60.0, 45.0]

    def setUp(self):
        self.mujoco = mjcf.RootElement(model="test")
        self.body = self.mujoco.worldbody.add("body")

    def moi_to_list(self, moi):
        return [
            moi(0, 0),
            moi(1, 1),
            moi(2, 2),
            moi(0, 1),
            moi(0, 2),
            moi(1, 2)
        ]

    def create_box(self, sdf_cls, name):
        item = sdf_cls()
        item.set_name(name)
        geometry = sdf.Geometry()
        geometry.set_box_shape(sdf.Box())
        geometry.set_type(sdf.GeometryType.BOX)
        item.set_geometry(geometry)
        return item

    def test_basic_link(self):
        link = sdf.Link()
        link.set_name("base_link")
        link.set_raw_pose(self.test_pose)
        mj_body = add_link(self.body, link)
        self.assertIsNotNone(mj_body)
        assert_allclose(self.expected_pos, mj_body.pos)
        assert_allclose(self.expected_euler, mj_body.euler)

    def test_link_inertia(self):
        # This following is equivalent to
        # <link name="base_link">
        #   <inertial>
        #       <pose degrees="true">1 2 3   90 60 45</pose>
        #       <mass>384</mass>
        #       <inertia>
        #           <ixx>544.0</ixx>
        #           <iyy>2624.0</iyy>
        #           <izz>3104.0</izz>
        #       </inertia>
        #   </inertial>
        link = sdf.Link()
        link.set_name("base_link")
        inertial = Inertiald(
            MassMatrix3d(384, Vector3d(544, 2624, 3104), Vector3d.ZERO),
            self.test_pose)
        link.set_inertial(inertial)
        mj_body = add_link(self.body, link)
        self.assertIsNotNone(mj_body)
        assert_allclose((2604, 2604, 1064, -500, 260 * sqrt(6), 260 * sqrt(6)),
                        mj_body.inertial.fullinertia)
        assert_allclose(self.moi_to_list(inertial.moi()),
                        mj_body.inertial.fullinertia)
        self.assertIsNone(mj_body.inertial.euler)

    def test_multiple_links(self):
        link1 = sdf.Link()
        link1.set_name("base_link")
        link1.set_raw_pose(Pose3d(-1, -2, -3, 0, 0, 0))
        mj_body1 = add_link(self.body, link1)

        link2 = sdf.Link()
        link2.set_name("lower_link")
        link2.set_raw_pose(self.test_pose)
        mj_body2 = add_link(mj_body1, link2)

        self.assertIsNotNone(mj_body2)
        assert_allclose(self.expected_pos, mj_body2.pos)
        assert_allclose(self.expected_euler, mj_body2.euler)

    def test_link_with_geometry(self):
        link = sdf.Link()
        link.set_name("base_link")
        link.set_raw_pose(self.test_pose)

        visual = sdf.Visual()
        visual.set_name("v1")
        visual.set_raw_pose(Pose3d(1, 2, 3, pi / 2, pi / 3, pi / 4))
        collision = sdf.Collision()
        collision.set_name("c1")
        collision.set_raw_pose(Pose3d(1, 2, 3, pi / 2, pi / 3, pi / 4))

        material = sdf.Material()
        material.set_emissive(Color(0.1, 0.1, 0.1))
        material.set_specular(Color(0.2, 0.2, 0.2))
        visual.set_material(material)

        geometry = sdf.Geometry()
        geometry.set_box_shape(sdf.Box())
        geometry.set_type(sdf.GeometryType.BOX)
        visual.set_geometry(geometry)
        collision.set_geometry(geometry)

        link.add_visual(visual)
        link.add_collision(collision)

        mj_body = add_link(self.body, link)
        self.assertIsNotNone(mj_body)
        assert_allclose(self.expected_pos, mj_body.pos)
        assert_allclose(self.expected_euler, mj_body.euler)
        geoms = mj_body.find_all('geom')
        self.assertEqual(2, len(geoms))
        self.assertEqual("c1", geoms[0].name)
        self.assertEqual(None, geoms[0].material)
        self.assertNotEqual(None, geoms[1].material)
        self.assertAlmostEqual(0.1, geoms[1].material.emission)
        self.assertAlmostEqual(0.2, geoms[1].material.specular)
        assert_allclose([0, 0, 0, 1], geoms[1].material.rgba)
        self.assertEqual("v1", geoms[1].name)

    def test_duplicate_collision_names(self):
        c1 = self.create_box(sdf.Collision, "c1")
        link1 = sdf.Link()
        link1.set_name("link1")
        link1.add_collision(c1)
        link2 = sdf.Link()
        link2.set_name("link2")
        link2.add_collision(c1)
        mj_body1 = add_link(self.body, link1)
        mj_body2 = add_link(self.body, link2)
        self.assertIsNotNone(mj_body1)
        self.assertIsNotNone(mj_body2)

    def test_duplicate_visual(self):
        v1 = self.create_box(sdf.Visual, "v1")
        link1 = sdf.Link()
        link1.set_name("link1")
        link1.add_visual(v1)
        link2 = sdf.Link()
        link2.set_name("link2")
        link2.add_visual(v1)
        mj_body1 = add_link(self.body, link1)
        mj_body2 = add_link(self.body, link2)
        self.assertIsNotNone(mj_body1)
        self.assertIsNotNone(mj_body2)

    def test_imu_sensor(self):
        link = sdf.Link()
        link.set_name("base_link")
        sensor = sdf.Sensor()
        sensor.set_name("imu_sensor")
        sensor.set_type(sdf.Sensortype.IMU)
        sensor.set_raw_pose(self.test_pose)
        imu = sdf.IMU()
        sensor.set_imu_sensor(imu)
        link.add_sensor(sensor)
        mj_body = add_link(self.body, link)
        self.assertIsNotNone(mj_body)
        self.assertIsNotNone(self.mujoco.sensor)
        mjcf_accels = self.mujoco.sensor.get_children("accelerometer")
        self.assertEqual(1, len(mjcf_accels))
        mjcf_gyros = self.mujoco.sensor.get_children("gyro")
        self.assertEqual(1, len(mjcf_gyros))

    def test_camera_sensor(self):
        link = sdf.Link()
        link.set_name("base_link")
        sensor = sdf.Sensor()
        sensor.set_name("camera_sensor")
        sensor.set_type(sdf.Sensortype.CAMERA)
        sensor.set_raw_pose(self.test_pose)
        camera = sdf.Camera()
        sensor.set_camera_sensor(camera)
        link.add_sensor(sensor)
        mj_body = add_link(self.body, link)
        self.assertIsNotNone(mj_body)
        self.assertEqual(1, len(mj_body.get_children("camera")))


class LinkIntegration(unittest.TestCase):
    expected_pos = [1.0, 2.0, 3.0]
    expected_euler = [90.0, 60.0, 45.0]

    # Test that the model pose is correctly reflected in the converted MJCF
    # body pose.
    def test_link_pose(self):
        model_string = """
        <sdf version="1.9">
            <model name="M1">
                <pose degrees="true">{} {} {} {} {} {}</pose>
                <link name="L1"/>
            </model>
        </sdf>""".format(*self.expected_pos, *self.expected_euler)

        root = sdf.Root()
        errors = root.load_sdf_string(model_string)
        self.assertEqual(0, len(errors))
        mjcf_root = add_root(root)
        mj_link = mjcf_root.find("body", "L1")
        assert_allclose(self.expected_pos, mj_link.pos)
        assert_allclose(self.expected_euler, mj_link.euler)


if __name__ == "__main__":
    unittest.main()
