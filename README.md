# 01-reliable-json-

Experiment comparing 5 ways to get reliable JSON out of an LLM (Claude), using an "appointments backend" as the use case: the user writes in natural language (reschedule, cancel, check an appointment, or ask for clarification) and the model has to translate that into a JSON with a fixed shape.

The goal is to measure, for each method: is the text the model returns valid JSON?, does it match the schema?, does it exactly match the expected output?, how many tokens and how much time does it cost?, are retries needed?

## The 5 methods

| Method | What it does |
|---|---|
| `prompt_only` | Asks for the JSON via instructions in the prompt and parses the response as-is |
| `prompt_only_limpio` | Same as above, but strips ` ```json ` code fences and extra text around the JSON before parsing |
| `tool_use` | Gives the model a *tool* whose `input_schema` is the schema, and forces it to use it (`tool_choice`) |
| `structured` | Passes the schema to the API (`output_config.format`) so it enforces it on the response |
| `structured_validated` | Same as `structured`, but validates the output and, if it fails, sends it back to the model asking it to fix it (up to 2 retries) |

All of them share the same system prompt, which includes a basic prompt-injection defense (if the user's text tries to give instructions, the model must respond with `pedir_aclaracion`).

## Structure

- **`config.py`** — model, JSON schema (`MOLDE`), system prompt. Loads `ANTHROPIC_API_KEY` from `.env`.
- **`dataset.jsonl`** — 100 test cases (`id`, `tipo`, `texto`, `esperado`). Types include `claro` (clear), `rebuscado` (convoluted), `ambiguo` (ambiguous), and `malicioso` (prompt-injection cases).
- **`metodos.py`** — implementation of the 5 methods from the table above.
- **`comprobar.py`** — validations: `leer_json`/`extraer_json` (parsing), `comprobar_molde` (shape), `comprobar_sentido` (business rules), `puntuar` (compares against the expected output).
- **`ejecutar.py`** — runs the dataset against the 5 methods and saves each result to `results/results_<date>.jsonl`.
- **`informe.py`** — reads a results file and summarizes it in tables: % valid JSON, % schema match, % exact match, tokens, latency, retries — broken down by method and by text type.

## Installation

```bash
pip install anthropic python-dotenv
```

Create a `.env` file at the root with your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

(Optional) to use a different model instead of `claude-haiku-4-5`:

```
MODEL=claude-sonnet-5
```

## Usage

Small test run (a few cents):

```bash
python3 ejecutar.py --limit 10
```

Full dataset:

```bash
python3 ejecutar.py
```

Repeat each case multiple times (to average results):

```bash
python3 ejecutar.py --repeticiones 3
```

Re-view the report from a previous run without spending anything:

```bash
python3 informe.py results/results_20261012_153000.jsonl
```
