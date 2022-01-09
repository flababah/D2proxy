D2proxy
=======

Simple proxy server for closed battle.net Diablo II LOD 1.13. Can be used to circumvent realm downs by playing from a proxy connection. It works for multiple concurrent clients with local, LAN and public IPs.

Diablo II and battle.net uses three connections between the client and server: chat, realm and game. The client first connects to chat and the server will send the IP and port of the realm server when logging in. The same is the case when joining a game, where realm will send the IP of the game server to connect to. The proxy works by intercepting these two special packets and patching them to contain the proxy's IP instead. The proxy will also note the original IP from the packets, and create a proxy connection between the client and that IP.

More information about the protocols is available at [bnetdocs.org](https://bnetdocs.org/).

## Instructions

#### Running the proxy
Execute directly in terminal (requires Python 3):
```
python d2proxy.py
```

Or build and run as a docker container:
```
docker build -t d2proxy .
docker run -d -p6112:6112 -p6113:6113 -p4000:4000 d2proxy
```

Both commands accepts appending an optional gateway to the end of the arguments if the desired realm is not ```europe.battle.net```.

#### Connecting to the proxy
Open ```HKEY_CURRENT_USER\SOFTWARE\Battle.net\Configuration``` in ```regedit``` and append the following lines to ```Diablo II Battle.net gateways```:

```
<proxy_ip>
-1
d2proxy
```

where ```<proxy_ip>``` needs to be replaced with the real IP. (Note that ```d2proxy``` can also be replaced with a more suitable name.) With this approach the proxy can simply be selected under "Gateway" in the main menu.

Alternatively, you can modity the hosts file to redirect the usual gateway to the proxy:

1. Press `Windows+R`
2. Paste in `notepad C:\WINDOWS\system32\drivers\etc\hosts`
3. Add `<proxy_ip> europe.battle.net` to the bottom of the file where `<proxy_ip>` is the proxy's IP.

If you run the proxy on the same machine as the game you need to note the IP of battle.net before modifying the `hosts` file. That IP should be passed as first argument to the proxy such that the proxy does not try to connect to itself.

MIT license
