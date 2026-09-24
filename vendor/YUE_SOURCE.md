# vendor/YuE — where it comes from

`vendor/YuE` is an **unmodified copy** of the official YuE2 repository
<https://github.com/multimodal-art-projection/YuE>, main branch as of September 2026 (package `yue2-infer` 0.1.6).

- The inference code (`src/yue2/`) and the skill scripts (`skills/yue2-music/scripts/`) are identical to the release tag
  [`yue2-v0.1.6`](https://github.com/multimodal-art-projection/YuE/releases/tag/yue2-v0.1.6).
- Documentation, README, `pyproject.toml` and the license files come from the later main-branch commit, which
  licenses the **code** under Apache-2.0 (`LICENSE`) and adds the 2026-09-16 individual-creator permission to the
  **model-weight** license (`MODEL_LICENSE`, CC BY-NC 4.0). The release tag itself still declared CC-BY-NC-4.0 for the code.
- Left out: the upstream `tests/` and `.github/` folders.

It is bundled so that installing needs no access to GitHub. YuE Studio does not change these files; at install time
`scripts/patch_windows.py` patches the *installed copy* in `.venv` (FlashAttention detection and a GQA memory fix for
Windows). All copyright belongs to the YuE2 authors; see `LICENSE`, `MODEL_LICENSE` and `THIRD_PARTY_NOTICES.md` here.
