"""
generate_complaints.py
Synthesizes 150 customer complaint records for EquipmentIQ VMC-3000 machines.
- 70 records anchored to real Bosch fault event IDs (one-to-one)
- 80 additional synthetic complaints (escalations, repeat failures, RMA cases)
Each record contains: case metadata, phone call notes, investigation notes,
remedy notes, RMA data, failure mode classification, and resolution status.
"""

import pandas as pd, json, random, csv, datetime, uuid
from copy import deepcopy

random.seed(2024)

# ── Load real fault events ─────────────────────────────────────────────────────
fault_df = pd.read_csv('/home/claude/equipmentiq/processed/fault_events.csv')
with open('/home/claude/equipmentiq/processed/error_code_master.json') as f:
    ecm = json.load(f)

# ── Reference data ─────────────────────────────────────────────────────────────
CUSTOMERS = [
    {'id':'CUST-001','name':'Precision Parts Midwest LLC',     'contact':'Dave Kowalski',    'phone':'(312) 555-0142','email':'dkowalski@precisionmidwest.com',  'site':'Chicago, IL',    'contract':'GOLD'},
    {'id':'CUST-002','name':'AeroMach Industries',             'contact':'Sandra Okonkwo',   'phone':'(714) 555-0287','email':'sokonkwo@aeromach.com',           'site':'Anaheim, CA',    'contract':'PLATINUM'},
    {'id':'CUST-003','name':'Lone Star Machining Co.',         'contact':'Billy Ray Tanner',  'phone':'(214) 555-0391','email':'brtanner@lonestarmach.com',       'site':'Dallas, TX',     'contract':'SILVER'},
    {'id':'CUST-004','name':'Great Lakes Tool & Die',          'contact':'Marie Johansson',   'phone':'(313) 555-0448','email':'mjohansson@gltd.com',             'site':'Detroit, MI',    'contract':'GOLD'},
    {'id':'CUST-005','name':'Pacific Rim Precision',           'contact':'Kevin Tanaka',      'phone':'(206) 555-0512','email':'ktanaka@pacrimprec.com',          'site':'Seattle, WA',    'contract':'PLATINUM'},
    {'id':'CUST-006','name':'Appalachian Machine Works',       'contact':'Bobby Hicks',       'phone':'(423) 555-0667','email':'bhicks@appmach.com',              'site':'Knoxville, TN',  'contract':'STANDARD'},
    {'id':'CUST-007','name':'Rio Grande Manufacturing',        'contact':'Carlos Mendez',     'phone':'(505) 555-0723','email':'cmendez@riograndemfg.com',        'site':'Albuquerque, NM','contract':'SILVER'},
    {'id':'CUST-008','name':'Atlantic Precision Group',        'contact':'Jennifer Walsh',    'phone':'(617) 555-0834','email':'jwalsh@atlanticprecision.com',    'site':'Boston, MA',     'contract':'GOLD'},
    {'id':'CUST-009','name':'Heartland CNC Services',          'contact':'Tom Hartley',       'phone':'(515) 555-0912','email':'thartley@heartlandcnc.com',       'site':'Des Moines, IA', 'contract':'STANDARD'},
    {'id':'CUST-010','name':'Mountain West Machining LLC',     'contact':'Janet Fujimoto',    'phone':'(303) 555-1034','email':'jfujimoto@mwmach.com',            'site':'Denver, CO',     'contract':'SILVER'},
]

TECHNICIANS = [
    'Rodriguez, M.', 'Chen, L.', 'Okafor, D.',
    'Petrov, A.', 'Williams, S.', 'Kumar, R.', 'Novak, P.',
]

FIELD_ENGINEERS = [
    'Jackson, T. (FE-07)', 'Lee, S. (FE-12)', 'Mbeki, J. (FE-03)',
    'Torres, R. (FE-09)', 'Brennan, K. (FE-15)',
]

STATUS_OPTIONS = ['CLOSED','CLOSED','CLOSED','IN_PROGRESS','PENDING_PARTS','ESCALATED']

OPERATION_LABELS = {
    'OP00':'Workpiece Loading','OP01':'Face Milling','OP02':'Contour Milling',
    'OP03':'Pocket Milling','OP04':'Drilling Cycle','OP05':'Thread Tapping',
    'OP06':'Boring Operation','OP07':'Profile Milling','OP08':'Slot Milling',
    'OP09':'Chamfering','OP10':'Reaming','OP11':'Surface Finishing',
    'OP12':'Tool Change','OP13':'Workpiece Inspection','OP14':'Spindle Run Test',
}

# ── Text templates keyed by fault_category ─────────────────────────────────────

