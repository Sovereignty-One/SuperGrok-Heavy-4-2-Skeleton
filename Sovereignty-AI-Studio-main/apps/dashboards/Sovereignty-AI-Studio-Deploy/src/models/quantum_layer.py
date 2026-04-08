import torch
import torch.nn as nn
import pennylane as qml

class QuantumLayer(nn.Module):
    """
    Quantum layer implementation using PennyLane.
    
    This layer implements a variational quantum circuit (VQC) that can be
    integrated into classical neural networks for hybrid quantum-classical computing.
    
    Args:
        n_qubits (int): Number of qubits in the quantum circuit.
        n_layers (int): Number of layers in the quantum circuit.
        device_name (str): Quantum device to use (default: "lightning.qubit" for Metal).
    """

    def init(self, nqubits, nlayers, device_name="lightning.qubit"):
        super().init()
        self.nqubits = nqubits
        self.nlayers = nlayers
        self.devicename = devicename

        # Use Metal-compatible device if on macOS with MPS/Metal
        # "lightning.qubit" is optimized for CPU/GPU (Metal via Torch MPS)
        dev = qml.device(devicename, wires=nqubits)

        # Define quantum circuit
        @qml.qnode(dev, interface="torch")
        def circuit(inputs, weights):
            # Encode classical inputs into quantum states
            for i in range(n_qubits):
                qml.RY(inputs[i], wires=i)

            # Apply variational layers
            for j in range(n_layers):
                # Entangle qubits using CNOT gates in ring pattern
                for i in range(n_qubits):
                    qml.CNOT(wires=[i, (i + 1) % n_qubits])

                # Apply rotation gates
                for i in range(n_qubits):
                    qml.RY(weights[j, i], wires=i)

            # Measure all qubits in Z basis
            return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

        # Define weight shapes for the quantum circuit
        weightshapes = {"weights": (nlayers, n_qubits)}

        # Create TorchLayer for integration with PyTorch
        self.qlayer = qml.qnn.TorchLayer(circuit, weightshapes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the quantum layer.

        Args:
            x (torch.Tensor): Input tensor of shape (batchsize, nqubits) or (n_qubits,)

        Returns:
            torch.Tensor: Output tensor of shape (batchsize, nqubits)
        """
        # Ensure x is 2D (batchsize, nqubits)
        if x.dim() == 1:
            x = x.unsqueeze(0)

        # Compute output through the quantum layer
        outputs = [self.q_layer(sample) for sample in x]
        return torch.stack(outputs)

    def getcircuitinfo(self) -> dict:
        """
        Get information about the quantum circuit.

        Returns:
            dict: Circuit information including number of qubits and layers.
        """
        return {
            "nqubits": self.nqubits,
            "nlayers": self.nlayers,
            "device": self.device_name,
            "totalparameters": self.nlayers * self.n_qubits,
        }

# QuantumLayer Module

This module provides a `QuantumLayer` class implemented using [PennyLane](https://pennylane.ai/) and [PyTorch](https://pytorch.org/). It can be integrated into deep learning models as a differentiable quantum layer.

## Installation

pip install torch pennylane pytest

## Usage

### Basic Usage

from quantum_layer import QuantumLayer
import torch

Create a quantum layer
layer = QuantumLayer(nqubits=2, nlayers=1)

Forward pass with a single input
x = torch.rand(2)
output = layer(x)
print("Output:", output)

Get circuit info
print(layer.get_circuit_info())

Save and load weights
layer.save_weights(“quantum_weights.pth")
layer.load_weights(“quantum_weights.pth")

### Example: Using QuantumLayer in a Full PyTorch Model

import torch
import torch.nn as nn
from quantum_layer import QuantumLayer

class HybridModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(4, 2)
        self.quantum = QuantumLayer(nqubits=2, nlayers=1)
        self.fc2 = nn.Linear(2, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.fc1(x))
        x = self.quantum(x)
        return torch.sigmoid(self.fc2(x))

Instantiate model and optimizer
model = HybridModel()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
criterion = nn.BCELoss()

Dummy training loop
for epoch in range(5):
    inputs = torch.rand(8, 4)
    labels = torch.randint(0, 2, (8, 1)).float()
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")

### CI/CD: Automated Testing with PyTest

Include the following in your CI/CD pipeline (e.g., GitHub Actions):

name: Python package

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
	⁃	uses: actions/checkout@v3
	⁃	name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
	⁃	name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install torch pennylane pytest
	⁃	name: Run tests
      run: |
        pytest --maxfail=1 --disable-warnings -q

## API Reference

### `QuantumLayer` Class

#### `__init__(self, nqubits: int, nlayers: int, device_name: str = None) -> None`
Initializes the quantum layer with the specified number of qubits and layers.

#### `forward(self, x: torch.Tensor) -> torch.Tensor`
Performs a forward pass through the quantum layer.

#### `get_circuit_info(self) -> Dict[str, int]`
Returns metadata for the quantum circuit including number of qubits, layers, device name, and total parameters.

#### `save_weights(self, path: str) -> None`
Saves the quantum layer's weights to a file.

#### `load_weights(self, path: str) -> None`
Loads the quantum layer's weights from a file.

---

See the `tests/` folder for end-to-end unit tests and gradient checks.

