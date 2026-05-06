"""
generate_pdfs.py — Generates 6 technical subsystem PDF documents for EquipmentIQ demo.
Documents:
  DOC-001  VMC-3000 Machine Overview & Specifications
  DOC-002  Spindle Drive System — Technical Manual
  DOC-003  Axis Servo & Motion Control — Technical Manual
  DOC-004  Coolant & Lubrication Systems — Maintenance Guide
  DOC-005  Vibration Monitoring & Condition Monitoring — Reference
  DOC-006  Electrical Cabinet & CNC Controller — Wiring Reference
"""

import sys, json
sys.path.insert(0, '/home/claude/equipmentiq')
from pdf_builder import *

OUT = '/home/claude/equipmentiq/pdfs'

# Load error codes for cross-references
with open('/home/claude/equipmentiq/processed/error_code_master.json') as f:
    ecm = json.load(f)
ec = ecm['error_codes']
params = ecm['parameters']

def get_codes(prefix_list):
    return [ec[c] for c in ec if any(c.startswith(p) for p in prefix_list)]


# ══════════════════════════════════════════════════════════════════════════════
# DOC-001: MACHINE OVERVIEW & SPECIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════
def build_doc001():
    styles = get_styles()
    story  = []
    pt     = DocPageTemplate('DOC-EIQ-001', 'VMC-3000 Machine Overview & Specifications', 'B')

    cover_block(story, styles,
        title       = 'VMC-3000 Series\nVertical Machining Centre',
        subtitle    = 'Machine Overview, Technical Specifications & System Architecture',
        doc_number  = 'DOC-EIQ-001',
        revision    = 'B',
        classification = 'CONTROLLED',
        issued_by   = 'EquipmentIQ Technical Publications'
    )

    # TOC
    section_heading(story, styles, '1. Table of Contents', 1)
    toc = [
        ('2', 'Machine Overview'),
        ('3', 'Technical Specifications'),
        ('4', 'System Architecture'),
        ('5', 'Subsystem Descriptions'),
        ('6', 'Nameplate & Identification'),
        ('7', 'Installation Requirements'),
        ('8', 'Safety Summary'),
    ]
    for num, title in toc:
        story.append(Paragraph(f"{num}.  {title}", styles['toc_entry']))
    story.append(PageBreak())

    # Section 2: Overview
    section_heading(story, styles, '2. Machine Overview', 1)
    story.append(Paragraph(
        'The EquipmentIQ VMC-3000 is a three-axis vertical machining centre designed for '
        'high-precision milling, drilling, boring, and tapping operations on aluminium, '
        'steel, and titanium alloys. The machine incorporates an integrated condition '
        'monitoring system comprising tri-axial accelerometers (Bosch CISS sensor, 2 kHz '
        'sampling), thermal sensors, and drive-level current monitoring, providing real-time '
        'health data to the EquipmentIQ monitoring platform.', styles['body']))
    story.append(Paragraph(
        'The VMC-3000 is configured for fleet deployment across three machine instances '
        '(M01, M02, M03) in a brownfield production environment. Sensor data is timestamped '
        'and transmitted via OPC-UA to the EquipmentIQ edge gateway at 2,000 samples per '
        'second per axis.', styles['body']))
    note_box(story, styles,
        'This document is the primary reference for service engineers commissioning, '
        'troubleshooting, or performing preventive maintenance on VMC-3000 series machines.')

    # Section 3: Specifications
    section_heading(story, styles, '3. Technical Specifications', 1)

    specs_mechanical = [
        ['Parameter', 'Specification'],
        ['Machine Type', 'Vertical Machining Centre, 3-axis (X/Y/Z)'],
        ['X-Axis Travel', '800 mm'],
        ['Y-Axis Travel', '500 mm'],
        ['Z-Axis Travel', '600 mm'],
        ['Table Size', '900 mm × 500 mm'],
        ['Table Load Capacity', '600 kg'],
        ['Spindle Speed Range', '100 – 8,000 RPM (standard); 12,000 RPM optional'],
        ['Spindle Taper', 'ISO 40 / BT40'],
        ['Spindle Power (rated)', '18.5 kW (S1) / 22 kW (S6-25%)'],
        ['Spindle Torque (max)', '145 Nm'],
        ['Rapid Traverse (X/Y/Z)', '36 / 36 / 30 m/min'],
        ['Feed Rate Range', '1 – 10,000 mm/min'],
        ['Positioning Accuracy', '±0.005 mm (per ISO 230-2)'],
        ['Repeatability', '±0.003 mm'],
        ['Tool Magazine Capacity', '30 tools (arm-type ATC)'],
        ['Max Tool Diameter', '80 mm (adjacent pockets empty: 150 mm)'],
        ['Max Tool Length', '300 mm'],
        ['Max Tool Weight', '8 kg'],
        ['ATC Change Time', '3.5 s (chip-to-chip)'],
    ]
    t = Table(specs_mechanical, colWidths=[70*mm, 107*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0),  C_WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1),  'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1),  C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(t)
    story.append(Paragraph('Table 3-1: Mechanical Specifications — VMC-3000', styles['caption']))
    story.append(Spacer(1,4*mm))

    specs_electrical = [
        ['Parameter', 'Specification'],
        ['Supply Voltage', '3-phase, 380–420 V AC, 50/60 Hz'],
        ['Power Consumption (rated)', '35 kVA'],
        ['DC Bus Voltage', '560–620 V DC (nominal 590 V)'],
        ['Main Fuse Rating', '80 A (gl/gG type)'],
        ['Ground Leakage (max)', '30 mA (RCD trip threshold)'],
        ['UPS Battery Backup', '20 min (CNC memory protection)'],
        ['Compressed Air Supply', '6 bar, 200 L/min, ISO 8573-1 Class 3'],
        ['Coolant Pump Power', '2.2 kW'],
        ['Lubrication Pump Power', '0.18 kW'],
        ['Control Voltage', '24 V DC (internal)'],
        ['CNC Controller', 'EquipmentIQ CNC-500 (Fanuc 31i-B compatible)'],
    ]
    t2 = Table(specs_electrical, colWidths=[70*mm, 107*mm])
    t2.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_STEEL),
        ('TEXTCOLOR',     (0,0),(-1,0),  C_WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1),  'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1),  C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(t2)
    story.append(Paragraph('Table 3-2: Electrical & Utility Specifications — VMC-3000', styles['caption']))

    # Section 4: Architecture
    story.append(PageBreak())
    section_heading(story, styles, '4. System Architecture', 1)
    story.append(Paragraph(
        'The VMC-3000 system architecture comprises ten integrated subsystems, each '
        'monitored by dedicated sensors and reporting to the CNC controller via '
        'CANopen fieldbus (ISO 11898). The Module Identification (MID) numbering '
        'follows SAE J2012 convention.', styles['body']))

    arch_rows = [['MID', 'Subsystem Code', 'Subsystem Name', 'Primary Sensors', 'Bus']]
    for code, sub in ecm['subsystems'].items():
        arch_rows.append([
            str(sub['mid']), code, sub['name'],
            'Accelerometer, Temp, Current' if code in ('SPN','AXS','VIB') else
            'Pressure, Flow, Level' if code in ('CLS','LUB','HYD') else
            'Voltage, Current, Temp' if code in ('ELC','THM') else
            'CPU, Memory, Bus' if code == 'CNC' else 'All sensors',
            'CANopen'
        ])
    t3 = Table(arch_rows, colWidths=[14*mm, 22*mm, 55*mm, 60*mm, 20*mm], repeatRows=1)
    t3.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0),  C_WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ('ALIGN',         (0,0),(1,-1),  'CENTER'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    story.append(t3)
    story.append(Paragraph('Table 4-1: Subsystem Architecture — MID Mapping', styles['caption']))
    story.append(Spacer(1,4*mm))

    # Section 5
    section_heading(story, styles, '5. Subsystem Descriptions', 1)
    subsys_desc = [
        ('Spindle Drive System (SPN, MID 128)',
         'The spindle system delivers 18.5 kW continuous power via a 3-phase induction motor '
         'with integral encoder. Bearing health is monitored by the Bosch CISS tri-axial '
         'accelerometer mounted at the spindle nose, sampling at 2,000 Hz. Vibration data is '
         'processed on the EquipmentIQ edge gateway to compute RMS, crest factor, and kurtosis '
         'index in real time. Refer to DOC-EIQ-002 for full spindle service documentation.'),
        ('Axis Servo System (AXS, MID 130)',
         'Three linear axes (X, Y, Z) driven by AC servo motors with absolute encoders '
         '(17-bit resolution). Ball screws (grade C3) and linear guides (grade H) provide '
         'positioning accuracy of ±0.005 mm. Servo drives communicate with the CNC controller '
         'via FSSB (Fibre-optic Servo Serial Bus). Refer to DOC-EIQ-003.'),
        ('Tool Change System (TCS, MID 132)',
         'A 30-position arm-type automatic tool changer (ATC) provides chip-to-chip change '
         'time of 3.5 s. Tool presence and identity are monitored by inductive sensors in each '
         'pocket. Tool length is verified by in-process touch probe after each change. Clamp '
         'force is monitored by pressure transducer (P021, normal 55–75 bar).'),
        ('Coolant System (CLS, MID 134)',
         'The coolant system delivers up to 40 L/min through-spindle and flood coolant. A '
         '2.2 kW centrifugal pump draws from a 300 L stainless tank. Coolant temperature is '
         'controlled by an air-cooled chiller (setpoint 20 °C ± 2 °C). Concentration and '
         'flow are monitored continuously. Refer to DOC-EIQ-004.'),
        ('Lubrication System (LUB, MID 136)',
         'A centralised oil-pulse lubrication system (Bijur Delimon type) delivers measured '
         'oil volumes to all linear guide rails and ball screw nuts on a timed cycle '
         '(default: 15 min interval, 2 s pulse). Oil grade: ISO VG 32 way lube oil. '
         'Refer to DOC-EIQ-004.'),
        ('Hydraulic System (HYD, MID 138)',
         'A dedicated hydraulic unit (8 L/min, 70 bar nominal) supplies the workpiece '
         'clamping fixtures and ATC arm swing mechanism. System pressure is monitored by '
         'P050 (normal 60–80 bar). Oil temperature is controlled below 55 °C.'),
        ('CNC Controller (CNC, MID 140)',
         'The EquipmentIQ CNC-500 controller runs a real-time Linux kernel with a Fanuc '
         '31i-B compatible NC interpreter. 10 MB of NC program memory, 64-axis interpolation '
         'capability, and OPC-UA server for data export. Refer to DOC-EIQ-006.'),
        ('Electrical Cabinet (ELC, MID 142)',
         'The IP54-rated electrical cabinet houses the main contactor, servo drives, '
         'DC bus, UPS module, and PLC I/O racks. Cabinet temperature is maintained below '
         '45 °C by forced-air cooling with filtered intake. Refer to DOC-EIQ-006.'),
        ('Vibration Monitoring (VIB, MID 144)',
         'The Bosch CISS tri-axial MEMS accelerometer (±8g range, 2 kHz) is '
         'permanently mounted at the spindle nose. Vibration severity is classified per '
         'ISO 10816-3 Zones A–D. Refer to DOC-EIQ-005.'),
        ('Thermal Management (THM, MID 146)',
         'Eight NTC thermistors monitor spindle motor, servo drives, electrical cabinet, '
         'ambient, coolant, hydraulic oil, and feed motor temperatures. Thermal compensation '
         'for axis positioning error is active above 25 °C ambient.'),
    ]
    for title, desc in subsys_desc:
        section_heading(story, styles, title, level=2)
        story.append(Paragraph(desc, styles['body']))

    # Section 6: Nameplate
    story.append(PageBreak())
    section_heading(story, styles, '6. Nameplate & Identification', 1)
    story.append(Paragraph(
        'The machine nameplate is located on the rear of the machine column, above the '
        'electrical cabinet. The following information is stamped on the nameplate:', styles['body']))
    np_rows = [
        ['Field', 'Example Value', 'Description'],
        ['Model', 'VMC-3000-B', 'Machine model and variant'],
        ['Serial Number', 'EIQ-M01-2019-0042', 'Unique machine identifier (Machine ID for monitoring)'],
        ['Manufacturing Date', '2019-02', 'Year-Month of manufacture'],
        ['Spindle Power', '18.5/22 kW', 'Rated / peak power'],
        ['Supply Voltage', '3~ 400V 50Hz', 'Electrical supply specification'],
        ['IP Rating', 'IP54', 'Enclosure protection class'],
        ['CE Mark', 'CE 2018/037', 'Conformity declaration reference'],
    ]
    nt = Table(np_rows, colWidths=[40*mm, 50*mm, 87*mm], repeatRows=1)
    nt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_STEEL),
        ('TEXTCOLOR',     (0,0),(-1,0),  C_WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(nt)
    story.append(Paragraph('Table 6-1: Nameplate Fields', styles['caption']))
    story.append(Spacer(1,4*mm))
    note_box(story, styles,
        'The Serial Number maps directly to the Machine ID used in the EquipmentIQ monitoring '
        'platform (M01, M02, M03 in the Bosch CNC dataset). Always quote the full serial number '
        'when logging a service request or complaint.')

    # Section 7: Installation
    section_heading(story, styles, '7. Installation Requirements', 1)
    install_items = [
        'Floor loading: minimum 6,000 kg/m2 reinforced concrete slab, 300 mm minimum thickness.',
        'Vibration isolation: anti-vibration levelling pads (supplied), torque to 80 Nm after 48-hour settling.',
        'Supply cable: 4-core 16 mm2 Cu, max 20 m from distribution panel to machine isolator.',
        'Earth bonding: dedicated PE conductor, max 1 ohm machine-to-earth resistance.',
        'Compressed air: 8 mm push-fit connector, 6.0–7.0 bar, dry and filtered (ISO 8573-1 Class 3).',
        'Coolant drain: DN50 gravity drain within 1 m of machine base.',
        'Ambient temperature: 5–40 °C operating, 40–75 % RH non-condensing.',
        'Lighting: minimum 500 lux at machine working area (EN 12464-1).',
    ]
    bullet_list(story, styles, install_items)

    # Section 8: Safety
    section_heading(story, styles, '8. Safety Summary', 1)
    warning_box(story, styles,
        'Before performing any maintenance on the VMC-3000, complete a full Lockout/Tagout '
        '(LOTO) procedure on the main isolator. Verify absence of voltage with a calibrated '
        'tester. The machine stores hazardous energy in the DC bus capacitors for up to '
        '5 minutes after power-off.', label='DANGER')
    warning_box(story, styles,
        'The spindle generates significant force during tool change. Never position hands '
        'near the ATC arm during an active or partially-completed tool change cycle.',
        label='WARNING')
    safety_items = [
        'Emergency stop buttons are located on the operator panel, rear of machine, and electrical cabinet door.',
        'The machine is guarded to EN ISO 23125 (machine tools – safety – turning machines). Never bypass interlocks.',
        'Coolant and lubricant disposal must comply with local environmental regulations.',
        'Use correct PPE: safety glasses, steel-toed boots, cut-resistant gloves when handling tools.',
        'Refer to SDS sheets for coolant concentrate (P031) and way oil (P040) before handling.',
    ]
    bullet_list(story, styles, safety_items)

    build_doc(f'{OUT}/DOC-EIQ-001_Machine_Overview.pdf', story, pt)


# ══════════════════════════════════════════════════════════════════════════════
# DOC-002: SPINDLE DRIVE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
def build_doc002():
    styles = get_styles()
    story  = []
    pt     = DocPageTemplate('DOC-EIQ-002', 'Spindle Drive System — Technical Manual', 'C')

    cover_block(story, styles,
        title='Spindle Drive System\nTechnical Manual',
        subtitle='VMC-3000 Series | MID 128 | Subsystem Code: SPN',
        doc_number='DOC-EIQ-002', revision='C',
        classification='CONTROLLED', issued_by='EquipmentIQ Technical Publications')

    section_heading(story, styles, '1. Introduction', 1)
    story.append(Paragraph(
        'This manual covers the complete spindle drive system of the VMC-3000 vertical '
        'machining centre. The spindle system (subsystem code SPN, Module Identification '
        'MID 128) is responsible for rotating the cutting tool at programmed speeds from '
        '100 to 8,000 RPM and transmitting torque to the workpiece material. This document '
        'provides component descriptions, parameter specifications, wiring references, '
        'error code definitions, maintenance procedures, and spare parts lists.', styles['body']))
    warning_box(story, styles,
        'Spindle maintenance must only be performed by trained service engineers. '
        'Incorrect bearing installation voids warranty and risks catastrophic spindle '
        'failure. Always perform LOTO before accessing spindle internals.', label='WARNING')

    section_heading(story, styles, '2. System Description', 1)
    section_heading(story, styles, '2.1 Spindle Motor', 2)
    story.append(Paragraph(
        'The VMC-3000 spindle motor is a 3-phase AC induction motor with integrated '
        'thermal protection (PTC thermistor embedded in stator winding). The motor '
        'is directly coupled to the spindle shaft via a rigid coupling — no belt or '
        'gearbox. Motor nameplate data:', styles['body']))
    motor_rows = [
        ['Parameter', 'Value'],
        ['Manufacturer', 'EquipmentIQ Drive Systems'],
        ['Model', 'SPN-18-8000-ISO40'],
        ['Rated Power (S1)', '18.5 kW'],
        ['Peak Power (S6-25%)', '22.0 kW'],
        ['Rated Speed', '4,500 RPM'],
        ['Maximum Speed', '8,000 RPM'],
        ['Rated Torque', '39 Nm'],
        ['Peak Torque', '145 Nm'],
        ['Rated Current', '38 A'],
        ['Motor Frame', 'IEC 200L'],
        ['Cooling Method', 'IC416 (forced air, external fan)'],
        ['Insulation Class', 'F (155 °C)'],
        ['Encoder Type', '2,048 PPR incremental + absolute zero mark'],
        ['Bearing Set (front)', '2× angular contact 7014 CDBP4'],
        ['Bearing Set (rear)', '1× cylindrical roller NU1014'],
        ['Grease Type', 'Kluber Isoflex NBU 15'],
        ['Grease Repack Interval', '4,000 h or 2 years (whichever earlier)'],
    ]
    mt = Table(motor_rows, colWidths=[70*mm, 107*mm])
    mt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0),  C_WHITE),
        ('FONTNAME',      (0,0),(-1,-1), 'Helvetica'),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(0,-1),  'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1),  C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(mt)
    story.append(Paragraph('Table 2-1: Spindle Motor Nameplate Data', styles['caption']))

    section_heading(story, styles, '2.2 Spindle Drive Inverter', 2)
    story.append(Paragraph(
        'The spindle motor is controlled by a regenerative AC drive inverter (model '
        'SPN-DRV-22KW) mounted in the electrical cabinet. The drive receives speed '
        'commands from the CNC controller via high-speed serial link (FSSB) and regulates '
        'motor current to achieve commanded speed with closed-loop feedback from the '
        'spindle encoder. The drive monitors output current (P002), motor temperature via '
        'PTC input (P003), and DC bus voltage (P090).', styles['body']))

    section_heading(story, styles, '2.3 Condition Monitoring — Bosch CISS Accelerometer', 2)
    story.append(Paragraph(
        'A Bosch CISS tri-axial MEMS accelerometer is permanently mounted at the spindle '
        'nose housing (refer to Figure 2-1 in installation drawing EIQ-DWG-SPN-003). '
        'Accelerometer specifications:', styles['body']))
    acc_rows = [
        ['Parameter', 'Specification'],
        ['Sensor Model', 'Bosch CISS (Connected Industrial Sensor Solution)'],
        ['Measurement Range', '±8 g (each axis)'],
        ['Sampling Rate', '2,000 Hz (2 kHz) per axis'],
        ['Axes Monitored', 'X (lateral), Y (longitudinal), Z (axial)'],
        ['Output Format', '16-bit signed integer, units: raw ADC counts'],
        ['Scaling', '1 count = 1 mg (approximately)'],
        ['Interface', 'Bluetooth 4.2 / USB (commissioning mode)'],
        ['Operating Temperature', '-20 °C to +70 °C'],
        ['IP Rating', 'IP67'],
        ['Mounting Torque', '12 Nm (M6 stainless bolts)'],
    ]
    at = Table(acc_rows, colWidths=[60*mm, 117*mm])
    at.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_STEEL),
        ('TEXTCOLOR',     (0,0),(-1,0),  C_WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1),  'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1),  C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(at)
    story.append(Paragraph('Table 2-2: Bosch CISS Accelerometer Specifications', styles['caption']))

    section_heading(story, styles, '3. Monitored Parameters', 1)
    story.append(Paragraph(
        'The following parameters are monitored by the SPN subsystem. Parameter IDs (PID) '
        'follow SAE J2012 convention. All values are available on the OPC-UA server at '
        'node ns=2;s=SPN.{param_id}.', styles['body']))
    spn_params = [(pid,p) for pid,p in params.items() if p['subsystem'] in ('SPN','VIB') and pid.startswith(('P00','P06'))]
    param_table(story, styles, spn_params,
        caption='Table 3-1: SPN/VIB Monitored Parameters — VMC-3000')

    section_heading(story, styles, '4. Error Codes — SPN Subsystem', 1)
    story.append(Paragraph(
        'The following error codes are defined for the Spindle Drive System (MID 128). '
        'Codes follow the format SPN-{SEVERITY}-{NUMBER}. Severity levels 1–8 correspond '
        'to CRITICAL through ADVISORY. All codes are indexed in the EquipmentIQ error '
        'database and RAG system.', styles['body']))
    spn_codes = get_codes(['SPN-'])
    error_code_table(story, styles, spn_codes,
        caption='Table 4-1: Spindle Drive System Error Codes (All Severity Levels)')

    # Detailed entries for CR and MJ codes
    story.append(PageBreak())
    section_heading(story, styles, '4.1 Critical & Major Error Code Details', 2)
    for code_id in ['SPN-CR-001','SPN-CR-002','SPN-CR-003','SPN-MJ-001','SPN-MJ-002','SPN-MJ-003','SPN-MJ-004']:
        if code_id not in ec: continue
        c = ec[code_id]
        sev_col = SEV_COLORS.get(c['severity_level'], C_GRAY)
        detail = [
            [Paragraph(f"<b>{c['error_code']}</b>", styles['tbl_hdr']),
             Paragraph(c['title'], styles['tbl_hdr']),
             Paragraph(c['severity_level'], styles['tbl_hdr'])],
        ]
        dt = Table(detail, colWidths=[28*mm, 120*mm, 29*mm])
        dt.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,0), sev_col),
            ('TEXTCOLOR',  (0,0),(-1,0), C_WHITE),
            ('FONTSIZE',   (0,0),(-1,0), 8.5),
            ('TOPPADDING', (0,0),(-1,0), 5),
            ('BOTTOMPADDING',(0,0),(-1,0), 5),
            ('LEFTPADDING',(0,0),(-1,0), 6),
        ]))
        story.append(dt)
        body_rows = [
            [Paragraph('<b>Description</b>', styles['tbl_cell']),
             Paragraph(c['description'], styles['tbl_cell_sm'])],
            [Paragraph('<b>Probable Cause</b>', styles['tbl_cell']),
             Paragraph(c['probable_cause'], styles['tbl_cell_sm'])],
            [Paragraph('<b>Diagnostic Steps</b>', styles['tbl_cell']),
             Paragraph('<br/>'.join(f'&#8226; {s}' for s in c['diagnostic_steps']), styles['tbl_cell_sm'])],
            [Paragraph('<b>Remedy</b>', styles['tbl_cell']),
             Paragraph(c['remedy'], styles['tbl_cell_sm'])],
            [Paragraph('<b>Required Action</b>', styles['tbl_cell']),
             Paragraph(c['required_action'], styles['tbl_cell_sm'])],
            [Paragraph('<b>Related Codes</b>', styles['tbl_cell']),
             Paragraph(', '.join(c['related_codes']) if c['related_codes'] else '—', styles['tbl_cell_sm'])],
        ]
        bt = Table(body_rows, colWidths=[35*mm, 142*mm])
        bt.setStyle(TableStyle([
            ('FONTSIZE',      (0,0),(-1,-1), 8.5),
            ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
            ('ROWBACKGROUNDS',(0,0),(-1,-1), [C_LIGHT, C_WHITE]),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0),(-1,-1), 4),
            ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ]))
        story.append(bt)
        story.append(Spacer(1,3*mm))

    # Section 5: Wiring
    section_heading(story, styles, '5. Wiring Reference', 1)
    story.append(Paragraph(
        'The following table defines the key electrical connections for the SPN subsystem. '
        'Full wiring diagrams are in drawing set EIQ-DWG-SPN-001 to EIQ-DWG-SPN-008. '
        'Wire gauge is AWG/metric equivalent.', styles['body']))
    spn_wiring = [
        {'signal':'Spindle Motor U-phase', 'from_pin':'SPN-DRV-22KW:U', 'to_pin':'MTR-SPN:U1', 'gauge':'6 mm2', 'color':'Brown', 'notes':'Screened power cable'},
        {'signal':'Spindle Motor V-phase', 'from_pin':'SPN-DRV-22KW:V', 'to_pin':'MTR-SPN:V1', 'gauge':'6 mm2', 'color':'Black', 'notes':'Screened power cable'},
        {'signal':'Spindle Motor W-phase', 'from_pin':'SPN-DRV-22KW:W', 'to_pin':'MTR-SPN:W1', 'gauge':'6 mm2', 'color':'Grey', 'notes':'Screened power cable'},
        {'signal':'Motor PE (ground)', 'from_pin':'SPN-DRV-22KW:PE', 'to_pin':'MTR-SPN:PE', 'gauge':'6 mm2', 'color':'Green/Yellow', 'notes':''},
        {'signal':'Encoder A+', 'from_pin':'MTR-SPN:ENC-A+', 'to_pin':'CNC-500:SPN-ENC-A+', 'gauge':'0.5 mm2', 'color':'White', 'notes':'Twisted pair, shielded'},
        {'signal':'Encoder A-', 'from_pin':'MTR-SPN:ENC-A-', 'to_pin':'CNC-500:SPN-ENC-A-', 'gauge':'0.5 mm2', 'color':'White/Black', 'notes':'Twisted pair, shielded'},
        {'signal':'Encoder B+', 'from_pin':'MTR-SPN:ENC-B+', 'to_pin':'CNC-500:SPN-ENC-B+', 'gauge':'0.5 mm2', 'color':'Green', 'notes':''},
        {'signal':'Encoder B-', 'from_pin':'MTR-SPN:ENC-B-', 'to_pin':'CNC-500:SPN-ENC-B-', 'gauge':'0.5 mm2', 'color':'Green/Black', 'notes':''},
        {'signal':'Encoder Z (zero mark)', 'from_pin':'MTR-SPN:ENC-Z', 'to_pin':'CNC-500:SPN-ENC-Z', 'gauge':'0.5 mm2', 'color':'Blue', 'notes':''},
        {'signal':'Motor PTC (thermal)', 'from_pin':'MTR-SPN:PTC+', 'to_pin':'SPN-DRV-22KW:PTC-IN', 'gauge':'0.75 mm2', 'color':'Red', 'notes':'PTC thermistor, 1330 ohm at 155 C'},
        {'signal':'CISS Sensor Power', 'from_pin':'CISS-SPN:VCC', 'to_pin':'EIQ-EDGE:SENS-VCC', 'gauge':'0.5 mm2', 'color':'Red', 'notes':'5 V DC'},
        {'signal':'CISS Sensor GND', 'from_pin':'CISS-SPN:GND', 'to_pin':'EIQ-EDGE:SENS-GND', 'gauge':'0.5 mm2', 'color':'Black', 'notes':''},
        {'signal':'Orientation Switch', 'from_pin':'SPN-ORIENT-SW:COM', 'to_pin':'PLC-I/O:X0.4', 'gauge':'0.75 mm2', 'color':'Orange', 'notes':'NPN, normally open'},
        {'signal':'Spindle Brake (24V)', 'from_pin':'PLC-Q:Y0.3', 'to_pin':'SPN-BRAKE-SOL:A1', 'gauge':'0.75 mm2', 'color':'Violet', 'notes':'24 V DC coil, 15 W'},
    ]
    wiring_schematic_text(story, styles, 'Table 5-1: Spindle Drive System — Wiring Connections', spn_wiring)

    # Section 6: Maintenance
    section_heading(story, styles, '6. Preventive Maintenance Schedule', 1)
    maint_rows = [
        ['Interval', 'Task', 'Reference', 'Duration'],
        ['Daily', 'Check spindle warm-up program executed (P003 >35 °C before full-speed cuts)', 'SPN-WN-002', '5 min'],
        ['Weekly', 'Inspect spindle taper bore for chips or damage; clean with IPA', 'Visual', '10 min'],
        ['Monthly', 'Check vibration trend P004 vs baseline; log result', 'SPN-SR-003', '15 min'],
        ['500 h', 'Verify spindle encoder signal quality on oscilloscope', 'SPN-SR-002', '30 min'],
        ['1,000 h', 'Clean spindle cooling air filter; check fan rotation', 'SPN-MJ-001', '20 min'],
        ['2,000 h', 'Full spindle vibration spectrum analysis (FFT)', 'DOC-EIQ-005', '60 min'],
        ['4,000 h', 'Spindle bearing grease repack (Kluber Isoflex NBU 15)', 'EIQ-PROC-SPN-001', '4 h'],
        ['On alarm', 'Review P004 trend; escalate per SPN-MJ-002 or SPN-CR-001', 'Error code', '—'],
    ]
    mt2 = Table(maint_rows, colWidths=[22*mm, 98*mm, 32*mm, 25*mm], repeatRows=1)
    mt2.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    story.append(mt2)
    story.append(Paragraph('Table 6-1: Spindle Preventive Maintenance Schedule', styles['caption']))

    # Section 7: Parts
    section_heading(story, styles, '7. Spare Parts List', 1)
    spn_parts = [
        {'pn':'EIQ-SPN-BRG-7014','desc':'Angular contact bearing 7014 CDBP4 (front, pair)','qty':1,'unit':'Pair','lead':'2 weeks','stock':2},
        {'pn':'EIQ-SPN-BRG-NU1014','desc':'Cylindrical roller bearing NU1014 (rear)','qty':1,'unit':'Each','lead':'1 week','stock':1},
        {'pn':'EIQ-SPN-ENC-2048','desc':'Spindle encoder, 2048 PPR, incremental + Z','qty':1,'unit':'Each','lead':'3 weeks','stock':1},
        {'pn':'EIQ-SPN-FAN-200L','desc':'Spindle motor cooling fan (IC416)','qty':1,'unit':'Each','lead':'1 week','stock':2},
        {'pn':'EIQ-SPN-FILTER-001','desc':'Spindle motor air filter mat (pack of 5)','qty':1,'unit':'Pack','lead':'1 week','stock':2},
        {'pn':'EIQ-SPN-GREASE-NBU15','desc':'Kluber Isoflex NBU 15 grease, 50 g cartridge','qty':1,'unit':'Each','lead':'3 days','stock':5},
        {'pn':'EIQ-SPN-BRAKE-SOL','desc':'Spindle orientation brake solenoid, 24VDC 15W','qty':1,'unit':'Each','lead':'2 weeks','stock':1},
        {'pn':'EIQ-CISS-SENSOR-001','desc':'Bosch CISS tri-axial accelerometer (replacement)','qty':1,'unit':'Each','lead':'4 weeks','stock':1},
        {'pn':'EIQ-SPN-DRV-22KW','desc':'Spindle drive inverter 22 kW (full replacement)','qty':1,'unit':'Each','lead':'6 weeks','stock':1},
        {'pn':'EIQ-SPN-CABLE-POWER','desc':'Spindle motor power cable, 6mm2 screened, 5m','qty':1,'unit':'Each','lead':'1 week','stock':2},
    ]
    parts_table(story, styles, spn_parts, caption='Table 7-1: Spindle System Spare Parts')

    build_doc(f'{OUT}/DOC-EIQ-002_Spindle_Drive_System.pdf', story, pt)