CALL_NOTES = {
'tool_wear': [
    "Customer called reporting elevated spindle load alarms on {machine} during {op} operation. "
    "Operator noticed surface finish degradation on last 8–12 parts before alarm triggered. "
    "Machine displaying {error_code} with spindle load P002 reading {p_val}%. Customer states "
    "tool was at approximately {pct}% of programmed tool life. Production halted on affected "
    "spindle. Customer requesting priority callback from field support. Machine M/N VMC-3000, "
    "S/N {serial}. Current shift supervisor: {contact}.",

    "Inbound call from {contact} at {customer}. Reports intermittent spindle load spikes on "
    "{machine} over the past 3 shifts. Error {error_code} appearing 4–6 times per shift, "
    "machine not stopping but operator applying feed override down to 70%. Surface finish "
    "on aluminium parts showing chatter marks. Customer believes tool is worn but wants "
    "confirmation before scrapping tooling. Last PM was {pm_ago} weeks ago.",

    "Customer {customer} called — {machine} threw hard alarm {error_code} mid-program "
    "during {op}. Spindle load P002 peaked at {p_val}% before drive tripped. Tool T{tool_num} "
    "found broken in spindle bore — approx 40mm of flute snapped. Last good part passed "
    "inspection; current part scrapped. Customer asking about warranty on tooling and whether "
    "machine caused the breakage or vice versa.",
],
'spindle_bearing_fault': [
    "Emergency call from {contact} at {customer}. {machine} stopped mid-production with "
    "CRITICAL alarm {error_code}. Unusual noise from spindle described as 'grinding then "
    "a bang'. Machine auto-stopped. Vibration sensor reading P004 = {p_val} mm/s at time "
    "of fault. Machine has been running 24/7 for past 6 weeks without scheduled PM. "
    "Customer needs machine back online within 48 hours — aerospace delivery deadline. "
    "Serial: {serial}.",

    "Call received from {contact}. {machine} has been showing progressive vibration increase "
    "on spindle bearing sensor P004 over the past 2 weeks — operator noticed noise change "
    "but kept running. Now at {p_val} mm/s RMS, alarm {error_code} active. Customer asks "
    "if bearing can be replaced on-site or if spindle needs to go to depot. Machine hours: "
    "approx {hours}h on current bearing set. Last grease service: {pm_ago} months ago.",

    "{customer} reporting {machine} spindle temperature P003 running high at {p_val}°C. "
    "Spindle cooling fan appears to be making intermittent noise — possibly bearing in "
    "fan motor. Alarm {error_code} active. Customer asking if they can continue running "
    "at reduced spindle speed while awaiting parts. Current part schedule is critical path.",
],
'chatter_vibration': [
    "Customer {customer} calling about part quality issue on {machine}. Surface finish "
    "failing inspection — visible chatter marks at {p_val} micron Ra vs. 0.8 Ra specified. "
    "Alarm {error_code} logged. Customer has already tried reducing feed rate by 20% but "
    "chatter persists. Process was stable for 3 months then started last week. No recent "
    "tooling changes. Machine {machine} S/N {serial}. {contact} is the shift supervisor.",

    "Inbound from {contact} at {customer}. {machine} exhibiting strong vibration during "
    "{op} — alarm {error_code}. Vibration visible on parts and audible in shop. Machine "
    "did not auto-stop but part is clearly scrap. Customer suspects fixture loosening. "
    "Asked us to confirm if vibration profile matches bearing issue or chatter. "
    "X-axis RMS reading {p_val} mm/s at time of alarm.",

    "Service call — {machine} at {customer} producing unacceptable surface finish on "
    "titanium parts. Alarm {error_code} logged intermittently during {op}. Customer "
    "reports problem started after recent toolholder swap. Vibration spike visible on "
    "CISS sensor readout. Crest factor P063 elevated at {p_val}. Customer requesting "
    "field engineer visit to perform stability lobe analysis.",
],
'actuator_fault': [
    "URGENT — {customer} reporting {machine} stuck in tool change. ATC arm stopped "
    "mid-swing, alarm {error_code} active. Machine cannot be reset — arm is blocking "
    "spindle access. Production line stopped. Customer has 14 people waiting. "
    "Contact: {contact}, phone: {phone}. Machine S/N {serial}. Requesting immediate "
    "escalation to field support.",

    "Customer {customer} called — {machine} throwing axis following error alarm "
    "{error_code}. P016 following error at {p_val} mm. Machine stops on every rapid "
    "move. Customer has confirmed no mechanical obstruction. Problem started after "
    "machine power outage 2 days ago. Axis re-homed but problem persists. "
    "Requesting remote diagnostic session.",

    "Call from {contact} at {customer}. {machine} hydraulic system alarm {error_code}. "
    "Clamping fixture not releasing correctly — workpiece stuck in fixture. Hydraulic "
    "pressure P050 reading {p_val} bar. Customer manually bled hydraulic circuit but "
    "pressure not recovering. Machine S/N {serial}.",
],
'process_anomaly': [
    "Customer {customer} reporting {machine} NC program execution error, alarm "
    "{error_code}. Machine stopped at block N{block_num} — program has run successfully "
    "100+ times before. No changes to program, operator, or tooling. Customer suspects "
    "CNC memory or controller issue. {contact} requesting level-2 technical support.",
],
}

