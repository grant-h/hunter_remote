# Hunter Fan Remote Tools
A set of flowgraphs to send and receive commands to Hunter fans and a QT GUI of a virtual fan controller.
See the companion blog post for details:
[https://hernan.de/blog/virtualizing-a-fan-controller-with-gnu-radio/](https://hernan.de/blog/virtualizing-a-fan-controller-with-gnu-radio/)

To use the GUI a working GNU Radio install (PyBOMBS recommended) is required. For the hunter_remote_decode flowgraph, the  [gr-satellites](https://github.com/daniestevez/gr-satellites) package is required. Flowgraphs tested on GNU Radio Companion 3.8.3.1.

## Index

* grc/ - GNU Radio flowgraphs
* grc/recordings/ - Sample Hunter remote recordings (gziped)
* hunterctl.py - The Hunter GUI main
* hunter_tx.py - The Hunter TX driver that uses GNU Radio libraries
* decoding_notes.txt - Notes on the protocol
