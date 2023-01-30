MIN_REGION_AREA = 25
MAX_REGION_AREA = 8500
BINARY_STRUCTURE = 2
RESOURCE_BLOCKER_RADIUS_FACTOR = 2
GEYSER_RADIUS_FACTOR = 1.055
NONPATHABLE_RADIUS_FACTOR = 0.8
CORNER_MIN_DISTANCE = 3
LOG_MODULE = "MapAnalyzer"
COLORS = {
    0: "azure",
    1: "black",
    2: "red",
    3: "green",
    4: "blue",
    5: "orange",
    6: "saddlebrown",
    7: "lime",
    8: "navy",
    9: "purple",
    10: "olive",
    11: "aquamarine",
    12: "indigo",
    13: "tan",
    14: "skyblue",
    15: "wheat",
    16: "azure",
    17: "azure",
    18: "azure",
    19: "azure",
    20: "azure",
}
LOG_FORMAT = (
    "<w><bold>{time:YY:MM:DD:HH:mm:ss}|"
    "<level>{level: <8}</level>|<green>{name: ^15}</green>|"
    "{function: ^15}|"
    "{line: >4}|"
    "<level> {level.icon} {message}</level></bold></w>"
)
