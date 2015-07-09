# -*- coding: utf-8 -*-
#
#     Copyright (c) 2015 Anders Høst
#     MIT license
#

import urllib2
import socket
import select
import struct
import time
import sys
import os

public_ip_url = "http://ip.42.pl/raw"

class IPRange(object):
	def __init__(self, cidr):
		ip, block = cidr.split("/")
		self.base = self.to_num(ip)
		self.mask = 1 << (32 - int(block))

	def to_num(self, ip):
		return reduce(lambda a, x: a << 8 | int(x), ip.split("."), 0)

	def __contains__(self, item):
		num = self.to_num(item)
		return (num - self.base) & 0xffffffff < self.mask

local_ip_ranges = (
	IPRange("127.0.0.0/8"), # Loopback addresses.
	IPRange("10.0.0.0/8"),
	IPRange("172.16.0.0/12"),
	IPRange("192.168.0.0/16"))

def local_ip(ip):
	return any(ip in s for s in local_ip_ranges)

class D2Proxy(object):
	"""
	Simple proxy server for Diablo II LOD v1.13.
	Supports multiple connections.
	"""
	def __init__(self, remote, public, chatp=6112, realmp=6113, gamep=4000):
		self.remote = remote
		self.public = public
		self.socks = {}       # sock -> (behavior, partner).
		self.waiting = {}     # sock -> (behavior, partner).
		self.next_remote = {} # kind -> (addr, port).

		# Pipes data between sockets, while applying transformation.
		def relay(transform=lambda sock, x: x):
			def relayer(sock, partner):
				try:
					data = sock.recv(0xffff)
				except socket.error as ex:
					if ex.errno == socket.errno.ECONNRESET:
						data = None
					else:
						raise
				if not data: # Disconnect.
					partner.close()
					for s in sock, partner:
						self.socks.pop(s)
					self.log("Proxy connection closed.")
				else:
					partner.send(transform(sock, data))
			return relayer

		# Return proxy's public IP if peer is public.
		def proxy_ip(sock):
			_, inner = self.socks[sock]
			peer   = inner.getpeername()[0]
			lan_ip = inner.getsockname()[0]
			return socket.inet_aton(lan_ip if local_ip(peer) else self.public)

		# SID_LOGONREALMEX - Redirect realm ip:port to proxy.
		def redir_realm(sock, d):
			if not d.startswith("\xff\x3e"): # Other packet.
				return d
			self.next_remote["realm"] = \
				socket.inet_ntoa(d[20:24]), \
				struct.unpack("!H", d[24:26])[0]

			self.log("Redirected REALM ip...")
			return d[:20] + proxy_ip(sock) + struct.pack("!H", realmp) + d[26:]

		# MCP_JOINGAME - Redirect game ip to proxy.
		def redir_game(sock, d):
			if not d.startswith("\x15\0\x04"): # Other packet.
				return d
			if d[17:21] != "\0\0\0\0": # Failed to join game.
				return d
			self.next_remote["game"] = \
				socket.inet_ntoa(d[9:13]), \
				gamep

			self.log("Redirected GAME ip...")
			return d[:9] + proxy_ip(sock) + d[13:]

		# Initialize the three kinds of proxies.
		self.listen("chat",  remote, chatp,  relay(), relay(redir_realm))
		self.listen("realm", remote, realmp, relay(), relay(redir_game))
		self.listen("game",  remote, gamep,  relay(), relay())

	def new_socket(self, sock=None):
		if sock is None:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
		sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
		sock.setblocking(False)
		return sock

	def listen(self, kind, addr, port, to_serv, from_serv):
		sock = self.new_socket()
		sock.bind(("", port))
		sock.listen(3)

		def on_accept(listener, _):
			inner, (ip, _) = listener.accept()
			outer = self.new_socket()
			inner = self.new_socket(inner)

			def on_finish(outer, inner):
				self.socks[inner] = to_serv, outer
				self.socks[outer] = from_serv, inner
				self.log("%s connected to %s." % (ip, kind))

			try:
				outer.connect(self.next_remote[kind])
				on_finish(outer, inner)
			except socket.error as ex:
				if ex.errno in (socket.errno.EWOULDBLOCK,
				                socket.errno.EINPROGRESS):
					self.waiting[outer] = on_finish, inner
					self.log("%s attempting connection..." % ip)
				else:
					raise

		self.socks[sock] = on_accept, None
		self.next_remote[kind] = addr, port

	def log(self, line):
		print time.strftime("[%H:%M:%S] ", time.localtime()) + line

	def run(self):
		self.log("Running...")
		while True:
			try:
				r, w, e = select.select(self.socks, self.waiting, self.waiting, 0.5)
				for sock in r:
					behavior, partner = self.socks[sock]
					behavior(sock, partner)
				for sock in w:
					behavior, inner = self.waiting[sock]
					self.waiting.pop(sock)
					behavior(sock, inner)
				for sock in e:
					behavior, inner = self.waiting[sock]
					self.waiting.pop(sock)
					self.log("%s connection failed!" % inner.getsockname()[0])
					inner.close()

			except KeyboardInterrupt:
				break

if __name__ == "__main__":
	remote = sys.argv[1] if len(sys.argv) > 1 else "europe.battle.net"
	public = urllib2.urlopen(public_ip_url).read()

	print "Usage        : %s [battle.net address]" % sys.argv[0]
	print "Remote       : %s" % remote
	print "Proxy public : %s" % public
	print

	p = D2Proxy(remote, public)
	p.run()

