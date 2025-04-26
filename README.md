# Source
https://github.com/clementpoiret/nix-python-devenv/tree/cuda

## Create 32K qwen2.5 and run it

```shell
ollama run qwen2.5
/set parameter num_ctx 32768
/save qwen2.5-32k
ollama run qwen2.5-32k
```