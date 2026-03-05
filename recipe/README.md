# Conda Recipe for Chiltepin

This directory contains the conda-forge recipe for the Chiltepin package.

## Testing the Recipe Locally

Before submitting to conda-forge, test the recipe locally:

```bash
# Install conda-build if needed
conda install conda-build

# Build the recipe
conda build recipe/

# Test install
conda create -n test-chiltepin chiltepin --use-local
conda activate test-chiltepin
chiltepin --help
```

## Submitting to conda-forge

1. **Publish to PyPI first** (conda-forge prefers PyPI sources):
   ```bash
   python -m build
   twine upload dist/*
   ```

2. **Update the SHA256 hash** in `meta.yaml`:
   ```bash
   # After publishing to PyPI, download and compute hash
   pip download chiltepin==0.1.0 --no-deps --no-binary :all:
   sha256sum chiltepin-0.1.0.tar.gz
   # Copy the hash and update the sha256 field in meta.yaml
   ```
   
   **Why PyPI tarball instead of git?**
   - PyPI is the official distribution channel for Python packages
   - Tarballs are immutable - the hash ensures content never changes
   - Faster builds (no git history to clone)
   - This is the conda-forge recommended practice

3. **Fork staged-recipes**:
   - Go to https://github.com/conda-forge/staged-recipes
   - Click "Fork" to create your fork

4. **Add your recipe**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/staged-recipes.git
   cd staged-recipes
   git checkout -b add-chiltepin
   cp -r /path/to/chiltepin/recipe recipes/chiltepin
   git add recipes/chiltepin
   git commit -m "Add chiltepin recipe"
   git push origin add-chiltepin
   ```

5. **Open a Pull Request**:
   - Go to your fork on GitHub
   - Click "Compare & pull request"
   - Fill out the PR template
   - Wait for automated tests and reviews

6. **After Merge**:
   - A `chiltepin-feedstock` repository will be automatically created
   - You'll be added as a maintainer
   - Future version updates are done via PRs to the feedstock

## Updating the Recipe for New Versions

**After your package is on conda-forge**, version updates are done in the **feedstock repository**, not this repo.

### First-time submission:
- Use `recipe/meta.yaml` from this repo
- Submit to `conda-forge/staged-recipes`

### For all future releases:
1. Release new version and publish to PyPI
2. Fork `https://github.com/conda-forge/chiltepin-feedstock`
3. Update `recipe/meta.yaml` in the **feedstock**:
   - Update `version` variable
   - Update `sha256` hash for new tarball
   - Reset `build: number:` to 0
4. Submit PR to the feedstock repository
5. Automated bots will help test and merge

**Note:** The `meta.yaml` in this repo serves as a reference/template.
After initial submission, the feedstock repository becomes the source of truth.

## Resources

- [conda-forge documentation](https://conda-forge.org/docs/)
- [Contributing packages guide](https://conda-forge.org/docs/maintainer/adding_pkgs.html)
- [Example recipes](https://github.com/conda-forge/staged-recipes/tree/main/recipes)