# ══════════════════════════════════════════════════════════════════════════════
# DOC-003: AXIS SERVO & MOTION CONTROL
# ══════════════════════════════════════════════════════════════════════════════
def build_doc003():
    styles = get_styles()
    story  = []
    pt     = DocPageTemplate('DOC-EIQ-003', 'Axis Servo & Motion Control — Technical Manual', 'B')

    cover_block(story, styles,
        title='Axis Servo & Motion Control\nTechnical Manual',
        subtitle='VMC-3000 Series | MID 130 | Subsystem Code: AXS',
        doc_number='DOC-EIQ-003', revision='B',
        classification='CONTROLLED', issued_by='EquipmentIQ Technical Publications')

    section_heading(story, styles, '1. Introduction', 1)
    story.append(Paragraph(
        'This manual covers the three-axis servo drive and motion control system of the '
        'VMC-3000 machining centre (subsystem AXS, MID 130). Each linear axis (X, Y, Z) '
        'is driven by a dedicated AC servo motor with absolute encoder, ball screw, and '
        'profiled linear guide rail. The servo drives receive interpolated position '
        'commands from the CNC-500 controller via FSSB and close the position loop at '
        '1 ms cycle time.', styles['body']))

    section_heading(story, styles, '2. Axis Servo Motors', 1)
    motor_spec = [
        ['Parameter', 'X-Axis', 'Y-Axis', 'Z-Axis'],
        ['Model', 'SVM-1500-X', 'SVM-1500-Y', 'SVM-2200-Z'],
        ['Rated Power', '1.5 kW', '1.5 kW', '2.2 kW'],
        ['Rated Torque', '7.2 Nm', '7.2 Nm', '10.5 Nm'],
        ['Peak Torque', '21.6 Nm', '21.6 Nm', '31.5 Nm'],
        ['Rated Current', '6.5 A', '6.5 A', '9.2 A'],
        ['Maximum Speed', '3,000 RPM', '3,000 RPM', '3,000 RPM'],
        ['Encoder', '17-bit absolute', '17-bit absolute', '17-bit absolute'],
        ['Brake', 'None', 'None', '24 V DC spring-set'],
        ['Frame', 'IEC 90L', 'IEC 90L', 'IEC 100L'],
    ]
    mt = Table(motor_spec, colWidths=[45*mm, 45*mm, 45*mm, 42*mm], repeatRows=1)
    mt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1), C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('ALIGN',         (1,0),(-1,-1),'CENTER'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(mt)
    story.append(Paragraph('Table 2-1: Axis Servo Motor Specifications', styles['caption']))
    story.append(Spacer(1,4*mm))
    note_box(story, styles,
        'The Z-axis motor includes a spring-set electromagnetic brake (PN: EIQ-AXS-BRK-Z) '
        'which engages automatically when the drive is de-energised to prevent axis drop. '
        'Do not disable the brake without first supporting the spindle head with a block.')

    section_heading(story, styles, '3. Ball Screw & Linear Guide Specifications', 1)
    mech_rows = [
        ['Parameter', 'X-Axis', 'Y-Axis', 'Z-Axis'],
        ['Ball Screw Diameter', '32 mm', '32 mm', '40 mm'],
        ['Ball Screw Lead', '16 mm/rev', '16 mm/rev', '16 mm/rev'],
        ['Ball Screw Grade', 'JIS C3', 'JIS C3', 'JIS C3'],
        ['Ball Screw Nut Type', 'Double-nut, preloaded', 'Double-nut, preloaded', 'Double-nut, preloaded'],
        ['Max Backlash (spec)', '< 0.005 mm', '< 0.005 mm', '< 0.005 mm'],
        ['Linear Guide Type', 'THK SRG 35C', 'THK SRG 35C', 'THK SRS 45C'],
        ['Number of Rails', '2', '2', '2'],
        ['Guide Preload Class', 'Z1 (light)', 'Z1 (light)', 'Z2 (medium)'],
        ['Lube Type', 'ISO VG 32 Way Lube', 'ISO VG 32 Way Lube', 'ISO VG 32 Way Lube'],
        ['Lube Interval', '15 min / 2 s pulse', '15 min / 2 s pulse', '15 min / 2 s pulse'],
    ]
    mt2 = Table(mech_rows, colWidths=[50*mm, 43*mm, 43*mm, 41*mm], repeatRows=1)
    mt2.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_STEEL),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1), C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('ALIGN',         (1,0),(-1,-1),'CENTER'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(mt2)
    story.append(Paragraph('Table 3-1: Ball Screw and Linear Guide Specifications', styles['caption']))

    section_heading(story, styles, '4. Monitored Parameters', 1)
    axs_params = [(pid,p) for pid,p in params.items() if p['subsystem']=='AXS']
    param_table(story, styles, axs_params, caption='Table 4-1: AXS Monitored Parameters')

    section_heading(story, styles, '5. Axis Wiring Reference', 1)
    axs_wiring = [
        {'signal':'X-Axis Motor U','from_pin':'AXS-DRV-X:U','to_pin':'MTR-X:U1','gauge':'2.5 mm2','color':'Brown','notes':'Screened, 5 m'},
        {'signal':'X-Axis Motor V','from_pin':'AXS-DRV-X:V','to_pin':'MTR-X:V1','gauge':'2.5 mm2','color':'Black','notes':''},
        {'signal':'X-Axis Motor W','from_pin':'AXS-DRV-X:W','to_pin':'MTR-X:W1','gauge':'2.5 mm2','color':'Grey','notes':''},
        {'signal':'X-Axis Encoder','from_pin':'MTR-X:ENC','to_pin':'CNC-500:AX1-ENC','gauge':'0.5 mm2','color':'Violet','notes':'17-bit absolute, Cat5e'},
        {'signal':'Y-Axis Motor U','from_pin':'AXS-DRV-Y:U','to_pin':'MTR-Y:U1','gauge':'2.5 mm2','color':'Brown','notes':'Screened, 5 m'},
        {'signal':'Y-Axis Motor V','from_pin':'AXS-DRV-Y:V','to_pin':'MTR-Y:V1','gauge':'2.5 mm2','color':'Black','notes':''},
        {'signal':'Y-Axis Encoder','from_pin':'MTR-Y:ENC','to_pin':'CNC-500:AX2-ENC','gauge':'0.5 mm2','color':'Violet','notes':'17-bit absolute, Cat5e'},
        {'signal':'Z-Axis Motor U','from_pin':'AXS-DRV-Z:U','to_pin':'MTR-Z:U1','gauge':'4.0 mm2','color':'Brown','notes':'Heavier gauge, 2.2 kW'},
        {'signal':'Z-Axis Motor W','from_pin':'AXS-DRV-Z:W','to_pin':'MTR-Z:W1','gauge':'4.0 mm2','color':'Grey','notes':''},
        {'signal':'Z-Axis Encoder','from_pin':'MTR-Z:ENC','to_pin':'CNC-500:AX3-ENC','gauge':'0.5 mm2','color':'Violet','notes':'17-bit absolute'},
        {'signal':'Z-Axis Brake','from_pin':'PLC-Q:Y0.5','to_pin':'MTR-Z:BRK+','gauge':'0.75 mm2','color':'Red','notes':'24 V DC, spring-set'},
        {'signal':'X Home Switch','from_pin':'SW-HM-X:NO','to_pin':'PLC-I:X1.0','gauge':'0.5 mm2','color':'White','notes':'NPN proximity, 24V'},
        {'signal':'Y Home Switch','from_pin':'SW-HM-Y:NO','to_pin':'PLC-I:X1.1','gauge':'0.5 mm2','color':'White','notes':'NPN proximity'},
        {'signal':'Z Home Switch','from_pin':'SW-HM-Z:NO','to_pin':'PLC-I:X1.2','gauge':'0.5 mm2','color':'White','notes':'NPN proximity'},
        {'signal':'X Over-travel +','from_pin':'SW-OT-X+:NC','to_pin':'EMG-CHAIN:IN4','gauge':'0.75 mm2','color':'Orange','notes':'Hardwired to E-stop chain'},
        {'signal':'Y Over-travel +','from_pin':'SW-OT-Y+:NC','to_pin':'EMG-CHAIN:IN5','gauge':'0.75 mm2','color':'Orange','notes':''},
        {'signal':'Z Over-travel -','from_pin':'SW-OT-Z-:NC','to_pin':'EMG-CHAIN:IN6','gauge':'0.75 mm2','color':'Orange','notes':''},
    ]
    wiring_schematic_text(story, styles, 'Table 5-1: Axis Servo System Wiring Connections', axs_wiring)

    section_heading(story, styles, '6. Error Codes — AXS Subsystem', 1)
    axs_codes = get_codes(['AXS-'])
    error_code_table(story, styles, axs_codes, caption='Table 6-1: Axis Servo Error Codes')

    section_heading(story, styles, '7. Servo Tuning & Commissioning', 1)
    story.append(Paragraph(
        'After any mechanical repair (ball screw replacement, bearing change, guide rail '
        'replacement), the affected axis servo loop must be re-tuned using the EIQ servo '
        'tuning utility (menu: SYS > SERVO > AUTO-TUNE). The following parameters must be '
        'recorded before and after tuning:', styles['body']))
    tuning_items = [
        'Position loop gain (Kp): nominal 80–120 (machine-dependent).',
        'Velocity loop gain (Kv): nominal 1500–2500.',
        'Following error at 1,000 mm/min rapid: must be <0.01 mm steady-state.',
        'Quadrant spike at reversal: must be <0.005 mm after backlash compensation.',
        'Servo vibration check: run at F=1000, F=5000 mm/min and verify P016 <0.02 mm.',
        'Thermal drift over 4-hour warm-up: record axis position shift at G54 datum.',
    ]
    bullet_list(story, styles, tuning_items)

    section_heading(story, styles, '8. Spare Parts — Axis Servo System', 1)
    axs_parts = [
        {'pn':'EIQ-AXS-BSC-X32','desc':'Ball screw X-axis 32mm dia, C3, 800mm length','qty':1,'unit':'Each','lead':'6 weeks','stock':1},
        {'pn':'EIQ-AXS-BSC-Z40','desc':'Ball screw Z-axis 40mm dia, C3, 600mm length','qty':1,'unit':'Each','lead':'6 weeks','stock':1},
        {'pn':'EIQ-AXS-NUT-32','desc':'Ball screw nut 32mm double-preloaded (X/Y)','qty':1,'unit':'Each','lead':'4 weeks','stock':2},
        {'pn':'EIQ-AXS-NUT-40','desc':'Ball screw nut 40mm double-preloaded (Z)','qty':1,'unit':'Each','lead':'4 weeks','stock':1},
        {'pn':'EIQ-AXS-ENC-17B','desc':'17-bit absolute encoder (any axis)','qty':1,'unit':'Each','lead':'3 weeks','stock':2},
        {'pn':'EIQ-AXS-BRK-Z','desc':'Z-axis electromagnetic brake, 24VDC spring-set','qty':1,'unit':'Each','lead':'2 weeks','stock':1},
        {'pn':'EIQ-AXS-DRV-15','desc':'Servo drive 1.5 kW (X/Y axis)','qty':1,'unit':'Each','lead':'4 weeks','stock':1},
        {'pn':'EIQ-AXS-DRV-22','desc':'Servo drive 2.2 kW (Z axis)','qty':1,'unit':'Each','lead':'4 weeks','stock':1},
        {'pn':'EIQ-AXS-PROX-24V','desc':'NPN proximity switch 24VDC (home/overtravel)','qty':1,'unit':'Each','lead':'1 week','stock':5},
    ]
    parts_table(story, styles, axs_parts, caption='Table 8-1: Axis Servo Spare Parts List')

    build_doc(f'{OUT}/DOC-EIQ-003_Axis_Servo_Motion_Control.pdf', story, pt)


# ══════════════════════════════════════════════════════════════════════════════
# DOC-004: COOLANT & LUBRICATION SYSTEMS
# ══════════════════════════════════════════════════════════════════════════════
def build_doc004():
    styles = get_styles()
    story  = []
    pt     = DocPageTemplate('DOC-EIQ-004', 'Coolant & Lubrication Systems — Maintenance Guide', 'A')

    cover_block(story, styles,
        title='Coolant & Lubrication Systems\nMaintenance Guide',
        subtitle='VMC-3000 Series | MID 134 (CLS) | MID 136 (LUB) | MID 138 (HYD)',
        doc_number='DOC-EIQ-004', revision='A',
        classification='CONTROLLED', issued_by='EquipmentIQ Technical Publications')

    section_heading(story, styles, '1. Coolant System (CLS, MID 134)', 1)
    section_heading(story, styles, '1.1 System Overview', 2)
    story.append(Paragraph(
        'The VMC-3000 coolant system delivers semi-synthetic metalworking fluid to the '
        'cutting zone via flood nozzles and through-spindle coolant (TSC). The system '
        'comprises a 300 L stainless steel tank, a 2.2 kW centrifugal pump, air-cooled '
        'chiller (setpoint 20 °C), inline flow meter (P030), pressure transducer (P032), '
        'temperature sensor (P031), and a level float switch (P033).', styles['body']))
    warning_box(story, styles,
        'Machine will perform an emergency stop (CLS-CR-001) if coolant flow P030 drops '
        'below 5 L/min during active cutting. Do not bypass the flow switch during '
        'production.', label='WARNING')

    section_heading(story, styles, '1.2 Coolant Specification', 2)
    cool_spec = [
        ['Parameter', 'Specification'],
        ['Fluid Type', 'Semi-synthetic metalworking emulsion'],
        ['Recommended Product', 'Blaser Swisslube Blasocut 4000 Strong or equivalent'],
        ['Concentration (aluminium)', '6–8% by volume (refractometer reading 3–4% Brix)'],
        ['Concentration (steel)', '8–10% by volume (4–5% Brix)'],
        ['pH Range', '8.5 – 9.5 (check weekly with pH strip)'],
        ['Maximum Temperature', '35 °C (alarm at 40 °C — CLS-MJ-001)'],
        ['Tank Volume', '300 L (fill to 85% operating level)'],
        ['Replacement Interval', 'Every 6 months or when concentration/pH out of range'],
        ['Disposal', 'Licensed waste coolant disposal only (consult local regulations)'],
    ]
    ct = Table(cool_spec, colWidths=[55*mm, 122*mm])
    ct.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1), C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(ct)
    story.append(Paragraph('Table 1-1: Coolant Specification', styles['caption']))

    section_heading(story, styles, '1.3 Coolant System Parameters', 2)
    cls_params = [(pid,p) for pid,p in params.items() if p['subsystem']=='CLS']
    param_table(story, styles, cls_params, caption='Table 1-2: CLS Monitored Parameters')

    section_heading(story, styles, '1.4 Coolant Error Codes', 2)
    cls_codes = get_codes(['CLS-'])
    error_code_table(story, styles, cls_codes, caption='Table 1-3: CLS Error Codes')

    section_heading(story, styles, '1.5 Coolant Maintenance Schedule', 2)
    cls_maint = [
        ['Interval', 'Task', 'Error Code Ref'],
        ['Daily', 'Check tank level P033 (min 25%); add pre-mixed coolant if low', 'CLS-WN-001'],
        ['Weekly', 'Measure concentration with refractometer; record Brix reading', 'CLS-MD-001'],
        ['Weekly', 'Measure pH with calibrated pH meter; record value', '—'],
        ['Weekly', 'Check coolant temperature P031 at start and end of shift', 'CLS-MJ-001'],
        ['Monthly', 'Clean coolant filter element; inspect for chips', 'CLS-SR-001'],
        ['Monthly', 'Check coolant pump current (compare to motor nameplate)', '—'],
        ['Monthly', 'Inspect coolant nozzle positions and alignment', 'CLS-MN-001'],
        ['3-monthly', 'Clean coolant tank: pump out, scrub, refill', 'DOC-EIQ-004'],
        ['6-monthly', 'Full coolant replacement; dispose of old coolant per regulations', '—'],
        ['6-monthly', 'Inspect chiller condenser fins; clean with fin comb', 'CLS-MJ-001'],
    ]
    clt = Table(cls_maint, colWidths=[22*mm, 121*mm, 34*mm], repeatRows=1)
    clt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    story.append(clt)
    story.append(Paragraph('Table 1-4: Coolant System Maintenance Schedule', styles['caption']))

    # Lubrication
    story.append(PageBreak())
    section_heading(story, styles, '2. Lubrication System (LUB, MID 136)', 1)
    section_heading(story, styles, '2.1 System Overview', 2)
    story.append(Paragraph(
        'The centralised lubrication system is a Bijur Delimon-type oil-pulse (progressive '
        'distributor) system. An electric pump (0.18 kW) delivers measured pulses of ISO '
        'VG 32 way lube oil to all ball screw nuts, linear guide carriages, and ball screw '
        'support bearings on a timed cycle (default 15 minutes interval, 2-second pump '
        'duration). The system monitors pump pressure (P040), reservoir level (P041), '
        'and pump motor current (P042).', styles['body']))
    note_box(story, styles,
        'The lubrication system is the single most important factor in ball screw and '
        'guide rail longevity. Failure to maintain oil level P041 above 25% will trigger '
        'LUB-SR-001 and accelerate wear, leading to axis following errors (AXS-MJ-001).')

    lub_spec = [
        ['Parameter', 'Specification'],
        ['Oil Type', 'ISO VG 32 Way Lube (mineral-based)'],
        ['Recommended Product', 'Mobil Vactra Oil No.1 or equivalent'],
        ['Reservoir Volume', '2.5 L'],
        ['Pump Cycle Interval', '15 min (adjustable via parameter P-LUB-01)'],
        ['Pump Duration', '2 s per cycle (adjustable via P-LUB-02)'],
        ['Nominal Delivery Pressure', '2.0–4.5 bar (P040)'],
        ['Critical Low Pressure', '0.5 bar (triggers LUB-CR-001 — machine stop)'],
        ['Pump Motor', '0.18 kW, 3-phase, 50 Hz'],
        ['Distributor Type', 'Progressive (SSV metering valves)'],
        ['Number of Lube Points', '18 (8 guide carriages, 6 ball screw nuts, 4 support bearings)'],
    ]
    lt = Table(lub_spec, colWidths=[55*mm, 122*mm])
    lt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_STEEL),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1), C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(lt)
    story.append(Paragraph('Table 2-1: Lubrication System Specification', styles['caption']))

    section_heading(story, styles, '2.2 Lubrication Parameters', 2)
    lub_params = [(pid,p) for pid,p in params.items() if p['subsystem']=='LUB']
    param_table(story, styles, lub_params, caption='Table 2-2: LUB Monitored Parameters')

    section_heading(story, styles, '2.3 Lubrication Error Codes', 2)
    lub_codes = get_codes(['LUB-'])
    error_code_table(story, styles, lub_codes, caption='Table 2-3: LUB Error Codes')

    section_heading(story, styles, '3. Hydraulic System (HYD, MID 138)', 1)
    story.append(Paragraph(
        'The hydraulic system powers workpiece clamping fixtures and the ATC arm swing '
        'cylinder. A gear pump (8 L/min, 70 bar nominal) draws from a 20 L reservoir. '
        'System pressure is regulated by a pilot-operated relief valve and monitored by '
        'P050. Oil temperature is controlled below 55 °C by an air-cooled heat exchanger.', styles['body']))
    hyd_params = [p for pid, p in params.items() if p['subsystem'] == 'HYD']
    param_table(story, styles, hyd_params, caption='Table 3-1: HYD Monitored Parameters')
    hyd_codes = get_codes(['HYD-'])
    error_code_table(story, styles, hyd_codes, caption='Table 3-2: HYD Error Codes')

    section_heading(story, styles, '4. Spare Parts — Fluid Systems', 1)
    fluid_parts = [
        {'pn':'EIQ-CLS-PUMP-22','desc':'Coolant pump 2.2 kW centrifugal (complete)','qty':1,'unit':'Each','lead':'3 weeks','stock':1},
        {'pn':'EIQ-CLS-FILTER-10','desc':'Coolant filter element 10 micron (pack of 10)','qty':1,'unit':'Pack','lead':'1 week','stock':2},
        {'pn':'EIQ-CLS-FLOW-001','desc':'Coolant flow meter (P030 sensor)','qty':1,'unit':'Each','lead':'2 weeks','stock':1},
        {'pn':'EIQ-CLS-TEMP-001','desc':'Coolant temperature sensor NTC (P031)','qty':1,'unit':'Each','lead':'1 week','stock':2},
        {'pn':'EIQ-LUB-PUMP-018','desc':'Lubrication pump 0.18 kW complete unit','qty':1,'unit':'Each','lead':'3 weeks','stock':1},
        {'pn':'EIQ-LUB-SSV-6','desc':'Progressive distributor SSV-6 metering block','qty':1,'unit':'Each','lead':'2 weeks','stock':2},
        {'pn':'EIQ-LUB-OIL-VG32','desc':'ISO VG32 way lube oil, 5 L container','qty':1,'unit':'Container','lead':'3 days','stock':4},
        {'pn':'EIQ-HYD-PUMP-8','desc':'Hydraulic gear pump 8 L/min 70 bar','qty':1,'unit':'Each','lead':'4 weeks','stock':1},
        {'pn':'EIQ-HYD-SEAL-KIT','desc':'Hydraulic cylinder seal kit (all circuits)','qty':1,'unit':'Kit','lead':'1 week','stock':2},
        {'pn':'EIQ-HYD-OIL-HM46','desc':'Hydraulic oil ISO VG 46, 20 L','qty':1,'unit':'Can','lead':'3 days','stock':1},
    ]
    parts_table(story, styles, fluid_parts, caption='Table 4-1: Coolant/Lubrication/Hydraulic Spare Parts')

    build_doc(f'{OUT}/DOC-EIQ-004_Coolant_Lubrication_Systems.pdf', story, pt)


