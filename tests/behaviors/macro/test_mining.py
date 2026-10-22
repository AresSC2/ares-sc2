from __future__ import annotations

from unittest.mock import MagicMock, patch

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

from ares.behaviors.macro import Mining
from ares.consts import MINING, TOWNHALL_DISTANCE_FACTOR

MINING_PATH: str = "ares.behaviors.macro.mining"
CONFIG: dict = {MINING: {TOWNHALL_DISTANCE_FACTOR: 1.08}}


def _resource(tag: int, type_id: UnitTypeId) -> MagicMock:
    resource = MagicMock(name=f"{type_id.name}_{tag}")
    resource.tag = tag
    resource.type_id = type_id
    resource.position = Point2((10.0, 10.0))
    resource.vespene_contents = 1000
    return resource


def _setup_execute(
    resource: MagicMock, worker_on_gas: bool
) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Mock a single safe worker, close to its assigned resource."""
    worker = MagicMock(name="worker")
    worker.tag = 1
    worker.position = Point2((11.0, 11.0))
    worker.health_percentage = 1.0
    worker.is_carrying_resource = False
    worker.is_gathering = False
    worker.orders = []

    ai = MagicMock()
    ai.race = Race.Terran
    ai.unit_tag_dict = {resource.tag: resource}

    mediator = MagicMock()
    mediator.get_units_from_role.return_value = [worker]
    mediator.is_position_safe.return_value = True
    assigned: dict[int, int] = {worker.tag: resource.tag}
    mediator.get_worker_to_vespene_dict = assigned if worker_on_gas else {}
    mediator.get_worker_to_mineral_patch_dict = {} if worker_on_gas else assigned

    return ai, mediator, worker


class TestMining:
    def test_vespene_boost_does_not_boost_mineral_workers(self):
        # arrange
        mineral = _resource(100, UnitTypeId.MINERALFIELD)
        ai, mediator, _ = _setup_execute(mineral, worker_on_gas=False)

        # act
        with (
            patch.object(Mining, "_do_mining_boost") as boost,
            patch.object(Mining, "_do_standard_mining") as standard,
        ):
            Mining(mineral_boost=False, vespene_boost=True, workers_per_gas=2).execute(
                ai, CONFIG, mediator
            )

        # assert
        boost.assert_not_called()
        standard.assert_called_once()

    def test_vespene_boost_boosts_gas_workers(self):
        # arrange
        refinery = _resource(200, UnitTypeId.REFINERY)
        ai, mediator, _ = _setup_execute(refinery, worker_on_gas=True)

        # act
        with (
            patch.object(Mining, "_do_mining_boost") as boost,
            patch.object(Mining, "_do_standard_mining") as standard,
        ):
            Mining(mineral_boost=False, vespene_boost=True, workers_per_gas=2).execute(
                ai, CONFIG, mediator
            )

        # assert
        boost.assert_called_once()
        standard.assert_not_called()

    def test_safe_long_distance_fields_exclude_assigned_patches(self):
        # arrange
        assigned_mf = _resource(1, UnitTypeId.MINERALFIELD)
        free_mf = _resource(2, UnitTypeId.MINERALFIELD)
        ai = MagicMock()
        ai.mineral_field = [assigned_mf, free_mf]
        ai.state.score.collection_rate_minerals = 1000
        mediator = MagicMock()
        mediator.get_mineral_patch_to_list_of_workers = {assigned_mf.tag: {10, 11}}
        mediator.is_position_safe.return_value = True

        # act
        with patch(
            f"{MINING_PATH}.cy_sorted_by_distance_to",
            side_effect=lambda units, _pos: list(units),
        ):
            safe_mfs = Mining._safe_long_distance_mineral_fields(ai, mediator)

        # assert
        assert safe_mfs == [free_mf]

    def test_long_distance_miner_not_reissued_gather_on_same_patch(self):
        # arrange: worker is already gathering from the chosen mineral patch
        mf = _resource(1, UnitTypeId.MINERALFIELD)
        worker = MagicMock()
        worker.position = Point2((11.0, 11.0))
        worker.is_gathering = True
        worker.is_carrying_resource = False
        worker.order_target = mf.tag
        ai = MagicMock()
        ai.time = 300.0
        ai.townhalls.filter.return_value = []
        mediator = MagicMock()
        patches: dict[int, set[int]] = {mf.tag: set()}
        mediator.get_mineral_patch_to_list_of_workers = patches
        mediator.is_position_safe.return_value = True
        mining = Mining(safe_long_distance_mineral_fields=[mf])

        # act
        with patch(f"{MINING_PATH}.cy_closest_to", return_value=mf):
            mining._long_distance_mining(
                ai, mediator, MagicMock(), worker, patches, worker.position
            )

        # assert
        worker.gather.assert_not_called()
