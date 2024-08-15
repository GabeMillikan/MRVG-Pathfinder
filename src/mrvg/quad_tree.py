from typing import Generator, Generic, TypeVar, overload

from .bounding_box import AABB

T = TypeVar("T")


class QuadTree(Generic[T]):
    @classmethod
    def create(cls, bounds: AABB, smallest: float = 1) -> "QuadTree[T]":
        b = bounds.copy()
        b.expand_inplace_to_positive_area()
        b.expand_inplace_to_aspect_ratio(1)
        return cls(b, smallest=smallest)

    @overload
    def __init__(self, bounds: AABB) -> None: ...

    @overload
    def __init__(self, bounds: AABB, *, parent: "QuadTree[T]") -> None: ...

    @overload
    def __init__(self, bounds: AABB, *, smallest: float) -> None: ...

    def __init__(
        self,
        bounds: AABB,  # NOTE: this should _really_ be a non-degenerate square!
        *,
        parent: "QuadTree[T] | None" = None,
        smallest: float = 1,
    ) -> None:
        self.parent = parent
        self.bounds = bounds
        self.items: dict[AABB, T] = {}
        self.smallest = parent.smallest if parent else smallest

        self.can_split = self.bounds.right

        self.quadrant_one = None  # upper right
        self.quadrant_two = None  # upper left
        self.quadrant_three = None  # lower left
        self.quadrant_four = None  # lower right

    def expand_leftwards(self, box: AABB) -> "QuadTree[T]":
        if self.parent is None:
            if box.bottom < self.bounds.bottom:  # expand left and down
                self.parent = QuadTree(self.bounds.expand_as_quadrant_one)
                self.parent.quadrant_one = self
            else:  # expand left and up
                self.parent = QuadTree(self.bounds.expand_as_quadrant_four)
                self.parent.quadrant_four = self
        return self.parent

    def expand_downwards(self, box: AABB) -> "QuadTree[T]":
        if self.parent is None:
            if box.left < self.bounds.left:  # expand down and left
                self.parent = QuadTree(self.bounds.expand_as_quadrant_one)
                self.parent.quadrant_one = self
            else:  # expand down and right
                self.parent = QuadTree(self.bounds.expand_as_quadrant_two)
                self.parent.quadrant_two = self
        return self.parent

    def expand_rightwards(self, box: AABB) -> "QuadTree[T]":
        if self.parent is None:
            if box.bottom < self.bounds.bottom:  # expand right and down
                self.parent = QuadTree(self.bounds.expand_as_quadrant_two)
                self.parent.quadrant_two = self
            else:  # expand right and up
                self.parent = QuadTree(self.bounds.expand_as_quadrant_three)
                self.parent.quadrant_three = self
        return self.parent

    def expand_upwards(self, box: AABB) -> "QuadTree[T]":
        if self.parent is None:
            if box.left < self.bounds.left:  # expand up and left
                self.parent = QuadTree(self.bounds.expand_as_quadrant_four)
                self.parent.quadrant_four = self
            else:  # expand up and right
                self.parent = QuadTree(self.bounds.expand_as_quadrant_three)
                self.parent.quadrant_three = self
        return self.parent

    def wholly_contains(self, aabb: AABB) -> bool:
        return (
            self.bounds.left <= aabb.left
            and aabb.right <= self.bounds.right
            and self.bounds.bottom <= aabb.bottom
            and aabb.top <= self.bounds.top
        )

    def intersects(self, aabb: AABB) -> bool:
        return not (
            self.bounds.right < aabb.left
            or aabb.right < self.bounds.left
            or self.bounds.top < aabb.bottom
            or aabb.top < self.bounds.bottom
        )

    def add_without_expanding(self, box: AABB, item: T) -> None:
        """
        Only call this function if you guarantee
        that `self.wholly_contains(box)` is true!
        """
        if box.left >= self.bounds.x:
            if box.bottom >= self.bounds.y:
                if self.quadrant_one is None:
                    self.quadrant_one = QuadTree(self.bounds.quadrant_one, parent=self)
                self.quadrant_one.add_without_expanding(box, item)
                return
            if box.top <= self.bounds.y:
                if self.quadrant_four is None:
                    self.quadrant_four = QuadTree(
                        self.bounds.quadrant_four,
                        parent=self,
                    )
                self.quadrant_four.add_without_expanding(box, item)
                return
        elif box.right <= self.bounds.x:
            if box.bottom >= self.bounds.y:
                if self.quadrant_two is None:
                    self.quadrant_two = QuadTree(self.bounds.quadrant_two, parent=self)
                self.quadrant_two.add_without_expanding(box, item)
                return
            if box.top <= self.bounds.y:
                if self.quadrant_three is None:
                    self.quadrant_three = QuadTree(
                        self.bounds.quadrant_three,
                        parent=self,
                    )
                self.quadrant_three.add_without_expanding(box, item)
                return

        self.items[box] = item

    def add(self, box: AABB, item: T) -> "QuadTree[T]":
        """
        Returns `self`, unless a `parent` was created, then returns the parent.
        This allows you to do `tree = tree.add(box)` and ensure you still have
        the root tree.
        """
        if box.left < self.bounds.left:
            return self.expand_leftwards(box).add(box, item)
        if box.bottom < self.bounds.bottom:
            return self.expand_downwards(box).add(box, item)
        if box.right > self.bounds.right:
            return self.expand_rightwards(box).add(box, item)
        if box.top > self.bounds.top:
            return self.expand_upwards(box).add(box, item)

        self.add_without_expanding(box, item)
        return self

    def remove(self, key: AABB) -> T | None:
        tree = self.narrow(key)
        if tree is None:
            return None

        v = tree.items.pop(key)
        tree.prune()
        return v

    @property
    def empty(self) -> bool:
        return (
            len(self.items) == 0
            and self.quadrant_one is None
            and self.quadrant_two is None
            and self.quadrant_three is None
            and self.quadrant_four is None
        )

    def prune(self) -> None:
        parent = self.parent
        if parent is None:
            # can't prune the root
            return

        if not self.empty:
            return

        self.parent = None
        if self is parent.quadrant_one:
            parent.quadrant_one = None
        elif self is parent.quadrant_two:
            parent.quadrant_two = None
        elif self is parent.quadrant_three:
            parent.quadrant_three = None
        else:
            parent.quadrant_four = None

        parent.prune()

    def narrow(self, key: AABB) -> "QuadTree[T] | None":
        """
        Returns the smallest QuadTree in the
        tree which completely contains the key,
        or None if `self` cannot contain it.
        """
        if (
            key.left < self.bounds.left
            or key.bottom < self.bounds.bottom
            or key.right > self.bounds.right
            or key.top > self.bounds.top
        ):
            return None

        tree = self
        while True:
            if key.left >= tree.bounds.x:
                if key.bottom >= tree.bounds.y and tree.quadrant_one is not None:
                    tree = tree.quadrant_one
                    continue
                if key.top <= tree.bounds.y and tree.quadrant_four is not None:
                    tree = tree.quadrant_four
                    continue
            elif key.right <= tree.bounds.x:
                if key.bottom >= tree.bounds.y and tree.quadrant_two is not None:
                    tree = tree.quadrant_two
                    continue
                if key.top <= tree.bounds.y and tree.quadrant_three is not None:
                    tree = tree.quadrant_three
                    continue

            return tree

    def find_items_on_line(
        self,
        ox: float,
        oy: float,
        dx: float,
        dy: float,
    ) -> Generator[T, None, None]:
        if not self.bounds.intersects_line_segment(ox, oy, dx, dy):
            return

        for box, item in self.items.items():
            if box.intersects_line_segment(ox, oy, dx, dy):
                yield item

        if self.quadrant_one is not None:
            yield from self.quadrant_one.find_items_on_line(ox, oy, dx, dy)

        if self.quadrant_two is not None:
            yield from self.quadrant_two.find_items_on_line(ox, oy, dx, dy)

        if self.quadrant_three is not None:
            yield from self.quadrant_three.find_items_on_line(ox, oy, dx, dy)

        if self.quadrant_four is not None:
            yield from self.quadrant_four.find_items_on_line(ox, oy, dx, dy)

    @property
    def quadrants(self) -> tuple["QuadTree[T]", ...]:
        return tuple(
            filter(
                None,
                (
                    self.quadrant_one,
                    self.quadrant_two,
                    self.quadrant_three,
                    self.quadrant_four,
                ),
            ),
        )
