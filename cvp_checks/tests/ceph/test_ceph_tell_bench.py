import pytest
import json
import math


def test_ceph_tell_bench(local_salt_client):
    """
    Test checks that each OSD MB per second speed 
    is not lower than 10 MB comparing with AVG. 
    Bench command by default writes 1Gb on each OSD 
    with the default values of 4M 
    and gives the "bytes_per_sec" speed for each OSD.

    """
    ceph_monitors = local_salt_client.cmd(
        'ceph:mon', 
        'test.ping', 
        expr_form='pillar')

    if not ceph_monitors:
        pytest.skip("Ceph is not found on this environment")

    cmd_result = local_salt_client.cmd(
        ceph_monitors.keys()[0], 
        'cmd.run', ["ceph tell osd.* bench -f json"], 
        expr_form='glob').get(
            ceph_monitors.keys()[0]).split('\n')

    cmd_result = filter(None, cmd_result)

    osd_pool = {}
    for osd in cmd_result:
        osd_ = osd.split(" ")
        osd_pool[osd_[0]] = osd_[1]

    mbps_sum = 0
    osd_count = 0
    for osd in osd_pool:
        osd_count += 1
        mbps_sum += json.loads(
            osd_pool[osd])['bytes_per_sec'] / 1000000

    mbps_avg = mbps_sum / osd_count
    result = {}
    for osd in osd_pool:
        mbps = json.loads(
            osd_pool[osd])['bytes_per_sec'] / 1000000
        if math.fabs(mbps_avg - mbps) > 10:
            result[osd] = osd_pool[osd]

    assert len(result) == 0, \
    "Performance of {} OSD lower " \
    "than AVG performance, " \
    "please check Ceph for possible problems".format(
        json.dumps(result, indent=4))