INVESTIGATION_NOTES = {
'tool_wear': [
    "Remote diagnostic session conducted with {tech}. Reviewed P002 spindle load trend "
    "via OPC-UA historian — clear monotonic increase over prior 50 cycles consistent with "
    "progressive flank wear. NDCG feature trend confirms tool_wear classification. "
    "Kurtosis P064 = {kurtosis:.1f} (normal range 2.5–5.0). Recommended immediate tool "
    "replacement. Advised customer to calibrate tool life counter to actual tool life "
    "rather than theoretical. No machine fault — tooling and process issue. "
    "Error code {error_code} confirmed appropriate.",

    "Field engineer {fe} attended site {days_later} business days after initial call. "
    "Inspection findings: tool T{tool_num} showed severe flank wear on 2 of 4 flutes, "
    "corner radius worn to near-zero. Chip formation analysis: short, powdery chips "
    "consistent with rubbing rather than cutting. Coolant concentration measured at "
    "{cool_conc}% (low — should be 8–10%); low concentration accelerating wear. "
    "Ball screw and guides inspected — nominal. No machine defect identified.",

    "Technical investigation by {tech}. Downloaded vibration data from Bosch CISS sensor "
    "for run_id {run_id}. X-axis RMS = {x_rms:.0f} (units: ADC counts), crest factor "
    "{x_crest:.2f}. Pattern consistent with increased cutting forces from worn tool. "
    "Compared against {machine} baseline from Aug 2019 — load elevated by {load_delta}%. "
    "No bearing defect frequency components detected in spectrum. Root cause confirmed: "
    "tool wear beyond service life. No warranty claim applicable.",
],
'spindle_bearing_fault': [
    "Remote diagnostic: retrieved vibration data for run_id {run_id}. Spindle bearing "
    "vibration P004 = {p_val:.2f} mm/s (ISO Zone {iso_zone}). Kurtosis P064 = "
    "{kurtosis:.1f} — defect frequency component confirmed at BPFO = {bpfo:.1f} Hz "
    "(consistent with outer race spall on 7014 bearing). Machine hours since last "
    "grease service: {hours}h (OEM limit: 4,000h). Bearing replacement recommended. "
    "Error code {error_code} confirmed CRITICAL/MAJOR — correct action taken by PLC.",

    "Field engineer {fe} attended {days_later} days after initial call. Removed spindle "
    "nose cap and measured bearing temperature with IR thermometer: front bearing at "
    "{p_val:.0f}°C vs. ambient 22°C — significant. Bearing noise clearly audible on "
    "mechanic's stethoscope. Vibration spectrum showed bearing defect frequencies. "
    "Bearings removed: front pair (7014 CDBP4) showed outer race spalling on one "
    "bearing — approx 8mm arc of pitting. Rear bearing NU1014 in good condition. "
    "Root cause: bearing fatigue from operation beyond grease service interval.",

    "Investigation by {tech}. Pulled Bosch CISS historical data for {machine} OP{op_num}. "
    "Crest factor trend showed gradual increase from 3.2 to {x_crest:.1f} over 90 days "
    "before alarm. Kurtosis crossed early-warning threshold (8.0) approximately "
    "{days_before} days before customer called — alarm SPN-SR-003 was generated but "
    "apparently not actioned by customer maintenance team. Investigation highlights need "
    "for customer to review alarm log regularly. Machine performed as designed.",
],
'chatter_vibration': [
    "Technical investigation by {tech}. Reviewed vibration data — dominant frequency at "
    "{freq:.0f} Hz matches spindle speed {rpm} RPM × {teeth} teeth (tooth-passing "
    "frequency). Stability lobe diagram analysis indicates current operating point is in "
    "unstable region. Recommended spindle speed adjustment to {new_rpm} RPM (+{delta_rpm} "
    "RPM shift) to move to adjacent stable lobe. Customer tested recommendation — chatter "
    "eliminated. Root cause: process parameter selection, not machine defect. "
    "Error code {error_code} appropriate for the vibration level detected.",

    "Field engineer {fe} attended site. Found toolholder taper dirty — significant "
    "fretting corrosion on HSK taper mating surface reducing contact stiffness. "
    "Fixture clamping hydraulic pressure measured at {p_val:.0f} bar (nominal 70 bar) — "
    "leak in fixture circuit reducing clamping force. Two independent causes both "
    "contributing to chatter. Taper cleaned and re-ground; hydraulic circuit repaired. "
    "Machine re-tested: chatter eliminated at standard parameters. Machine in good condition.",

    "Remote session {tech}. Vibration RMS X={x_rms:.0f} Y={y_rms:.0f} Z={z_rms:.0f} "
    "(ADC counts) for run_id {run_id}. Crest factor {x_crest:.2f} consistent with "
    "regenerative chatter rather than bearing defect (kurtosis {kurtosis:.1f}, normal "
    "range for chatter). Process engineer recommends: reduce axial depth of cut by 20%, "
    "apply variable pitch tooling. No mechanical fault on machine identified.",
],
'actuator_fault': [
    "Emergency remote diagnostic by {tech}. ATC arm position log shows arm stopped at "
    "23° of 90° swing — proximity sensor SW-ATC-MID not triggering. Customer technician "
    "guided to manually rotate ATC arm to home using maintenance jog mode. Sensor "
    "adjusted — fretting of mounting bracket caused sensor to drift out of range. "
    "ATC tested 20 cycles without recurrence. No parts required. Error {error_code} "
    "correctly triggered machine stop to prevent collision.",

    "Field engineer {fe} attended. Axis following error P016 = {p_val:.3f} mm on "
    "{axis}-axis. Ball screw backlash measured: {backlash:.3f} mm (limit 0.005 mm — "
    "exceeded). Guide rail lubrication found dry on two carriages — lube distributor "
    "piston stuck in one SSV block. Root causes: (1) lube blockage causing guide "
    "friction increase; (2) ball screw nut preload loss. Both corrected: SSV block "
    "replaced, lube cycle verified, servo backlash compensation adjusted.",

    "Investigation {tech}. Hydraulic pressure trend for {machine} shows gradual decay "
    "from 72 bar to {p_val:.0f} bar over 3 weeks — internal leak in pressure relief "
    "valve (RV1) allowing bypass. Relief valve inspected: seat worn, allowing "
    "{leak_rate:.1f} L/min internal bypass at nominal pressure. Relief valve replaced "
    "— pressure restored to 71 bar. Clamping function tested: all 4 fixture stations "
    "confirmed >55 bar clamp pressure. Error code {error_code} triggered correctly.",
],
'process_anomaly': [
    "Remote diagnostic by {tech}. CNC program file MD5 checksum mismatch vs. revision "
    "control system — corrupted file transfer via DNC. Program re-transferred and "
    "verified. Machine executed 10 consecutive cycles without alarm. Root cause: "
    "network timeout during DNC transfer corrupted block N{block_num}. Customer advised "
    "to implement file transfer verification (checksum) before running production. "
    "No machine defect.",
],
}

