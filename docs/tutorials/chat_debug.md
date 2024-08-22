`ares` features an in game chat debug system, this is especially handy for quickly testing different scenarios.

## Activating chat debug
In your `config.yml` set the following options to `True`:<br/>

 * `Debug: True`
 * `ChatDebug: True` (found under `DebugOptions`)

## Using chat debug
The chat debug feature should be used in the SC2 game window only.
The chat debug service in `ares` will parse chat messages
and check for valid debug commands.

### Spawning units
Spawn new units directly where the in game camera is.
To trigger the first word should be `make` or `create`, the second word is the amount of units/structures 
to create,
the third is a valid `UnitTypeId` type, and the fourth should be the player for which units should be spawned 
(there is a default value of `1` for this, so omit if spawning for player 1).

Here are some valid commands you can try:

`make 4 marine` - Spawns 4 marines for player 1 at camera location.<br/>

`make 3 mothership 1` - Spawns 3 motherships for player 1 at camera location. <br/>

`make 1 hive 2` - Spawn a hive for the enemy at camera location. Note
the 2 in the chat command, this spawns units for the enemy. <br/>

`create 4 banshee 2` - Spawn four banshees for the enemy at camera location. <br/>

`create 2 ultralisk 1` - Spawn two ultralisks for player one at camera location. Specifying player one in
this command even though it's not required.

![mothership](https://github.com/user-attachments/assets/4b9bb602-d05d-419a-86b3-53215c4de555)

### Destroying units
Destroy units using the same syntax for creating units, but for the first word use
`kill` or `destroy`. The destroy commands do not take into account camera location
and will kill units off camera if needed.

Here are some valid commands you can try:

`kill 4 marine` - Destroys 4 marines for player 1.<br/>

`kill 125 mothership 2` - Destroys 125 motherships. Note
the 2 in the chat command, this kills units for the enemy. <br/>

`kill 1 hive` - Destroys a hive for player one. <br/>

`destroy 4 banshee` - Destroys three banshees for player one. <br/>

`destroy 2 ultralisk 1` - Destroys two ultralisks for player one. Specifying player one in
this command even though it's not required.

### Additional options
You can toggle cheats with the following chat commands:

* `cooldown` - Disables cooldowns of unit abilities for the bot
* `food` - Disable food usage (not sure this one works)
* `god` - Units and structures no longer take damage
* `resources` - Get 5000 minerals and 5000 vespene
* `show` - Reveal map
* `tech` - Remove all tech requirements
* `upgrades` - Research all currently available upgrades
