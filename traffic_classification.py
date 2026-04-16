from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet import ethernet, ipv4

log = core.getLogger()

# Stats dictionary
stats = {
    "TCP": 0,
    "UDP": 0,
    "ICMP": 0,
    "Others": 0
}

def _handle_PacketIn(event):
    packet = event.parsed

    if not packet.parsed:
        return

    ip_packet = packet.find('ipv4')

    # CLASSIFICATION
    if ip_packet:
        proto = ip_packet.protocol

        if proto == 6:
            stats["TCP"] += 1
        elif proto == 17:
            stats["UDP"] += 1
        elif proto == 1:
            stats["ICMP"] += 1
        else:
            stats["Others"] += 1

        # CLEAN OUTPUT
        total = sum(stats.values())
        log.info("\n===== Traffic Statistics =====")
        for p in stats:
            percent = (stats[p] / total) * 100 if total > 0 else 0
            log.info(f"{p}: {stats[p]} packets ({percent:.2f}%)")
        log.info("==============================\n")

    # FLOW RULE INSTALLATION 
    match = of.ofp_match.from_packet(packet)

    flow_mod = of.ofp_flow_mod()
    flow_mod.match = match
    flow_mod.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))

    event.connection.send(flow_mod)

    # ALSO FORWARD CURRENT PACKET
    msg = of.ofp_packet_out()
    msg.data = event.ofp
    msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
    event.connection.send(msg)


def launch():
    log.info("Traffic Classification Controller with Flow Rules Running...")
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)