REMEDY_NOTES = {
'tool_wear': [
    "Tool T{tool_num} replaced with new insert grade IC900 (customer's standard). "
    "Tool life counter reset to 0. Coolant concentration checked and adjusted to 9% "
    "(from {cool_conc}%). First-off part inspected: dimensions within tolerance, "
    "surface finish Ra 0.8 μm achieved. Production resumed. Customer advised to "
    "increase tool change frequency by 20% for this material/operation combination "
    "and to check coolant concentration weekly. No chargeable service.",

    "No machine repair required. Customer coaching on tool life management completed "
    "by {fe}. Provided updated tooling recommendation for {op} on aluminium: "
    "increase feed rate by 10%, reduce depth of cut by 15%, change tool grade to "
    "uncoated carbide. New parameters tested and validated. Surface finish improved "
    "to Ra 0.6 μm. Case closed — no charge under GOLD service contract.",

    "Recommended process change: implement tool condition monitoring via spindle load "
    "P002 trending. Set adaptive alarm at +25% above baseline load for each operation. "
    "Customer's process engineer will configure alarm thresholds in next maintenance "
    "window. No machine parts replaced. Case closed.",
],
'spindle_bearing_fault': [
    "Spindle bearing set replaced on-site by {fe}. Parts used: "
    "2× 7014 CDBP4 angular contact bearings (PN: EIQ-SPN-BRG-7014, "
    "batch {batch_num}), 1× NU1014 rear bearing (PN: EIQ-SPN-BRG-NU1014). "
    "Bearings installed with correct preload per EIQ-PROC-SPN-001. "
    "Spindle warmed up per SPD-WARMUP-001 (15 min). "
    "Acceptance vibration test run: P004 = {post_vib:.2f} mm/s (Zone A — pass). "
    "Machine returned to production. Labour: {labour_h:.1f} h. Parts charged to "
    "customer (bearing set outside warranty — {machine_age} months in service).",

    "Spindle sent to depot for full rebuild (grease repack + runout check). "
    "Loaner spindle installed — job EIQ-LOAN-{loan_num}. Rebuilt spindle returned "
    "and installed {rebuild_days} business days later. Post-installation vibration: "
    "P004 = {post_vib:.2f} mm/s. All axes re-qualified. Customer down-time: "
    "{downtime_h} hours. RMA raised for spindle core: RMA-{rma_num}.",

    "Spindle cooling fan motor replaced (PN: EIQ-SPN-FAN-200L). Air filter "
    "cleaned — found 60% blocked. Post-repair spindle temperature P003 running "
    "at {post_temp:.0f}°C vs. {fault_temp:.0f}°C pre-repair. Machine re-qualified. "
    "Advised customer to add fan inspection to monthly PM checklist. "
    "No charge under PLATINUM service contract.",
],
'chatter_vibration': [
    "Spindle speed adjusted from {old_rpm} to {new_rpm} RPM. Feed rate increased "
    "by 8% to maintain chip load. First-off part inspected: Ra {post_ra:.1f} μm "
    "(spec 0.8 μm — pass). Stability lobe diagram provided to customer process "
    "engineer for future reference. No machine parts replaced. Case closed.",

    "Toolholder taper cleaned and re-lapped. Hydraulic fixture circuit repaired: "
    "replaced solenoid valve seal kit (PN: EIQ-HYD-SEAL-KIT). Pressure restored "
    "to 71 bar. Re-test: 20 consecutive parts — all within surface finish spec. "
    "Recommended annual toolholder taper inspection. Labour: {labour_h:.1f} h under "
    "SILVER service contract (customer co-pay {copay}%).",

    "Variable pitch tooling (4-flute, pitch 30/32/34/36°) recommended and sourced "
    "by customer. New toolholder balanced to G2.5 at 12,000 RPM. Re-test with new "
    "tooling: chatter eliminated, Ra improved to {post_ra:.1f} μm. Machine in good "
    "condition. Closed — no charge.",
],
'actuator_fault': [
    "ATC arm proximity sensor SW-ATC-MID re-adjusted and bracket re-secured. "
    "20 ATC cycle test conducted without fault. Customer maintenance team advised "
    "to include sensor mounting check in quarterly PM. No parts replaced. "
    "Labour: 0.5 h (covered under GOLD contract).",

    "SSV lube distributor block replaced (PN: EIQ-LUB-SSV-6). Ball screw "
    "backlash compensation parameter adjusted from 0.003 to 0.006 mm. "
    "Lubrication system primed and verified — all 18 lube points confirmed "
    "receiving oil. Following error P016 re-tested: max 0.008 mm on rapid "
    "traverse — within specification. Machine re-qualified. Parts cost: ${parts_cost}. "
    "Labour: {labour_h:.1f} h.",

    "Hydraulic pressure relief valve RV1 replaced (PN: EIQ-HYD-RV1-70BAR). "
    "System pressure restored to 71 bar. All fixture clamp circuits tested — "
    "confirmed >60 bar. ATC clamp test: P021 = {post_clamp:.0f} bar — pass. "
    "Machine returned to production. Labour: {labour_h:.1f} h. Parts under warranty "
    "(relief valve failed within 12 months of installation).",
],
'process_anomaly': [
    "DNC file transfer protocol updated to include MD5 checksum verification on "
    "receive. IT team configured auto-reject for failed checksums. NC program "
    "re-loaded from revision control — machine ran 50 cycles without fault. "
    "No machine repair required. Case closed — process improvement only.",
],
}

