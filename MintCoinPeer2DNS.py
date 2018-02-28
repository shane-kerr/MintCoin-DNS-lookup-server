"""
This program reads the peers that the currently running MintCoin
daemon is connected to, and then uses that to update a DNS owner name
with those IP addresses.

That DNS entry can then be used by other MintCoin wallets to discover
who to connect to.
"""
import argparse
import json
import subprocess
import sys


# Some default names for our executables
MINTCOIN_EXE = 'mintcoind'
NSUPDATE_EXE = 'nsupdate'


def update_domain(nsupdate_args, domain, ipv4_peers, ipv6_peers, zone):
    """
    Invoke the nsupdate program and use it to send a DDNS message
    to the server with the zone.
    """
    with subprocess.Popen(nsupdate_args, stdin=subprocess.PIPE,
                          universal_newlines=True) as proc:
        # Set our zone, if we are given one (otherwise the nsupdate
        # program will guess).
        if zone:
            proc.stdin.write('zone ' + zone + '\n')
        # Delete any existing records for this owner name.
        proc.stdin.write('del ' + domain + '\n')
        # Add any IPv4 peers as A records.
        for ipv4_peer in ipv4_peers:
            proc.stdin.write('add ' + domain +
                             ' 60 IN A ' + ipv4_peer + '\n')
        # Add any IPv6 peers as AAAA records.
        for ipv6_peer in ipv6_peers:
            proc.stdin.write('add ' + domain +
                             ' 60 IN AAAA ' + ipv6_peer + '\n')
        # Finally send our update command, which will execute all
        # of the changes atomically on the DNS server.
        proc.stdin.write('send\n')
        proc.stdin.flush()


def main(args):
    """This is the main program. Call it with any commmand-line arguments."""
    # Parse our arguments.
    desc = 'Put MintCoin nodes into DNS.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--mintcoind', '-m',
                        help='Location of the mintcoind executable.')
    parser.add_argument('--nsupdate', '-n',
                        help='Location of the nsupdate executable.')
    parser.add_argument('--keyfile', '-k', required=True,
                        help='File containing the TSIG authentication key.')
    parser.add_argument('--zone', '-z',
                        help='Zone to update (optional).')
    parser.add_argument('domain',
                        help='Domain name to update.')
    args = parser.parse_args()

    # Get the peers from MintCoin.
    if args.mintcoind:
        mintcoin_cmd = args.mintcoind
    else:
        mintcoin_cmd = MINTCOIN_EXE
    mintcoin_args = [mintcoin_cmd, "getpeerinfo"]
    with subprocess.Popen(mintcoin_args, stdout=subprocess.PIPE) as proc:
        peer_data = proc.stdout.read()
    peers = json.loads(peer_data.decode())

    # We separate out the IPv4 and IPv6 addresses, since these will become
    # the A and AAAA records, respectively.
    ipv4_peers = []
    ipv6_peers = []
    for peer in peers:
        if peer['addr'].endswith(':12788'):
            if peer['addr'][0] == '[':
                ipv6_peers.append(peer['addr'][1:-7])
            else:
                ipv4_peers.append(peer['addr'][:-6])

    # We don't really need to sort these since DNS is unordered,
    # but it makes debugging easier.
    ipv4_peers.sort()
    ipv6_peers.sort()

    # Update the zone.
    if args.nsupdate:
        nsupdate_cmd = args.nsupdate
    else:
        nsupdate_cmd = NSUPDATE_EXE
    nsupdate_args = [nsupdate_cmd, "-k", args.keyfile]
    update_domain(nsupdate_args, args.domain,
                  ipv4_peers, ipv6_peers, args.zone)


if __name__ == '__main__':
    main(sys.argv)
