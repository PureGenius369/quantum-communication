"""
Quantum Teleportation
=====================

Transfers an arbitrary single-qubit state |psi> from Alice's qubit to Bob's
qubit using one shared Bell pair and two classical bits. No quantum information
travels down the wire -- only two classical bits do.

Verification trick
------------------
We never get to "see" a quantum state directly. So to prove teleportation
worked, we prepare |psi> on the source qubit with a known circuit U, teleport
it, then apply U-dagger on Bob's qubit. If teleportation was perfect, Bob's
qubit returns to |0> and every measurement reads 0. A non-zero count would
signal a bug.

Run:
    python src/teleportation.py
"""

import os
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator


def state_prep(theta: float, phi: float) -> QuantumCircuit:
    """Circuit U that maps |0> -> cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>."""
    qc = QuantumCircuit(1, name="U(psi)")
    qc.ry(theta, 0)
    qc.rz(phi, 0)
    return qc


def build_teleportation_circuit(theta: float, phi: float) -> QuantumCircuit:
    psi = QuantumRegister(1, "psi")    # Alice's payload qubit
    a = QuantumRegister(1, "a")        # Alice's half of the Bell pair
    b = QuantumRegister(1, "b")        # Bob's half of the Bell pair
    cr = ClassicalRegister(2, "m")     # Alice's two measured bits
    out = ClassicalRegister(1, "out")  # Bob's verification readout
    qc = QuantumCircuit(psi, a, b, cr, out)

    # 1. Prepare the unknown state on Alice's payload qubit.
    qc.compose(state_prep(theta, phi), qubits=psi, inplace=True)
    qc.barrier()

    # 2. Distribute a Bell pair between Alice (a) and Bob (b).
    qc.h(a)
    qc.cx(a, b)
    qc.barrier()

    # 3. Alice entangles her payload with her Bell half and measures both.
    qc.cx(psi, a)
    qc.h(psi)
    qc.measure(psi, cr[0])
    qc.measure(a, cr[1])
    qc.barrier()

    # 4. Bob corrects his qubit using Alice's two classical bits.
    with qc.if_test((cr[1], 1)):
        qc.x(b)
    with qc.if_test((cr[0], 1)):
        qc.z(b)
    qc.barrier()

    # 5. Verification: undo U on Bob's qubit; a perfect teleport gives |0>.
    qc.compose(state_prep(theta, phi).inverse(), qubits=b, inplace=True)
    qc.measure(b, out)
    return qc


def main():
    rng = np.random.default_rng(7)
    theta = rng.uniform(0, np.pi)
    phi = rng.uniform(0, 2 * np.pi)
    print(f"Teleporting state with theta={theta:.3f}, phi={phi:.3f}")

    qc = build_teleportation_circuit(theta, phi)
    sim = AerSimulator()
    shots = 4096
    result = sim.run(qc, shots=shots).result()
    counts = result.get_counts()

    # Bob's verification bit is the leftmost classical register ("out").
    bob_zero = sum(c for bits, c in counts.items() if bits.split()[0] == "0")
    fidelity = bob_zero / shots
    print(f"Bob's qubit returned to |0> in {bob_zero}/{shots} shots "
          f"(success = {fidelity:.4f})")
    assert fidelity > 0.99, "Teleportation verification failed!"
    print("PASS: arbitrary state teleported with fidelity > 0.99")

    os.makedirs("figures", exist_ok=True)
    try:
        qc.draw("mpl", fold=-1).savefig("figures/teleportation_circuit.png",
                                        dpi=150, bbox_inches="tight")
        print("Saved figures/teleportation_circuit.png")
    except Exception as e:
        print(f"(circuit figure skipped: {e})")


if __name__ == "__main__":
    main()