# RMA templates — only for cases requiring part return
RMA_TEMPLATES = [
    {'type':'BEARING_RETURN',
     'desc':'Defective spindle bearing set returned for failure analysis',
     'disposition':'Failure analysis at EquipmentIQ bearing lab. Confirmed outer race spall — fatigue failure consistent with service beyond recommended interval. No manufacturing defect.',
     'credit':False},
    {'type':'DRIVE_WARRANTY',
     'desc':'Servo drive returned under warranty claim — internal IGBT failure',
     'disposition':'Drive tested at factory — confirmed IGBT module failure. Within 24-month warranty period. Full replacement issued at no charge.',
     'credit':True},
    {'type':'SPINDLE_REBUILD',
     'desc':'Spindle cartridge sent to depot for bearing replacement and runout check',
     'disposition':'Rebuilt spindle returned. New bearing set installed, preload set to spec, runout verified <0.003mm. Returned to customer.',
     'credit':False},
    {'type':'SENSOR_WARRANTY',
     'desc':'Bosch CISS accelerometer suspected fault — reading zero on Z-axis',
     'disposition':'Sensor tested at calibration lab. Confirmed Z-axis MEMS element failure. Replaced under manufacturer warranty. New unit calibrated.',
     'credit':True},
    {'type':'VALVE_WARRANTY',
     'desc':'Hydraulic relief valve returned — premature internal seat wear',
     'disposition':'Valve inspected — seat wear confirmed at 11 months in service. Within 12-month warranty. Replacement valve issued.',
     'credit':True},
    {'type':'LUBE_BLOCK',
     'desc':'SSV lube distributor block returned — stuck piston',
     'disposition':'Piston freed and cleaned. Contamination found in oil supply — customer advised to use filtered oil only. No manufacturing defect. No credit.',
     'credit':False},
]

# ── Generator functions ────────────────────────────────────────────────────────

def pick(lst): return random.choice(lst)

def days_later(base_ts, min_d=1, max_d=5):
    base = datetime.datetime.fromisoformat(base_ts)
    delta = datetime.timedelta(days=random.randint(min_d, max_d),
                               hours=random.randint(0, 8))
    return (base + delta).strftime('%Y-%m-%dT%H:%M:00')

def fmt_date(ts):
    return datetime.datetime.fromisoformat(ts).strftime('%d %b %Y %H:%M')

