## Latest Update - March 28, 2026

### Subject Data Analysis (Read-Only)

#### Data Source
All subject data comes from SQL migrations only. No external syllabus documents (.docx, .pdf, .xlsx) found in project.

#### Semester Distribution in migrations/019_real_subjects_final.sql
Production database contains subject_offerings for EVEN semesters ONLY:

**Semester 2 (MCA Sem II)**: ~78 offerings
- Programs: MCA(General+BD), MCA(General+CC), MCA(BD), MCA(General), MCA(CC)
- Sections: A, B
- Example subjects: CCA42006 (Machine Learning), CCA42007 (Full Stack Web Dev), CCA42008 (Advanced DB)

**Semester 4 (MCA Sem IV / BCA Sem IV)**: ~60 offerings  
- MCA: CCA42802 (Project Work) for MCA(General), MCA(BD+CC)
- BCA: ACA31011 (Software Engineering), ACA31015 (E-Commerce), ACA31012 (Mobile App Dev), ACA31014 (Digital Marketing)
- Programs: BCA(General), BCA(General+DB), BCA(DB+MM), BCA(Cyber+MM)

**Semester 6 (BCA Sem VI)**: ~56 offerings
- Programs: BCA(General), BCA(DB+MM), BCA(DB), BCA(MM)
- Sections: A, B, A+B (combined sections)
- Example subjects: ACA31017 (IoT), ACA31018 (Web Services), ACA31801 (Project), ACA31525 (Animation)

**Odd Semesters (1, 3, 5)**: ZERO offerings

#### Academic Structure (migrations/006_academic_seed.sql)
- MCA program: Semesters I-IV
- BCA program: Semesters I-VI
- Sections: A, B, C, D, E, F (varies by program)

#### Faculty Data (migrations/007_faculty_seed.sql)
27 faculty members seeded with class teacher assignments

### Conclusion
The production database architecture is designed for EVEN semester cycles only. Odd semesters have no subject_offering data and should remain CLOSED.
