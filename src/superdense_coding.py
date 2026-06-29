"""
Superdense Coding
=================

The dual of teleportation: Alice sends TWO classical bits to Bob by physically
transmitting only ONE qubit -- provided they pre-share a Bell pair.

Protocol
--------
1. Alice and Bob share a Bell pair (Alice holds qubit a, Bob holds qubit b).
2. To send the two-bit message m1 m0, Alice applies a local gate to her qubit:
       00 -> I        01 -> X        10 -> Z        11 -> Z then X  (i.e. ZX)
3. Alice sends her single qubit to Bob.
4. Bob undoes the Bell entanglement (CX then H) and measures both qubits,
   recovering m1 m0 exactly.

This file sends all four messages and checks each one decodes perfectly.

Run:
    python src/superdense_coding.py
"""

import os
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def encode_decode_circuit(message: str) -> QuantumCircuit:
    """Build the full superdense-coding circuit for a 2-bit message 'm1m0'."""
    qc = QuantumCircuit(2, 2)

    # Shared Bell pair: qubit 0 = Alice, qubit 1 = Bob.
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()

    # Alice encodes two classical bits with one local gate on her qubit.
    m1, m0 = message[0], message[1]
    if m0 == "1":
        qc.x(0)
    if m1 == "1":
        qc.z(0)
    qc.barrier()

    # Alice ships her qubit to Bob; Bob disentangles and reads both qubits.
    qc.cx(0, 1)
    qc.h(0)
    # Qiskit prints bitstrings little-endian (c[1]c[0]). Route Alice's qubit
    # (carries the Z bit = m1) to c[1] and Bob's qubit (X bit = m0) to c[0] so
    # the printed string reads "m1m0" directly.
    qc.measure(0, 1)
    qc.measure(1, 0)
    return qc


def main():
    sim = AerSimulator()
    shots = 2048
    print("Sending all four 2-bit messages through one qubit:\n")
    all_ok = True
    for message in ["00", "01", "10", "11"]:
        qc = encode_decode_circuit(message)
        counts = sim.run(qc, shots=shots).result().get_counts()
        decoded = max(counts, key=counts.get)
        ok = decoded == message
        all_ok &= ok
        print(f"  message {message} -> decoded {decoded}  "
              f"({counts.get(message, 0)}/{shots} correct)  "
              f"{'OK' if ok else 'FAIL'}")

    assert all_ok, "Superdense coding failed for at least one message!"
    print("\nPASS: 2 classical bits delivered per transmitted qubit, all messages.")

    os.makedirs("figures", exist_ok=True)
    try:
        encode_decode_circuit("11").draw("mpl", fold=-1).savefig(
            "figures/superdense_circuit.png", dpi=150, bbox_inches="tight")
        print("Saved figures/superdense_circuit.png")
    except Exception as e:
        print(f"(circuit figure skipped: {e})")


if __name__ == "__main__":
    main()
