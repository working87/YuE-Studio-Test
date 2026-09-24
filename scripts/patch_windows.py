"""Windows compatibility patches for the installed yue2 package (idempotent).

1. cuda_graph.py: Windows PyTorch wheels register aten::_flash_attention_forward but ship
   without FlashAttention kernels, so auto-detection picks "flash" and fails with
   "USE_FLASH_ATTENTION was not enabled for build". Also require the runtime check.
2. nar.py: without FlashAttention, grouped-query SDPA (enable_gqa=True) falls back to the
   math kernel, which materialises the full attention matrix: ~20 GiB for a 3-minute song,
   so synthesis runs out of memory on 16 GB cards. Expanding K/V to all heads (exactly what
   GQA means) lets the memory-efficient kernel run instead (~0.05 GiB). The same expansion
   is already used on MPS.
"""
import importlib.util
from pathlib import Path

root = Path(importlib.util.find_spec("yue2").origin).parent
PATCHES = [
    ("cuda_graph.py",
     'flash = fused and config.head_dim <= 256 and hasattr(torch.ops.aten, "_flash_attention_forward") and (',
     'flash = fused and config.head_dim <= 256 and torch.backends.cuda.is_flash_attention_available() '
     'and hasattr(torch.ops.aten, "_flash_attention_forward") and ('),
    ("nar.py",
     '    if grouped and q.device.type == "mps":',
     '    if grouped and (q.device.type == "mps" or (q.device.type == "cuda" and '
     'not torch.backends.cuda.is_flash_attention_available())):'),
]
for name, old, new in PATCHES:
    target = root / name
    text = target.read_text(encoding="utf-8")
    if new in text:
        print("already patched:", target)
    elif old in text:
        target.write_text(text.replace(old, new), encoding="utf-8")
        print("patched:", target)
    else:
        raise SystemExit(f"Unexpected {name} layout; check {target}")
