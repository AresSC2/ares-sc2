from functools import lru_cache
from typing import List, Set, Tuple, TYPE_CHECKING, Union

import numpy as np
from loguru import logger
from numpy import int64, ndarray
from sc2.position import Point2
from scipy.ndimage import center_of_mass

if TYPE_CHECKING:
    from MapAnalyzer import MapData, Region


class Buildables:
    """

    Represents the Buildable Points in a :class:`.Polygon`,

    "Lazy" class that will only update information when it is needed

    Tip:
        :class:`.BuildablePoints` that belong to a :class:`.ChokeArea`

        are always the edges, this is useful for walling off

    """

    def __init__(self, polygon):
        self.polygon = polygon
        self.points = None

    @property
    def free_pct(self) -> float:
        """

        A simple method for knowing what % of the points is left available out of the total

        """
        if self.points is None:
            logger.warning("BuildablePoints needs to update first")
            self.update()
        return len(self.points) / len(self.polygon.points)

    def update(self) -> None:
        """

        To be called only by :class:`.Polygon`, this ensures that updates are done in a lazy fashion,

        the update is evaluated only when there is need for the information, otherwise it is ignored

        """
        parr = self.polygon.map_data.points_to_numpy_array(self.polygon.points)
        # passing safe false to reduce the warnings,
        # which are irrelevant in this case
        [
            self.polygon.map_data.add_cost(
                position=(unit.position.x, unit.position.y),
                radius=unit.radius * 0.9,
                grid=parr,
                safe=False,
            )
            for unit in self.polygon.map_data.bot.all_units.not_flying
        ]
        buildable_indices = np.where(parr == 1)
        buildable_points = []
        _points = list(self.polygon.map_data.indices_to_points(buildable_indices))
        placement_grid = self.polygon.map_data.placement_arr.T
        for p in _points:
            if p[0] < placement_grid.shape[0] and p[1] < placement_grid.shape[1]:
                if placement_grid[p] == 1:
                    buildable_points.append(p)
        self.points = list(map(Point2, buildable_points))


