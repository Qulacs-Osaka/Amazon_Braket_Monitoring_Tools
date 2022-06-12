DEVICE_PROVIDERS: list[str] = ["d-wave", "d-wave", "ionq", "rigetti", "rigetti"]
# index should be the same as device_providers's one
DEVICE_NAMES: list[str] = [
    "DW_2000Q_6",
    "Advantage_system4",
    "ionQdevice",
    "Aspen-11",
    "Aspen-M-1",
]
# 0,1,2 represents the region of the device. s_west_1:0, us_west_2:1, us_east_1:2
DEVICE_REGION_INDEX_DICT: dict[str, int] = {
    "d-wave": 1,
    "rigetti": 0,
    "ionq": 2,
    "DW_2000Q_6": 1,
    "Advantage_system4": 1,
    "ionQdevice": 2,
    "Aspen-11": 0,
    "Aspen-M-1": 0,
}
PRICE_PER_TASK: float = 0.3
PRICE_TABLE: dict = {
    "rigetti": 0.00035,
    "d-wave": 0.00019,
    "ionq": 0.01,
}
