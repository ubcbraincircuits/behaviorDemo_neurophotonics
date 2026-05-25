# DeepLabCut GUI — Simple Install Guide

This is a clean student-friendly setup for **DeepLabCut with GUI**

Tested target versions:

* `deeplabcut==3.0.0rc6`
* `matplotlib==3.8.4`
* `numpy==1.26.4`
* `napari==0.4.18`
* `napari-deeplabcut==0.2.1.6`

Tested GPU stack:

* `torch==2.5.1`
* `torchvision==0.20.1`
* `torchaudio==2.5.1`
* `pytorch-cuda=12.1`

Useful links:

* DeepLabCut install docs: [https://deeplabcut.github.io/DeepLabCut/docs/installation.html](https://deeplabcut.github.io/DeepLabCut/docs/installation.html)
* DeepLabCut package: [https://pypi.org/project/deeplabcut/](https://pypi.org/project/deeplabcut/)
* PyTorch install page: [https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)
* PyTorch previous versions: [https://pytorch.org/get-started/previous-versions/](https://pytorch.org/get-started/previous-versions/)

---

## Before you start

1. Install **Anaconda**.
2. Open **Anaconda Prompt**.
3. Do everything in a **new environment**.

Do **not** install DeepLabCut in `base`.

---

## Which version should you install?

### Use the GPU version if:

* you have an **NVIDIA GPU**
* or PyTorch GPU already works on your computer

### Use the CPU version if:

* you do **not** have an NVIDIA GPU
* or the GPU install fails
* or you just want the simplest fallback

---

## How to check if GPU already works on your computer

If you already have another PyTorch environment, activate it and run:

```bash
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
```

Example:

```bash
2.5.1
12.1
True
```

This means:

* PyTorch version = `2.5.1`
* CUDA runtime used by PyTorch = `12.1`
* GPU is available = `True`

If you get something like this, the safest choice is usually to install the **same Torch/CUDA combination** in your DeepLabCut environment.

---

# Recommended install: GPU version

```bash
conda create -n DLC3 python=3.10.13 -y
conda activate DLC3
conda install pytorch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 pytorch-cuda=12.1 -c pytorch -c nvidia -y
pip install --pre "deeplabcut[gui]==3.0.0rc6"
pip install matplotlib==3.8.4 numpy==1.26.4 napari==0.4.18 napari-deeplabcut==0.2.1.6
```

## Check that it worked

```bash
python -c "import torch, deeplabcut, napari, napari_deeplabcut; print('torch', torch.__version__); print('cuda', torch.version.cuda); print('gpu?', torch.cuda.is_available()); print('dlc', deeplabcut.__version__); print('napari', napari.__version__)"
```

## Launch the GUI

```bash
python -m deeplabcut
```

---

# Fallback install: CPU version

Use this only if the GPU version does not work.

```bash
conda create -n DLC3_cpu python=3.10.13 -y
conda activate DLC3_cpu
conda install pytorch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 cpuonly -c pytorch -y
pip install --pre "deeplabcut[gui]==3.0.0rc6"
pip install matplotlib==3.8.4 numpy==1.26.4 napari==0.4.18 napari-deeplabcut==0.2.1.6
```

## Check that it worked

```bash
python -c "import torch, deeplabcut; print('torch', torch.__version__); print('gpu?', torch.cuda.is_available()); print('dlc', deeplabcut.__version__)"
```

For CPU install, `gpu?` should be `False`.

## Launch the GUI

```bash
python -m deeplabcut
```

---

## If you are not sure what CUDA/Torch to install

### Best case

If you already have a working PyTorch environment, run:

```bash
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
```

Then copy that same Torch/CUDA setup into the new DeepLabCut environment.

### If they do not already have a working PyTorch setup

Use the official PyTorch install page and choose:

* OS: your computer's OS
* Package: **Conda**
* Language: **Python**
* Compute Platform: the recommended CUDA version for your machine

If you are unsure, use the **CPU version** above.

---

## Troubleshooting

```bash
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
python -c "import deeplabcut; print(deeplabcut.__version__)"
python -c "import napari; print(napari.__version__)"
python -c "import napari_deeplabcut; print(napari_deeplabcut.__version__)"
```

---

## Clean reinstall

If the environment gets messy, delete it and start over:

```bash
conda deactivate
conda env remove -n DLC3 -y
```

or, for the CPU version:

```bash
conda deactivate
conda env remove -n DLC3_cpu -y
```

---

## Very short version

### GPU

```bash
conda create -n DLC3 python=3.10.13 -y
conda activate DLC3
conda install pytorch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 pytorch-cuda=12.1 -c pytorch -c nvidia -y
pip install --pre "deeplabcut[gui]==3.0.0rc6"
pip install matplotlib==3.8.4 numpy==1.26.4 napari==0.4.18 napari-deeplabcut==0.2.1.6
python -m deeplabcut
```

### CPU

```bash
conda create -n DLC3_cpu python=3.10.13 -y
conda activate DLC3_cpu
conda install pytorch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 cpuonly -c pytorch -y
pip install --pre "deeplabcut[gui]==3.0.0rc6"
pip install matplotlib==3.8.4 numpy==1.26.4 napari==0.4.18 napari-deeplabcut==0.2.1.6
python -m deeplabcut
```
