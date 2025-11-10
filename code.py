#importando bibliotecas necessárias
%matplotlib inline
import qiskit, math
from IPython.display import display
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit, transpile
from qiskit.circuit.library import *
from qiskit.quantum_info import Statevector, DensityMatrix, state_fidelity
from qiskit.visualization import plot_bloch_multivector, plot_bloch_vector, plot_state_qsphere, plot_state_city, plot_histogram
from qiskit_aer import Aer, AerSimulator
from qiskit.providers.basic_provider import BasicSimulator
import numpy as np
import random
import matplotlib.pyplot as plt

def get_psswd(num_qubits):
  senha = random.randint(0, 2**num_qubits - 1)  # Senha aleatória entre 0 e 2^n - 1
  senha_bin = format(senha, f'0{num_qubits}b')  # Converte senha para binário ex: 01011011
  return senha, senha_bin

def oracle(circuit, senha_bin, num_qubits):
    # 1. Aplica X nos qubits que representam '0' na senha.
    #    Isso transforma o estado alvo (senha) em |111...1⟩
    #    para que a porta MCX o reconheça.
    for i, bit in enumerate(reversed(senha_bin)):
        if bit == '0':
            circuit.x(i)  # Porta X (NOT quântico)

    # 2. Aplica uma inversão de fase controlada:
    #    - H: muda a base para transformar a inversão de fase em inversão de amplitude.
    #    - MCX: inverte a fase do estado |111...1⟩ (equivalente à senha correta).
    #    - H: retorna à base original.
    circuit.h(num_qubits - 1)  # Porta Hadamard
    circuit.mcx(list(range(num_qubits - 1)), num_qubits - 1)  # Multi-Controlled-X
    circuit.h(num_qubits - 1)  # Porta Hadamard

    # 3. Desfaz as inversões iniciais (retorna os qubits ao estado original)
    for i, bit in enumerate(reversed(senha_bin)):
        if bit == '0':
            circuit.x(i)  # Porta X novamente (reverte a preparação)

def diffuser(circuit, num_qubits):
    # 1. Aplica H e X para mover o espaço de estados à base onde a média é refletida.
    circuit.h(range(num_qubits))  # Cria superposição uniforme
    circuit.x(range(num_qubits))  # Inverte |0⟩ ↔ |1⟩

    # 2. Inverte o estado |111...1⟩ (reflexão no eixo da média)
    circuit.h(num_qubits - 1)
    circuit.mcx(list(range(num_qubits - 1)), num_qubits - 1)
    circuit.h(num_qubits - 1)

    # 3. Desfaz as transformações (volta à base computacional)
    circuit.x(range(num_qubits))
    circuit.h(range(num_qubits))

def init_circ(num_qubits):
  qr = QuantumRegister(num_qubits)
  cr = ClassicalRegister(num_qubits)
  circuit = QuantumCircuit(qr, cr)

  circuit.h(qr)  # Porta Hadamard em todos os qubits
  return circuit, qr, cr

def iterar(circuit, num_qubits, senha_bin):
  iterations = int(np.pi / 4 * np.sqrt(2 ** num_qubits))
  for _ in range(iterations):
      oracle(circuit, senha_bin, num_qubits)
      diffuser(circuit, num_qubits)
  return iterations

def measure_circ(circuit, shots, qr, cr):
  circuit.measure(qr, cr)  # Mede todos os qubits

  sim = AerSimulator()
  compiled = transpile(circuit, sim)
  job = sim.run(compiled, shots=shots)
  result = job.result()
  counts = result.get_counts()

  circuit.draw('mpl')
  return counts

def tentar_classico(num_qubits, senha):
  tentativas_classicas = 0  # força bruta
  todas_as_senhas = list(range(0, 2** num_qubits))  # espaço de busca
  random.shuffle(todas_as_senhas)  # embaralha
  for tentativa in todas_as_senhas:  # busca clássica
      tentativas_classicas += 1
      if tentativa == senha:
          tentativa_bruta = tentativa
          break
  return tentativas_classicas, tentativa_bruta

import time

dados_classico = []
dados_quantico = []
tempo = 0

for num_qubits in range(2, 100):  # evita num_qubits=0 e 1 (não faz sentido)
    if tempo > 60 * 10: break
    start = time.perf_counter()

    senha, senha_bin = get_psswd(num_qubits)
    circuit, qr, cr = init_circ(num_qubits)
    iterations = iterar(circuit, num_qubits, senha_bin)
    counts = measure_circ(circuit, 1000, qr, cr)
    tentativas_classicas, tentativa_bruta = tentar_classico(num_qubits, senha)

    quantum_found = max(counts, key=counts.get)
    quantum_prob = counts[quantum_found] / sum(counts.values())

    print(f"\n--- {num_qubits} QUBITS ---")
    print(f"Senha: {senha} (binário: {senha_bin})")
    print(f"Clássico: {tentativas_classicas} tentativas")
    print(f"Quântico: {iterations} iterações (~√N = {int(np.sqrt(2**num_qubits))})")
    print(f"Resultado mais provável: {int(quantum_found, 2)} com {quantum_prob:.2%} de probabilidade")

    dados_classico.append(tentativas_classicas)
    dados_quantico.append(iterations)

    end = time.perf_counter()
    tempo = end - start
    print(f"Tempo de execução: {tempo} s")

# --- Gráfico comparativo ---
plt.figure(figsize=(10,6))
plt.plot(range(2, 2 + len(dados_classico)), dados_classico, 'o-', label='Clássico (N)')
plt.plot(range(2, 2 + len(dados_quantico)), dados_quantico, 's-', label='Quântico (√N)')
plt.yscale('log')
plt.xlabel('Número de qubits')
plt.ylabel('Iterações')
plt.title('Comparação de Escalabilidade: Clássico vs Quântico (Grover)')
plt.legend()
plt.grid(True)
plt.show()

