#!/usr/bin/env python3
# Hunter Remote Transmit Flowgraph Controller
#   by Grant H. (https://hernan.de/z)

# GNU Radio Python Flow Graph
# GNU Radio version: v3.8.3.1-16-g9d94c8a6

from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from enum import Enum
import osmosdr
import time

class HunterCommand(Enum):
    ON_TOGGLE = 1
    FAN_0 = 2
    FAN_1 = 3
    FAN_2 = 4
    FAN_3 = 5
    PAIR = 6

class HunterTX(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "HunterTX")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 2e6
        self.freq = freq = 433.92e6
        self.baud = baud = 2500
        self.sps = sps = int(samp_rate/baud)
        self.data = []

        self.PREAMBLE = self._bin2arr("101010101010101010101010000000000000")
        self.COMMAND_GAP = self._bin2arr("0"*62)

        ##################################################
        # Blocks
        ##################################################
        self.osmosdr_sink_0 = osmosdr.sink(
            args="numchan=" + str(1) + " " + ""
        )
        self.osmosdr_sink_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_sink_0.set_sample_rate(samp_rate)
        self.osmosdr_sink_0.set_center_freq(freq, 0)
        self.osmosdr_sink_0.set_freq_corr(0, 0)
        self.osmosdr_sink_0.set_gain(30, 0)
        self.osmosdr_sink_0.set_if_gain(10, 0)
        self.osmosdr_sink_0.set_bb_gain(10, 0)
        self.osmosdr_sink_0.set_antenna('', 0)
        self.osmosdr_sink_0.set_bandwidth(0, 0)
        self.blocks_vector_source_x_0_0 = blocks.vector_source_c(self.data, False, 1, [])
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_gr_complex*1, sps)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_repeat_0, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.blocks_vector_source_x_0_0, 0), (self.blocks_repeat_0, 0))

    def set_cmd(self, cmd):
        self.data = []

        if cmd == HunterCommand.ON_TOGGLE:
            ON_PRESS = "1000000001110111111110"
            ON_RELEASE = "0001001101111110110010"

            self.data += self._mkcmd(ON_PRESS)*2
            self.data += self._mkcmd(ON_RELEASE)*2
        elif cmd == HunterCommand.FAN_0:
            ON_PRESS = "0000000011111111111100"
            ON_RELEASE = "0001000101111110111010"

            self.data += self._mkcmd(ON_PRESS)*2
            self.data += self._mkcmd(ON_RELEASE)*2
        elif cmd == HunterCommand.FAN_1:
            CMD = "0000000101111111111010"
            self.data += self._mkcmd(CMD)*2
        elif cmd == HunterCommand.FAN_2:
            CMD = "0001000001111110111110"
            self.data += self._mkcmd(CMD)*2
        elif cmd == HunterCommand.FAN_3:
            CMD = "0010000001111101111110"
            self.data += self._mkcmd(CMD)*2
        # Pairing not implemented as need continuous transmission until release
        else:
            assert 0

        # Command MUST be padded. Sink requires certain amount of samples before xmit
        self.data += [0]*4096

    def set_addr(self, addr):
        self.addr = self._bin2arr(addr)

    def _mkcmd(self, cmd):
        return self.PREAMBLE + self._encode(self.addr + [0, 1, 0, 0, 0] + self._bin2arr(cmd)) + self.COMMAND_GAP

    def _bin2arr(self, s):
        return [int(b) for b in s]

    def _encode(self, data):
        out_data = []
        for d in data:
            d = int(d)
            if d == 0:
                out_data += [1, 0, 0]
            else:
                out_data += [1, 1, 0]

        return out_data

    def restart(self):
        self.samp_rate = samp_rate = 2e6
        self.freq = freq = 433.92e6
        self.baud = baud = 2500

        # Disconnect and reconnect the vector source to start the flowgraph over
        self.lock()
        self.disconnect((self.blocks_repeat_0, 0), (self.osmosdr_sink_0, 0))
        self.disconnect((self.blocks_vector_source_x_0_0, 0), (self.blocks_repeat_0, 0))

        self.blocks_vector_source_x_0_0 = blocks.vector_source_c(self.data, False, 1, [])
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_gr_complex*1, int(samp_rate/baud))

        self.connect((self.blocks_repeat_0, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.blocks_vector_source_x_0_0, 0), (self.blocks_repeat_0, 0))
        self.unlock()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_baud(self.get_baud())
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_baud(self):
        return self.baud

    def set_baud(self, baud):
        self.baud = baud
        self.sps = int(samp_rate/baud)
        self.blocks_repeat_0.set_interpolation(self.sps)
