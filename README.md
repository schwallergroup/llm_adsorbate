<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/repo_logo_dark.png" width='100%'>
  <source media="(prefers-color-scheme: light)" srcset="./assets/repo_logo_light.png" width='100%'>
  <img alt="Project logo" src="./assets/logo.png" width="100%">
</picture>

<br>


[![Cookiecutter template from @SchwallerGroup](https://img.shields.io/badge/Cookiecutter-schwallergroup-blue)](https://github.com/schwallergroup/liac-repo)
[![Learn more @SchwallerGroup](https://img.shields.io/badge/Learn%20%0Amore-schwallergroup-blue)](https://schwallergroup.github.io)




<h1 align="center">
  adsKRK
</h1>


<br>

LLM hackathon - An LLM agent system for the autonomous exploration of stable absorbate structures on catalytic surfaces.

## 👩‍💻 Installation
The most recent code and data can be installed directly from GitHub with:

```bash
$ pip install git+https://github.com/schwallergroup/llm_adsorbate.git
```

## 🔥 Usage
This project is used via its Streamlit interface.
```shell
streamlit run src/app/app.py
```

Then, provide the required inputs ( SMILES, XYZ file, and your query) in the sidebar nad click "Run Agent".
