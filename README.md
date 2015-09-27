D2proxy
=======

Simple proxy server for closed battle.net Diablo II LOD 1.13. Can be used to circumvent realm downs by playing from a proxy connection. It works for multiple concurrent clients with local, LAN and public IPs.

Diablo II and battle.net uses three connections between the client and server: chat, realm and game. The client first connects to chat and the server will send the IP and port of the realm server when logging in. The same is the case when joining a game, where realm will send the IP of the game server to connect to. The proxy works by intercepting these two special packets and patching them to contain the proxy's IP instead. The proxy will also note the original IP from the packets, and create a proxy connection between the client and that IP.

More information about the protocols is available at [bnetdocs.org](https://bnetdocs.org/).

## Instructions

    python2 d2proxy.py [battle.net address]

You either need to set your DNS server up such that it maps `europe.battle.net` to the proxy's IP, or some other domain if you are not playing on europe. Or you can simply modify the `hosts` file on the client computer:

1. Press `Ctrl+R`
2. Paste in `notepad C:\WINDOWS\system32\drivers\etc\hosts`
3. Add `<proxy_ip> europe.battle.net` to the bottom of the file where `<proxy_ip>` is the proxy's IP.

If you run the proxy on the same machine as the game you need to note the IP of battle.net before modifying the `hosts` file. That IP should be passed as first argument to the proxy such that the proxy does not try to connect to itself.

MIT license
