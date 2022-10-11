DEVICE_TABLE: dict[str, list[str]] = {
    "d-wave": ["DW_2000Q_6", "Advantage_system4", "Advantage_system6"],
    "ionq": ["ionQdevice"],
    "rigetti": ["Aspen-11", "Aspen-M-1", "Aspen-M-2"],
    "xanadu": ["Borealis"],
}

US_WEST_1: int = 0
US_WEST_2: int = 1
US_EAST_1: int = 2
DEVICE_REGION_INDEX_DICT: dict[str, int] = {
    "d-wave": US_WEST_2,
    "rigetti": US_WEST_1,
    "ionq": US_EAST_1,
    "xanadu": US_EAST_1,
}

PRICE_PER_TASK: float = 0.3
PRICE_TABLE: dict[str, float] = {
    "rigetti": 0.00035,
    "d-wave": 0.00019,
    "ionq": 0.01,
    "xanadu": 0.0002,
}
