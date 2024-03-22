# Copyright 2024 The Flax Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for flax.struct."""

import dataclasses
from typing import Any

import jax
from absl.testing import absltest
from jax._src.tree_util import prefix_errors

from flax import struct

# Parse absl flags test_srcdir and test_tmpdir.
jax.config.parse_flags_with_absl()


@struct.dataclass
class Point:
  x: float
  y: float
  meta: Any = struct.field(pytree_node=False)


class StructTest(absltest.TestCase):
  def test_no_extra_fields(self):
    p = Point(x=1, y=2, meta={})
    with self.assertRaises(dataclasses.FrozenInstanceError):
      p.new_field = 1

  def test_mutation(self):
    p = Point(x=1, y=2, meta={})
    new_p = p.replace(x=3)
    self.assertEqual(new_p, Point(x=3, y=2, meta={}))
    with self.assertRaises(dataclasses.FrozenInstanceError):
      p.y = 3

  # Slots param is not supported in Python 3.9
  # TODO(lew): Uncomment when Flax upgrades to Python 3.10.

  # def test_slots(self):
  #   slots_dataclass = partial(struct.dataclass, frozen=False, slots=True)
  #   @slots_dataclass
  #   class SlotsPoint:
  #     x: float
  #     y: float
  #   p = SlotsPoint(x=1., y=2.)
  #   p.x = 3.  # can assign to existing fields
  #   self.assertEqual(p, SlotsPoint(x=3., y=2.))
  #   with self.assertRaises(AttributeError):
  #     p.z = 0.  # can't create new fields by accident.

  def test_pytree_nodes(self):
    p = Point(x=1, y=2, meta={'abc': True})
    leaves = jax.tree_util.tree_leaves(p)
    self.assertEqual(leaves, [1, 2])
    new_p = jax.tree_util.tree_map(lambda x: x + x, p)
    self.assertEqual(new_p, Point(x=2, y=4, meta={'abc': True}))

  def test_keypath_error(self):
    # TODO(mattjj): avoid using internal prefix_errors by testing vmap error msg
    (e,) = prefix_errors(Point(1.0, [2.0], meta={}), Point(1.0, 2.0, meta={}))
    with self.assertRaisesRegex(ValueError, r'in_axes\.y'):
      raise e('in_axes')

  def test_double_wrap_no_op(self):
    class A:
      a: int

    self.assertFalse(hasattr(A, '_flax_dataclass'))

    A = struct.dataclass(A)
    self.assertTrue(hasattr(A, '_flax_dataclass'))

    A = struct.dataclass(A)  # no-op
    self.assertTrue(hasattr(A, '_flax_dataclass'))

  def test_wrap_pytree_node_no_error(self):
    @struct.dataclass
    class A(struct.PyTreeNode):
      a: int

  # TODO(marcuschiam): Uncomment when Flax upgrades to Python 3.10.
  # def test_kw_only(self):
  #   @struct.dataclass
  #   class A:
  #     a: int = 1

  #   with self.assertRaisesRegex(TypeError, "non-default argument 'b' follows default argument"):
  #     @struct.dataclass
  #     class B(A):
  #       b: int

  #   @functools.partial(struct.dataclass, kw_only=True)
  #   class B(A):
  #     b: int

  #   obj = B(b=2)
  #   self.assertEqual(obj.a, 1)
  #   self.assertEqual(obj.b, 2)


if __name__ == '__main__':
  absltest.main()
