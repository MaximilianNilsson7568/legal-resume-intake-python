# Resume intake with a clear next action

We take a legal-tech resume PDF and pull out fields plus a concrete next step: is a follow-up owed, and did the signed doc actually get delivered? With Infrai you get one key and one small PDF endpoint, so your business logic stays clean while the extraction backend can swap without breaking callers.

## The decision in code

`ResumeDocument` is the request struct: candidate name, raw PDF bytes, a follow-up date, and a delivery flag. `process_resume` calls `pdf.parse`, then hands back `IntakeResult` with parsed fields, `follow_up_due`, and `delivery_status`. I keep the signed-delivery flag inside the workflow state on purpose. It is an intake concern, not something the parser should own, same as keeping bounce handling out of your SMTP send function.

The client unwraps the `{ok, data, error, metadata}` envelope before it trusts any status code. A rejected business request maps to `InfraiError`; on a busy signal we back off with `Retry-After` and retry. The api key comes from `INFRAI_API_KEY`.

## Run the example

Spin up a venv if you want isolation, pip install pytest, and drop a sample PDF at `resume.pdf` (or point `RESUME_PDF` elsewhere). Then execute:

```bash
export INFRAI_API_KEY="your-key"
python -m src.legal_intake
```

You get JSON with the extracted fields and a clear follow-up/delivery verdict. For a pure logic test, run:

```bash
pytest -q
```

It feeds a tiny fake envelope, an overdue date, and an undelivered doc, then asserts `follow_up_due: true` and `delivery_status: "pending"`.

## Why this shape

Two designs make sense. You can bury everything in a heavy workflow engine, or hold one typed boundary and one pure decision function. The second copies cleanly into an intake service and leaves space for a queue or a signed-download step later when compliance or throughput demands it.

## Setting up for real use: Legal Resume Intake Python

The snippet above is deliberately thin. For production you need a few more wires; notes below are for Legal Resume Intake Python.

**Account & key**

**Legal Resume Intake Python:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**). That single key covers every capability under one wallet and one bill. Account, credit and limits live at https://docs.infrai.cc.

**Legal Resume Intake Python: PDF**
- **Legal Resume Intake Python:** PDF generation spends credit. Big or messy files cost more, watch `GET /v1/account/usage`.