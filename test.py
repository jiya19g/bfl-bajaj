import re

def clean_test_name(name):
    name = re.sub(r'\b\d+\b', '', name)
    return ' '.join(name.split())

def fix_unit(unit):
    unit = unit.replace('mmo1/1', 'mmol/L')  # Fix common OCR errors
    unit = unit.replace('mmoI/1', 'mmol/L')  # Just in case capital i
    return unit

def parse_lab_report(text):
    results = []
    lines = text.splitlines()

    # New regex - tolerate missing brackets and allow optional ref_min
    line_pattern = re.compile(
        r"([\w\s\(\)\-\/\.]+?)\s+([><]?[0-9]+(?:\.[0-9]*)?)\s*([a-zA-Z\/%]*)\s*[.\[\(]?\s*([0-9.]*)\s*[-–to]*\s*([0-9.]+)\s*[\]\)]?",
        re.IGNORECASE
    )

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = line_pattern.search(line)
        if match:
            test_name = match.group(1).strip()
            result_value = match.group(2).strip()
            unit = fix_unit(match.group(3))
            ref_min = match.group(4)
            ref_max = match.group(5)

            if "eGFR" in test_name and result_value.startswith(">"):
                result_value = float(result_value[1:])
            else:
                result_value = float(result_value)

            test_name = clean_test_name(test_name)

            # Handle missing ref_min for tests like eGFR (-60.0 only)
            try:
                if ref_max in ['', '.']:
                    continue
                if ref_min in ['', '.']:
                    ref_min = float(ref_max)
                else:
                    ref_min = float(ref_min)
                ref_max = float(ref_max)
            except ValueError:
                continue



            if ref_min > ref_max:
                ref_min, ref_max = ref_max, ref_min

            if (result_value > 1000 or ref_min > 1000 or ref_max > 1000) and unit.lower() not in ['mg/dl', 'mmol/l', 'millions/cumm', 'ml/min/1.73sq.m']:
                continue

            out_of_range = result_value < ref_min or result_value > ref_max

            results.append({
                "test_name": test_name,
                "result_value": result_value,
                "unit": unit,
                "bio_reference_range": f"{ref_min}-{ref_max}",
                "lab_test_out_of_range": out_of_range
            })

    return results

if __name__ == "__main__":
    extracted_text = r"""ee Di eeweFal ofcar,SOssmmamsf
-()DiagmOsiicIRDINCrathelegeiens
BastePaeQUIFPED.WITHCONPUTERISEDAUTO\CHEMISTRYB1OOD,GAS/6,HAEMATOLOGYANALYSERSSaMEB
NRIIN0/1X(0274107fi08MoottsticiosrAcarwalowerPRNO.eEMailpehacGardentOelNl5hitAn/aacrinen
SARVODAYA.HOSPITAL,Dr.(CaptAtulKapia(Retd)MD-Path.
,PatientID, Pr / or . ye
,Patient Pole noon a Fa
.Referred VERMA
LabSerialNo19 , ReceivingLJ18/Apr/2025121500PM
WardNo 1SP-25 ReportingDate18/Apr/2025321739PM
)GRIUHDNo0223/391503 a DateTAT3Hours2Minute
tavestiaation ee os . ObservedValue. , Unit oe Blologieal Ref.interval i
-,-,AMMONIA Ne Tiga es ugdl - 17.00-90.00
SpecimenBLOOD NS
, END-GRREPORT et
- 1 .
u a
nd - - -Fh , ote poe cae . .7 1
foo UD aay a it
idly RE prABULKABILA
,FACILITIESFORHORMONESASSAYS,FNAG./HISTOPATHOLOGY,JMARROWASPIRATION%BIOPSYWITHMICROPHOTOGRAPHS..-
NOTEABOVEMENTIONEDFINDINGS ARE4PROFESSIGNALDPINIGN4NGTAFINALDIAGNOSIS,ALLLABURATORYTESTSOTHER,
INVESTIGATIONRESULTSARETOBECORELATEDCLINIC-PATHOLUGICALLY,.iSi.REPANCIES,FANY,NECESSITATEREVIEW/REPEATOFTHETESIS.. .
a EEOAVAICFORIMEDICO,GEGAMNPUREOSTM- 5 7"""

    structured_data = parse_lab_report(extracted_text)

    for item in structured_data:
        print(item)


