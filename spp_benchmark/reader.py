#!/usr/bin/env python3

import random
import networkx

from spp_benchmark.model import CustomerProviderAS

def load_as_rel(filepath, dst=None):
    """
    Read AS business relationships from CAIDA dataset and augment it into a
    networkx directed graph.
    """
    dg = networkx.DiGraph()
    dg.dst = dst
    with open(filepath, 'r') as as_rel:
        for line in as_rel.readlines():
            if line.startswith('#'):
                continue
            src_as, dst_as, rel = line.strip('\n').split('|')
            src_asn = int(src_as)
            dst_asn = int(dst_as)
            dg.add_edge(src_asn, dst_asn)
            dg.add_edge(dst_asn, src_asn)
            if not dg.node[src_asn].get('as'):
                dg.node[src_asn]['as'] = CustomerProviderAS(src_asn)
            if not dg.node[dst_asn].get('as'):
                dg.node[dst_asn]['as'] = CustomerProviderAS(dst_asn)
            rel_type = int(rel)
            if not rel_type:
                dg.edges[src_asn, dst_asn]['relationship'] = 'pp'
                dg.node[src_asn]['as'].peers.add(dst_asn)
                dg.edges[dst_asn, src_asn]['relationship'] = 'pp'
                dg.node[dst_asn]['as'].peers.add(src_asn)
            else:
                dg.edges[src_asn, dst_asn]['relationship'] = 'pc'
                dg.node[src_asn]['as'].customers.add(dst_asn)
                dg.edges[dst_asn, src_asn]['relationship'] = 'cp'
                dg.node[dst_asn]['as'].providers.add(src_asn)
    if not dg.dst and dg.dst in dg.nodes():
        dg.node[dg.dst]['as'].unannounced_rib.append((dg.dst,))
    return dg

def load_as_type(filepath, dg):
    """
    Read AS types from CAIDA dataset and augment it into the network graph.
    """
    with open(filepath, 'r') as as_types:
        for line in as_types.readlines():
            if line.startswith('#'):
                continue
            asn, _, as_type = line.strip('\n').split('|')
            asn = int(asn)
            if asn in dg.nodes():
                dg.nodes[asn]['type'] = as_type[0]

def load_as_country(filepath, dg):
    """
    Read AS countries and augment it into the network graph.
    """
    with open(filepath, 'r') as as_country:
        for line in as_country.readlines():
            asn, country = line.strip('\n').split('|')
            asn = int(asn)
            if asn in dg.nodes():
                dg.nodes[asn]['country'] = country

def set_dst(dg, dst):
    """
    Set destination AS for a graph.
    """
    if dst not in dg.nodes():
        return
    dg.dst = dst
    for n in dg.nodes():
        dg.node[n]['as'].dst = dst
    dg.node[dg.dst]['as'].unannounced_rib.append((dg.dst,))

def read_as_by_country(dg, country):
    return [n for n in dg.nodes() if dg.nodes[n].get('country', '') == country]

def get_subtopo(dg, country):
    sub_nodes = read_as_by_country(dg, country)
    sdg = dg.subgraph(sub_nodes)
    all_comps = [c for c in networkx.components.connected_components(sdg.to_undirected())]
    max_sub_nodes = max(all_comps, key=lambda c: len(c)) if len(all_comps) else []
    return dg.subgraph(max_sub_nodes)

def get_stub_networks_by_rel(dg):
    return [n for n in dg.nodes() if all([dg.edges[e]['relationship'] != 'pc' for e in dg.out_edges(n)])]

def get_random_stub_network(dg):
    stub_networks = get_stub_networks_by_rel(dg)
    if not stub_networks:
        return None
    return random.choice(stub_networks)

def example_topology():
    dg = networkx.DiGraph()
    dg.dst = 0
    dg.add_edge(0, 1, relationship='cp')
    dg.add_edge(1, 0, relationship='pc')
    dg.add_edge(0, 2, relationship='cp')
    dg.add_edge(2, 0, relationship='pc')
    dg.add_edge(0, 3, relationship='cp')
    dg.add_edge(3, 0, relationship='pc')
    dg.add_edge(1, 2, relationship='cp')
    dg.add_edge(2, 1, relationship='pc')
    dg.add_edge(1, 3, relationship='cp')
    dg.add_edge(3, 1, relationship='pc')
    dg.add_edge(1, 4, relationship='cp')
    dg.add_edge(4, 1, relationship='pc')
    dg.add_edge(2, 3, relationship='cp')
    dg.add_edge(3, 2, relationship='pc')
    dg.add_edge(2, 4, relationship='cp')
    dg.add_edge(4, 2, relationship='pc')
    dg.add_edge(3, 4, relationship='pp')
    dg.add_edge(4, 3, relationship='pp')
    dg.add_edge(3, 5, relationship='pc')
    dg.add_edge(5, 3, relationship='cp')
    dg.add_edge(3, 6, relationship='pc')
    dg.add_edge(6, 3, relationship='cp')
    dg.add_edge(3, 7, relationship='pp')
    dg.add_edge(7, 3, relationship='pp')
    dg.add_edge(5, 6, relationship='pc')
    dg.add_edge(6, 5, relationship='cp')
    dg.add_edge(5, 7, relationship='cp')
    dg.add_edge(7, 5, relationship='pc')
    dg.add_edge(6, 7, relationship='cp')
    dg.add_edge(7, 6, relationship='pc')

    dg.node[0]['as'] = CustomerProviderAS(0, dst=0, providers={1, 2, 3})
    dg.node[1]['as'] = CustomerProviderAS(1, dst=0, customers={0}, providers={2, 3, 4})
    dg.node[2]['as'] = CustomerProviderAS(2, dst=0, customers={0, 1}, providers={3, 4})
    dg.node[3]['as'] = CustomerProviderAS(3, dst=0, customers={0, 1, 2, 5, 6}, peers={4, 7})
    dg.node[4]['as'] = CustomerProviderAS(4, dst=0, customers={1, 2}, peers={3})
    dg.node[5]['as'] = CustomerProviderAS(5, dst=0, customers={6}, providers={3, 7})
    dg.node[6]['as'] = CustomerProviderAS(6, dst=0, providers={3, 5, 7})
    dg.node[7]['as'] = CustomerProviderAS(7, dst=0, customers={5, 6}, peers={3})

    dg.node[dg.dst]['as'].unannounced_rib.append((dg.dst,))
    return dg
