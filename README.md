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
and any addresses returned will be attmpted.

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
$ sudo apt install bind9 bind9utils
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

...