def error_codes_for(cat):
    mapping = {
        'tool_wear':             ['SPN-MJ-003','SPN-SR-001','SPN-WN-001','SPN-MN-001','VIB-MD-001'],
        'spindle_bearing_fault': ['SPN-CR-001','SPN-MJ-001','SPN-MJ-002','SPN-SR-003','VIB-MJ-001'],
        'chatter_vibration':     ['SPN-MJ-004','VIB-SR-001','AXS-SR-001','VIB-MD-001'],
        'actuator_fault':        ['AXS-CR-001','AXS-MJ-001','TCS-CR-001','TCS-MJ-001','LUB-CR-001','HYD-MJ-001'],
        'process_anomaly':       ['CNC-MJ-001','CNC-SR-001','CLS-CR-001'],
    }
    codes = mapping.get(cat, ['SPN-MJ-002'])
    return pick(codes)


def make_complaint(fault_row, cmp_id, customer, extra_synthetic=False):
    """Build one complete complaint record."""
    cat   = fault_row['fault_category']
    mach  = fault_row['machine']
    op    = fault_row['operation']
    ts    = fault_row['timestamp']
    run_id= fault_row['run_id']
    sev   = fault_row['vibration_severity_score']
    xrms  = fault_row['x_rms']
    yrms  = fault_row['y_rms']
    zrms  = fault_row['z_rms']
    xcrest= fault_row['x_crest']
    ykurt = fault_row['y_kurtosis']

    error_code = error_codes_for(cat)
    tech       = pick(TECHNICIANS)
    fe         = pick(FIELD_ENGINEERS)
    days_to_fe = random.randint(1, 5)
    serial     = f"EIQ-{mach}-{fault_row['year']}-{random.randint(1000,9999):04d}"
    machine_age= random.randint(6, 42)   # months since install
    tool_num   = random.randint(1, 30)
    pct        = random.randint(75, 110)
    pm_ago     = random.randint(1, 16)
    hours      = random.randint(800, 4200)
    cool_conc  = round(random.uniform(4.5, 7.2), 1)
    load_delta = random.randint(15, 45)
    iso_zone   = pick(['B','C','C','D']) if cat=='spindle_bearing_fault' else 'B'
    bpfo       = round(random.uniform(80, 240), 1)
    kurtosis   = round(ykurt, 1)
    freq       = round(random.uniform(80, 400), 0)
    rpm        = random.choice([2000, 3000, 4000, 5000, 6000])
    teeth      = random.choice([2, 3, 4, 5])
    new_rpm    = rpm + random.choice([-300,-200,200,300,500])
    delta_rpm  = abs(new_rpm - rpm)
    axis       = pick(['X','Y','Z'])
    backlash   = round(random.uniform(0.006, 0.025), 3)
    leak_rate  = round(random.uniform(1.5, 4.0), 1)
    block_num  = random.randint(100, 9999)
    op_num     = op.replace('OP','')
    days_before= random.randint(5, 30)
    post_vib   = round(random.uniform(0.8, 2.3), 2)
    post_temp  = round(random.uniform(42, 62), 0)
    fault_temp = round(post_temp + random.uniform(15, 30), 0)
    old_rpm    = rpm
    post_ra    = round(random.uniform(0.4, 0.8), 1)
    labour_h   = round(random.uniform(1.5, 6.5), 1)
    copay      = random.choice([20, 30])
    parts_cost = random.randint(180, 850)
    post_clamp = round(random.uniform(62, 74), 0)
    batch_num  = f"BRG-{random.randint(10000,99999)}"
    loan_num   = f"{random.randint(100,999):03d}"
    rebuild_days= random.randint(5, 12)
    downtime_h = random.randint(18, 96)
    rma_num    = f"{random.randint(10000,99999)}"
    p_val      = round(xrms / 100, 2) if cat in ('tool_wear',) else round(xcrest, 2)
    phone      = customer['phone']

    # Determine if RMA required
    needs_rma  = cat == 'spindle_bearing_fault' or (cat == 'actuator_fault' and random.random() < 0.4)
    rma_rec    = pick(RMA_TEMPLATES) if needs_rma else None

    # Status
    status = pick(STATUS_OPTIONS)
    if extra_synthetic and random.random() < 0.3:
        status = pick(['ESCALATED','IN_PROGRESS','PENDING_PARTS'])

    # Resolution time (hours)
    if status == 'CLOSED':
        resolution_h = random.randint(4, 120)
    elif status == 'IN_PROGRESS':
        resolution_h = None
    else:
        resolution_h = None

    call_ts  = ts
    inv_ts   = days_later(ts, 0, 1)
    rem_ts   = days_later(inv_ts, 1, 4)
    close_ts = days_later(rem_ts, 0, 2) if status=='CLOSED' else None

    # Fill call note template
    call_tmpl = pick(CALL_NOTES.get(cat, CALL_NOTES['process_anomaly']))
    call_note  = call_tmpl.format(
        machine=mach, op=OPERATION_LABELS.get(op, op),
        error_code=error_code, p_val=round(p_val,2),
        pct=pct, serial=serial, contact=customer['contact'],
        customer=customer['name'], pm_ago=pm_ago, tool_num=tool_num,
        hours=hours, phone=phone, block_num=block_num,
    )

    # Fill investigation template
    inv_tmpl  = pick(INVESTIGATION_NOTES.get(cat, INVESTIGATION_NOTES['process_anomaly']))
    inv_note  = inv_tmpl.format(
        tech=tech, run_id=run_id, machine=mach, op_num=op_num,
        error_code=error_code, p_val=p_val, kurtosis=kurtosis,
        iso_zone=iso_zone, bpfo=bpfo, hours=hours, pm_ago=pm_ago,
        x_rms=xrms, y_rms=yrms, z_rms=zrms, x_crest=xcrest,
        fe=fe, days_later=days_to_fe, days_before=days_before,
        load_delta=load_delta, freq=freq, rpm=rpm, teeth=teeth,
        new_rpm=new_rpm, delta_rpm=delta_rpm, axis=axis,
        backlash=backlash, leak_rate=leak_rate, block_num=block_num,
        cool_conc=cool_conc, tool_num=tool_num,
    )

    # Fill remedy template
    rem_tmpl  = pick(REMEDY_NOTES.get(cat, REMEDY_NOTES['process_anomaly']))
    rem_note  = rem_tmpl.format(
        fe=fe, tech=tech, op=OPERATION_LABELS.get(op,op),
        error_code=error_code, tool_num=tool_num, cool_conc=cool_conc,
        old_rpm=old_rpm, new_rpm=new_rpm, post_ra=post_ra,
        labour_h=labour_h, copay=copay, parts_cost=parts_cost,
        post_clamp=post_clamp, post_vib=post_vib, post_temp=post_temp,
        fault_temp=fault_temp, machine_age=machine_age,
        batch_num=batch_num, loan_num=loan_num,
        rebuild_days=rebuild_days, downtime_h=downtime_h, rma_num=rma_num,
    )

    rec = {
        # ── Case metadata ────────────────────────────────────────
        'complaint_case_id'   : cmp_id,
        'case_status'         : status,
        'priority'            : 'P1-CRITICAL' if 'CR' in error_code else
                                'P2-HIGH' if 'MJ' in error_code else
                                'P3-MEDIUM' if 'SR' in error_code else 'P4-LOW',
        'case_opened_ts'      : fmt_date(call_ts),
        'case_closed_ts'      : fmt_date(close_ts) if close_ts else '',
        'resolution_hours'    : resolution_h if resolution_h else '',
        # ── Customer info ────────────────────────────────────────
        'customer_id'         : customer['id'],
        'customer_name'       : customer['name'],
        'customer_contact'    : customer['contact'],
        'customer_phone'      : customer['phone'],
        'customer_email'      : customer['email'],
        'customer_site'       : customer['site'],
        'service_contract'    : customer['contract'],
        # ── Machine info ─────────────────────────────────────────
        'machine_id'          : mach,
        'machine_serial'      : serial,
        'machine_model'       : 'VMC-3000',
        'operation_code'      : op,
        'operation_name'      : OPERATION_LABELS.get(op, op),
        'run_id'              : run_id if not extra_synthetic else '',
        # ── Fault classification ──────────────────────────────────
        'fault_category'      : cat,
        'error_code_triggered': error_code,
        'vibration_severity_score': round(sev, 3),
        'failure_mode'        : cat.replace('_',' ').title(),
        'failure_mode_detail' : {
            'tool_wear'            : 'Progressive cutting edge wear beyond service life',
            'spindle_bearing_fault': 'Bearing race or rolling element fatigue defect',
            'chatter_vibration'    : 'Regenerative chatter — process outside stability lobe',
            'actuator_fault'       : 'Mechanical or electrical actuator failure',
            'process_anomaly'      : 'NC program or controller process exception',
        }.get(cat,'Unknown'),
        # ── Sensor data at time of fault ──────────────────────────
        'sensor_x_rms'        : round(xrms, 2),
        'sensor_y_rms'        : round(yrms, 2),
        'sensor_z_rms'        : round(zrms, 2),
        'sensor_x_crest'      : round(xcrest, 3),
        'sensor_kurtosis'     : round(ykurt, 3),
        # ── Call / investigation / remedy ─────────────────────────
        'phone_call_notes'    : call_note,
        'assigned_technician' : tech,
        'assigned_fe'         : fe if cat in ('spindle_bearing_fault','actuator_fault') or random.random()>0.6 else '',
        'investigation_notes' : inv_note,
        'remedy_notes'        : rem_note,
        # ── RMA ──────────────────────────────────────────────────
        'rma_required'        : 'YES' if rma_rec else 'NO',
        'rma_number'          : f"RMA-{rma_num}" if rma_rec else '',
        'rma_type'            : rma_rec['type'] if rma_rec else '',
        'rma_description'     : rma_rec['desc'] if rma_rec else '',
        'rma_disposition'     : rma_rec['disposition'] if rma_rec else '',
        'rma_credit_issued'   : ('YES' if rma_rec['credit'] else 'NO') if rma_rec else '',
        # ── Financial ────────────────────────────────────────────
        'parts_cost_usd'      : parts_cost if cat in ('spindle_bearing_fault','actuator_fault') else 0,
        'labour_hours'        : labour_h,
        'billable'            : 'NO' if customer['contract'] in ('PLATINUM','GOLD') else 'YES',
        # ── Linked docs ──────────────────────────────────────────
        'linked_error_codes'  : error_code,
        'linked_run_id'       : run_id if not extra_synthetic else '',
        'source'              : 'bosch_real_fault' if not extra_synthetic else 'synthetic_extension',
    }
    return rec

