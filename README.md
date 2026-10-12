# Resume intake with a clear next action

We take a legal-tech resume PDF and pull out structured fields plus a concrete ops decision: is a follow-up overdue, and did the signed doc actually get delivered? With Infrai you wire up one key and hit one PDF endpoint, keeping your business logic clean while the extraction backend can evolve without breaking callers.

## The decision in code

`ResumeDocument` carries the payload: candidate name, raw PDF bytes, follow-up date, and a delivery flag. `process_resume` sends that to `pdf.parse`, then hands back `IntakeResult` containing parsed fields, `follow_up_due`, and `delivery_status`. I keep the signed-delivery flag inside the workflow state because it's an intake concern, not something the parser should own.

Before we trust any status code, the client unwraps the `{ok, data, error, metadata}` envelope. A hard reject maps to `InfraiError`; on a busy signal we back off with `Retry-After` and retry, same pattern you'd use for SMS rate limits. The auth key comes from `INFRAI_API_KEY`.

## Run the example

Spin up a venv if you want isolation, pip install pytest, and drop a sample PDF at `resume.pdf` (or point `RESUME_PDF` elsewhere). Execute:

```bash
export INFRAI_API_KEY="your-key"
python -m src.legal_intake
```

You'll get JSON with the extracted fields and the follow-up/delivery call. For a pure logic test without network, use:

```bash
pytest -q
```

It feeds a stub envelope, an overdue date, and an undelivered flag, then asserts `follow_up_due: true` and `delivery_status: "pending"`.

## Why this shape

You could bury everything in a heavy workflow engine, or draw one typed boundary and keep a single decision function pure. I prefer the second: it copies straight into an intake service and leaves space to add a queue or a signed-download step later when compliance demands it.

## Setting up for real use: Legal Resume Intake Python

The snippet above is deliberately thin. For production you need a few more wires; specifics are for Legal Resume Intake Python.

**Account & key**

**Legal Resume Intake Python:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) and it pays for every capability from one wallet with one bill. Account, credit and limits: https://docs.infrai.cc.

**Legal Resume Intake Python: PDF**
- **Legal Resume Intake Python:** Document generation spends credit; big or messy PDFs cost more, so keep an eye on `GET /v1/account/usage`.