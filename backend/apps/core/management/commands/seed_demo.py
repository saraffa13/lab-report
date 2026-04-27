"""
Seed a working demo environment:
  - 1 Lab ("Demo Diagnostics")
  - 1 admin user (demo@labreport.local / demo1234)
  - Roles and core permissions
  - Full test catalog (~60 tests) covering every Pathkind-style report type
  - 14 report templates (CBC, LFT, KFT, Liver+Kidney, LDH, GGT, Urine R/M,
    Thyroid, Malaria Antigen, MP Smear, Widal, Dengue NS1, Dengue IgG/IgM,
    Typhidot Enterocheck)

Idempotent: safe to re-run. Uses update_or_create and hard_deletes children
before re-inserting.
"""
from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Permission, Role, RolePermission, User
from apps.catalog.models import (
    ReferenceRange,
    ReportTemplate,
    ReportTemplateTest,
    Test,
    TestCategory,
)
from apps.tenancy.models import Lab

ROLES = [
    ("admin", "Admin"),
    ("lab_owner", "Lab owner"),
    ("pa", "Pathologist's Assistant"),
    ("patient", "Patient"),
]

CORE_PERMISSIONS = [
    ("report.create", "Create report", "reports"),
    ("report.view_all", "View all reports", "reports"),
    ("report.sign", "Sign report", "reports"),
    ("report.amend", "Amend report", "reports"),
    ("report.delete", "Delete report", "reports"),
    ("report.view_revenue", "View revenue", "reports"),
    ("patient.view_all", "View all patients", "patients"),
    ("patient.create", "Create patient", "patients"),
    ("catalog.manage", "Manage catalog", "catalog"),
    ("user.manage", "Manage users", "admin"),
    ("user.delete", "Delete users", "admin"),
    ("lab.manage", "Manage lab settings", "admin"),
]

# Role → default permissions.
ROLE_PERMS: dict[str, list[str]] = {
    "admin": [  # everything
        "report.create", "report.view_all", "report.sign", "report.amend",
        "report.delete", "report.view_revenue",
        "patient.view_all", "patient.create",
        "catalog.manage",
        "user.manage", "user.delete", "lab.manage",
    ],
    "lab_owner": [
        "report.create", "report.view_all", "report.sign", "report.amend",
        "report.delete", "report.view_revenue",
        "patient.view_all", "patient.create",
        "catalog.manage",
        "user.manage", "user.delete", "lab.manage",
    ],
    "pa": [
        "report.create", "report.view_all", "report.sign",
        "patient.view_all", "patient.create",
    ],
    "patient": [],
}

CATEGORIES = [
    {"code": "HAEM", "name": "Haematology", "order": 10},
    {"code": "BIOCHEM", "name": "Biochemistry", "order": 20},
    {"code": "IMMUNO", "name": "Immunology / Serology", "order": 30},
    {"code": "CLIN_PATH", "name": "Clinical Pathology", "order": 40},
    {"code": "MICRO", "name": "Microbiology", "order": 50},
]

