# Evaluation

`dataset.json` holds 41 short academic paragraphs with 35 gold issues (and 8 clean paragraphs to measure false alarms). Each gold issue has an exact phrase, a category and a list of acceptable fixes.

**Labeling:** the labels were written by the AI assistant that helped build DocOcto. They have **not** been reviewed by independent humans. Before you quote results anywhere, read every label and correct the ones you disagree with.

Run it:
```
source .venv/bin/activate
python eval/run_eval.py --systems rules                 # always works, no setup
python eval/run_eval.py --systems rules,lt,combined      # after installing LanguageTool (see README)
python eval/run_eval.py --systems rules,lt,ai,combined   # also needs Ollama or a free API key in .env
```
Output: `eval/RESULTS.md` (readable table, definitions and limitations) and `eval/results/latest.json`. Systems that cannot run are listed as "not run", never scored as zero.

The AI prompt in `run_eval.py` is a copy of the one in `public/index.html`. If you change one, change the other.
