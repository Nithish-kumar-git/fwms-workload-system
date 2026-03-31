BEGIN;

-- Update all staff with their real university email addresses
-- Source: WORKLOADGENERATIONEVENSEM20252026.xlsx FACULTY-LIST sheet

UPDATE staff SET email = 'nsivakumar@hindustanuniv.ac.in' WHERE emp_code = 'CNS02';
UPDATE staff SET email = 'bagyalc@hindustanuniv.ac.in' WHERE emp_code = 'LAT74';
UPDATE staff SET email = 'pt.vskumar@hindustanuniv.ac.in' WHERE emp_code = 'MCP04';
UPDATE staff SET email = 'pt.anithasp@hindustanuniv.ac.in' WHERE emp_code = 'MCT01';
UPDATE staff SET email = 'sherine@hindustanuniv.ac.in' WHERE emp_code = 'MCT39';
UPDATE staff SET email = 'pt.sramanayagam@hindustanuniv.ac.in' WHERE emp_code = 'MCT42';
UPDATE staff SET email = 'sgokila@hindustanuniv.ac.in' WHERE emp_code = 'MCT44';
UPDATE staff SET email = 'sathishkm@hindustanuniv.ac.in' WHERE emp_code = 'MCT48';
UPDATE staff SET email = 'dangeline@hindustanuniv.ac.in' WHERE emp_code = 'MCT49';
UPDATE staff SET email = 'sudhas@hindustanuniv.ac.in' WHERE emp_code = 'MCT50';
UPDATE staff SET email = 'rsophia@hindustanuniv.ac.in' WHERE emp_code = 'MCT53';
UPDATE staff SET email = 'svinita@hindustanuniv.ac.in' WHERE emp_code = 'MCT54';
UPDATE staff SET email = 'kalpanak@hindustanuniv.ac.in' WHERE emp_code = 'MCT58';
UPDATE staff SET email = 'vanitaj@hindustanuniv.ac.in' WHERE emp_code = 'MCT59';
UPDATE staff SET email = 'nathiyar@hindustanuniv.ac.in' WHERE emp_code = 'MCT60';
UPDATE staff SET email = 'hjshanthi@hindustanuniv.ac.in' WHERE emp_code = 'MCT61';
UPDATE staff SET email = 'karunamr@hindustanuniv.ac.in' WHERE emp_code = 'MCT63';
UPDATE staff SET email = 'lakshms@hindustanuniv.ac.in' WHERE emp_code = 'MCT65';
UPDATE staff SET email = 'ayyanathn@hindustanuniv.ac.in' WHERE emp_code = 'MCT68';
UPDATE staff SET email = 'mpriya@hindustanuniv.ac.in' WHERE emp_code = 'MCT69';
UPDATE staff SET email = 'cbalak@hindustanuniv.ac.in' WHERE emp_code = 'MCT70';
UPDATE staff SET email = 'prabus@hindustanuniv.ac.in' WHERE emp_code = 'MCT71';
UPDATE staff SET email = 'bmaryr@hindustanuniv.ac.in' WHERE emp_code = 'MCT73';
UPDATE staff SET email = 'shyampb@hindustanuniv.ac.in' WHERE emp_code = 'MCT75';
UPDATE staff SET email = 'mkarthika@hindustanuniv.ac.in' WHERE emp_code = 'MCT76';
UPDATE staff SET email = 'jayas@hindustanuniv.ac.in' WHERE emp_code = 'MCT77';
UPDATE staff SET email = 'sheejas@hindustanuniv.ac.in' WHERE emp_code = 'MCT78';
UPDATE staff SET email = 'divyapb@hindustanuniv.ac.in' WHERE emp_code = 'MCT79';

-- Verify final state
SELECT emp_code, name, email, role FROM staff ORDER BY emp_code;

COMMIT;
