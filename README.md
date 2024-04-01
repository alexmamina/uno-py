# uno-py
Multiplayer Uno game in Python with sockets.

Requirements: Python 3, tkmacosx, Tkinter, Pillow

## Regular play
2-4 players allowed. One of the players needs to start both the server and their own client.

If you don't already have the `uno-py-master` folder in your Downloads, do that first.

To start the server, simply double click on `start-server-mac.command` (or right click -> Open with
Terminal to avoid permissions issues). Answer the prompts on the screen and wait until it says
`CONNECT TO:` - that's the information that each client will need to paste to connect to the server.

To start a client, double click on `play.command` on a Mac, or `play.bat` on Windows (make sure this
is run _after_ the server has started). Follow the prompts on the screen to enter server's
connection information (of the form `ipaddress portnumber`), and your name afterwards. The
Terminal/Command Prompt window that starts up should say something along the lines of `Connected to
the server. Waiting for other players`. Once all the players have connected, the game should start
automatically and the cards should appear.

### Manual steps
If for some reason double clicking on the files does not work, you can follow the steps
below to start the server/client manually. (Again, assuming the folder is downloaded and located in
Downloads):
- Open Terminal (Mac/Linux)/Command Prompt (Windows)
- If client:
  - Copy and paste commands into the newly opened window:
  ```bash
  cd && cd Downloads/uno-py-master
  python3 client.py
  ```
  - If running on Windows, replace `python3` with `py`
- If server:
  - Copy and paste commands into the newly opened window:
  ```bash
  cd && cd Downloads/uno-py-master
  ifconfig en0 inet | grep inet | awk {'print $2'}
  ```
  - Make sure the command above prints out an IPv4 address (something like `192.168.X.Y`)
  - Run the command to start the server, replacing variables with applicable values:
  ```bash
  python3 server.py <ip> <port> <number of players> <modes>
  ```
    - Replace `<ip>` with the ip address obtained on the last step; `<port>` with the port to
    connect to (e.g. 44444), `<number of players>` with the number (2-4) and `<modes>` with the game
    modes you want to enable (1 - 7/0, 2 - stacking +2, 3 - taking many cards; no separation. So if
    you want 7/0 and taking many cards, you add `13`. If you don't want any modes, enter `0`)
- Then either the game prompt will appear, or an error that will need to be fixed first



## First time

1. Download and install the latest compatible Python 3 from python.org (3.9 preferred)
2. Download and unzip the code (green `Code` button top right -> Download ZIP)

Mac:

3. Open Terminal
4. Run `cd Downloads/uno-py-master/mac_scripts`
5. Run `./setup-mac.sh`
  - (If it says `Permission denied`, write `chmod +x setup-mac.sh`, then repeat step 5)
6. If it says `Setup complete` and no errors are shown, everything has been installed correctly.
  - If you are the first player in the group, start the server - follow the instructions above
  After that, open a new window and start a client for yourself (instructions above).
    - Allow incoming network connections on the port if prompted
    - 44444 can be replaced by any other similar port number (e.g. 54321)
  - If you are not the first player (someone else set up the server), start the client


Windows:

  3. Open the unzipped code folder and double-click on `setup-win.bat`
    - The Command Prompt will open and show the installation process. If it says `Setup complete`
    and no errors are shown, everything has been installed correctly. Press any key to continue
  4. Open the Command Prompt if it closed
  5. Run `cd Downloads/uno-py-master/windows_scripts`
  6. - If you are the first player in the group, start the server: `py server.py <ip> 44444 N m`
  where `N` is the number of players (e.g. 4), `m` is a list of game modes (see Regular play), and
  `<ip>` is your local IP address, obtained by running `whats-my-ip.bat`.
    After that, open a new window and write `py client.py` to start your own game.
      - Allow incoming network connections on the port if prompted
      - 44444 can be replaced by any other similar port number (e.g. 54321)
    - If you are not the first player (someone else set up the server), start the client only



## Updates:

If there is an update to the code, delete the folder `uno-py-master` from Downloads and download
the new zip folder (and unzip). Then follow the steps for when regular play.