# ── Build 70 anchored + 80 synthetic extension records ────────────────────────

complaints = []

# Assign customers round-robin across fault events
for i, row in fault_df.iterrows():
    cust = CUSTOMERS[i % len(CUSTOMERS)]
    rec  = make_complaint(row, row['complaint_case_id'], cust, extra_synthetic=False)
    complaints.append(rec)

print(f"Built {len(complaints)} anchored complaints from Bosch fault events")

# 80 synthetic extension records
# These simulate: repeat failures, escalations, cross-machine issues,
# and complaints not tied to a specific logged run
synthetic_cats = (
    ['tool_wear']*28 + ['spindle_bearing_fault']*22 +
    ['chatter_vibration']*12 + ['actuator_fault']*14 + ['process_anomaly']*4
)
random.shuffle(synthetic_cats)

# Build fake fault rows for synthetic records
for j, cat in enumerate(synthetic_cats):
    cmp_id = f"CMP-SYN-{2000+j:04d}"
    mach   = pick(['M01','M02','M03'])
    op_map = {
        'tool_wear':['OP01','OP02','OP07','OP08','OP11'],
        'spindle_bearing_fault':['OP04','OP05','OP10','OP14'],
        'chatter_vibration':['OP03','OP06','OP09'],
        'actuator_fault':['OP00','OP12','OP14'],
        'process_anomaly':['OP01','OP03','OP07'],
    }
    op     = pick(op_map.get(cat,['OP01']))
    yr     = random.choice([2019,2019,2020,2020,2021])
    mo     = pick(['Feb','Aug'])
    day    = random.randint(1,28)
    hr     = random.randint(6,22)
    ts     = f"{yr}-{2 if mo=='Feb' else 8:02d}-{day:02d}T{hr:02d}:00:00"
    sev    = round(random.uniform(2.5, 8.0), 3)
    xrms   = round(random.uniform(200, 600), 2)
    yrms   = round(random.uniform(100, 400), 2)
    zrms   = round(random.uniform(800, 1200), 2)
    xcrest = round(random.uniform(3.0, 8.0), 3)
    ykurt  = round(random.uniform(2.0, 18.0), 3)
    run_id = f"{mach}_{mo}_{yr}_SYN_{j:03d}"

    fake_row = {
        'run_id': run_id, 'machine': mach, 'operation': op,
        'process_name': OPERATION_LABELS.get(op,op),
        'timestamp': ts, 'year': yr, 'month': mo,
        'fault_category': cat, 'vibration_severity_score': sev,
        'complaint_case_id': cmp_id,
        'x_rms': xrms, 'y_rms': yrms, 'z_rms': zrms,
        'x_crest': xcrest, 'y_kurtosis': ykurt,
    }
    cust = CUSTOMERS[j % len(CUSTOMERS)]
    rec  = make_complaint(fake_row, cmp_id, cust, extra_synthetic=True)
    complaints.append(rec)

