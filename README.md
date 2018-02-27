# MintCoin-DNS-lookup-server
Scripts to allow you to publish information about available MintCoin
nodes in the DNS.

## Problem Statement

The MintCoin wallet needs to connect to other nodes running MintCoin
software. After it has connected to one or more nodes, then it can
download a list of other nodes to connect to from them. However,
getting the initial connection requires some information.

One way to tell the wallet about other nodes is to manually configure
them when the wallet starts, either with a command-line option or by
adding them to the configuration file. The MintCoin block explorer has
a list of active nodes to seed with.

The other way is to use the DNS. The wallet looks up a domain name,
and any addresses returned will be attempted.

The DNS method is clean and should be fast, but we need DNS servers
that hold the correct information. That is what this repository
provides.

## BIND Setup

The approach we will use is something called Dynamic DNS, or DDNS. It
is a standard way to update a DNS zone with the DNS protocol itself.

You need a BIND 9 server serving any zone. The zone needs to be
configured to allow updates. Typically updates are secured either by
restricting to specific IP addresses or with TSIG. If updates are to
be allowed over the network, TSIG is recommended.

On a Debian or Ubuntu system you can install the needed packages:

```
$ sudo apt install bind9 bind9utils dnsutils
```

You can then create a TSIG key:

```
$ /usr/sbin/dnssec-keygen -a HMAC-SHA512 -b 512 -n HOST mintysig
```

This command creates two files, `Kmintysig.+NNN+NNNNN.private` and
`Kmintysig.+NNN+NNNNN.key`. 

You need to get the randomly-generated bits from the file, which you
can do like this:

```
$ awk '/^Key:/{ print $2 }' Kmintysig.*.private
iGizm/q4RR6fT7vy6zEnazDZdWppk9RDFVXz9wDLcy/APujLjST3/CBQQMBeDmxTTv25BV+0p1FuW1V+0arZLg==
```

You can then update the BIND configuration with the appropriate zone
and key information. In Debian this is `/etc/bind/named.conf.local`,
and you want to add a key stanza like this:

```
key mintysig {
    algorithm HMAC-SHA512;
    secret "iGizm/q4RR6fT7vy6zEnazDZdWppk9RDFVXz9wDLcy/APujLjST3/CBQQMBeDmxTTv25BV+0p1FuW1V+0arZLg==";
};
```

The zone you want to update will need an `allow-update` clause, and
will end up looking something like this:

```
zone mintysig.zz {
    type master;
    file "/var/lib/bind/mintysig.zz.zone";
    allow-query { any; };
    allow-update { key mintysig; };
};
```

# MintCoin Wallet Setup

You need to set up the MintCoin wallet and run it. This is where we
will get peers to add to our DNS zone. You do _not_ need to have any
MintCoins in the wallet - and in fact probably you should not.

What you do want to have is a lot of peers, so your `MintCoin.conf`
should look something like this: 

```
testnet=0
maxconnections=101
listen=1

rpcuser=mintcoinrpc
rpcpassword=somereallylongandhardtoguesspassword
```

# Running the Update Script

The update script will connect to the running `mintcoind`, get the
list of peers, and use DDNS to push the changes to the DNS.

A typical execution might look like this:

```
$ python3 MintCoinPeer2DNS.py -m /opt/mintcoin/bin/mintcoind -k Kmintysig.+165+59162.key -z vanaheimr.cf mintseed.vanaheimr.cf
```

The `-m` option is the location of `mintcoind`. If it is in your
`PATH` then it is not necessary. The `-k` option is the name of the
key file created with `dnssec-keygen` previously and added to your
BIND configuration. The `-z` option is the name of the zone, which
`nsupdate` will use to try to figure out the correct server to connect
to (it is optional). And finally you have the actual DNS name to
update.

You can use the `-h` option to get the full syntax:

```
$ python3 MintCoinPeer2DNS.py -h
usage: MintCoinPeer2DNS.py [-h] [--mintcoind MINTCOIND] [--nsupdate
NSUPDATE]
                           --keyfile KEYFILE [--zone ZONE]
                           domain

Put MintCoin nodes into DNS.

positional arguments:
  domain                Domain name to update.

optional arguments:
  -h, --help            show this help message and exit
  --mintcoind MINTCOIND, -m MINTCOIND
                        Location of the mintcoind executable.
  --nsupdate NSUPDATE, -n NSUPDATE
                        Location of the nsupdate executable.
  --keyfile KEYFILE, -k KEYFILE
                        File containing the TSIG authentication key.
  --zone ZONE, -z ZONE  Zone to update (optional).
```

# Automate Running

Typically you will want to run the update script periodically. You can
use `cron` for this, which you update with `crontab -e`:

```
# Update the DNS with MintCoin peers every minute.
* * * * * python3 ~/MintCoin-DNS-lookup-server/MintCoinPeer2DNS.py -m /opt/mintcoin/bin/mintcoind -k Kmintysig.+165+59162.key -z vanaheimr.cf mintseed.vanaheimr.cf
```

# Manual Lookups

You can query the DNS manually by using the `host` command, something
like this:

```
$ host -t any mintseed.vanaheimr.cf | sort
mintseed.vanaheimr.cf descriptive text "[2601:441:8700:4660:2940:41c6:30e:698e]:55528"
mintseed.vanaheimr.cf has address 107.4.242.195
mintseed.vanaheimr.cf has address 144.76.237.39
mintseed.vanaheimr.cf has address 188.40.131.43
mintseed.vanaheimr.cf has address 212.26.191.22
mintseed.vanaheimr.cf has address 46.4.113.143
mintseed.vanaheimr.cf has address 50.53.100.217
mintseed.vanaheimr.cf has address 73.5.13.195
mintseed.vanaheimr.cf has address 79.124.7.89
mintseed.vanaheimr.cf has address 87.226.38.178
mintseed.vanaheimr.cf has IPv6 address 2001:470:78c8:2:a00:27ff:fe6a:7c68
mintseed.vanaheimr.cf has IPv6 address 2a02:1205:34e4:9880:257e:79c8:7d33:d8bf
mintseed.vanaheimr.cf has IPv6 address 2a03:f680:fe03:1577:20c:29ff:fe59:3ec2
```

If you prefer, you can also use the `dig` command (preferred by 4 out
of 5 DNS professionals), something like this:

```
$ dig +noall +answer  -t any mintseed.vanaheimr.cf  | sort
mintseed.vanaheimr.cf.	57	IN	A	107.4.242.195
mintseed.vanaheimr.cf.	57	IN	A	144.76.237.39
mintseed.vanaheimr.cf.	57	IN	A	188.40.131.43
mintseed.vanaheimr.cf.	57	IN	A	212.26.191.22
mintseed.vanaheimr.cf.	57	IN	A	46.4.113.143
mintseed.vanaheimr.cf.	57	IN	A	50.53.100.217
mintseed.vanaheimr.cf.	57	IN	A	73.5.13.195
mintseed.vanaheimr.cf.	57	IN	A	79.124.7.89
mintseed.vanaheimr.cf.	57	IN	A	87.226.38.178
mintseed.vanaheimr.cf.	57	IN	AAAA	2001:470:78c8:2:a00:27ff:fe6a:7c68
mintseed.vanaheimr.cf.	57	IN	AAAA	2a02:1205:34e4:9880:257e:79c8:7d33:d8bf
mintseed.vanaheimr.cf.	57	IN	AAAA	2a03:f680:fe03:1577:20c:29ff:fe59:3ec2
mintseed.vanaheimr.cf.	57	IN	TXT	"[2601:441:8700:4660:2940:41c6:30e:698e]:55528"
```

# Integration into the MintCoin Wallet

To add your server into the MintCoin wallet, you can either issue a
pull request on GitHub (you probably only need to add yourself to the
list of servers in the `strDNSSeed[]` array), or you can contact the
developers and ask them to add your server.
