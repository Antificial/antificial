Usage
======
## Running the Game
Once the basic setup is complete (see README for further instructions), the game can be started like this:
```
python main.py
```
Please note that this software uses Python3, so make sure your python installation links to the correct version before executing.

## In-Game Usage
Once started, the game will present you with a black screen and the words `Press [Space] to play!`. Pressing `Space` will automatically set-up and start a game cycle.  
Before and during any part of the game, the arrow keys `←` and `→` can be sued to navigate between different screens. In order from left to right, the available screens are:

* Game Start (waiting for keypress to start new game)
* Simulation (shows the simulation during a running game)
* Game End (show the result after a game)
* Settings (adjustable sliders for important parameters)
* Splash Screen (shown during load)

The following key bindings are available:

* `Space`: Start a new game, if no agme is currently running
* `D`: Enable debug mode (currently only shows FPS and resolution)
* `R`: Resets the game by finishing it immediately and starting a new cycle

## Tests

### Run unit tests
```
python -m unittest discover antificial "*_test.py"
```