# ══════════════════════════════════════════════════════════════════════════════
# DOC-005: VIBRATION MONITORING & CONDITION MONITORING
# ══════════════════════════════════════════════════════════════════════════════
def build_doc005():
    styles = get_styles()
    story  = []
    pt     = DocPageTemplate('DOC-EIQ-005', 'Vibration Monitoring & Condition Monitoring — Reference', 'B')

    cover_block(story, styles,
        title='Vibration Monitoring &\nCondition Monitoring Reference',
        subtitle='VMC-3000 Series | MID 144 (VIB) | Bosch CISS Dataset | ISO 10816-3',
        doc_number='DOC-EIQ-005', revision='B',
        classification='CONTROLLED', issued_by='EquipmentIQ Technical Publications')

    section_heading(story, styles, '1. Introduction', 1)
    story.append(Paragraph(
        'This reference document describes the vibration monitoring system integrated into '
        'the VMC-3000 machining centre, the data collected by the Bosch CISS tri-axial '
        'accelerometer, the statistical features extracted for condition monitoring, and '
        'the ISO 10816-3 severity classification zones used to trigger error codes. '
        'This document is the technical basis for the EquipmentIQ predictive maintenance '
        'AI system and the RAG-powered diagnostic agent.', styles['body']))

    section_heading(story, styles, '2. Vibration Severity — ISO 10816-3 Classification', 1)
    story.append(Paragraph(
        'Machine vibration severity is evaluated per ISO 10816-3 (Mechanical vibration — '
        'Evaluation of machine vibration by measurements on non-rotating parts — Part 3: '
        'Industrial machines with nominal power above 15 kW and nominal speeds between '
        '120 RPM and 15,000 RPM). The VMC-3000 spindle falls in Group 2 (flexible '
        'mounting) of ISO 10816-3.', styles['body']))
    iso_rows = [
        ['Zone', 'RMS Range (mm/s)', 'Description', 'Machine Status', 'Error Codes Triggered'],
        ['A', '0 – 2.3', 'New machine reference', 'Optimal — unrestricted long-term operation', 'VIB-AD-001, VIB-WN-001'],
        ['B', '2.3 – 4.5', 'Acceptable for long-term', 'Normal production — monitor trend', 'VIB-NC-001, VIB-MN-001'],
        ['B upper', '4.5 – 7.1', 'Elevated but not alarming', 'Reduce load; inspect tool', 'VIB-SR-001, VIB-MD-001'],
        ['C', '7.1 – 11.2', 'Unsatisfactory — short-term only', 'Plan maintenance within 4 h', 'VIB-MJ-001, SPN-MJ-002'],
        ['D', '> 11.2', 'Dangerous — machine damage risk', 'Emergency stop', 'VIB-CR-001, SPN-CR-001'],
    ]
    it = Table(iso_rows, colWidths=[18*mm, 30*mm, 42*mm, 48*mm, 39*mm], repeatRows=1)
    row_bg = [C_GREEN, HexColor('#d5f5e3'), HexColor('#fef9e7'), C_ORANGE, C_RED]
    it.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ALIGN',         (0,0),(1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    for i, bg in enumerate(row_bg, 1):
        it.setStyle(TableStyle([('BACKGROUND', (0,i),(0,i), bg)]))
    story.append(it)
    story.append(Paragraph('Table 2-1: ISO 10816-3 Vibration Severity Zones — VMC-3000', styles['caption']))

    section_heading(story, styles, '3. Statistical Features Extracted', 1)
    story.append(Paragraph(
        'The EquipmentIQ edge gateway processes raw accelerometer data from the Bosch CISS '
        'sensor in real time, extracting eight statistical features per axis per operation '
        'cycle. These features form the feature vector used by the predictive maintenance '
        'ML model and are stored in the EquipmentIQ time-series database.', styles['body']))
    feat_rows = [
        ['Feature', 'Symbol', 'Formula', 'Fault Sensitivity', 'Threshold Action'],
        ['RMS', 'x_rms', 'sqrt(mean(x^2))', 'Overall energy — rises with any fault', 'ISO zone classification'],
        ['Peak', 'x_peak', 'max(|x|)', 'Impact events — transient faults', 'CR threshold if >2x normal'],
        ['Crest Factor', 'x_crest', 'x_peak / x_rms', 'Impulsive faults (early bearing)', 'Alert if >4.5'],
        ['Kurtosis', 'x_kurt', 'E[(x-mu)^4] / sigma^4', 'Best early-fault indicator', 'Warning if >5.0, Alarm if >8.0'],
        ['Mean', 'x_mean', 'mean(x)', 'DC offset — static load', 'Cross-check only'],
        ['Std Dev', 'x_std', 'std(x)', 'Signal spread — general health', 'Trend monitoring'],
        ['Min', 'x_min', 'min(x)', 'Negative peak value', 'Absolute limit check'],
        ['Max', 'x_max', 'max(x)', 'Positive peak value', 'Absolute limit check'],
    ]
    ft = Table(feat_rows, colWidths=[22*mm, 18*mm, 42*mm, 55*mm, 40*mm], repeatRows=1)
    ft.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (2,1),(2,-1), 'Courier'),
        ('FONTSIZE',      (0,0),(-1,-1), 7.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    story.append(ft)
    story.append(Paragraph('Table 3-1: Statistical Features — Per-Axis Extraction (Bosch CISS Data)', styles['caption']))

    section_heading(story, styles, '4. Fault Category Signatures', 1)
    story.append(Paragraph(
        'The following table describes the characteristic vibration signatures for each '
        'fault category observed in the Bosch CNC Machining dataset (3 machines, 15 '
        'operations, 2019–2021). Fault categories are used to route queries to the '
        'correct diagnostic agent in the EquipmentIQ RAG system.', styles['body']))
    fault_sig = [
        ['Fault Category', 'Dominant Feature', 'Typical Values (Fault)', 'Affected Operations', 'Primary Error Codes'],
        ['tool_wear', 'x_rms, spindle load P002', 'RMS 3–6 mm/s; Kurtosis 3–6', 'OP01,02,07,08,11', 'SPN-MJ-003, SPN-SR-001'],
        ['spindle_bearing_fault', 'x_crest, x_kurtosis, P004', 'Crest >5; Kurtosis >8; RMS 4–11 mm/s', 'OP04,05,10,14', 'SPN-CR-001, VIB-MJ-001'],
        ['chatter_vibration', 'x_rms all axes, P063', 'RMS 5–9 mm/s; periodic peaks at tooth-pass freq', 'OP03,06,09', 'SPN-MJ-004, AXS-SR-001'],
        ['actuator_fault', 'P016 following error, servo current', 'Following error >0.5 mm; current spike', 'OP00,12,14', 'AXS-CR-001, TCS-CR-001'],
        ['process_anomaly', 'P001 deviation, P083 override', 'Speed deviation >50 RPM; override ≠100%', 'Any', 'CNC-MJ-001, SPN-MD-002'],
    ]
    fst = Table(fault_sig, colWidths=[35*mm, 32*mm, 42*mm, 30*mm, 38*mm], repeatRows=1)
    fst.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 7.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    story.append(fst)
    story.append(Paragraph('Table 4-1: Fault Category Vibration Signatures — Bosch CNC Dataset', styles['caption']))

    section_heading(story, styles, '5. Vibration Monitoring Parameters', 1)
    vib_params = [(pid,p) for pid,p in params.items() if p['subsystem']=='VIB']
    param_table(story, styles, vib_params, caption='Table 5-1: VIB Monitored Parameters')

    section_heading(story, styles, '6. Vibration Error Codes — Full Reference', 1)
    vib_codes = get_codes(['VIB-'])
    error_code_table(story, styles, vib_codes, caption='Table 6-1: Vibration Monitoring Error Codes')

    section_heading(story, styles, '7. Condition Monitoring — Dataset Reference', 1)
    story.append(Paragraph(
        'The EquipmentIQ condition monitoring system is grounded in real sensor data from '
        'the Bosch CNC Machining Dataset (CC-BY-4.0). Dataset characteristics used to '
        'train the predictive models and calibrate alarm thresholds:', styles['body']))
    ds_rows = [
        ['Parameter', 'Value'],
        ['Dataset Source', 'Bosch Research — CNC_Machining (GitHub)'],
        ['Citation', 'Tnani et al. Procedia CIRP 2022, 107, 131-136'],
        ['License', 'Creative Commons CC-BY-4.0'],
        ['Total Files', '1,702 HDF5 recordings'],
        ['Machines', '3 (M01, M02, M03)'],
        ['Operations', '15 (OP00–OP14)'],
        ['Date Range', 'February 2019 – August 2021'],
        ['Normal Samples', '1,632 (95.9%)'],
        ['Fault Samples', '70 (4.1%)'],
        ['Fault Categories', '5: tool_wear (34), spindle_bearing_fault (20), actuator_fault (8), chatter_vibration (7), process_anomaly (1)'],
        ['Sampling Rate', '2,000 Hz per axis (X, Y, Z)'],
        ['Sensor', 'Bosch CISS tri-axial MEMS accelerometer (±8g)'],
        ['Features Extracted', '8 per axis: mean, std, RMS, peak, crest factor, kurtosis, min, max'],
    ]
    dst = Table(ds_rows, colWidths=[55*mm, 122*mm])
    dst.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,1),(0,-1), C_STEEL),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    story.append(dst)
    story.append(Paragraph('Table 7-1: Bosch CNC Machining Dataset — Reference Summary', styles['caption']))

    build_doc(f'{OUT}/DOC-EIQ-005_Vibration_Condition_Monitoring.pdf', story, pt)


