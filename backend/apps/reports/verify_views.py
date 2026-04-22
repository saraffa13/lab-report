"""Public report verification page reached by scanning the QR on a printed PDF."""
from __future__ import annotations

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from .models import Report


_TEMPLATE = Template(
    """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Report {{ report.accession_number }} — {{ lab.name }}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Inter", system-ui, sans-serif; background: #f7f9fb; color: #191c1e; min-height: 100vh; padding: 24px 16px; }
  .wrap { max-width: 720px; margin: 0 auto; }
  .lab { font-size: 14px; font-weight: 900; letter-spacing: 0.5px; color: #0b2a5b; text-transform: uppercase; text-align: center; }
  .verified { display:inline-flex; align-items:center; gap:6px; background:#6df5e1; color:#006f64; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; margin: 12px auto 0; }
  .verified-wrap { text-align: center; }
  .card { background: #ffffff; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,22,58,0.06); padding: 24px; margin-top: 16px; }
  h1 { font-size: 24px; font-weight: 800; color: #001a42; margin-bottom: 4px; }
  .sub { color: #44474f; font-size: 13px; margin-bottom: 20px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px 20px; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .label { font-size: 11px; color: #44474f; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
  .value { font-size: 14px; color: #191c1e; font-weight: 600; }
  .mono { font-family: ui-monospace, Menlo, monospace; }
  .navy-bar { background: #0b2a5b; color: #fff; padding: 10px 16px; border-radius: 10px 10px 0 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-top: 24px; }
  table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 0 0 10px 10px; overflow: hidden; box-shadow: 0 8px 30px rgba(0,22,58,0.04); }
  th, td { text-align: left; padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #f2f4f6; }
  th { background: #f2f4f6; color: #44474f; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
  td.flag-abn { color: #b91c1c; font-weight: 700; }
  .footer { text-align:center; margin-top: 24px; font-size: 11px; color: #6b7280; }
  @media (max-width: 520px) { .grid { grid-template-columns: 1fr; } h1 { font-size: 20px; } }
</style>
</head><body>
<div class="wrap">
  <div class="lab">{{ lab.name }}</div>
  <div class="verified-wrap"><span class="verified">&#10003; Verified Report</span></div>

  <div class="card">
    <h1>{{ template_name }}</h1>
    <div class="sub">Accession <span class="mono">{{ report.accession_number }}</span></div>
    <div class="grid">
      <div class="field"><div class="label">Patient Name</div><div class="value">{{ patient.name }}</div></div>
      <div class="field"><div class="label">Patient ID</div><div class="value mono">{{ patient.patient_code }}</div></div>
      {% if patient.age %}<div class="field"><div class="label">Age / Sex</div><div class="value">{{ patient.age }} {{ patient.age_unit|default:"yrs" }} / {{ patient.get_sex_display }}</div></div>{% endif %}
      <div class="field"><div class="label">Status</div><div class="value">{{ report.get_status_display|default:report.status }}</div></div>
      <div class="field"><div class="label">Reported On</div><div class="value">{{ report.signed_at|date:"d M Y, h:i A"|default:"—" }}</div></div>
      <div class="field"><div class="label">Referred By</div><div class="value">{{ report.referred_by_text|default:"Self" }}</div></div>
    </div>
  </div>

  <div class="navy-bar">Test Results &middot; {{ results|length }} parameter{{ results|length|pluralize }}</div>
  <table>
    <thead><tr><th>Test</th><th>Result</th><th>Unit</th><th>Reference</th></tr></thead>
    <tbody>
    {% for r in results %}
      <tr>
        <td>{{ r.test.name }}</td>
        <td class="{% if r.is_abnormal %}flag-abn{% endif %}">{{ r.result_value }}</td>
        <td>{{ r.unit_used|default:"—" }}</td>
        <td>{{ r.reference_range_used|default:"—" }}</td>
      </tr>
    {% empty %}
      <tr><td colspan="4" style="text-align:center;color:#9ca3af;padding:24px;">No results recorded.</td></tr>
    {% endfor %}
    </tbody>
  </table>

  <div class="footer">
    This page confirms that the printed report originates from {{ lab.name }}.<br>
    For queries contact {{ lab.phone|default:"the lab directly" }}.
  </div>
</div>
</body></html>"""
)


@require_GET
@cache_control(no_store=True)
def verify_report(request, accession_number: str) -> HttpResponse:
    report = get_object_or_404(
        Report.all_objects.select_related("patient", "lab", "report_template").prefetch_related("results__test"),
        accession_number=accession_number,
        deleted_at__isnull=True,
    )
    ctx = Context({
        "report": report,
        "patient": report.patient,
        "lab": report.lab,
        "template_name": (report.report_template.name if report.report_template_id else "Lab Report"),
        "results": list(report.results.select_related("test").all()),
    })
    return HttpResponse(_TEMPLATE.render(ctx))