print(f"Built {len(complaints)-70} synthetic extension complaints")
print(f"Total complaints: {len(complaints)}")

# ── Save to CSV ────────────────────────────────────────────────────────────────
out_csv = '/home/claude/equipmentiq/processed/customer_complaints.csv'
df = pd.DataFrame(complaints)
df.to_csv(out_csv, index=False, quoting=csv.QUOTE_ALL)

# ── Summary stats ──────────────────────────────────────────────────────────────
print(f"\n=== COMPLAINT DATASET SUMMARY ===")
print(f"Total records    : {len(df)}")
print(f"Anchored (Bosch) : {(df['source']=='bosch_real_fault').sum()}")
print(f"Synthetic        : {(df['source']=='synthetic_extension').sum()}")
print(f"\nBy fault category:")
print(df['fault_category'].value_counts().to_string())
print(f"\nBy case status:")
print(df['case_status'].value_counts().to_string())
print(f"\nBy priority:")
print(df['priority'].value_counts().to_string())
print(f"\nBy customer:")
print(df['customer_name'].value_counts().to_string())
print(f"\nRMA cases: {(df['rma_required']=='YES').sum()}")
print(f"Billable cases: {(df['billable']=='YES').sum()}")
print(f"\nAvg resolution hours (closed): {df[df['case_status']=='CLOSED']['resolution_hours'].astype(float).mean():.1f} h")
print(f"\nSaved: {out_csv}")

# ── Save rich JSON version (with full notes) ────────────────────────────────────
import json
complaints_json = df.to_dict('records')
with open('/home/claude/equipmentiq/processed/customer_complaints.json','w') as f:
    json.dump({'total': len(complaints_json), 'records': complaints_json}, f, indent=2)
print("Saved: customer_complaints.json")
