from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Union

from ares.behaviors.behavior import Behavior
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot
    from ares.behaviors.combat.group import CombatGroupBehavior
    from ares.behaviors.combat.individual import CombatIndividualBehavior


@dataclass
class CombatManeuver(Behavior):
    """Execute behaviors sequentially.

    Add behaviors

    Example:
    ```py
    from ares import AresBot
    from ares.behaviors.combat import CombatManeuver
    from ares.behaviors.combat.individual import (
        DropCargo,
        KeepUnitSafe,
        PathUnitToTarget,
        PickUpCargo,
    )

    class MyBot(AresBot):
        mine_drop_medivac_tag: int

        async def on_step(self, iteration):
            # Left out here, but `self.mine_drop_medivac_tag`
            # bookkeeping is up to the user
            medivac: Optional[Unit] = self.unit_tag_dict.get(
                self.mine_drop_medivac_tag, None
            )
            if not medivac:
                return

            air_grid: np.ndarray = self.mediator.get_air_grid

            # initiate a new CombatManeuver
            mine_drop: CombatManeuver = CombatManeuver()

            # then add behaviors in the order they should be executed
            # first priority is picking up units
            # (will return False if no cargo and move to next behavior)
            mine_drop.add(
                PickUpCargo(
                    unit=medivac,
                    grid=air_grid,
                    pickup_targets=mines_to_pickup
                )
            )

            # if there is cargo, path to target and drop them off
            if medivac.has_cargo:
                # path
                mine_drop.add(
                    PathUnitToTarget(
                        unit=medivac,
                        grid=air_grid,
                        target=self.enemy_start_locations[0],
                    )
                )
                # drop off the mines
                mine_drop.add(DropCargo(unit=medivac, target=medivac.position))

            # no cargo and no units to pick up, stay safe
            else:
                mine_drop.add(KeepUnitSafe(unit=medivac, grid=air_grid))

            # register the mine_drop behavior
            self.register_behavior(mine_drop)
    ```

    Attributes
    ----------
    micros : list[Behavior] (optional, default: [])
        A list of behaviors that should be executed. (Optional)
    """

    micros: list[Behavior] = field(default_factory=list)

    def add(
        self,
        behavior: Union[
            "CombatIndividualBehavior", "CombatGroupBehavior", "CombatManeuver"
        ],
    ) -> None:
        """
        Parameters
        ----------
        behavior : CombatBehavior
            Add a new combat behavior to the current maneuver object.

        Returns
        -------
            None
        """
        self.micros.append(behavior)

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        for order in self.micros:
            if order.execute(ai, config, mediator):
                # executed an action
                return True
        # none of the combat micros completed, no actions executed
        return False
