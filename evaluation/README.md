# Evaluation data

Add one reviewed JSON object per line to `questions.jsonl` using this schema:

```json
{"question":"What does the paper say about X?","relevant_chunk_ids":["doc-id:0"],"expected_answer":"A short, evidence-backed reference answer.","answerable":true}
```

Use `answerable: false` and an empty relevant list for questions unsupported by the corpus. Do not put private documents or credentials in this directory. Keep the question set and corpus versioned together so reported comparisons can be reproduced.