class Polygon:
    """

    Base Class for Representing an "Area"

    """

    # noinspection PyProtectedMember
    def __init__(self, map_data: "MapData", array: ndarray) -> None:  # pragma: no cover
        self.map_data = map_data
        self.array = array
        self.extended_array = array.copy()
        # Include the outer_perimeter in the points
        outer_perimeter = self.outer_perimeter
        self.extended_array[outer_perimeter[:, 0], outer_perimeter[:, 1]] = 1
        self.id = None  # TODO
        self.is_choke = False
        self.is_ramp = False
        self.is_vision_blocker = False
        self.is_region = False
        self.areas = []  # set by map_data / Region
        self.map_data.polygons.append(self)
        self._buildables = Buildables(polygon=self)

    @property
    def top(self):
        return max(self.points, key=lambda x: x[1])

    @property
    def bottom(self):
        return min(self.points, key=lambda x: x[1])

    @property
    def right(self):
        return max(self.points, key=lambda x: x[0])

    @property
    def left(self):
        return min(self.points, key=lambda x: x[0])

    @property
    def buildables(self) -> Buildables:
        """

        :rtype: :class:`.BuildablePoints`

        Is a responsible for holding and updating the buildable points of it's respected :class:`.Polygon`

        """
        self._buildables.update()
        return self._buildables

    @property
    def regions(self) -> List["Region"]:
        """

        :rtype: List[:class:`.Region`]

        Filters out every Polygon that is not a region, and is inside / bordering with ``self``

        """
        from MapAnalyzer.Region import Region

        if len(self.areas) > 0:
            return [r for r in self.areas if isinstance(r, Region)]
        return []

    def calc_areas(self) -> None:
        # This is called by MapData, at a specific point in the sequence of compiling the map
        # this method uses where_all which means
        # it should be called at the end of the map compilation when areas are populated

        areas = self.areas
        for point in self.outer_perimeter:
            point = point[0], point[1]
            new_areas = self.map_data.where_all(point)
            if self in new_areas:
                new_areas.pop(new_areas.index(self))
            areas.extend(new_areas)
        self.areas = list(set(areas))

    def plot(self, testing: bool = False) -> None:  # pragma: no cover
        """

        plot

        """
        import matplotlib.pyplot as plt

        plt.style.use("ggplot")

        plt.imshow(self.array, origin="lower")
        if testing:
            return
        plt.show()

    @property
    @lru_cache()
    def points(self) -> Set[Point2]:
        """

        Set of :class:`.Point2`

        """
        return {Point2(p) for p in np.argwhere(self.extended_array == 1)}

    @property
    @lru_cache()
    def corner_array(self) -> ndarray:
        """

        :rtype: :class:`.ndarray`

        """

        from skimage.feature import corner_harris, corner_peaks

        array = corner_peaks(
            corner_harris(self.array),
            min_distance=self.map_data.corner_distance,
            threshold_rel=0.01,
        )
        return array

    @property
    @lru_cache()
    def width(self) -> float:
        """

        Lazy width calculation,   will be approx 0.5 < x < 1.5 of real width

        """
        pl = list(self.outer_perimeter_points)
        s1 = min(pl)
        s2 = max(pl)
        x1, y1 = s1[0], s1[1]
        x2, y2 = s2[0], s2[1]
        return np.math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    @property
    @lru_cache()
    def corner_points(self) -> List[Point2]:
        """

        :rtype: List[:class:`.Point2`]

        """
        points = [
            Point2((int(p[0]), int(p[1])))
            for p in self.corner_array
            if self.is_inside_point(Point2(p))
        ]
        return points

    @property
    @lru_cache()
    def center(self) -> Point2:
        """

        Since the center is always going to be a ``float``,

        and for performance considerations we use integer coordinates.

        We will return the closest point registered

        """

        cm = self.map_data.closest_towards_point(
            points=list(self.points), target=center_of_mass(self.array)
        )
        return cm

    def is_inside_point(self, point: Union[Point2, tuple]) -> bool:
        """

        Query via Set(Point2)  ''fast''

        """
        test = int(point[0]), int(point[1])
        shape = self.extended_array.shape
        if 0 < test[0] < shape[0] and 0 < test[1] < shape[1]:
            # Return python bool instead of numpy bool
            return_val = True if self.extended_array[test] == 1 else False
            return return_val
        return False

    @property
    def outer_perimeter(self) -> np.ndarray:
        """
        Find all the individual points that surround the area
        """
        d1 = np.diff(self.array, axis=0, prepend=0)
        d2 = np.diff(self.array, axis=1, prepend=0)
        d1_pos = np.argwhere(d1 > 0) - [1, 0]
        d1_neg = np.argwhere(d1 < 0)
        d2_pos = np.argwhere(d2 > 0) - [0, 1]
        d2_neg = np.argwhere(d2 < 0)
        perimeter_arr = np.zeros(self.array.shape)
        perimeter_arr[d1_pos[:, 0], d1_pos[:, 1]] = 1
        perimeter_arr[d1_neg[:, 0], d1_neg[:, 1]] = 1
        perimeter_arr[d2_pos[:, 0], d2_pos[:, 1]] = 1
        perimeter_arr[d2_neg[:, 0], d2_neg[:, 1]] = 1

        edge_indices = np.argwhere(perimeter_arr != 0)
        return edge_indices

    @property
    def outer_perimeter_points(self) -> Set[Point2]:
        """

        Useful method for getting  perimeter points

        """
        return {Point2((p[0], p[1])) for p in self.outer_perimeter}

    @property
    @lru_cache()
    def perimeter(self) -> np.ndarray:
        """
        Find all the individual points that surround the area
        """
        d1 = np.diff(self.array, axis=0, prepend=0)
        d2 = np.diff(self.array, axis=1, prepend=0)
        d1_pos = np.argwhere(d1 > 0)
        d1_neg = np.argwhere(d1 < 0) - [1, 0]
        d2_pos = np.argwhere(d2 > 0)
        d2_neg = np.argwhere(d2 < 0) - [0, 1]
        perimeter_arr = np.zeros(self.array.shape)
        perimeter_arr[d1_pos[:, 0], d1_pos[:, 1]] = 1
        perimeter_arr[d1_neg[:, 0], d1_neg[:, 1]] = 1
        perimeter_arr[d2_pos[:, 0], d2_pos[:, 1]] = 1
        perimeter_arr[d2_neg[:, 0], d2_neg[:, 1]] = 1

        edge_indices = np.argwhere(perimeter_arr != 0)
        return edge_indices

    @property
    @lru_cache()
    def perimeter_points(self) -> Set[Point2]:
        """

        Useful method for getting  perimeter points

        """
        return {Point2((p[0], p[1])) for p in self.perimeter}

    @property
    @lru_cache()
    # type hinting complains if ndarray is not here, but always returns a numpy.int32
    def area(self) -> Union[int, np.ndarray]:
        """
        Sum of all points

        """
        return np.sum(self.extended_array)

    def __repr__(self) -> str:
        return f"<Polygon[size={self.area}]: {self.areas}>"