# Range shorthand: (sex, amin, amax, rmin, rmax, text)
# Use rmin/rmax=None and put a string in `text` for qualitative tests like "Negative".
TESTS = [
    # ── HAEMATOLOGY (CBC) ───────────────────────────────────────────
    ("HAEM", "CBC-HB", "Haemoglobin (Hb)", "g/dL", "Cynmeth Method", "Whole Blood EDTA",
        [("M", None, None, "13.0", "17.0", ""), ("F", None, None, "12.0", "15.0", "")], ""),
    ("HAEM", "CBC-RBC", "RBC Count", "10^12/L", "Cell Impedence", "Whole Blood EDTA",
        [("M", None, None, "4.5", "5.5", ""), ("F", None, None, "3.8", "4.8", "")], ""),
    ("HAEM", "CBC-HCT", "Haematocrit (HCT)", "%", "Calculated", "Whole Blood EDTA",
        [("A", None, None, "40", "50", "")], ""),
    ("HAEM", "CBC-MCV", "MCV", "fl", "Calculated", "Whole Blood EDTA",
        [("A", None, None, "81", "101", "")], ""),
    ("HAEM", "CBC-MCH", "MCH", "pg", "Calculated", "Whole Blood EDTA",
        [("A", None, None, "27", "32", "")], ""),
    ("HAEM", "CBC-MCHC", "MCHC", "g/dL", "Calculated", "Whole Blood EDTA",
        [("A", None, None, "32.5", "34.5", "")], ""),
    ("HAEM", "CBC-RDW", "RDW-CV", "%", "Calculated", "Whole Blood EDTA",
        [("A", None, None, "11.6", "14.0", "")], ""),
    ("HAEM", "CBC-PLT", "Platelet Count (PLT)", "10^9/L", "Cell Impedance", "Whole Blood EDTA",
        [("A", None, None, "150", "410", "")], ""),
    ("HAEM", "CBC-WBC", "Total WBC Count", "10^9/L", "Impedance", "Whole Blood EDTA",
        [("A", None, None, "4.0", "10.0", "")], ""),
    # Differential leukocyte count (%)
    ("HAEM", "DLC-NEUT", "Neutrophils", "%", "Cell Impedence", "Whole Blood EDTA",
        [("A", None, None, "40", "70", "")], ""),
    ("HAEM", "DLC-LYMP", "Lymphocytes", "%", "Cell Impedence", "Whole Blood EDTA",
        [("A", None, None, "20", "40", "")], ""),
    ("HAEM", "DLC-MONO", "Monocytes", "%", "Microscopy", "Whole Blood EDTA",
        [("A", None, None, "2", "10", "")], ""),
    ("HAEM", "DLC-EOSI", "Eosinophils", "%", "Microscopy", "Whole Blood EDTA",
        [("A", None, None, "1", "6", "")], ""),
    ("HAEM", "DLC-BASO", "Basophils", "%", "Microscopy", "Whole Blood EDTA",
        [("A", None, None, "1", "2", "")], ""),
    # Absolute counts
    ("HAEM", "ABS-NEUT", "Absolute Neutrophils Count", "10^9/L", "Impedence", "Whole Blood EDTA",
        [("A", None, None, "2.0", "7.0", "")], ""),
    ("HAEM", "ABS-LYMP", "Absolute Lymphocyte Count", "10^9/L", "Impedence", "Whole Blood EDTA",
        [("A", None, None, "1.0", "3.0", "")], ""),
    ("HAEM", "ABS-MONO", "Absolute Monocyte Count", "10^9/L", "Calculated", "Whole Blood EDTA",
        [("A", None, None, "0.2", "1.0", "")], ""),
    ("HAEM", "ABS-EOSI", "Absolute Eosinophils Count", "10^9/L", "Calculated", "Whole Blood EDTA",
        [("A", None, None, "0.02", "0.5", "")], ""),
    ("HAEM", "ABS-BASO", "Absolute Basophil Count", "10^9/L", "Calculated", "Whole Blood EDTA",
        [("A", None, None, "0.0", "0.3", "")], ""),
    ("HAEM", "CBC-ATYP", "Atypical cells", "%", "Microscopy", "Whole Blood EDTA",
        [("A", None, None, "0", "0", "")], ""),

    ("HAEM", "ESR", "ESR (Westergren)", "mm/hr", "Westergren", "Whole Blood EDTA",
        [("M", None, None, "0", "15", ""), ("F", None, None, "0", "20", "")], ""),

    # ── BIOCHEMISTRY · LFT ──────────────────────────────────────────
    ("BIOCHEM", "LFT-BILT", "Bilirubin Total", "mg/dL", "Diazo", "Serum",
        [("A", None, None, "0.2", "1.2", "")], ""),
    ("BIOCHEM", "LFT-BILD", "Bilirubin Direct", "mg/dL", "Diazo", "Serum",
        [("A", None, None, "0.0", "0.3", "")], ""),
    ("BIOCHEM", "LFT-BILI", "Bilirubin Indirect", "mg/dL", "Calculated", "Serum",
        [("A", None, None, "0.1", "1.0", "")], ""),
    ("BIOCHEM", "LFT-SGOT", "SGOT (AST)", "U/L", "IFCC", "Serum",
        [("M", None, None, "0", "40", ""), ("F", None, None, "0", "35", "")], ""),
    ("BIOCHEM", "LFT-SGPT", "SGPT (ALT)", "U/L", "IFCC", "Serum",
        [("M", None, None, "0", "45", ""), ("F", None, None, "0", "35", "")], ""),
    ("BIOCHEM", "LFT-ALP", "Alkaline Phosphatase (ALP)", "U/L", "IFCC", "Serum",
        [("A", None, None, "40", "130", "")], ""),
    ("BIOCHEM", "LFT-TP", "Total Protein", "g/dL", "Biuret", "Serum",
        [("A", None, None, "6.0", "8.3", "")], ""),
    ("BIOCHEM", "LFT-ALB", "Albumin", "g/dL", "BCG", "Serum",
        [("A", None, None, "3.5", "5.0", "")], ""),
    ("BIOCHEM", "LFT-GLOB", "Globulin", "g/dL", "Calculated", "Serum",
        [("A", None, None, "2.0", "3.5", "")], ""),
    ("BIOCHEM", "LFT-AGR", "Albumin : Globulin Ratio (A/G)", "Ratio", "Calculated", "Serum",
        [("A", None, None, "1.0", "2.1", "")], ""),

    # ── BIOCHEMISTRY · KFT ──────────────────────────────────────────
    ("BIOCHEM", "KFT-BUN", "Blood Urea Nitrogen (BUN)", "mg/dL", "Urease UV", "Serum",
        [("A", None, None, "8", "23", "")], ""),
    ("BIOCHEM", "KFT-UREA", "Blood Urea", "mg/dL", "Urease UV", "Serum",
        [("A", None, None, "18", "50", "")], ""),
    ("BIOCHEM", "KFT-CREA", "Creatinine", "mg/dL", "Jaffe Kinetic", "Serum",
        [("M", None, None, "0.70", "1.30", ""), ("F", None, None, "0.55", "1.10", "")], ""),
    ("BIOCHEM", "KFT-BCR", "BUN : Creatinine Ratio", "Ratio", "Calculated", "Serum",
        [("A", None, None, "10", "20", "")], ""),
    ("BIOCHEM", "KFT-CA", "Calcium", "mg/dL", "Arsenazo III", "Serum",
        [("A", None, None, "8.6", "10.3", "")], ""),
    ("BIOCHEM", "KFT-UA", "Uric Acid", "mg/dL", "Uricase", "Serum",
        [("M", None, None, "3.5", "7.2", ""), ("F", None, None, "2.6", "6.0", "")], ""),
    ("BIOCHEM", "KFT-NA", "Sodium", "mmol/L", "ISE Indirect", "Serum",
        [("A", None, None, "136", "145", "")], ""),
    ("BIOCHEM", "KFT-K", "Potassium", "mmol/L", "ISE Indirect", "Serum",
        [("A", None, None, "3.5", "5.1", "")], ""),
    ("BIOCHEM", "KFT-CL", "Chloride", "mmol/L", "ISE Indirect", "Serum",
        [("A", None, None, "97", "108", "")], ""),

    # ── BIOCHEMISTRY · LDH / GGT ────────────────────────────────────
    ("BIOCHEM", "LDH", "Lactate Dehydrogenase (LDH)", "U/L", "IFCC", "Serum",
        [("A", None, None, "135", "225", "")],
        "LDH is elevated in many conditions including myocardial infarction, haemolysis, hepatitis, muscle trauma, and malignancies."),
    ("BIOCHEM", "GGT", "Gamma-Glutamyl Transferase (GGT)", "U/L", "IFCC", "Serum",
        [("M", None, None, "10", "71", ""), ("F", None, None, "6", "42", "")],
        "GGT is a sensitive marker of hepatobiliary disease and alcohol-induced liver damage."),

    # ── IMMUNOLOGY · Thyroid ────────────────────────────────────────
    ("IMMUNO", "TFT-T3", "Triiodothyronine (T3) - Total", "ng/dL", "CLIA", "Serum",
        [("A", None, None, "80", "200", "")], ""),
    ("IMMUNO", "TFT-T4", "Thyroxine (T4) - Total", "µg/dL", "CLIA", "Serum",
        [("A", None, None, "5.1", "14.1", "")], ""),
    ("IMMUNO", "TFT-TSH", "TSH 3rd Generation", "µIU/mL", "CLIA", "Serum",
        [("A", None, None, "0.35", "5.50", "")],
        "TSH is the most sensitive marker for thyroid function. Pregnancy-specific ranges apply during gestation."),

    # ── IMMUNOLOGY · Malaria Rapid Antigen ─────────────────────────
    ("IMMUNO", "MP-PV-AG", "Plasmodium Vivax (Pv) Antigen", "", "Immunochromatography", "Whole Blood EDTA",
        [("A", None, None, None, None, "Not Detected")], ""),
    ("IMMUNO", "MP-PF-AG", "Plasmodium Falciparum (Pf) Antigen", "", "Immunochromatography", "Whole Blood EDTA",
        [("A", None, None, None, None, "Not Detected")], ""),

    # ── HAEMATOLOGY · Malaria Smear ─────────────────────────────────
    ("HAEM", "MP-THIN", "MP - Thin Smear", "", "Microscopy", "Whole Blood EDTA",
        [("A", None, None, None, None, "Not Detected")], ""),
    ("HAEM", "MP-THICK", "MP - Thick Smear", "", "Microscopy", "Whole Blood EDTA",
        [("A", None, None, None, None, "Not Detected")], ""),

    # ── IMMUNOLOGY · Widal ──────────────────────────────────────────
    ("IMMUNO", "WIDAL-TO", "Salmonella Typhi 'O' (somatic)", "", "Slide Agglutination", "Serum",
        [("A", None, None, None, None, "< 1:80")], ""),
    ("IMMUNO", "WIDAL-TH", "Salmonella Typhi 'H' (flagellar)", "", "Slide Agglutination", "Serum",
        [("A", None, None, None, None, "< 1:80")], ""),
    ("IMMUNO", "WIDAL-AH", "Salmonella Paratyphi 'AH'", "", "Slide Agglutination", "Serum",
        [("A", None, None, None, None, "< 1:80")], ""),
    ("IMMUNO", "WIDAL-BH", "Salmonella Paratyphi 'BH'", "", "Slide Agglutination", "Serum",
        [("A", None, None, None, None, "< 1:80")], ""),

    # ── IMMUNOLOGY · Dengue ─────────────────────────────────────────
    ("IMMUNO", "DEN-NS1", "Dengue NS1 Antigen (ELISA)", "Index", "ELISA", "Serum",
        [("A", None, None, None, None, "Negative < 0.8 · Equivocal 0.8-1.1 · Positive ≥ 1.1")], ""),
    ("IMMUNO", "DEN-IGG", "Dengue Virus IgG Antibodies (ELISA)", "Index", "ELISA", "Serum",
        [("A", None, None, None, None, "Negative < 0.8 · Equivocal 0.8-1.1 · Positive ≥ 1.1")], ""),
    ("IMMUNO", "DEN-IGM", "Dengue Virus IgM Antibodies (ELISA)", "Index", "ELISA", "Serum",
        [("A", None, None, None, None, "Negative < 0.8 · Equivocal 0.8-1.1 · Positive ≥ 1.1")], ""),

    # ── IMMUNOLOGY · Typhidot (Enterocheck) ────────────────────────
    ("IMMUNO", "TYP-IGG", "Typhidot IgG (Enterocheck)", "", "Immunochromatography", "Serum",
        [("A", None, None, None, None, "Negative")], ""),
    ("IMMUNO", "TYP-IGM", "Typhidot IgM (Enterocheck)", "", "Immunochromatography", "Serum",
        [("A", None, None, None, None, "Negative")], ""),

    # ── CLINICAL PATHOLOGY · Urine R/M ──────────────────────────────
    ("CLIN_PATH", "URINE-COL", "Colour", "", "Physical", "Random Urine",
        [("A", None, None, None, None, "Pale Yellow")], ""),
    ("CLIN_PATH", "URINE-APP", "Appearance", "", "Physical", "Random Urine",
        [("A", None, None, None, None, "Clear")], ""),
    ("CLIN_PATH", "URINE-SG", "Specific Gravity", "", "Dipstick", "Random Urine",
        [("A", None, None, "1.005", "1.030", "")], ""),
    ("CLIN_PATH", "URINE-PH", "pH", "", "Dipstick", "Random Urine",
        [("A", None, None, "4.6", "8.0", "")], ""),
    ("CLIN_PATH", "URINE-GLU", "Glucose", "", "Dipstick", "Random Urine",
        [("A", None, None, None, None, "Nil")], ""),
    ("CLIN_PATH", "URINE-PROT", "Protein", "", "Dipstick", "Random Urine",
        [("A", None, None, None, None, "Nil")], ""),
    ("CLIN_PATH", "URINE-KET", "Ketone", "", "Dipstick", "Random Urine",
        [("A", None, None, None, None, "Nil")], ""),
    ("CLIN_PATH", "URINE-BLOOD", "Blood", "", "Peroxidase", "Random Urine",
        [("A", None, None, None, None, "Not Detected")], ""),
    ("CLIN_PATH", "URINE-BIL", "Bilirubin", "", "Diazo reaction", "Random Urine",
        [("A", None, None, None, None, "Not Detected")], ""),
    ("CLIN_PATH", "URINE-UBG", "Urobilinogen", "", "Ehrlich's reaction", "Random Urine",
        [("A", None, None, None, None, "Normal")], ""),
    ("CLIN_PATH", "URINE-NIT", "Nitrite", "", "Nitrite test", "Random Urine",
        [("A", None, None, None, None, "Not Detected")], ""),
    ("CLIN_PATH", "URINE-PUS", "Pus Cells", "/hpf", "Microscopy", "Random Urine",
        [("A", None, None, "0", "5", "")], ""),
    ("CLIN_PATH", "URINE-RBC", "RBC (microscopy)", "/hpf", "Microscopy", "Random Urine",
        [("A", None, None, "0", "2", "")], ""),
    ("CLIN_PATH", "URINE-EPI", "Epithelial Cells", "/hpf", "Microscopy", "Random Urine",
        [("A", None, None, "0", "5", "")], ""),
    ("CLIN_PATH", "URINE-CAST", "Casts", "", "Microscopy", "Random Urine",
        [("A", None, None, None, None, "Not Detected")], ""),
    ("CLIN_PATH", "URINE-CRYS", "Crystals", "", "Microscopy", "Random Urine",
        [("A", None, None, None, None, "Not Detected")], ""),
    ("CLIN_PATH", "URINE-BACT", "Bacteria", "", "Microscopy", "Random Urine",
        [("A", None, None, None, None, "Not Detected")], ""),
]

