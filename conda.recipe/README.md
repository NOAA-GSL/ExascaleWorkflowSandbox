# Conda Recipe for Chiltepin

This directory contains the conda-forge recipe for the Chiltepin package.

## Testing the Recipe Locally

Before submitting to conda-forge, test the recipe locally:

```bash
# Install conda-build if needed
conda install conda-build

# Build the recipe
conda build conda.recipe/

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
   # Download the tarball and compute its hash
   wget https://pypi.io/packages/source/c/chiltepin/chiltepin-0.1.0.tar.gz
   sha256sum chiltepin-0.1.0.tar.gz
   # Update the sha256 field in meta.yaml
   ```

3. **Fork staged-recipes**:
   - Go to https://github.com/conda-forge/staged-recipes
   - Click "Fork" to create your fork

4. **Add your recipe**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/staged-recipes.git
   cd staged-recipes
   git checkout -b add-chiltepin
   cp -r /path/to/chiltepin/conda.recipe recipes/chiltepin
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

When releasing a new version:

1. Update the `version` variable in `meta.yaml`
2. Update the `sha256` hash for the new tarball
3. Reset `build: number:` to 0
4. Submit a PR to the feedstock repository

## Resources

- [conda-forge documentation](https://conda-forge.org/docs/)
- [Contributing packages guide](https://conda-forge.org/docs/maintainer/adding_pkgs.html)
- [Example recipes](https://github.com/conda-forge/staged-recipes/tree/main/recipes)
