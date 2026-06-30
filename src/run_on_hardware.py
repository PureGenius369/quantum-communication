"""
Run a Bell pair on REAL IBM quantum hardware -- and compare to the ideal simulator.

This is the "hello world" of real quantum hardware. A Bell pair should give only
'00' and '11' (50/50). On a real chip, noise produces a few '01'/'10' counts that
should not exist -- and that gap IS the story: it shows what real qubits do.

Prerequisites:
  - You have already saved your account once (setup_account.py).
  - pip install qiskit qiskit-aer qiskit-ibm-runtime matplotlib

Budget note:
  Runs ONE small circuit. Uses only a few seconds of your monthly QPU time.
  Do not put this in a loop.

Run:
    python src/run_on_hardware.py
"""

import os
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

SHOTS = 2048


def bell_circuit():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)          # entangle: creates (|00> + |11>)/sqrt(2)
    qc.measure_all()     # measures into a classical register named "meas"
    return qc


def run_simulator(qc):
    """Ideal, noiseless reference."""
    counts = AerSimulator().run(qc, shots=SHOTS).result().get_counts()
    return counts


def run_hardware(qc):
    """Submit to a real IBM quantum processor and wait for the result."""
    service = QiskitRuntimeService()
    backend = service.least_busy(operational=True, simulator=False)
    print(f"Selected real backend: {backend.name} ({backend.num_qubits} qubits)")

    # Rewrite the circuit using only gates/connections this chip physically has.
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_circuit = pm.run(qc)

    sampler = SamplerV2(mode=backend)
    job = sampler.run([isa_circuit], shots=SHOTS)
    print(f"Job submitted. ID: {job.job_id()}")
    print("Waiting in the queue... (this can take minutes to an hour)")

    result = job.result()
    counts = result[0].data.meas.get_counts()
    return backend.name, counts


def plot_comparison(sim_counts, hw_counts, hw_name):
    os.makedirs("figures", exist_ok=True)
    labels = ["00", "01", "10", "11"]
    sim = [sim_counts.get(l, 0) for l in labels]
    hw = [hw_counts.get(l, 0) for l in labels]

    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([i - 0.2 for i in x], sim, width=0.4, label="Ideal simulator",
           color="#2a9d8f")
    ax.bar([i + 0.2 for i in x], hw, width=0.4, label=f"Real hardware ({hw_name})",
           color="#e76f51")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_xlabel("measurement outcome")
    ax.set_ylabel(f"counts (out of {SHOTS} shots)")
    ax.set_title("Bell pair: ideal vs. real quantum hardware")
    ax.legend()
    fig.tight_layout()
    fig.savefig("figures/bell_sim_vs_hardware.png", dpi=150)
    print("Saved figures/bell_sim_vs_hardware.png")


def main():
    qc = bell_circuit()

    print("=== Ideal simulator ===")
    sim_counts = run_simulator(qc)
    print(sim_counts)

    print("\n=== Real IBM quantum hardware ===")
    hw_name, hw_counts = run_hardware(qc)
    print(hw_counts)

    # The '01' and '10' outcomes should be ~0 ideally; on hardware they are not.
    noise = sum(hw_counts.get(l, 0) for l in ["01", "10"]) / SHOTS
    print(f"\nHardware noise (forbidden 01/10 outcomes): {noise:.1%}")

    plot_comparison(sim_counts, hw_counts, hw_name)


if __name__ == "__main__":
    main()