TEMPLATES = [
    {"code": "CBC", "name": "Complete Blood Count (CBC)",
     "tests": ["CBC-HB", "CBC-RBC", "CBC-HCT", "CBC-MCV", "CBC-MCH", "CBC-MCHC", "CBC-RDW",
               "CBC-PLT", "CBC-WBC",
               "DLC-NEUT", "ABS-NEUT",
               "DLC-LYMP", "ABS-LYMP",
               "DLC-MONO", "ABS-MONO",
               "DLC-EOSI", "ABS-EOSI",
               "DLC-BASO", "ABS-BASO",
               "CBC-ATYP"]},
    {"code": "LFT", "name": "Liver Function Test (LFT)",
     "tests": ["LFT-BILT", "LFT-BILD", "LFT-BILI", "LFT-SGOT", "LFT-SGPT", "LFT-ALP",
               "LFT-TP", "LFT-ALB", "LFT-GLOB", "LFT-AGR"]},
    {"code": "KFT", "name": "Kidney Function Test (KFT)",
     "tests": ["KFT-BUN", "KFT-UREA", "KFT-CREA", "KFT-BCR", "KFT-UA", "KFT-CA",
               "KFT-NA", "KFT-K", "KFT-CL"]},
    {"code": "LIVER_KIDNEY", "name": "Liver & Kidney Profile",
     "tests": ["LFT-BILT", "LFT-BILD", "LFT-SGOT", "LFT-SGPT", "LFT-ALP", "LFT-TP",
               "LFT-ALB", "LFT-GLOB", "LFT-AGR",
               "KFT-BUN", "KFT-UREA", "KFT-CREA", "KFT-UA", "KFT-CA",
               "KFT-NA", "KFT-K", "KFT-CL"]},
    {"code": "LDH", "name": "Lactate Dehydrogenase (LDH)", "tests": ["LDH"]},
    {"code": "GGT", "name": "Gamma-Glutamyl Transferase (GGT)", "tests": ["GGT"]},
    {"code": "URINE", "name": "Urine Routine & Microscopic Examination",
     "tests": ["URINE-COL", "URINE-APP", "URINE-SG", "URINE-PH",
               "URINE-GLU", "URINE-PROT", "URINE-KET",
               "URINE-BLOOD", "URINE-BIL", "URINE-UBG", "URINE-NIT",
               "URINE-PUS", "URINE-RBC", "URINE-EPI",
               "URINE-CAST", "URINE-CRYS", "URINE-BACT"]},
    {"code": "TFT", "name": "Thyroid Profile Total", "tests": ["TFT-T3", "TFT-T4", "TFT-TSH"]},
    {"code": "TSH", "name": "TSH 3rd Generation", "tests": ["TFT-TSH"]},
    {"code": "MP-AG", "name": "Malaria Antigen Detection (Rapid)",
     "tests": ["MP-PV-AG", "MP-PF-AG"]},
    {"code": "MP-SMEAR", "name": "Malaria Parasite (MP) Smear",
     "tests": ["MP-THIN", "MP-THICK"]},
    {"code": "WIDAL", "name": "Widal (Slide)",
     "tests": ["WIDAL-TO", "WIDAL-TH", "WIDAL-AH", "WIDAL-BH"]},
    {"code": "DEN-NS1", "name": "Dengue NS1 Antigen (ELISA)", "tests": ["DEN-NS1"]},
    {"code": "DEN-IGGM", "name": "Dengue IgG & IgM Antibodies (ELISA)",
     "tests": ["DEN-IGG", "DEN-IGM"]},
    {"code": "TYPHIDOT", "name": "Typhidot IgG & IgM Rapid (Enterocheck)",
     "tests": ["TYP-IGG", "TYP-IGM"]},
]


