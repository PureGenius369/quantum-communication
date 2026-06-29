"""
BB84 Quantum Key Distribution (with eavesdropper detection)
==========================================================

BB84 lets Alice and Bob agree on a secret key over a quantum channel such that
any eavesdropper (Eve) necessarily disturbs the qubits and is exposed by a
raised error rate. This is the foundation of the satellite/photonic QKD work
done at groups like RRI Bangalore.

Each bit is physically encoded in a qubit:
    basis Z (rectilinear): bit 0 -> |0>,  bit 1 -> |1>
    basis X (diagonal):    bit 0 -> |+>,  bit 1 -> |->

Steps
-----
1. Alice picks random bits and random bases, encodes each in a qubit.
2. (Optional) Eve intercepts, measures in a random basis, and resends.
3. Bob measures each qubit in his own random basis.
4. Sifting: keep only positions where Alice's and Bob's bases matched.
5. Estimate the error rate (QBER) on a sample of the sifted key.
   No Eve  -> QBER ~ 0.       Eve present -> QBER ~ 25%.

Run:
    python src/bb84_qkd.py
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

SIM = AerSimulator()


def measure_qubit(bit: int, prep_basis: str, meas_basis: str) -> int:
    """Encode `bit` in `prep_basis`, measure in `meas_basis`, return outcome."""
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        qc.x(0)
    if prep_basis == "X":
        qc.h(0)              # rotate Z eigenstate into X basis
    if meas_basis == "X":
        qc.h(0)              # rotate X back to computational basis to measure
    qc.measure(0, 0)
    counts = SIM.run(qc, shots=1).result().get_counts()
    return int(max(counts, key=counts.get))


def run_bb84(n_bits: int, eavesdropper: bool, seed: int = 1):
    rng = np.random.default_rng(seed)
    alice_bits = rng.integers(0, 2, n_bits)
    alice_bases = rng.choice(["Z", "X"], n_bits)
    bob_bases = rng.choice(["Z", "X"], n_bits)
    eve_bases = rng.choice(["Z", "X"], n_bits)

    bob_results = np.empty(n_bits, dtype=int)
    for i in range(n_bits):
        if eavesdropper:
            # Eve measures (collapsing the qubit) then resends what she saw.
            eve_bit = measure_qubit(alice_bits[i], alice_bases[i], eve_bases[i])
            bob_results[i] = measure_qubit(eve_bit, eve_bases[i], bob_bases[i])
        else:
            bob_results[i] = measure_qubit(alice_bits[i], alice_bases[i],
                                           bob_bases[i])

    # Sifting: keep positions where the bases agree.
    matched = alice_bases == bob_bases
    alice_key = alice_bits[matched]
    bob_key = bob_results[matched]

    qber = np.mean(alice_key != bob_key) if len(alice_key) else 0.0
    return alice_key, bob_key, qber


def main():
    n_bits = 600
    print("=== BB84 with NO eavesdropper ===")
    a_key, b_key, qber = run_bb84(n_bits, eavesdropper=False)
    print(f"  sifted key length: {len(a_key)}   QBER: {qber:.3f}")
    print(f"  keys identical: {np.array_equal(a_key, b_key)}")

    print("\n=== BB84 WITH eavesdropper (Eve) ===")
    a_key_e, b_key_e, qber_e = run_bb84(n_bits, eavesdropper=True)
    print(f"  sifted key length: {len(a_key_e)}   QBER: {qber_e:.3f}")
    print(f"  (theory: Eve forces QBER ~ 0.25 -> attack detected)")

    assert qber < 0.05, "Unexpected errors without an eavesdropper!"
    assert qber_e > 0.15, "Eavesdropper was not detected!"
    print("\nPASS: secure key with no Eve; eavesdropping detected via raised QBER.")

    os.makedirs("figures", exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(["No Eve", "With Eve"], [qber, qber_e],
           color=["#2a9d8f", "#e76f51"])
    ax.axhline(0.11, ls="--", color="gray", label="typical abort threshold")
    ax.set_ylabel("QBER (sifted-key error rate)")
    ax.set_title("BB84: eavesdropping raises the error rate")
    ax.legend()
    fig.tight_layout()
    fig.savefig("figures/bb84_qber.png", dpi=150)
    print("Saved figures/bb84_qber.png")


if __name__ == "__main__":
    main()
