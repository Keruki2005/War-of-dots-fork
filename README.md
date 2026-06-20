BATTLE OF DOTS
=====
BATTLE OF DOTS is a LAN RTS war game, a war simulation built in python with pygame. Original credit goes to https://warofdots.net/ and as this is a fork to https://github.com/gamepycoder/War-of-dots.
Part two of this game is created with Godot Engine: https://github.com/SudoMakeMeASandwichDE/battle-of-dots-2

Feel free to start issues.
Feel free to contribute.

TODO
====
| Priority    | Task                                | Details / Examples                                                                                             | Status  | 
|-------------|-------------------------------------|----------------------------------------------------------------------------------------------------------------|---------|
| 3  | Send global stats to client         | `{"cities owned":[# per player], "troops owned":[# per player], "total damage":[# per player], "current winner": <id>}` |done
| 3  | Send troop stats to client          | `{"terrain on": <value>, "number of attackers": <count>, "attacking dir":[<dir xy, dist, offset of closest>]}`          |done
| 3  | Send city stats to client           | `{"timer": <current>, "timer target": <target>, "produced":[so far]}`                                                   |done
| 4  | Win condition & client UI           | Client continuously reads `current winner` and displays final result                                                    |?
| 9  | Playtest & refine constants         | Balancing through playtesting                                                                                           |Planned
| 9  | Add strategy information            | e.g., recommended moves, AI heuristics                                                                                  |maybe later
| 1  | Use NumPy better                    | Performance optimizations                                                                                               |?
| 10 | Improve robustness to internet      | Reconnect, lag-tolerance, state-sync                                                                                    |under development
| 8  | Map making / editor                 | GUI editor, procedural generators, seed saving                                                                          |done
| 7  | Save seed + city layout             | Export/import seeds and layouts                                                                                         |done
| 7  | Save & load game state              | Checkpoints, save files                                                                                                 |halfway
| 4  | More visual features                | UI/UX improvements, effects                                                                                             |halfway
| 4  | More Units                          | Tanks, Fast Tanks, Infantry                                                                                             |done
                               

(just edit to add suggestions)



Installation:
=====================

`pipx install git+https://github.com/Keruki2005/battle-of-dots.git`

Make sure you have [pipx](https://github.com/pypa/pipx) installed.

Run with `bod` in the terminal.

INSTRUCTIONS TO PLAY (old)
=====================
 - start server and enter number of players (run bod_server.py)
 - enter port, just enter 0, use other numbers when you think other people are playing the game on the same lan/router/network
 - should say waiting for players, will connect with first `PLAYERS` (number of players you entered) number of clients
 - start the clients (bod_client.py)
 - on each client type in the ip address then the port number you typed in the server (e.g. '0')
 - start playing when the pygame window pops up by pressing `p` to unpause, have fun!

INSTRUCTIONS TO PLAY (new)
=====================
- run `bod` in your terminal
- **server (1)**: enter number of players, choose random map or a saved map, enter port, wait for players
- **client (2)**: enter host IP and port, start playing
- **map editor (3)**: paint terrain, place cities, save maps to the `maps/` folder, then host with option 2

Map editor controls
======
- Keys 1–7: water, plains, hill, mountain, forest, clear forest, place/remove city
- Left-drag: paint | Right-drag: pan | Scroll: zoom
- `G`: generate random island | `S`: save | `[` `]`: brush size | `Esc`: quit

Saved maps are stored in `maps/*.json` and can be selected when hosting a server.


Controls
======

Left Click: Grab a unit and draw a line to show it where to go. Release to save the path.

Right Click: Drag the mouse to move your view across the map.

Scroll Wheel: Zoom in and out on the spot where your mouse is pointing.

Spacebar: Send all your saved moves to the server.

C: Delete the paths you drew before you send them.

P: Send pause request.

Terminal: Use the terminal to set the IP/PORT address and restart the client.

Thanks for playing! :)
