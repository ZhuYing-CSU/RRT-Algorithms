from __future__ import annotations

import random
from typing import Any, Union

import numpy as np
from nptyping import NDArray
from RRT.core.info import DroneInfo, MapInfo, MissionInfo, RouteInfo
from RRT.core.sign import FAILURE, SUCCESS
from RRT.core.tree import RRT
from RRT.util.distcalc import dist_calc
from RRT.util.extendmethod import directly_extend
from RRT.util.samplemethod import random_sample, resample


class BasicRRT:
    """basic Rapidly-exploring Random Tree algorithm with only one forward-search tree"""

    def __init__(
        self,
        drone_info: DroneInfo,
        mission_info: MissionInfo,
        explore_prob: np.float64,
        step_size: np.float64,
        max_attempts: np.int32 = np.Infinity,
    ):
        """the init method of the basic RRT

        Parameters
        ----------
        drone_info : DroneInfo
            the drone infomation
        mission_info : MissionInfo
            the mission infomation
        explore_prob : np.float64
            the probability of exploration (1 - the probability of going forward target)
        step_size : np.float64
            the size/length of each step
        max_attempts : np.int32, optional
            the maximum number of attempts, by default np.Infinity
        """
        self.drone_info: DroneInfo = drone_info
        self.mission_info: MissionInfo = mission_info
        self.map_info: MapInfo = mission_info.map_info
        self.explore_prob: np.float64 = explore_prob
        self.max_attempts: Union[np.int32, None] = max_attempts
        self.step_size: np.float64 = step_size

        # initialize the forward search tree
        origin: NDArray[Any]
        target: NDArray[Any]
        origin, target = mission_info.origin, mission_info.target
        self.search_tree: RRT = RRT(origin, target)

    def run(self) -> bool:
        """the method to run the basic RRT algorithm

        Returns
        -------
        bool
            whether basic RRT algorithm reach the target from origin
        """
        attempt_cnt = 0
        while not self.search_tree.is_reach_target:
            attempt_cnt += 1

            explore = random.random() < self.explore_prob
            if explore:
                new_sample = random_sample(
                    self.map_info.min_border, self.map_info.max_border
                )
            else:
                new_sample = self.mission_info.target

            neighbors = self.search_tree.get_nearest_neighbors(new_sample, num=1)
            neighbor_info = self.search_tree.get_nodes()[neighbors[0]]["coord"]

            if explore:
                new_sample = resample(neighbor_info, new_sample, self.step_size)
            else:
                out_range = dist_calc(neighbor_info, new_sample) > self.step_size
                new_sample = (
                    resample(neighbor_info, new_sample, self.step_size)
                    if out_range
                    else new_sample
                )

            if self.mission_info.map_info.is_feasible(
                self.search_tree.get_route(target=neighbor_info).append(new_sample)
            ):
                directly_extend(self.search_tree, new_sample, neighbors[0])

            if np.isfinite(self.max_attempts) and attempt_cnt > self.max_attempts:
                break

        if attempt_cnt > self.max_attempts:
            return FAILURE
        return self.search_tree.is_reach_target

    def get_route(self) -> RouteInfo:
        """the instance method to get route info

        Returns
        -------
        RouteInfo
            the route information containing the route from origin to target
        """
        return self.search_tree.get_route(
            origin=self.mission_info.origin, target=self.mission_info.target
        )
