# GitHub Terminal Commands

```bash
cd ~/Downloads
unzip -o DataCentreWaterFootprintOptimizer_Local_Complete_GitHub.zip
cd AquaCompute_Local_GitHub_Package

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

## Push to GitHub

```bash
cd ~/Downloads/AquaCompute_Local_GitHub_Package

rm -f .git/index.lock

git init
git branch -M main
git add .
git status
git commit -m "feat: add AquaCompute Local data-centre water footprint optimizer"

gh auth login

gh repo create data-centre-water-footprint-optimizer   --public   --description "Privacy-conscious, local-first data-centre water-footprint screening and optimization platform with explainable cooling, workload, weather, water-stress, reuse, and operational analytics."

git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/shaunakmirajgaonkar/data-centre-water-footprint-optimizer.git
git push -u origin main
```

## Future updates

```bash
cd ~/Downloads/AquaCompute_Local_GitHub_Package
rm -f .git/index.lock
git add .
git commit -m "feat: update AquaCompute Local"
git push
```

Never run `git add .` from `~`; use the project directory.