# ══════════════════════════════════════════════════════════════════════════════
# DOC-006: ELECTRICAL CABINET & CNC CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════
def build_doc006():
    styles = get_styles()
    story  = []
    pt     = DocPageTemplate('DOC-EIQ-006', 'Electrical Cabinet & CNC Controller — Wiring Reference', 'A')

    cover_block(story, styles,
        title='Electrical Cabinet &\nCNC Controller Wiring Reference',
        subtitle='VMC-3000 Series | MID 140 (CNC) | MID 142 (ELC) | MID 146 (THM)',
        doc_number='DOC-EIQ-006', revision='A',
        classification='CONTROLLED — ELECTRICAL HAZARD',
        issued_by='EquipmentIQ Technical Publications')

    warning_box(story, styles,
        'This document contains information on high-voltage circuits (400 V AC, 600 V DC). '
        'Electrical work must only be performed by a qualified electrician. Always perform '
        'Lockout/Tagout and verify absence of voltage before accessing the cabinet. '
        'DC bus capacitors retain hazardous charge for up to 5 minutes after power-off. '
        'Never open the drive DC bus covers without first waiting 5 minutes and verifying '
        'DC bus voltage <50 V with a calibrated meter.', label='DANGER')

    section_heading(story, styles, '1. Electrical Cabinet Layout', 1)
    story.append(Paragraph(
        'The IP54 steel electrical cabinet (600 mm W × 800 mm H × 400 mm D) is mounted '
        'on the rear of the VMC-3000 machine column. The cabinet contains (from top to '
        'bottom): incoming isolator, main contactor, servo drive stack, spindle drive, '
        'DC bus capacitor bank, 24 V DC PSU, UPS module, PLC I/O rack, CNC controller, '
        'terminal strips, and cable entry glands.', styles['body']))

    cab_layout = [
        ['Row', 'Component', 'Part Number', 'Rating', 'Description'],
        ['1 (Top)', 'Main Isolator', 'ELC-ISO-80A', '80 A, 3-pole', 'Lockable rotary isolator, DIN rail'],
        ['1', 'Main Contactor', 'ELC-CTR-63A', '63 A, AC3', 'Electrically held, auxiliary contacts'],
        ['1', 'Surge Arrester', 'ELC-SPD-B+C', 'Type B+C', '3-phase + N + PE, 25 kA'],
        ['2', 'Servo Drive — X', 'AXS-DRV-15', '1.5 kW', 'X-axis servo drive'],
        ['2', 'Servo Drive — Y', 'AXS-DRV-15', '1.5 kW', 'Y-axis servo drive'],
        ['2', 'Servo Drive — Z', 'AXS-DRV-22', '2.2 kW', 'Z-axis servo drive'],
        ['3', 'Spindle Drive', 'SPN-DRV-22KW', '22 kW', 'Regenerative spindle inverter'],
        ['3', 'DC Bus Capacitor', 'ELC-CAP-DCB', '590 V / 4700 uF', 'Shared DC bus buffer'],
        ['4', '24 V DC PSU', 'ELC-PSU-24V-20A', '24 V / 20 A', 'Control voltage supply'],
        ['4', 'UPS Module', 'ELC-UPS-24V', '24 V / 10 Ah', '20 min backup for CNC memory'],
        ['5', 'PLC — CPU', 'PLC-CPU-500', '—', 'EquipmentIQ PLC-500 with CAN master'],
        ['5', 'PLC — I/O (DI)', 'PLC-DI-32', '24 V DC sink', '32× digital inputs'],
        ['5', 'PLC — I/O (DO)', 'PLC-DO-16', '24 V DC 2A', '16× digital outputs'],
        ['6', 'CNC Controller', 'CNC-500', '—', 'EquipmentIQ CNC-500, 10 MB program memory'],
        ['6', 'OPC-UA Gateway', 'EIQ-EDGE-001', '—', 'Edge gateway, 2 kHz sensor data, OPC-UA server'],
        ['7 (Bot)', 'Terminal Blocks', 'ELC-TB-4mm2', '—', 'Phoenix Contact, 4 mm2 DIN rail'],
    ]
    clt = Table(cab_layout, colWidths=[18*mm, 38*mm, 32*mm, 28*mm, 61*mm], repeatRows=1)
    clt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (2,1),(2,-1), 'Courier'),
        ('FONTSIZE',      (0,0),(-1,-1), 7.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    story.append(clt)
    story.append(Paragraph('Table 1-1: Electrical Cabinet Component Layout', styles['caption']))

    section_heading(story, styles, '2. Power Distribution Wiring', 1)
    power_wiring = [
        {'signal':'L1 Supply (Phase R)', 'from_pin':'MAINS:L1', 'to_pin':'ELC-ISO-80A:1', 'gauge':'16 mm2', 'color':'Brown', 'notes':'From site distribution'},
        {'signal':'L2 Supply (Phase S)', 'from_pin':'MAINS:L2', 'to_pin':'ELC-ISO-80A:3', 'gauge':'16 mm2', 'color':'Black', 'notes':''},
        {'signal':'L3 Supply (Phase T)', 'from_pin':'MAINS:L3', 'to_pin':'ELC-ISO-80A:5', 'gauge':'16 mm2', 'color':'Grey', 'notes':''},
        {'signal':'PE (Protective Earth)', 'from_pin':'MAINS:PE', 'to_pin':'CAB-PE-BAR', 'gauge':'16 mm2', 'color':'Green/Yellow', 'notes':'Must be <1 ohm to earth'},
        {'signal':'Contactor coil A1', 'from_pin':'ELC-PSU-24V:+', 'to_pin':'ELC-CTR-63A:A1', 'gauge':'1.5 mm2', 'color':'Red', 'notes':'Via PLC-DO:Y0.0'},
        {'signal':'DC Bus + to drives', 'from_pin':'SPN-DRV-22KW:DC+', 'to_pin':'AXS-DRV-X:DC+', 'gauge':'10 mm2', 'color':'Red (DC)', 'notes':'Shared DC bus link bar'},
        {'signal':'DC Bus - to drives', 'from_pin':'SPN-DRV-22KW:DC-', 'to_pin':'AXS-DRV-X:DC-', 'gauge':'10 mm2', 'color':'Blue (DC)', 'notes':''},
        {'signal':'24 VDC Bus +', 'from_pin':'ELC-PSU-24V:+24V', 'to_pin':'24V-DIST-BAR:+', 'gauge':'2.5 mm2', 'color':'Red', 'notes':'Feeds PLC, sensors, solenoids'},
        {'signal':'24 VDC Bus 0V', 'from_pin':'ELC-PSU-24V:0V', 'to_pin':'0V-DIST-BAR', 'gauge':'2.5 mm2', 'color':'Blue', 'notes':''},
        {'signal':'UPS bypass', 'from_pin':'ELC-UPS-24V:OUT+', 'to_pin':'CNC-500:24V-IN', 'gauge':'1.5 mm2', 'color':'Orange', 'notes':'CNC always on UPS'},
        {'signal':'Ground bond — machine bed', 'from_pin':'CAB-PE-BAR', 'to_pin':'MACH-BED:PE', 'gauge':'16 mm2', 'color':'Green/Yellow', 'notes':'<0.1 ohm'},
        {'signal':'Ground bond — coolant tank', 'from_pin':'CAB-PE-BAR', 'to_pin':'COOL-TANK:PE', 'gauge':'6 mm2', 'color':'Green/Yellow', 'notes':''},
    ]
    wiring_schematic_text(story, styles, 'Table 2-1: Power Distribution Wiring', power_wiring)

    section_heading(story, styles, '3. CNC Controller & PLC I/O Mapping', 1)
    section_heading(story, styles, '3.1 PLC Digital Inputs (DI)', 2)
    di_rows = [
        ['Address', 'Signal Name', 'Source', 'Type', 'Description'],
        ['X0.0', 'E-STOP-OP-PANEL', 'Operator panel E-stop', 'NC, safety relay', 'Main e-stop chain'],
        ['X0.1', 'E-STOP-REAR', 'Rear panel E-stop', 'NC, safety relay', ''],
        ['X0.2', 'GUARD-DOOR-1', 'Main guard door switch', 'NC, key switch', 'Interlocked to spindle enable'],
        ['X0.3', 'GUARD-DOOR-2', 'Chip conveyor door', 'NC', ''],
        ['X0.4', 'SPN-ORIENT-SW', 'Spindle orientation switch', 'NPN NO', 'P006 orientation confirm'],
        ['X0.5', 'ATC-ARM-HOME', 'ATC arm home position', 'NPN NO', ''],
        ['X0.6', 'ATC-TOOL-CLAMP', 'Tool clamp confirmed', 'NPN NO', 'P021 clamp pressure OK'],
        ['X0.7', 'COOLANT-FLOW-SW', 'Coolant flow switch', 'NPN NO', 'P030 flow confirm'],
        ['X1.0', 'HOME-X', 'X-axis home switch', 'NPN NO', ''],
        ['X1.1', 'HOME-Y', 'Y-axis home switch', 'NPN NO', ''],
        ['X1.2', 'HOME-Z', 'Z-axis home switch', 'NPN NO', ''],
        ['X1.3', 'OT-X+', 'X+ over-travel', 'NC hardwired', 'In e-stop chain'],
        ['X1.4', 'OT-X-', 'X- over-travel', 'NC hardwired', ''],
        ['X1.5', 'OT-Y+', 'Y+ over-travel', 'NC hardwired', ''],
        ['X1.6', 'LUB-FLOW-OK', 'Lubrication flow switch', 'NPN NO', 'P040 delivery confirm'],
        ['X1.7', 'HYD-PRESSURE-OK', 'Hydraulic pressure switch', 'NPN NO', 'P050 >60 bar confirm'],
    ]
    dit = Table(di_rows, colWidths=[16*mm, 38*mm, 44*mm, 28*mm, 51*mm], repeatRows=1)
    dit.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1), 'Courier'),
        ('FONTSIZE',      (0,0),(-1,-1), 7.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    story.append(dit)
    story.append(Paragraph('Table 3-1: PLC Digital Input (DI) Mapping', styles['caption']))

    section_heading(story, styles, '3.2 PLC Digital Outputs (DO)', 2)
    do_rows = [
        ['Address', 'Signal Name', 'Load', 'Description'],
        ['Y0.0', 'MAIN-CONTACTOR', 'ELC-CTR-63A coil, 24V 10W', 'Main power on'],
        ['Y0.1', 'COOLANT-PUMP', 'CLS-PUMP relay, 2.2 kW', 'Coolant pump run'],
        ['Y0.2', 'LUB-PUMP', 'LUB-PUMP relay, 0.18 kW', 'Lubrication pump run'],
        ['Y0.3', 'SPN-BRAKE', 'Spindle brake solenoid, 24V 15W', 'Release spindle orientation brake'],
        ['Y0.4', 'HYD-PUMP', 'HYD pump relay, 1.5 kW', 'Hydraulic pump run'],
        ['Y0.5', 'Z-BRAKE', 'Z-axis brake, 24V 30W', 'Release Z-axis gravity brake'],
        ['Y0.6', 'ATC-ARM-FWD', 'ATC solenoid A, 24V 10W', 'ATC arm swing forward'],
        ['Y0.7', 'ATC-ARM-RET', 'ATC solenoid B, 24V 10W', 'ATC arm swing return'],
        ['Y1.0', 'TOOL-UNCLAMP', 'Tool unclamp solenoid, 24V', 'Release draw-bar for tool change'],
        ['Y1.1', 'COOLANT-TSC', 'TSC solenoid valve, 24V', 'Through-spindle coolant valve'],
        ['Y1.2', 'ALARM-LIGHT-R', 'Stack light red, 24V 5W', 'Active alarm indication'],
        ['Y1.3', 'ALARM-LIGHT-Y', 'Stack light yellow, 24V 5W', 'Warning indication'],
        ['Y1.4', 'ALARM-LIGHT-G', 'Stack light green, 24V 5W', 'Machine ready'],
    ]
    dot = Table(do_rows, colWidths=[16*mm, 40*mm, 60*mm, 61*mm], repeatRows=1)
    dot.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',      (0,1),(0,-1), 'Courier'),
        ('FONTSIZE',      (0,0),(-1,-1), 7.5),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    story.append(dot)
    story.append(Paragraph('Table 3-2: PLC Digital Output (DO) Mapping', styles['caption']))

    section_heading(story, styles, '4. Electrical & CNC Parameters', 1)
    elc_params = [(pid,p) for pid,p in params.items() if p['subsystem'] in ('ELC','THM','CNC')]
    param_table(story, styles, elc_params, caption='Table 4-1: ELC/THM/CNC Monitored Parameters')

    section_heading(story, styles, '5. Error Codes — ELC, THM, CNC Subsystems', 1)
    elc_codes = get_codes(['ELC-','THM-','CNC-'])
    error_code_table(story, styles, elc_codes, caption='Table 5-1: Electrical, Thermal & CNC Controller Error Codes')

    section_heading(story, styles, '6. Spare Parts — Electrical Cabinet', 1)
    elc_parts = [
        {'pn':'ELC-ISO-80A','desc':'Main rotary isolator 80A 3-pole lockable','qty':1,'unit':'Each','lead':'1 week','stock':1},
        {'pn':'ELC-CTR-63A','desc':'Main contactor 63A AC3 with 24V coil','qty':1,'unit':'Each','lead':'1 week','stock':1},
        {'pn':'ELC-PSU-24V-20A','desc':'24 VDC power supply 20 A DIN rail','qty':1,'unit':'Each','lead':'1 week','stock':1},
        {'pn':'ELC-UPS-24V','desc':'UPS module 24V 10 Ah (20 min backup)','qty':1,'unit':'Each','lead':'2 weeks','stock':1},
        {'pn':'ELC-CAP-DCB','desc':'DC bus capacitor 590V 4700uF (matched pair)','qty':1,'unit':'Pair','lead':'4 weeks','stock':1},
        {'pn':'PLC-CPU-500','desc':'PLC CPU module EIQ-500 with CANopen master','qty':1,'unit':'Each','lead':'4 weeks','stock':1},
        {'pn':'PLC-DI-32','desc':'PLC digital input module 32ch 24VDC','qty':1,'unit':'Each','lead':'2 weeks','stock':1},
        {'pn':'PLC-DO-16','desc':'PLC digital output module 16ch 24VDC 2A','qty':1,'unit':'Each','lead':'2 weeks','stock':1},
        {'pn':'CNC-500','desc':'CNC controller complete (backup replacement)','qty':1,'unit':'Each','lead':'6 weeks','stock':1},
        {'pn':'EIQ-EDGE-001','desc':'EquipmentIQ OPC-UA edge gateway','qty':1,'unit':'Each','lead':'3 weeks','stock':1},
        {'pn':'ELC-FILTER-CAB','desc':'Cabinet air filter mat 300x300mm (10 pack)','qty':1,'unit':'Pack','lead':'1 week','stock':2},
    ]
    parts_table(story, styles, elc_parts, caption='Table 6-1: Electrical Cabinet Spare Parts List')

    build_doc(f'{OUT}/DOC-EIQ-006_Electrical_CNC_Wiring.pdf', story, pt)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)

    print("Building 6 technical PDFs...")
    build_doc001(); print("  [1/6] DOC-EIQ-001 Machine Overview — DONE")
    build_doc002(); print("  [2/6] DOC-EIQ-002 Spindle Drive System — DONE")
    build_doc003(); print("  [3/6] DOC-EIQ-003 Axis Servo & Motion — DONE")
    build_doc004(); print("  [4/6] DOC-EIQ-004 Coolant & Lubrication — DONE")
    build_doc005(); print("  [5/6] DOC-EIQ-005 Vibration Monitoring — DONE")
    build_doc006(); print("  [6/6] DOC-EIQ-006 Electrical & CNC Wiring — DONE")

    print("\nAll PDFs written to:", OUT)
    import os
    total = sum(os.path.getsize(f'{OUT}/{f}') for f in os.listdir(OUT) if f.endswith('.pdf'))
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.pdf'):
            sz = os.path.getsize(f'{OUT}/{f}') // 1024
            print(f"  {f}  ({sz} KB)")
    print(f"\nTotal: {total//1024} KB across 6 documents")