class Command(BaseCommand):
    help = "Seed a ready-to-use demo: lab, admin user, catalog, templates."

    @transaction.atomic
    def handle(self, *args, **opts):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding demo data..."))

        # Roles
        roles: dict[str, Role] = {}
        for code, name in ROLES:
            role, _ = Role.objects.update_or_create(code=code, defaults={"name": name})
            roles[code] = role

        # Permissions
        perms: dict[str, Permission] = {}
        for code, name, category in CORE_PERMISSIONS:
            p, _ = Permission.objects.update_or_create(
                code=code, defaults={"name": name, "category": category}
            )
            perms[code] = p
        # Grant each role its configured permissions.
        for role_code, perm_codes in ROLE_PERMS.items():
            role = roles.get(role_code)
            if not role:
                continue
            for perm_code in perm_codes:
                p = perms.get(perm_code)
                if p:
                    RolePermission.objects.get_or_create(role=role, permission=p)

        # Lab
        lab, created = Lab.objects.update_or_create(
            slug="demo",
            defaults={
                "name": "K S Ganga Medical Clinic",
                "address": "Torpa chowk, Torpa",
                "city": "Khunti",
                "state": "Jharkhand",
                "pincode": "835227",
                "country": "India",
                "phone": "9507098416, 8340430597",
                "email": "ksgangamedicalclinic@gmail.com",
                "accreditation_info": "ISO 9001:2015 Certified",
                "tax_registration": "Reg. No. 2036500318",
                "primary_color": "#1e3a8a",
                "subscription_status": "trial",
                "settings": {
                    "iso_reg_no": "QMS/092020/19663",
                    "registration_number": "2036500318",
                    "brand_logo_path": "static/branding/logo.png",
                    "iso_badge_path": "static/branding/iso.png",
                },
            },
        )
        self.stdout.write(f"  Lab: {lab.name} ({'created' if created else 'updated'})")

        # Admin user
        admin_email = "demo@labreport.local"
        admin, u_created = User.objects.update_or_create(
            email=admin_email,
            defaults={
                "full_name": "Dr. A. Pathologist",
                "lab": lab,
                "role": roles["admin"],
                "designation": "Senior Consultant, Pathology",
                "qualification": "MBBS, DNB (Pathology)",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "phone": "+91 98200 00001",
                "phone_verified": True,
                "email_verified": True,
            },
        )
        if u_created or not admin.has_usable_password():
            admin.set_password("demo1234")
            admin.save(update_fields=["password"])
        self.stdout.write(f"  Admin user: {admin_email} / demo1234")

        # Categories
        cats: dict[str, TestCategory] = {}
        for c in CATEGORIES:
            cat, _ = TestCategory.objects.update_or_create(
                lab=None, code=c["code"],
                defaults={"name": c["name"], "display_order": c["order"]},
            )
            cats[c["code"]] = cat

        # Tests
        tests_by_code: dict[str, Test] = {}
        for cat_code, code, name, unit, method, sample, ranges, clinical in TESTS:
            test, _ = Test.objects.update_or_create(
                lab=None, code=code,
                defaults={
                    "category": cats[cat_code],
                    "name": name,
                    "unit": unit,
                    "method": method,
                    "sample_type": sample,
                    "clinical_significance": clinical,
                },
            )
            tests_by_code[code] = test
            ReferenceRange.all_objects.filter(test=test).hard_delete()
            for sex, amin, amax, rmin, rmax, text in ranges:
                ReferenceRange.objects.create(
                    test=test, sex=sex,
                    age_min_years=amin, age_max_years=amax,
                    range_min=Decimal(rmin) if rmin else None,
                    range_max=Decimal(rmax) if rmax else None,
                    range_text=text,
                )
        self.stdout.write(f"  Tests seeded: {len(tests_by_code)}")

        # Templates
        template_pdf_paths = {"CBC": "pdf/reports/cbc.html"}
        for t in TEMPLATES:
            tmpl, _ = ReportTemplate.objects.update_or_create(
                lab=None, code=t["code"],
                defaults={
                    "name": t["name"],
                    "pdf_template_path": template_pdf_paths.get(t["code"], "pdf/reports/generic.html"),
                },
            )
            ReportTemplateTest.all_objects.filter(template=tmpl).hard_delete()
            for order, test_code in enumerate(t["tests"]):
                if test_code not in tests_by_code:
                    raise ValueError(f"Template {t['code']} references unknown test {test_code}")
                ReportTemplateTest.objects.create(
                    template=tmpl, test=tests_by_code[test_code], display_order=order,
                )
        self.stdout.write(f"  Templates: {len(TEMPLATES)}")

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. Login at /api/v1/auth/login/ with {admin_email} / demo1234"
        ))
