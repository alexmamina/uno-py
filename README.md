# uno-py
Multiplayer Uno game in Python with sockets.

Requirements: Python 3, tkmacosx, Tkinter, Pillow

How to start:
1. Download and install the latest compatible Python 3 from python.org
2. Download and unzip the code

Mac:  
3. Open Terminal  
4. Without quotes write "cd Downloads/uno-py-master/uno-py-master"  
5. Again, without quotes write "./setup-mac.sh"  
(If it says "Permission denied", write "chmod +x setup-mac.sh", then repeat step 5)  
6. If it says "Setup complete" and no errors are shown, everything has been installed correctly.   
  - If you are the first player in the group, start the server: "python server.py 44444 N" where N is the number of players (e.g. 4). 
  After that, open a new window and write "python client.py".  
    - Allow incoming network connections on the port if prompted  
    - 44444 can be replaced by any other similar port number (e.g. 54321)  
  - If you are not the first player (someone else set up the server), simply write "python client.py" and follow the instructions there  
 
Windows:  
  3. Open the unzipped code folder and double-click on "setup-win.bat"  
    - The Command Prompt will open and show the installation process. If it says "Setup complete" and no errors are shown, everything has been installed correctly.  
      Press any key to continue  
  4. Open the Command Prompt if it closed  
  5. Without quotes write "cd Downloads/uno-py-master/uno-py-master"  
  6. - If you are the first player in the group, start the server: "py server.py 44444 N" where N is the number of players (e.g. 4).  
    After that, open a new window and write "py client.py".  
      - Allow incoming network connections on the port if prompted  
      - 44444 can be replaced by any other similar port number (e.g. 54321)  
    - If you are not the first player (someone else set up the server), simply write "py client.py" and follow the instructions there  
    
     
     
       
How to play after everything is installed:  
Mac: - First player: without quotes write "cd Downloads/uno-py-master/uno-py-master & python server.py 44444 4 & python client.py" (replace 4 with the number of players)  
     - Others: "cd Downloads/uno-py-master/uno-py-master & python client.py"  
Windows: - First player: "cd Downloads/uno-py-master/uno-py-master & py server.py 44444 4 & py client.py" (replace 4 with numberof players)  
         - Other players: "cd Downloads/uno-py-master/uno-py-master & py client.py"
         
Or simply open Terminal/Command Prompt and press the UP arrow to scroll until the commands pop up from history




Updates:
If there is an update to the code, simply delete the folder uno-py-master from Downloads and download the new zip folder (and unzip). Then follow the steps for when everything is installed 
