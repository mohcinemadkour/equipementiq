import json, csv, random, math
from copy import deepcopy

random.seed(42)

# ─── 1. TAXONOMY ──────────────────────────────────────────────────────────────
# 8 severity levels (1=Critical → 8=Advisory), modeled on Fagor CNC + SAE J2012
SEVERITY_LEVELS = {
    1: {"name": "CRITICAL",   "code_prefix": "CR", "color": "RED",    "action": "Immediate machine stop. Do not restart without authorised technician inspection.",  "max_downtime_min": 480},
    2: {"name": "MAJOR",      "code_prefix": "MJ", "color": "ORANGE", "action": "Stop current operation. Machine must be inspected before resuming production.",       "max_downtime_min": 240},
    3: {"name": "SERIOUS",    "code_prefix": "SR", "color": "YELLOW", "action": "Complete current cycle then stop. Schedule maintenance within 4 hours.",             "max_downtime_min": 120},
    4: {"name": "MODERATE",   "code_prefix": "MD", "color": "AMBER",  "action": "Log fault. Schedule maintenance within 24 hours. Reduce feed rate by 20%.",          "max_downtime_min":  60},
    5: {"name": "MINOR",      "code_prefix": "MN", "color": "BLUE",   "action": "Log fault. Monitor parameters. Schedule inspection at next planned maintenance.",    "max_downtime_min":  30},
    6: {"name": "WARNING",    "code_prefix": "WN", "color": "CYAN",   "action": "Log event. No immediate action required. Review at end of shift.",                   "max_downtime_min":   0},
    7: {"name": "NOTICE",     "code_prefix": "NC", "color": "GREEN",  "action": "Informational. Parameter approaching limit. Review during next maintenance window.", "max_downtime_min":   0},
    8: {"name": "ADVISORY",   "code_prefix": "AD", "color": "WHITE",  "action": "Performance advisory only. No maintenance action required.",                        "max_downtime_min":   0},
}

# ─── 2. SUBSYSTEMS (MID — Module Identification, per SAE J2012) ───────────────
SUBSYSTEMS = {
    "SPN": {"name": "Spindle Drive System",       "mid": 128, "ops": ["OP01","OP02","OP03","OP04","OP05","OP06","OP07","OP08","OP09","OP10","OP11","OP14"]},
    "AXS": {"name": "Axis Servo System",          "mid": 130, "ops": ["OP01","OP02","OP03","OP07","OP08","OP11"]},
    "TCS": {"name": "Tool Change System",         "mid": 132, "ops": ["OP12"]},
    "CLS": {"name": "Coolant System",             "mid": 134, "ops": ["OP01","OP02","OP03","OP04","OP05","OP06","OP07","OP08","OP09","OP10","OP11"]},
    "LUB": {"name": "Lubrication System",         "mid": 136, "ops": ["OP00","OP01","OP02","OP03","OP04","OP05","OP06","OP07","OP08","OP09","OP10","OP11","OP12","OP13","OP14"]},
    "HYD": {"name": "Hydraulic System",           "mid": 138, "ops": ["OP00","OP12","OP14"]},
    "CNC": {"name": "CNC Controller",             "mid": 140, "ops": ["OP00","OP01","OP02","OP03","OP04","OP05","OP06","OP07","OP08","OP09","OP10","OP11","OP12","OP13","OP14"]},
    "ELC": {"name": "Electrical Cabinet",         "mid": 142, "ops": ["OP00","OP14"]},
    "VIB": {"name": "Vibration Monitoring",       "mid": 144, "ops": ["OP01","OP02","OP03","OP04","OP05","OP06","OP07","OP08","OP10","OP11","OP14"]},
    "THM": {"name": "Thermal Management",         "mid": 146, "ops": ["OP01","OP02","OP03","OP04","OP05","OP06","OP07","OP08","OP09","OP10","OP11","OP14"]},
}

# ─── 3. PARAMETER SCHEMA (PID — Parameter Identification, per SAE J2012) ──────
# Each param: pid, name, unit, normal_min, normal_max, critical_min, critical_max
PARAMETERS = {
    # Spindle
    "P001": {"pid": 1,  "name": "Spindle Speed",              "unit": "RPM",   "normal_min": 100,   "normal_max": 8000,  "critical_min": 0,     "critical_max": 8500,  "subsystem": "SPN"},
    "P002": {"pid": 2,  "name": "Spindle Load",               "unit": "%",     "normal_min": 0,     "normal_max": 85,    "critical_min": 0,     "critical_max": 105,   "subsystem": "SPN"},
    "P003": {"pid": 3,  "name": "Spindle Motor Temperature",  "unit": "°C",    "normal_min": 20,    "normal_max": 75,    "critical_min": 0,     "critical_max": 95,    "subsystem": "SPN"},
    "P004": {"pid": 4,  "name": "Spindle Bearing Vibration",  "unit": "mm/s",  "normal_min": 0,     "normal_max": 4.5,   "critical_min": 0,     "critical_max": 11.2,  "subsystem": "VIB"},
    "P005": {"pid": 5,  "name": "Spindle Torque",             "unit": "Nm",    "normal_min": 0,     "normal_max": 120,   "critical_min": 0,     "critical_max": 145,   "subsystem": "SPN"},
    "P006": {"pid": 6,  "name": "Spindle Orientation Error",  "unit": "deg",   "normal_min": -0.05, "normal_max": 0.05,  "critical_min": -0.5,  "critical_max": 0.5,   "subsystem": "SPN"},
    # Axes
    "P010": {"pid": 10, "name": "X-Axis Position Error",      "unit": "mm",    "normal_min": -0.01, "normal_max": 0.01,  "critical_min": -0.5,  "critical_max": 0.5,   "subsystem": "AXS"},
    "P011": {"pid": 11, "name": "Y-Axis Position Error",      "unit": "mm",    "normal_min": -0.01, "normal_max": 0.01,  "critical_min": -0.5,  "critical_max": 0.5,   "subsystem": "AXS"},
    "P012": {"pid": 12, "name": "Z-Axis Position Error",      "unit": "mm",    "normal_min": -0.01, "normal_max": 0.01,  "critical_min": -0.5,  "critical_max": 0.5,   "subsystem": "AXS"},
    "P013": {"pid": 13, "name": "X-Axis Servo Current",       "unit": "A",     "normal_min": 0,     "normal_max": 18,    "critical_min": 0,     "critical_max": 25,    "subsystem": "AXS"},
    "P014": {"pid": 14, "name": "Y-Axis Servo Current",       "unit": "A",     "normal_min": 0,     "normal_max": 18,    "critical_min": 0,     "critical_max": 25,    "subsystem": "AXS"},
    "P015": {"pid": 15, "name": "Z-Axis Servo Current",       "unit": "A",     "normal_min": 0,     "normal_max": 22,    "critical_min": 0,     "critical_max": 30,    "subsystem": "AXS"},
    "P016": {"pid": 16, "name": "Axis Following Error",       "unit": "mm",    "normal_min": 0,     "normal_max": 0.05,  "critical_min": 0,     "critical_max": 2.0,   "subsystem": "AXS"},
    "P017": {"pid": 17, "name": "Servo Drive Temperature",    "unit": "°C",    "normal_min": 20,    "normal_max": 70,    "critical_min": 0,     "critical_max": 90,    "subsystem": "AXS"},
    # Tool Change
    "P020": {"pid": 20, "name": "Tool Magazine Position",     "unit": "slot",  "normal_min": 1,     "normal_max": 30,    "critical_min": 0,     "critical_max": 31,    "subsystem": "TCS"},
    "P021": {"pid": 21, "name": "Tool Clamp Pressure",        "unit": "bar",   "normal_min": 55,    "normal_max": 75,    "critical_min": 40,    "critical_max": 80,    "subsystem": "TCS"},
    "P022": {"pid": 22, "name": "ATC Arm Cycle Time",         "unit": "s",     "normal_min": 3.5,   "normal_max": 6.0,   "critical_min": 0,     "critical_max": 10,    "subsystem": "TCS"},
    "P023": {"pid": 23, "name": "Tool Length Offset Error",   "unit": "mm",    "normal_min": -0.02, "normal_max": 0.02,  "critical_min": -2.0,  "critical_max": 2.0,   "subsystem": "TCS"},
    # Coolant
    "P030": {"pid": 30, "name": "Coolant Flow Rate",          "unit": "L/min", "normal_min": 15,    "normal_max": 40,    "critical_min": 5,     "critical_max": 50,    "subsystem": "CLS"},
    "P031": {"pid": 31, "name": "Coolant Temperature",        "unit": "°C",    "normal_min": 15,    "normal_max": 35,    "critical_min": 5,     "critical_max": 45,    "subsystem": "CLS"},
    "P032": {"pid": 32, "name": "Coolant Pressure",           "unit": "bar",   "normal_min": 4,     "normal_max": 8,     "critical_min": 1,     "critical_max": 12,    "subsystem": "CLS"},
    "P033": {"pid": 33, "name": "Coolant Tank Level",         "unit": "%",     "normal_min": 20,    "normal_max": 100,   "critical_min": 5,     "critical_max": 100,   "subsystem": "CLS"},
    # Lubrication
    "P040": {"pid": 40, "name": "Lubrication Oil Pressure",   "unit": "bar",   "normal_min": 2.0,   "normal_max": 4.5,   "critical_min": 0.5,   "critical_max": 6.0,   "subsystem": "LUB"},
    "P041": {"pid": 41, "name": "Lubrication Oil Level",      "unit": "%",     "normal_min": 25,    "normal_max": 100,   "critical_min": 10,    "critical_max": 100,   "subsystem": "LUB"},
    "P042": {"pid": 42, "name": "Lubrication Pump Current",   "unit": "A",     "normal_min": 0.5,   "normal_max": 2.5,   "critical_min": 0,     "critical_max": 4.0,   "subsystem": "LUB"},
    # Hydraulic
    "P050": {"pid": 50, "name": "Hydraulic System Pressure",  "unit": "bar",   "normal_min": 60,    "normal_max": 80,    "critical_min": 40,    "critical_max": 100,   "subsystem": "HYD"},
    "P051": {"pid": 51, "name": "Hydraulic Oil Temperature",  "unit": "°C",    "normal_min": 30,    "normal_max": 55,    "critical_min": 20,    "critical_max": 70,    "subsystem": "HYD"},
    "P052": {"pid": 52, "name": "Hydraulic Pump Flow",        "unit": "L/min", "normal_min": 20,    "normal_max": 35,    "critical_min": 5,     "critical_max": 40,    "subsystem": "HYD"},
    # Vibration
    "P060": {"pid": 60, "name": "X-Axis Vibration RMS",       "unit": "mm/s",  "normal_min": 0,     "normal_max": 4.5,   "critical_min": 0,     "critical_max": 11.2,  "subsystem": "VIB"},
    "P061": {"pid": 61, "name": "Y-Axis Vibration RMS",       "unit": "mm/s",  "normal_min": 0,     "normal_max": 4.5,   "critical_min": 0,     "critical_max": 11.2,  "subsystem": "VIB"},
    "P062": {"pid": 62, "name": "Z-Axis Vibration RMS",       "unit": "mm/s",  "normal_min": 0,     "normal_max": 4.5,   "critical_min": 0,     "critical_max": 11.2,  "subsystem": "VIB"},
    "P063": {"pid": 63, "name": "Vibration Crest Factor",     "unit": "-",     "normal_min": 1.0,   "normal_max": 4.5,   "critical_min": 0,     "critical_max": 12.0,  "subsystem": "VIB"},
    "P064": {"pid": 64, "name": "Kurtosis Index",             "unit": "-",     "normal_min": 2.5,   "normal_max": 5.0,   "critical_min": 0,     "critical_max": 25.0,  "subsystem": "VIB"},
    # Thermal
    "P070": {"pid": 70, "name": "Ambient Temperature",        "unit": "°C",    "normal_min": 15,    "normal_max": 35,    "critical_min": 5,     "critical_max": 45,    "subsystem": "THM"},
    "P071": {"pid": 71, "name": "Electrical Cabinet Temp",    "unit": "°C",    "normal_min": 20,    "normal_max": 45,    "critical_min": 10,    "critical_max": 60,    "subsystem": "THM"},
    "P072": {"pid": 72, "name": "Feed Drive Motor Temp",      "unit": "°C",    "normal_min": 20,    "normal_max": 72,    "critical_min": 0,     "critical_max": 90,    "subsystem": "THM"},
    # CNC Controller
    "P080": {"pid": 80, "name": "CNC CPU Load",               "unit": "%",     "normal_min": 0,     "normal_max": 75,    "critical_min": 0,     "critical_max": 100,   "subsystem": "CNC"},
    "P081": {"pid": 81, "name": "CNC Memory Usage",           "unit": "%",     "normal_min": 0,     "normal_max": 80,    "critical_min": 0,     "critical_max": 100,   "subsystem": "CNC"},
    "P082": {"pid": 82, "name": "NC Program Block Number",    "unit": "block",  "normal_min": 0,    "normal_max": 99999, "critical_min": 0,     "critical_max": 99999, "subsystem": "CNC"},
    "P083": {"pid": 83, "name": "Feed Override",              "unit": "%",     "normal_min": 0,     "normal_max": 120,   "critical_min": 0,     "critical_max": 150,   "subsystem": "CNC"},
    # Electrical
    "P090": {"pid": 90, "name": "DC Bus Voltage",             "unit": "V",     "normal_min": 560,   "normal_max": 620,   "critical_min": 480,   "critical_max": 680,   "subsystem": "ELC"},
    "P091": {"pid": 91, "name": "Main Supply Voltage",        "unit": "V",     "normal_min": 380,   "normal_max": 420,   "critical_min": 340,   "critical_max": 440,   "subsystem": "ELC"},
    "P092": {"pid": 92, "name": "Ground Leakage Current",     "unit": "mA",    "normal_min": 0,     "normal_max": 10,    "critical_min": 0,     "critical_max": 30,    "subsystem": "ELC"},
    "P093": {"pid": 93, "name": "UPS Battery Level",          "unit": "%",     "normal_min": 80,    "normal_max": 100,   "critical_min": 20,    "critical_max": 100,   "subsystem": "ELC"},
}

print(f"Defined {len(PARAMETERS)} parameters across {len(SUBSYSTEMS)} subsystems")

# ─── 4. ERROR CODE DEFINITIONS ────────────────────────────────────────────────
# Format: code, severity, subsystem, fault_category, params (list of param keys),
#         title, description, cause, diagnostic_steps, remedy, related_codes

ERROR_DEFINITIONS = [

  # ══════════════════════ SPINDLE DRIVE SYSTEM ══════════════════════════════

  # CRITICAL (1)
  {"code":"SPN-CR-001","sev":1,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P001","P003","P004","P005"],
   "title":"Spindle Bearing Catastrophic Failure",
   "desc":"Spindle bearing has reached catastrophic failure threshold. Vibration RMS on spindle exceeds 11.2 mm/s with kurtosis index >20. Continued operation risks spindle shaft damage and workpiece ejection.",
   "cause":"Bearing race spalling, loss of lubrication, contamination ingress, or end-of-life fatigue. May follow undetected progression through WN-060 and MN-061 warnings.",
   "diag":["Stop spindle immediately and lock out/tag out","Measure bearing vibration with handheld analyser at spindle nose","Inspect spindle cooling lines for blockage","Check oil mist lubrication nozzle P040","Review vibration trend log for P004 over prior 72 hours"],
   "remedy":"Replace spindle bearing set. Re-grease per OEM specification. Run acceptance test program SPD-TEST-001 before production restart.",
   "related":["SPN-MJ-002","VIB-WN-060","VIB-MN-061"]},

  {"code":"SPN-CR-002","sev":1,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P001","P002","P005"],
   "title":"Spindle Drive Overcurrent — Hard Fault",
   "desc":"Spindle drive current exceeded 145% of rated value for more than 200ms. Drive has tripped on hardware overcurrent protection. P002 read {val} % (limit 105%).",
   "cause":"Spindle motor short circuit, drive IGBT failure, or mechanical seizure of spindle bearings. Distinguish from thermal overcurrent SPN-MJ-005.",
   "diag":["Do not reset drive until root cause identified","Check spindle motor insulation resistance (megger test)","Inspect drive power stage for burn marks","Verify no mechanical obstruction in spindle bore","Check P005 torque log for sudden spike event"],
   "remedy":"Replace faulty drive module or motor depending on fault localisation. Verify DC bus voltage P090 is within spec before power-on.",
   "related":["SPN-MJ-005","ELC-CR-001","SPN-CR-001"]},

  {"code":"SPN-CR-003","sev":1,"sub":"SPN","fault":"actuator_fault",
   "params":["P006","P001"],
   "title":"Spindle Orientation Failure — Tool Change Blocked",
   "desc":"Spindle failed to reach orientation position within timeout (5 s). Orientation error P006 = {val} deg (limit ±0.5 deg). Tool change cycle aborted to prevent ATC arm collision.",
   "cause":"Encoder signal loss, orientation proximity switch failure, or mechanical brake malfunction.",
   "diag":["Check spindle encoder cable continuity","Verify orientation switch target disk alignment","Inspect pneumatic brake actuation pressure","Test orientation cycle manually in JOG mode","Review parameter P082 for last NC block executed"],
   "remedy":"Replace encoder or repair signal cable. Re-teach orientation position parameter. Re-run tool change acceptance cycle TCS-TEST-002.",
   "related":["TCS-CR-001","SPN-MJ-003","CNC-MD-011"]},

  # MAJOR (2)
  {"code":"SPN-MJ-001","sev":2,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P003","P001","P002"],
   "title":"Spindle Motor Overtemperature",
   "desc":"Spindle motor winding temperature P003 = {val} °C exceeds major threshold (85 °C). Thermal model predicts critical threshold (95 °C) in <15 minutes at current load.",
   "cause":"Cooling fan failure, blocked air filter, excessive duty cycle, or degraded motor winding insulation.",
   "diag":["Check spindle cooling fan rotation","Inspect and clean air filter on motor housing","Verify coolant-through-spindle flow if equipped","Reduce spindle load P002 by lowering feed rate","Check ambient temperature P070"],
   "remedy":"Replace cooling fan motor. Clean filters. If repeated, check motor insulation class and compare to duty cycle.",
   "related":["SPN-CR-002","THM-WN-070","SPN-MN-006"]},

  {"code":"SPN-MJ-002","sev":2,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P004","P063","P064"],
   "title":"Spindle Bearing Vibration — Major Threshold Exceeded",
   "desc":"Spindle bearing vibration P004 = {val} mm/s exceeds ISO 10816-3 Zone C limit (7.1 mm/s). Kurtosis index P064 = {val2} indicates bearing defect frequency component present.",
   "cause":"Bearing inner or outer race defect, ball spall, or loss of preload. Consistent with tool_wear or spindle_bearing_fault events in operational data.",
   "diag":["Capture vibration spectrum via on-machine sensor","Compare dominant frequency to bearing defect frequencies (BPFO, BPFI, BSF)","Check spindle thermal growth compensation active","Inspect tool holder for imbalance","Review trend for P004 over prior 30 days"],
   "remedy":"Schedule spindle bearing replacement within 8 hours. Reduce spindle speed by 30% until replacement. Do not run over 6000 RPM.",
   "related":["SPN-CR-001","VIB-MN-061","SPN-SR-003"]},

  {"code":"SPN-MJ-003","sev":2,"sub":"SPN","fault":"tool_wear",
   "params":["P002","P005","P001"],
   "title":"Spindle Load Anomaly — Possible Tool Breakage",
   "desc":"Spindle load P002 jumped from baseline by >40% within one NC block. P005 torque = {val} Nm. Pattern consistent with sudden tool breakage during milling operation.",
   "cause":"Tool fracture due to worn cutting edges, excessive depth of cut, incorrect tool material, or coolant failure at cutting zone.",
   "diag":["Halt program and inspect tool in spindle","Check tool length with probe if available","Review P033 coolant level and P030 flow rate","Inspect workpiece surface for gouging","Review NC block G-code for programmed depth of cut"],
   "remedy":"Replace broken or worn tool. Verify tool offset in tool table. Run first-off inspection before resuming production.",
   "related":["CLS-SR-001","SPN-WN-004","TCS-MD-001"]},

  {"code":"SPN-MJ-004","sev":2,"sub":"SPN","fault":"chatter_vibration",
   "params":["P060","P061","P062","P063"],
   "title":"Regenerative Chatter — Stability Limit Exceeded",
   "desc":"Vibration pattern on X/Y/Z axes indicates regenerative chatter. Dominant frequency {val} Hz matches spindle-speed-to-tooth-passing ratio. Crest factor P063 = {val2}.",
   "cause":"Operating at unstable depth-of-cut for current spindle speed and tool geometry. May worsen with tool wear.",
   "diag":["Record dominant chatter frequency from vibration log","Apply stability lobe diagram for tool/fixture combination","Check workpiece clamping force","Inspect tool holder taper contact for fretting","Review programmed RPM P001 vs stability lobe chart"],
   "remedy":"Adjust spindle speed by ±10% to shift operating point to stable lobe. Reduce axial depth of cut. Consider high-damping tool holder.",
   "related":["VIB-WN-060","SPN-MJ-002","AXS-MN-002"]},

  {"code":"SPN-MJ-005","sev":2,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P002","P003","P005"],
   "title":"Spindle Drive Thermal Overcurrent",
   "desc":"Drive reports thermal overcurrent condition. Motor current P002 sustained at {val}% for >60 s. Drive will shut down in {val2} s if condition persists.",
   "cause":"Excessive cutting load, incorrect feed/speed parameters, or degraded drive cooling.",
   "diag":["Check drive heatsink temperature","Verify drive fan is operational","Inspect drive filter mat","Reduce programmed feed rate P083","Verify tool geometry matches material"],
   "remedy":"Allow drive to cool (20 min minimum). Clean drive filters. If recurring, upgrade drive to next current rating.",
   "related":["SPN-CR-002","THM-MD-001","SPN-MJ-001"]},

  # SERIOUS (3)
  {"code":"SPN-SR-001","sev":3,"sub":"SPN","fault":"tool_wear",
   "params":["P002","P005","P001"],
   "title":"Spindle Load Gradually Increasing — Tool Wear Trend",
   "desc":"Spindle load P002 shows monotonic increase of {val}% over last 50 tool engagements. Pattern consistent with progressive tool flank wear. Current load {val2}%.",
   "cause":"Tool cutting edge wear beyond recommended tool life. Insufficient coolant delivery or incorrect cutting parameters accelerating wear.",
   "diag":["Inspect cutting edge under 10× loupe","Compare current tool life to OEM recommendation","Check coolant concentration (refractometer)","Review chip formation — short chips indicate worn tool","Trend P002 on same operation across last 20 parts"],
   "remedy":"Replace tool at next part completion. Update tool life counter in tool table. Optimise cutting parameters.",
   "related":["SPN-MJ-003","SPN-WN-004","TCS-MD-001"]},

  {"code":"SPN-SR-002","sev":3,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P001","P006"],
   "title":"Spindle Speed Deviation — Encoder Signal Degraded",
   "desc":"Actual spindle speed deviates from commanded speed by >{val} RPM for >500 ms. Encoder signal shows {val2} missing pulses per revolution.",
   "cause":"Encoder disc contamination, bearing play causing encoder misalignment, or encoder cable shield failure causing EMI.",
   "diag":["Clean encoder disc with IPA","Check encoder mounting bolts torque","Inspect cable routing for pinch points","Measure signal quality on oscilloscope","Check cable shield continuity to ground"],
   "remedy":"Clean or replace encoder. Re-route cable away from power cables. Re-commission speed loop.",
   "related":["SPN-CR-003","SPN-MJ-002","CNC-MD-011"]},

  {"code":"SPN-SR-003","sev":3,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P004","P064"],
   "title":"Bearing Kurtosis Threshold — Defect Initiation Detected",
   "desc":"Kurtosis index P064 = {val} has exceeded early-defect threshold (8.0). Statistical analysis of vibration signal indicates impulse-type events consistent with bearing defect initiation.",
   "cause":"Early-stage bearing race or rolling element defect. Expected remaining useful life: 200–500 operating hours depending on load.",
   "diag":["Enable continuous vibration trending for this spindle","Reduce spindle speed by 20% as precaution","Schedule borescope inspection at next planned downtime","Compare P064 trend rate of change to historical baseline"],
   "remedy":"Plan bearing replacement within 200 operating hours. Continue monitoring P064 daily. Reduce maximum spindle speed to 70% until replacement.",
   "related":["SPN-MJ-002","SPN-CR-001","VIB-WN-060"]},

  # MODERATE (4)
  {"code":"SPN-MD-001","sev":4,"sub":"SPN","fault":"tool_wear",
   "params":["P002","P005"],
   "title":"Spindle Load — Elevated Baseline",
   "desc":"Spindle load P002 baseline on operation {val} is {val2}% above historical mean for same program. No acute spike. Gradual trend suggests accumulating mechanical resistance.",
   "cause":"Tool wear progression, slight bearing preload increase, or minor misalignment.",
   "diag":["Compare current cycle time to nominal","Inspect tool visually for chip edge","Run dry cycle (spindle only, no feed) and check no-load current","Trend over next 20 cycles"],
   "remedy":"Schedule tool inspection at next shift change. Log in maintenance history.",
   "related":["SPN-SR-001","SPN-WN-004"]},

  {"code":"SPN-MD-002","sev":4,"sub":"SPN","fault":"process_anomaly",
   "params":["P001","P083"],
   "title":"Feed Override Active — Non-Standard Cutting Condition",
   "desc":"Feed override P083 set to {val}% (nominal 100%) during production program. Spindle speed P001 = {val2} RPM. Non-standard override active for >10 parts.",
   "cause":"Operator compensation for tool wear, material hardness variation, or unresolved vibration issue.",
   "diag":["Interview operator for reason override was applied","Check if override masks a recurring alarm","Verify correct tool is loaded in spindle","Review last SPC data for dimension drift"],
   "remedy":"Restore nominal feed rate. If override required for quality, initiate cutting parameter review with process engineer.",
   "related":["SPN-SR-001","SPN-MJ-003"]},

  # MINOR (5)
  {"code":"SPN-MN-001","sev":5,"sub":"SPN","fault":"tool_wear",
   "params":["P002"],
   "title":"Spindle Load — Upper Advisory Threshold",
   "desc":"Spindle load P002 = {val}% is above upper advisory band (70%) but below major threshold. Sustained for {val2} minutes.",
   "cause":"Normal heavy-cut condition or early tool wear. Monitor for progression.",
   "diag":["Verify programmed depth of cut is nominal","Check tool life counter remaining","Monitor for next 10 cycles"],
   "remedy":"No immediate action. Log and monitor trend.",
   "related":["SPN-MD-001","SPN-SR-001"]},

  {"code":"SPN-MN-002","sev":5,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P003"],
   "title":"Spindle Motor Temperature — Elevated",
   "desc":"Spindle motor temperature P003 = {val} °C. Within normal range but {val2} °C above 30-day average for same duty cycle.",
   "cause":"Slight cooling degradation or increased duty cycle.",
   "diag":["Check air filter cleanliness","Verify coolant flow to motor if liquid-cooled","Compare ambient P070 to historical"],
   "remedy":"Clean filters at next shift break. Monitor trend.",
   "related":["SPN-MJ-001","THM-WN-070"]},

  {"code":"SPN-MN-003","sev":5,"sub":"SPN","fault":"tool_wear",
   "params":["P005","P002"],
   "title":"Spindle Torque — Elevated During Entry Move",
   "desc":"Spindle torque P005 = {val} Nm during tool entry move. Exceeds expected entry torque model by {val2}%. Possible chip re-cutting or worn tool entry geometry.",
   "cause":"Insufficient chip evacuation at tool entry or worn tool corner radius.",
   "diag":["Check chip evacuation — increase coolant pressure P032","Inspect tool corner condition","Review approach strategy in NC program"],
   "remedy":"Adjust tool entry strategy (ramp instead of plunge). Inspect tool.",
   "related":["SPN-MJ-003","CLS-MN-001"]},

  {"code":"SPN-MN-004","sev":5,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P004","P060","P061","P062"],
   "title":"Vibration RMS — Gradual Increase Detected",
   "desc":"Vibration RMS P004 shows {val}% increase over last 7 days. Current value {val2} mm/s. Still within ISO Zone B (acceptable for long-term operation) but trend requires monitoring.",
   "cause":"Normal bearing wear progression or loosening of machine foundation bolts.",
   "diag":["Check and re-torque foundation bolts","Inspect ballscrew support bearing","Compare to factory acceptance vibration record"],
   "remedy":"Schedule preventive inspection at next planned maintenance. Document in maintenance log.",
   "related":["SPN-SR-003","SPN-MJ-002"]},

  # WARNING (6)
  {"code":"SPN-WN-001","sev":6,"sub":"SPN","fault":"tool_wear",
   "params":["P002"],
   "title":"Spindle Load — Tool Life 80% Consumed",
   "desc":"Tool life counter for tool T{val} in spindle has reached 80% of programmed tool life. Spindle load P002 = {val2}%. Plan tool change before next scheduled run.",
   "cause":"Normal tool wear progression within expected life.",
   "diag":["Visually inspect tool at next opportunity","Verify tool life setting is calibrated to actual tool","Check surface finish on last produced part"],
   "remedy":"Prepare replacement tool. Schedule tool change at end of current batch.",
   "related":["SPN-MN-001","TCS-MD-001"]},

  {"code":"SPN-WN-002","sev":6,"sub":"SPN","fault":"spindle_bearing_fault",
   "params":["P003"],
   "title":"Spindle Temperature — Warm-Up Reminder",
   "desc":"Machine has been idle >4 hours. Spindle temperature P003 = {val} °C. Run warm-up program SPD-WARMUP-001 before resuming production to avoid thermal shock to bearings.",
   "cause":"Standard thermal management — bearing preload changes with temperature.",
   "diag":["Check ambient temperature P070","Verify warm-up program is loaded in CNC memory"],
   "remedy":"Execute spindle warm-up program (15 min). Do not exceed 30% of maximum speed during first 5 minutes.",
   "related":["SPN-MN-002","THM-NC-001"]},

  {"code":"SPN-WN-003","sev":6,"sub":"SPN","fault":"tool_wear",
   "params":["P002","P005"],
   "title":"Tool Life Counter — Approaching Limit",
   "desc":"Tool T{val} has reached {val2}% of programmed tool life. Spindle load trend is stable. Tool change recommended before next production shift.",
   "cause":"Normal cumulative tool usage.",
   "diag":["Inspect tool surface condition","Confirm replacement tool is available in magazine"],
   "remedy":"Schedule tool change at shift end.",
   "related":["SPN-WN-001","TCS-NC-001"]},

  {"code":"SPN-WN-004","sev":6,"sub":"SPN","fault":"tool_wear",
   "params":["P002"],
   "title":"Spindle Load Variance — Increased Part-to-Part Variation",
   "desc":"Spindle load P002 standard deviation across last 20 parts has increased by {val}% vs. baseline. Mean load unchanged. Variability indicates inconsistent cutting condition.",
   "cause":"Workpiece material hardness variation, inconsistent clamping, or intermittent coolant delivery.",
   "diag":["Check material certificate for hardness specification","Inspect fixture clamping force with hydraulic gauge","Verify coolant nozzle position"],
   "remedy":"Investigate material batch. Verify fixture setup procedure.",
   "related":["SPN-MN-001","CLS-WN-001"]},

  # NOTICE (7)
  {"code":"SPN-NC-001","sev":7,"sub":"SPN","fault":"process_anomaly",
   "params":["P001","P002"],
   "title":"Spindle Speed Program Limit Active",
   "desc":"Active NC program has set spindle speed limit to {val} RPM via G50 command. Maximum achievable P001 = {val2} RPM for this operation.",
   "cause":"Programmed speed limit for fixture or tool safety.",
   "diag":["Confirm speed limit is intentional in NC program","Verify tool/fixture speed rating"],
   "remedy":"No action required unless limit is unintentional.",
   "related":[]},

  {"code":"SPN-NC-002","sev":7,"sub":"SPN","fault":"process_anomaly",
   "params":["P003"],
   "title":"Spindle Warm-Up Complete",
   "desc":"Spindle warm-up cycle complete. Motor temperature P003 = {val} °C. Machine ready for production at full speed.",
   "cause":"Normal machine readiness notification.",
   "diag":[],"remedy":"No action required. Proceed with production.",
   "related":["SPN-WN-002"]},

  # ADVISORY (8)
  {"code":"SPN-AD-001","sev":8,"sub":"SPN","fault":"process_anomaly",
   "params":["P001","P083"],
   "title":"Spindle Running at Reduced Speed — Override Active",
   "desc":"Spindle running at {val} RPM with feed override P083 at {val2}%. Performance advisory only.",
   "cause":"Operator or program-initiated speed reduction.",
   "diag":[],"remedy":"No action required.",
   "related":["SPN-MD-002"]},

  {"code":"SPN-AD-002","sev":8,"sub":"SPN","fault":"process_anomaly",
   "params":["P002"],
   "title":"Spindle Idle — No Load Detected",
   "desc":"Spindle running at programmed speed but P002 load = {val}%. No cutting engagement detected. Tool may be in air or rapid traversal block.",
   "cause":"Normal between-operation spindle state.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  # ══════════════════════ AXIS SERVO SYSTEM ══════════════════════════════════

  {"code":"AXS-CR-001","sev":1,"sub":"AXS","fault":"actuator_fault",
   "params":["P016","P010","P011","P012"],
   "title":"Axis Following Error — Emergency Stop",
   "desc":"Axis following error P016 = {val} mm exceeds emergency stop threshold (2.0 mm). All axes halted. Position integrity cannot be guaranteed. P010={val2}, P011={val3}, P012={val4} mm.",
   "cause":"Drive fault, ball screw failure, axis collision, or encoder loss.",
   "diag":["Do not move axes until cause identified","Check all servo drive status LEDs","Verify no mechanical obstruction on axis","Inspect ball screw for damage","Check encoder feedback signal integrity"],
   "remedy":"Identify faulted axis. Repair mechanical cause. Re-home all axes before resuming.",
   "related":["AXS-MJ-001","AXS-MJ-002","CNC-CR-001"]},

  {"code":"AXS-CR-002","sev":1,"sub":"AXS","fault":"actuator_fault",
   "params":["P013","P014","P015"],
   "title":"Servo Drive Hardware Fault — Axis Disabled",
   "desc":"Servo drive reports hardware fault on axis. Drive has disabled output stage. P013={val}A (X), P014={val2}A (Y), P015={val3}A (Z).",
   "cause":"IGBT overcurrent, DC bus undervoltage, or drive internal fault.",
   "diag":["Check drive status display for specific sub-code","Measure DC bus voltage P090","Inspect drive power connections","Check motor phase resistance balance"],
   "remedy":"Replace faulted drive. Verify motor winding integrity before re-enabling.",
   "related":["ELC-CR-001","AXS-CR-001","SPN-CR-002"]},

  {"code":"AXS-MJ-001","sev":2,"sub":"AXS","fault":"actuator_fault",
   "params":["P016","P010","P011","P012"],
   "title":"Axis Following Error — Major Limit",
   "desc":"Following error P016 = {val} mm exceeds major threshold (0.5 mm). Cutting has been suspended. Position error on {val2}-axis.",
   "cause":"Servo gain mismatch, mechanical friction increase, or ball screw backlash.",
   "diag":["Check servo gain parameters vs commissioning record","Inspect axis guide lubrication","Measure backlash on ball screw","Run servo tuning cycle"],
   "remedy":"Re-tune servo gain. Lubricate linear guides. If backlash >0.02mm, schedule ball screw inspection.",
   "related":["AXS-CR-001","AXS-SR-001","LUB-MD-001"]},

  {"code":"AXS-MJ-002","sev":2,"sub":"AXS","fault":"actuator_fault",
   "params":["P013","P014","P015","P017"],
   "title":"Servo Drive Thermal Warning — Overtemperature",
   "desc":"Servo drive temperature P017 = {val} °C exceeds 80°C. Drive will fault at 90°C. Current draw: X={val2}A, Y={val3}A, Z={val4}A.",
   "cause":"Inadequate cabinet ventilation, blocked drive heatsink, or sustained high-load machining.",
   "diag":["Check cabinet fans are operational P071","Clean drive heatsink fins","Reduce duty cycle temporarily","Check ambient temperature P070"],
   "remedy":"Restore cabinet ventilation. Clean filters. If recurring, upsize drive cooling.",
   "related":["THM-MD-001","AXS-CR-002","ELC-MJ-001"]},

  {"code":"AXS-SR-001","sev":3,"sub":"AXS","fault":"chatter_vibration",
   "params":["P060","P061","P062","P016"],
   "title":"Axis Vibration — Resonance Detected",
   "desc":"Axis vibration on {val}-axis shows resonant frequency at {val2} Hz. Following error P016 = {val3} mm. Pattern consistent with chatter or axis mechanical resonance.",
   "cause":"Feed rate at resonant frequency, worn ball screw nut, or inadequate servo filter.",
   "diag":["Measure resonant frequency from vibration log","Check servo filter notch frequency setting","Inspect ball screw nut preload","Change feed rate by ±15% and observe effect"],
   "remedy":"Apply servo notch filter at resonant frequency. Inspect ball screw nut.",
   "related":["SPN-MJ-004","AXS-MJ-001","VIB-WN-060"]},

  {"code":"AXS-SR-002","sev":3,"sub":"AXS","fault":"actuator_fault",
   "params":["P013","P014","P015"],
   "title":"Servo Current — Elevated Load on Axis",
   "desc":"Servo current on {val}-axis P0{val2} = {val3} A, elevated {val4}% above baseline for equivalent move. Ball screw or guide resistance increasing.",
   "cause":"Insufficient lubrication on linear guides or ball screw, guide wear, or contamination ingress.",
   "diag":["Manually jog axis and feel for stiction","Inspect linear guide surface for scoring","Check lubrication oil delivery to guides P040","Review lubrication interval log"],
   "remedy":"Apply lubrication per maintenance schedule. If stiction persists, inspect guide rail and carriage.",
   "related":["LUB-MD-001","AXS-MJ-001","AXS-MN-001"]},

  {"code":"AXS-MD-001","sev":4,"sub":"AXS","fault":"actuator_fault",
   "params":["P016"],
   "title":"Following Error — Elevated But Within Limit",
   "desc":"Following error P016 = {val} mm is elevated above advisory threshold (0.02 mm) but below halt limit. Trend over last 100 moves: increasing.",
   "cause":"Servo loop gain reduction or mechanical friction increase.",
   "diag":["Run test cycle and log P016 per block","Compare to commissioning baseline","Check guide lubrication"],
   "remedy":"Log and monitor. Schedule servo re-tuning if trend continues.",
   "related":["AXS-MJ-001","AXS-SR-002"]},

  {"code":"AXS-MD-002","sev":4,"sub":"AXS","fault":"actuator_fault",
   "params":["P017"],
   "title":"Servo Drive Temperature — Elevated",
   "desc":"Drive temperature P017 = {val} °C. Within spec but {val2} °C above seasonal baseline. Monitor for progression.",
   "cause":"Marginal cabinet cooling or increased cutting load.",
   "diag":["Check cabinet fan speed","Verify door seals are intact"],
   "remedy":"Clean cabinet filters. Monitor.",
   "related":["AXS-MJ-002","THM-WN-070"]},

  {"code":"AXS-MN-001","sev":5,"sub":"AXS","fault":"actuator_fault",
   "params":["P013","P014","P015"],
   "title":"Servo Current — Minor Variance",
   "desc":"Servo current on {val}-axis shows {val2}% variance vs. baseline on identical move profile. No limit exceeded.",
   "cause":"Normal mechanical variation or minor lubrication change.",
   "diag":["Monitor for 24 hours","Review lubrication log"],
   "remedy":"Log and monitor.",
   "related":["AXS-SR-002"]},

  {"code":"AXS-MN-002","sev":5,"sub":"AXS","fault":"chatter_vibration",
   "params":["P060","P061","P062"],
   "title":"Axis Vibration — Minor Threshold",
   "desc":"Axis vibration RMS on {val}-axis = {val2} mm/s. Above minor threshold (3.5 mm/s) but below major (7.1 mm/s).",
   "cause":"Tool wear induced vibration or minor chatter.",
   "diag":["Inspect tool condition","Try ±10% spindle speed"],
   "remedy":"Monitor and log. Inspect tool at next change.",
   "related":["SPN-MJ-004","AXS-SR-001"]},

  {"code":"AXS-WN-001","sev":6,"sub":"AXS","fault":"process_anomaly",
   "params":["P016"],
   "title":"Following Error — Intermittent Spikes",
   "desc":"Following error P016 shows intermittent spikes to {val} mm during direction reversals. Mean error within spec.",
   "cause":"Ball screw backlash or servo reversal compensation mismatch.",
   "diag":["Check backlash compensation parameter","Measure physical backlash with dial indicator"],
   "remedy":"Adjust backlash compensation parameter. If physical backlash >0.015mm, plan ball screw nut replacement.",
   "related":["AXS-MD-001","AXS-MJ-001"]},

  {"code":"AXS-NC-001","sev":7,"sub":"AXS","fault":"process_anomaly",
   "params":["P010","P011","P012"],
   "title":"Axis Position — Reference Established",
   "desc":"All axes homed successfully. X={val}, Y={val2}, Z={val3} mm from machine zero. Reference position confirmed.",
   "cause":"Normal machine homing cycle complete.",
   "diag":[],"remedy":"No action required. Machine ready for operation.",
   "related":[]},

  {"code":"AXS-AD-001","sev":8,"sub":"AXS","fault":"process_anomaly",
   "params":["P083"],
   "title":"Rapid Override Active",
   "desc":"Rapid traverse override P083 = {val}%. Axes moving at reduced rapid speed.",
   "cause":"Operator or program-set rapid override.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  # ══════════════════════ TOOL CHANGE SYSTEM ═════════════════════════════════

  {"code":"TCS-CR-001","sev":1,"sub":"TCS","fault":"actuator_fault",
   "params":["P020","P021","P022"],
   "title":"ATC Arm Collision — Emergency Stop",
   "desc":"ATC arm detected unexpected resistance during swing cycle. Emergency stop activated. Magazine position P020 = slot {val}. Clamp pressure P021 = {val2} bar. Cycle time exceeded at T+{val3}s.",
   "cause":"Tool not seated correctly in spindle, obstructed magazine pocket, or broken ATC arm.",
   "diag":["Do not reset until area is clear and inspected","Check spindle bore for retained chip or damaged tool","Inspect ATC arm for physical damage","Verify magazine pocket is clear","Check pneumatic pressure to ATC cylinder"],
   "remedy":"Clear obstruction. Inspect and repair ATC arm if damaged. Re-run ATC cycle in manual step mode.",
   "related":["SPN-CR-003","TCS-MJ-001","HYD-MJ-001"]},

  {"code":"TCS-MJ-001","sev":2,"sub":"TCS","fault":"actuator_fault",
   "params":["P021","P022"],
   "title":"Tool Clamp Pressure — Below Minimum",
   "desc":"Tool clamp pressure P021 = {val} bar, below minimum safe value (55 bar). Tool change aborted. Risk of tool ejection if machining continues.",
   "cause":"Pneumatic supply pressure drop, clamp valve leakage, or draw-bar spring fatigue.",
   "diag":["Check pneumatic supply pressure at machine entry","Inspect clamp solenoid valve for leakage","Measure draw-bar pull force with tool pull gauge","Check air service unit filter/regulator"],
   "remedy":"Restore pneumatic pressure. Replace draw-bar spring if pull force <12 kN. Do not machine until clamp pressure verified.",
   "related":["TCS-CR-001","HYD-SR-001","TCS-SR-001"]},

  {"code":"TCS-MJ-002","sev":2,"sub":"TCS","fault":"actuator_fault",
   "params":["P023","P020"],
   "title":"Tool Length Measurement — Out of Tolerance",
   "desc":"In-process tool length measurement via touch probe reports P023 = {val} mm offset from stored value. Tolerance ±0.05 mm. Tool slot {val2}. Risk of dimensional error on workpiece.",
   "cause":"Tool not fully seated, incorrect tool loaded, or tool breakage not detected by P002 load monitor.",
   "diag":["Inspect tool in spindle for seating","Verify tool ID matches NC program expectation","Re-measure with tool presetter offline","Check probe calibration"],
   "remedy":"Re-seat tool and re-measure. If offset confirmed, update tool table and scrap/inspect last part.",
   "related":["SPN-MJ-003","TCS-CR-001"]},

  {"code":"TCS-SR-001","sev":3,"sub":"TCS","fault":"actuator_fault",
   "params":["P022","P021"],
   "title":"ATC Cycle Time — Degraded",
   "desc":"ATC arm cycle time P022 = {val} s, exceeds nominal {val2} s by >20%. Clamp pressure P021 = {val3} bar.",
   "cause":"ATC cylinder seal wear, lubrication degradation, or magazine drive motor wear.",
   "diag":["Run 5 consecutive ATC cycles and log P022","Check ATC lubrication grease condition","Measure air cylinder actuation force","Inspect magazine drive gearbox"],
   "remedy":"Grease ATC arm pivot. If cycle time continues degrading, replace ATC cylinder seals.",
   "related":["TCS-MJ-001","TCS-MD-001"]},

  {"code":"TCS-MD-001","sev":4,"sub":"TCS","fault":"tool_wear",
   "params":["P020"],
   "title":"Magazine Tool Count — Inventory Discrepancy",
   "desc":"CNC tool table shows {val} tools; magazine sensor count = {val2}. Discrepancy of {val3} tools. Risk of calling empty pocket.",
   "cause":"Tool loaded without updating tool table, or tool removed manually without clearing table entry.",
   "diag":["Run magazine inventory check program","Physically verify each occupied pocket vs. tool table","Check for manual tool removal log entries"],
   "remedy":"Reconcile tool table with physical magazine. Clear empty pocket entries.",
   "related":["TCS-SR-001","SPN-WN-001"]},

  {"code":"TCS-MN-001","sev":5,"sub":"TCS","fault":"tool_wear",
   "params":["P020"],
   "title":"Magazine Pocket — Tool Life Expired",
   "desc":"Tool in magazine slot {val} has exceeded 100% of programmed tool life. Tool will not be called by NC program until life counter is reset.",
   "cause":"Normal tool life expiry.",
   "diag":["Inspect tool before resetting counter","Confirm replacement is in magazine"],
   "remedy":"Replace tool. Reset life counter.",
   "related":["SPN-WN-001","TCS-MD-001"]},

  {"code":"TCS-WN-001","sev":6,"sub":"TCS","fault":"tool_wear",
   "params":["P020"],
   "title":"Next Tool Pre-Call — Long ATC Cycle Expected",
   "desc":"Next tool T{val} is in magazine slot {val2}, requiring full magazine rotation of {val3} positions. ATC pre-call initiated.",
   "cause":"Normal magazine logistics based on program sequence.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"TCS-NC-001","sev":7,"sub":"TCS","fault":"process_anomaly",
   "params":["P020","P022"],
   "title":"Tool Change Complete",
   "desc":"ATC cycle completed successfully. Tool T{val} in spindle. Cycle time P022 = {val2} s. Magazine at position {val3}.",
   "cause":"Normal tool change event.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"TCS-AD-001","sev":8,"sub":"TCS","fault":"process_anomaly",
   "params":["P020"],
   "title":"Magazine Position Update",
   "desc":"Magazine indexed to reference position {val} after power-on.",
   "cause":"Normal start-up sequence.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  # ══════════════════════ COOLANT SYSTEM ══════════════════════════════════════

  {"code":"CLS-CR-001","sev":1,"sub":"CLS","fault":"process_anomaly",
   "params":["P030","P033"],
   "title":"Coolant Flow Loss — Emergency Stop",
   "desc":"Coolant flow P030 = {val} L/min (below minimum 5 L/min). Coolant tank level P033 = {val2}%. Machine stopped to prevent tool and workpiece thermal damage.",
   "cause":"Coolant pump failure, blocked filter, ruptured hose, or empty tank.",
   "diag":["Check coolant tank level physically","Inspect pump operation (audible)","Check coolant supply hose for kinking or rupture","Inspect coolant filter element differential pressure","Verify pump motor circuit breaker"],
   "remedy":"Restore coolant supply. Replace pump if failed. Do not restart machining until minimum flow P030 >15 L/min confirmed.",
   "related":["CLS-MJ-001","SPN-MJ-003","CLS-SR-001"]},

  {"code":"CLS-MJ-001","sev":2,"sub":"CLS","fault":"process_anomaly",
   "params":["P031","P030"],
   "title":"Coolant Overtemperature",
   "desc":"Coolant temperature P031 = {val} °C, above major threshold (40 °C). Flow rate P030 = {val2} L/min. Thermal control of cutting zone compromised.",
   "cause":"Chiller unit failure, high ambient temperature, excessive heat load from cutting, or inadequate coolant tank volume.",
   "diag":["Check chiller unit operation","Verify coolant tank volume is adequate","Inspect heat exchanger for fouling","Reduce cutting parameters to lower heat generation"],
   "remedy":"Restore chiller operation. Clean heat exchanger. Allow coolant to cool before resuming heavy cuts.",
   "related":["CLS-CR-001","THM-MD-001"]},

  {"code":"CLS-SR-001","sev":3,"sub":"CLS","fault":"process_anomaly",
   "params":["P032","P030"],
   "title":"Coolant Pressure — Low",
   "desc":"Coolant pressure P032 = {val} bar, below lower advisory limit (4 bar). Flow rate P030 = {val2} L/min. Coolant-through-spindle delivery may be insufficient.",
   "cause":"Partially blocked filter, partially closed isolation valve, or pump cavitation from low tank level.",
   "diag":["Check filter differential pressure gauge","Verify all isolation valves open","Check tank level P033","Listen for pump cavitation (irregular noise)"],
   "remedy":"Replace coolant filter. Refill tank. Re-prime pump.",
   "related":["CLS-MJ-001","CLS-CR-001","CLS-MD-001"]},

  {"code":"CLS-MD-001","sev":4,"sub":"CLS","fault":"process_anomaly",
   "params":["P033"],
   "title":"Coolant Tank Level — Low",
   "desc":"Coolant tank level P033 = {val}%. Below recommended operating level (25%). Machine will halt at 5%.",
   "cause":"Coolant consumption exceeds refill rate, or evaporation/drag-out.",
   "diag":["Check refractometer for coolant concentration","Inspect for leaks","Review coolant consumption log"],
   "remedy":"Top up coolant tank. Check concentration and adjust. Investigate consumption rate if elevated.",
   "related":["CLS-CR-001","CLS-WN-001"]},

  {"code":"CLS-MN-001","sev":5,"sub":"CLS","fault":"process_anomaly",
   "params":["P030","P031"],
   "title":"Coolant Flow — Minor Deviation",
   "desc":"Coolant flow P030 = {val} L/min, {val2}% below setpoint. Temperature P031 = {val3} °C. No immediate machining impact.",
   "cause":"Minor filter restriction or nozzle partial blockage.",
   "diag":["Inspect coolant nozzles for chip blockage","Check filter condition"],
   "remedy":"Clean nozzles. Schedule filter inspection at shift end.",
   "related":["CLS-SR-001","CLS-MD-001"]},

  {"code":"CLS-WN-001","sev":6,"sub":"CLS","fault":"process_anomaly",
   "params":["P033"],
   "title":"Coolant Tank — Refill Reminder",
   "desc":"Coolant tank level P033 = {val}%. Refill recommended within {val2} hours based on consumption rate.",
   "cause":"Normal coolant consumption.",
   "diag":[],"remedy":"Add coolant mix at correct concentration (check refractometer).",
   "related":["CLS-MD-001"]},

  {"code":"CLS-NC-001","sev":7,"sub":"CLS","fault":"process_anomaly",
   "params":["P031"],
   "title":"Coolant Temperature Stabilised",
   "desc":"Coolant temperature P031 = {val} °C. Within optimal range. Thermal equilibrium reached after {val2} minutes warm-up.",
   "cause":"Normal start-up thermal stabilisation.",
   "diag":[],"remedy":"No action required. Machine ready for production.",
   "related":[]},

  {"code":"CLS-AD-001","sev":8,"sub":"CLS","fault":"process_anomaly",
   "params":["P030"],
   "title":"Coolant — Through-Spindle Active",
   "desc":"Through-spindle coolant active. Flow P030 = {val} L/min at spindle nose.",
   "cause":"NC program M-code activated through-spindle coolant.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  # ══════════════════════ LUBRICATION SYSTEM ═════════════════════════════════

  {"code":"LUB-CR-001","sev":1,"sub":"LUB","fault":"actuator_fault",
   "params":["P040","P041"],
   "title":"Lubrication System Failure — Machine Stopped",
   "desc":"Lubrication oil pressure P040 = {val} bar (below critical minimum 0.5 bar). Oil level P041 = {val2}%. Continued operation will cause rapid guide and ball screw wear.",
   "cause":"Lubrication pump failure, empty reservoir, or blocked distributor.",
   "diag":["Check oil level in reservoir P041 physically","Listen for pump motor running","Check pump outlet pressure","Inspect progressive distributor piston movement","Check motor circuit breaker in electrical cabinet"],
   "remedy":"Restore lubrication system. Do not restart machine without verified lube pressure. After restoration, jog all axes 100mm to distribute oil before production.",
   "related":["LUB-MJ-001","AXS-SR-002","LUB-SR-001"]},

  {"code":"LUB-MJ-001","sev":2,"sub":"LUB","fault":"actuator_fault",
   "params":["P040","P042"],
   "title":"Lubrication Pump — No Flow Confirmation",
   "desc":"Lubrication pump current P042 = {val} A (pump running) but flow switch did not confirm delivery within {val2} s. P040 = {val3} bar.",
   "cause":"Blocked oil distributor, closed isolation valve, or internal pump bypass.",
   "diag":["Check oil inlet strainer","Inspect distributor output at each lube point","Verify isolation valve position","Check for air lock in suction line"],
   "remedy":"Clear blockage in distributor. Bleed air from suction. Replace pump if internal bypass confirmed.",
   "related":["LUB-CR-001","LUB-SR-001"]},

  {"code":"LUB-SR-001","sev":3,"sub":"LUB","fault":"actuator_fault",
   "params":["P041"],
   "title":"Lubrication Oil Level — Low",
   "desc":"Lubrication oil reservoir level P041 = {val}%. Below recommended level (25%). Lube interval may be affected. Machine will stop at 10%.",
   "cause":"Normal oil consumption or minor leak.",
   "diag":["Check for oil leaks at guide covers","Verify lube cycle interval setting","Check oil type matches specification"],
   "remedy":"Top up reservoir with correct oil grade. Inspect for leaks.",
   "related":["LUB-CR-001","LUB-MD-001"]},

  {"code":"LUB-MD-001","sev":4,"sub":"LUB","fault":"actuator_fault",
   "params":["P040","P042"],
   "title":"Lubrication Pressure — Marginal",
   "desc":"Lubrication delivery pressure P040 = {val} bar. Marginally above critical but {val2}% below nominal. Pump current P042 = {val3} A.",
   "cause":"Partially blocked strainer, slightly worn pump, or increased line restriction.",
   "diag":["Clean inlet strainer","Check pump discharge pressure with calibrated gauge","Inspect distributor for sticking piston"],
   "remedy":"Clean strainer. If pump discharge confirmed low, plan pump replacement at next maintenance.",
   "related":["LUB-SR-001","LUB-MJ-001"]},

  {"code":"LUB-MN-001","sev":5,"sub":"LUB","fault":"process_anomaly",
   "params":["P042"],
   "title":"Lubrication Pump Current — Elevated",
   "desc":"Pump current P042 = {val} A, {val2}% above baseline. Pump running but increased load detected.",
   "cause":"Increased oil viscosity (cold start), partial line restriction.",
   "diag":["Check oil temperature","Confirm oil grade matches viscosity specification"],
   "remedy":"Allow machine to warm up. Monitor for 30 minutes.",
   "related":["LUB-MD-001"]},

  {"code":"LUB-WN-001","sev":6,"sub":"LUB","fault":"process_anomaly",
   "params":["P041"],
   "title":"Lubrication — Scheduled Interval Due",
   "desc":"Lubrication cycle interval counter has reached {val} hours since last full service. Lube point inspection recommended.",
   "cause":"Normal maintenance interval.",
   "diag":["Inspect all lube points for oil film","Check distribution block operation"],
   "remedy":"Perform lubrication inspection per maintenance checklist MAINT-LUB-001.",
   "related":["LUB-SR-001"]},

  {"code":"LUB-NC-001","sev":7,"sub":"LUB","fault":"process_anomaly",
   "params":["P040","P042"],
   "title":"Lubrication Cycle Complete",
   "desc":"Scheduled lubrication cycle delivered. P040 = {val} bar confirmed. Pump current P042 = {val2} A. Next cycle in {val3} min.",
   "cause":"Normal automatic lubrication cycle.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"LUB-AD-001","sev":8,"sub":"LUB","fault":"process_anomaly",
   "params":["P041"],
   "title":"Lubrication Oil Level — Nominal",
   "desc":"Oil level P041 = {val}%. Lubrication system operating normally.",
   "cause":"Status advisory.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  # ══════════════════════ VIBRATION MONITORING ════════════════════════════════

  {"code":"VIB-CR-001","sev":1,"sub":"VIB","fault":"spindle_bearing_fault",
   "params":["P060","P061","P062","P063","P064"],
   "title":"Vibration — ISO Zone D — Machine Stop",
   "desc":"Vibration RMS exceeds ISO 10816-3 Zone D limit (11.2 mm/s). X={val}, Y={val2}, Z={val3} mm/s. Crest factor P063={val4}. Kurtosis P064={val5}. Machine stopped.",
   "cause":"Catastrophic bearing failure, tool breakage, workpiece ejection, or structure loosening.",
   "diag":["Do not restart until vibration source identified","Check spindle for mechanical damage","Inspect machine bed levelling","Verify workpiece is still clamped","Check foundation bolts"],
   "remedy":"Identify and repair vibration source before restart. Full machine inspection required.",
   "related":["SPN-CR-001","AXS-CR-001","VIB-MJ-001"]},

  {"code":"VIB-MJ-001","sev":2,"sub":"VIB","fault":"spindle_bearing_fault",
   "params":["P060","P061","P062","P063"],
   "title":"Vibration — ISO Zone C — Major Alert",
   "desc":"Vibration RMS has entered ISO Zone C (7.1–11.2 mm/s). X={val}, Y={val2}, Z={val3} mm/s. Crest P063={val4}. Long-term operation at this level will cause bearing damage.",
   "cause":"Advanced tool wear, bearing defect, or machine structural loosening.",
   "diag":["Perform spectral analysis if portable analyser available","Inspect tool immediately","Check machine foundation","Review trending from last 48 hours"],
   "remedy":"Reduce cutting parameters. Schedule maintenance within 4 hours.",
   "related":["VIB-CR-001","SPN-MJ-002","VIB-SR-001"]},

  {"code":"VIB-SR-001","sev":3,"sub":"VIB","fault":"chatter_vibration",
   "params":["P060","P061","P062"],
   "title":"Vibration — ISO Zone B Upper — Elevated",
   "desc":"Vibration RMS = {val} mm/s on {val2}-axis. At upper boundary of ISO Zone B (4.5–7.1 mm/s). Acceptable for limited operation but not long-term.",
   "cause":"Moderate tool wear, fixture loosening, or minor bearing degradation.",
   "diag":["Inspect tool condition","Check fixture clamping","Review spindle speed vs stability lobe","Measure bearing temperature"],
   "remedy":"Inspect and replace tool. Re-verify fixture. Monitor for further increase.",
   "related":["VIB-MJ-001","SPN-SR-003","AXS-SR-001"]},

  {"code":"VIB-MD-001","sev":4,"sub":"VIB","fault":"tool_wear",
   "params":["P063","P064"],
   "title":"Crest Factor — Elevated Above Baseline",
   "desc":"Vibration crest factor P063 = {val} on spindle sensor. Kurtosis P064 = {val2}. Both elevated vs. 30-day baseline. Pattern may indicate early bearing defect or tool imbalance.",
   "cause":"Incipient bearing defect, tool imbalance, or minor structural change.",
   "diag":["Compare to historical baseline for same operation","Inspect tool holder for contamination in taper","Check tool balance if >12000 RPM operation"],
   "remedy":"Log and monitor daily. Inspect tool holder taper. Plan bearing inspection at next opportunity.",
   "related":["SPN-SR-003","VIB-SR-001"]},

  {"code":"VIB-MN-001","sev":5,"sub":"VIB","fault":"tool_wear",
   "params":["P064"],
   "title":"Kurtosis Index — Rising Trend",
   "desc":"Kurtosis index P064 = {val}. Trending upward over last 14 days: +{val2}% per week. Currently in early-warning zone (5.0–8.0).",
   "cause":"Early-stage bearing defect initiation or accumulating surface fatigue.",
   "diag":["Enable high-frequency logging on spindle vibration","Review full spectrum for defect frequencies"],
   "remedy":"Schedule detailed inspection at next planned downtime. Continue monitoring.",
   "related":["VIB-MD-001","SPN-SR-003"]},

  {"code":"VIB-WN-001","sev":6,"sub":"VIB","fault":"process_anomaly",
   "params":["P060","P061","P062"],
   "title":"Vibration — Normal Operating Range",
   "desc":"All axes within ISO Zone A (<2.3 mm/s). X={val}, Y={val2}, Z={val3} mm/s. Machine operating in optimal vibration envelope.",
   "cause":"Status notification.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"VIB-NC-001","sev":7,"sub":"VIB","fault":"process_anomaly",
   "params":["P063"],
   "title":"Crest Factor — Within Normal Band",
   "desc":"Vibration crest factor P063 = {val}. Within normal operating band (1.0–4.5). No bearing defect signature detected.",
   "cause":"Status notification.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"VIB-AD-001","sev":8,"sub":"VIB","fault":"process_anomaly",
   "params":["P060","P061","P062"],
   "title":"Vibration Baseline Update",
   "desc":"Vibration baseline recalculated from last 30-day dataset. New baseline: X={val}, Y={val2}, Z={val3} mm/s.",
   "cause":"Automatic monthly baseline update.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  # ══════════════════════ ELECTRICAL / THERMAL / CNC ═════════════════════════

  {"code":"ELC-CR-001","sev":1,"sub":"ELC","fault":"actuator_fault",
   "params":["P090","P091"],
   "title":"DC Bus Undervoltage — All Drives Disabled",
   "desc":"DC bus voltage P090 = {val} V, below minimum {val2} V. All servo and spindle drives disabled. Main supply P091 = {val3} V.",
   "cause":"Main supply phase loss, incoming fuse blown, or DC bus capacitor failure.",
   "diag":["Check main incoming supply voltage at isolator","Measure all three phases for balance","Inspect main fuses and circuit breakers","Check DC bus capacitor bank for bulging"],
   "remedy":"Restore supply. Replace fuse if blown. Capacitor replacement requires qualified electrician.",
   "related":["AXS-CR-002","SPN-CR-002","ELC-MJ-001"]},

  {"code":"ELC-MJ-001","sev":2,"sub":"ELC","fault":"actuator_fault",
   "params":["P091","P090"],
   "title":"Supply Voltage — Out of Tolerance",
   "desc":"Main supply voltage P091 = {val} V. Outside ±10% tolerance band ({val2}–{val3} V). DC bus P090 = {val4} V.",
   "cause":"Site power quality issue, undersized transformer, or high demand on shared bus.",
   "diag":["Measure voltage at main incoming terminal","Check transformer tap setting","Contact facility electrical team","Log time of occurrence vs. site load profile"],
   "remedy":"Notify facility maintenance. Install line conditioner if recurring.",
   "related":["ELC-CR-001","ELC-SR-001"]},

  {"code":"ELC-SR-001","sev":3,"sub":"ELC","fault":"actuator_fault",
   "params":["P092"],
   "title":"Ground Leakage — Elevated",
   "desc":"Ground leakage current P092 = {val} mA, above advisory threshold (10 mA). Risk of nuisance RCD tripping.",
   "cause":"Degraded motor winding insulation, cable damage, or moisture ingress.",
   "diag":["Perform insulation resistance test on all motor cables","Inspect cable entry points for moisture","Check RCD rating vs measured leakage"],
   "remedy":"Locate and repair insulation fault. Replace damaged cables.",
   "related":["ELC-MJ-001","ELC-MD-001"]},

  {"code":"ELC-MD-001","sev":4,"sub":"ELC","fault":"process_anomaly",
   "params":["P093"],
   "title":"UPS Battery — Low Charge",
   "desc":"UPS battery level P093 = {val}%. Battery backup time estimated {val2} minutes. CNC memory protection duration may be insufficient for extended power outage.",
   "cause":"Battery aging, recent extended power interruption, or battery charger fault.",
   "diag":["Check UPS charger LED status","Measure battery float voltage","Check battery age against replacement schedule (typically 3–5 years)"],
   "remedy":"Recharge UPS. If charge does not recover to >80% within 24h, replace battery.",
   "related":["ELC-CR-001","ELC-MN-001"]},

  {"code":"ELC-MN-001","sev":5,"sub":"ELC","fault":"process_anomaly",
   "params":["P071"],
   "title":"Electrical Cabinet Temperature — Elevated",
   "desc":"Cabinet temperature P071 = {val} °C. Above minor threshold (40 °C) but below major (55 °C).",
   "cause":"Cabinet fan partial failure, clogged filter, or high ambient temperature.",
   "diag":["Check cabinet fan operation","Clean filter mats","Verify cabinet door seals"],
   "remedy":"Clean filters. Monitor for increase.",
   "related":["THM-MD-001","ELC-MJ-001"]},

  {"code":"ELC-WN-001","sev":6,"sub":"ELC","fault":"process_anomaly",
   "params":["P090"],
   "title":"DC Bus — Minor Voltage Ripple Detected",
   "desc":"DC bus voltage P090 shows increased ripple: peak-to-peak = {val} V (limit 15 V). Mean voltage {val2} V within spec.",
   "cause":"Aging DC bus capacitors or increased regenerative energy.",
   "diag":["Measure capacitance of DC bus capacitors","Check for excessive regenerative braking events"],
   "remedy":"Monitor. Plan capacitor inspection at next scheduled maintenance.",
   "related":["ELC-CR-001","ELC-MD-001"]},

  {"code":"ELC-NC-001","sev":7,"sub":"ELC","fault":"process_anomaly",
   "params":["P090","P091"],
   "title":"Power-On Self-Test — Passed",
   "desc":"All electrical systems passed POST. DC bus P090={val}V, supply P091={val2}V. System ready.",
   "cause":"Normal start-up sequence.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"ELC-AD-001","sev":8,"sub":"ELC","fault":"process_anomaly",
   "params":["P093"],
   "title":"UPS Battery — Fully Charged",
   "desc":"UPS battery at {val}% capacity. Backup time: {val2} minutes.",
   "cause":"Status advisory.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"THM-CR-001","sev":1,"sub":"THM","fault":"process_anomaly",
   "params":["P003","P017","P071","P072"],
   "title":"Multi-Zone Overtemperature — Emergency Stop",
   "desc":"Multiple thermal zones simultaneously over critical threshold. Spindle P003={val}°C, servo P017={val2}°C, cabinet P071={val3}°C, motor P072={val4}°C. Machine stopped.",
   "cause":"Chiller failure, blocked ventilation, or ambient temperature event.",
   "diag":["Check ambient temperature in machine area","Verify all cooling fans active","Check chiller unit","Inspect all air filters"],
   "remedy":"Restore cooling. Do not restart until all zones below 70% of critical threshold.",
   "related":["SPN-MJ-001","AXS-MJ-002","ELC-MN-001","CLS-MJ-001"]},

  {"code":"THM-MD-001","sev":4,"sub":"THM","fault":"process_anomaly",
   "params":["P070","P071","P072"],
   "title":"Thermal Gradient — Elevated Ambient",
   "desc":"Ambient temperature P070 = {val} °C. Cabinet P071 = {val2} °C. Feed motor P072 = {val3} °C. All within spec but elevated vs seasonal baseline.",
   "cause":"HVAC system in machine area running below capacity or unusual ambient conditions.",
   "diag":["Check room HVAC status","Verify all machine air filters clean","Review duty cycle vs. thermal model"],
   "remedy":"Request HVAC inspection for machine area. Clean all filters.",
   "related":["THM-CR-001","ELC-MN-001"]},

  {"code":"THM-WN-001","sev":6,"sub":"THM","fault":"process_anomaly",
   "params":["P070"],
   "title":"Ambient Temperature — Above Recommended Range",
   "desc":"Ambient temperature P070 = {val} °C, above recommended operating range (35°C). Machine can operate but thermal compensation active.",
   "cause":"Seasonal high temperatures or HVAC reduced capacity.",
   "diag":["Confirm HVAC is functional","Increase frequency of coolant concentration checks"],
   "remedy":"Monitor thermal parameters. Consider running reduced duty cycle during peak heat hours.",
   "related":["THM-MD-001"]},

  {"code":"THM-NC-001","sev":7,"sub":"THM","fault":"process_anomaly",
   "params":["P070","P003"],
   "title":"Thermal Compensation Active",
   "desc":"CNC thermal error compensation is active. Ambient P070={val}°C, spindle P003={val2}°C. Axis offsets automatically adjusted for thermal expansion.",
   "cause":"Normal thermal compensation function.",
   "diag":[],"remedy":"No action required. Monitor part quality.",
   "related":[]},

  {"code":"THM-AD-001","sev":8,"sub":"THM","fault":"process_anomaly",
   "params":["P072"],
   "title":"Feed Motor Temperature — Nominal",
   "desc":"Feed motor temperature P072 = {val} °C. Within optimal band.",
   "cause":"Status advisory.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"CNC-CR-001","sev":1,"sub":"CNC","fault":"actuator_fault",
   "params":["P080","P081"],
   "title":"CNC Controller — Watchdog Timeout",
   "desc":"CNC real-time kernel watchdog timed out. All motion halted. CPU load at time of fault: P080={val}%. Memory P081={val2}%.",
   "cause":"Software exception in motion planner, hardware interrupt overload, or memory corruption.",
   "diag":["Record fault dump from CNC system log","Check for recent software updates","Verify RAM hardware via POST diagnostics","Check CPU temperature"],
   "remedy":"Reboot CNC controller. If recurring, contact CNC manufacturer support with fault dump. Do not restart machine with persistent watchdog faults.",
   "related":["AXS-CR-001","ELC-CR-001"]},

  {"code":"CNC-MJ-001","sev":2,"sub":"CNC","fault":"actuator_fault",
   "params":["P080","P082"],
   "title":"NC Program — Syntax Error at Block",
   "desc":"NC program execution halted at block N{val}. P082={val}. Syntax error detected: illegal G-code combination or out-of-range parameter.",
   "cause":"Incorrect NC program modification, corrupted file transfer, or unsupported G-code for this CNC model.",
   "diag":["Review NC block P082 in program editor","Check G-code reference manual for supported codes","Re-transfer program from CAM system","Run program in single-block test mode"],
   "remedy":"Correct NC program. Re-verify with dry run before production restart.",
   "related":["CNC-SR-001","CNC-MD-011"]},

  {"code":"CNC-SR-001","sev":3,"sub":"CNC","fault":"actuator_fault",
   "params":["P080"],
   "title":"CNC CPU Load — High",
   "desc":"CNC CPU load P080 = {val}% sustained over last {val2} minutes. May cause motion interpolation jitter if load exceeds 90%.",
   "cause":"Complex NC program with many small blocks, excessive macro execution, or background task conflict.",
   "diag":["Check number of active background tasks","Review NC program block density","Disable unnecessary data logging during critical cuts","Check for DNC streaming vs. stored program"],
   "remedy":"Optimise NC program (increase minimum arc chord tolerance). Use stored program instead of DNC stream.",
   "related":["CNC-CR-001","CNC-MD-011"]},

  {"code":"CNC-MD-011","sev":4,"sub":"CNC","fault":"process_anomaly",
   "params":["P081","P082"],
   "title":"CNC Memory — Program Storage Near Full",
   "desc":"CNC program memory P081 = {val}%. Less than {val2} MB available. Large programs may not load.",
   "cause":"Accumulated NC programs not archived.",
   "diag":["Review program list for obsolete programs","Archive and delete old programs"],
   "remedy":"Delete or archive old NC programs. Maintain minimum 20% free memory.",
   "related":["CNC-SR-001"]},

  {"code":"CNC-MN-001","sev":5,"sub":"CNC","fault":"process_anomaly",
   "params":["P083"],
   "title":"Feed Override — Non-100% Setting",
   "desc":"Feed override P083 = {val}% (nominal 100%). Machine running at non-standard feed rate.",
   "cause":"Operator-applied override.",
   "diag":["Confirm override is intentional","Check if masking a vibration or quality issue"],
   "remedy":"Restore to 100% if not intentional. Log reason if intentional.",
   "related":["SPN-MD-002"]},

  {"code":"CNC-WN-001","sev":6,"sub":"CNC","fault":"process_anomaly",
   "params":["P082"],
   "title":"Program — Approaching End of File",
   "desc":"NC program at block N{val}, approaching end. {val2} blocks remaining.",
   "cause":"Normal program end approach.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"CNC-NC-001","sev":7,"sub":"CNC","fault":"process_anomaly",
   "params":["P080","P081"],
   "title":"CNC System — Normal Operation",
   "desc":"CNC controller operating normally. CPU P080={val}%, memory P081={val2}%. All axes enabled.",
   "cause":"Status notification.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"CNC-AD-001","sev":8,"sub":"CNC","fault":"process_anomaly",
   "params":["P082"],
   "title":"NC Block Counter",
   "desc":"NC program execution at block N{val}. Advisory status update.",
   "cause":"Status advisory.",
   "diag":[],"remedy":"No action required.",
   "related":[]},

  {"code":"HYD-MJ-001","sev":2,"sub":"HYD","fault":"actuator_fault",
   "params":["P050","P051"],
   "title":"Hydraulic Pressure — Low",
   "desc":"Hydraulic pressure P050 = {val} bar, below minimum operating pressure ({val2} bar). Workholding and ATC clamp functions may be unreliable.",
   "cause":"Pump wear, pressure relief valve stuck open, or internal leak in hydraulic circuit.",
   "diag":["Check pump outlet pressure with calibrated gauge","Listen for pump bypass noise","Inspect hydraulic hoses and fittings for leaks","Check oil level in reservoir","Verify relief valve setting"],
   "remedy":"Replace pump if output pressure confirmed low. Set relief valve to correct pressure. Repair leaks.",
   "related":["TCS-MJ-001","HYD-SR-001","HYD-CR-phantom"]},

  {"code":"HYD-SR-001","sev":3,"sub":"HYD","fault":"actuator_fault",
   "params":["P051","P052"],
   "title":"Hydraulic Oil Overtemperature",
   "desc":"Hydraulic oil temperature P051 = {val} °C, above advisory limit (55 °C). Flow rate P052 = {val2} L/min. Seal degradation accelerates above 60 °C.",
   "cause":"Oil cooler fouling, high duty cycle, or low oil level reducing heat dissipation.",
   "diag":["Check oil cooler condition","Verify fan operation on cooler","Check oil level","Reduce duty cycle if possible"],
   "remedy":"Clean oil cooler. Top up oil. Allow temperature to drop before resuming full cycle rate.",
   "related":["HYD-MJ-001","THM-MD-001"]},

  {"code":"HYD-MD-001","sev":4,"sub":"HYD","fault":"actuator_fault",
   "params":["P050"],
   "title":"Hydraulic Pressure — Minor Drift",
   "desc":"Hydraulic pressure P050 = {val} bar. Drifted {val2} bar below nominal setpoint over last 24 hours.",
   "cause":"Minor internal leakage or relief valve creep.",
   "diag":["Re-check relief valve setting","Monitor for continued drift"],
   "remedy":"Adjust relief valve if within range. Log and monitor.",
   "related":["HYD-MJ-001"]},

  {"code":"HYD-WN-001","sev":6,"sub":"HYD","fault":"process_anomaly",
   "params":["P052"],
   "title":"Hydraulic Pump — Scheduled Service Due",
   "desc":"Hydraulic pump has accumulated {val} operating hours since last service. Service interval is {val2} hours.",
   "cause":"Normal maintenance interval.",
   "diag":[],"remedy":"Schedule hydraulic system service per MAINT-HYD-001.",
   "related":["HYD-MD-001"]},
]

print(f"Defined {len(ERROR_DEFINITIONS)} error codes")
print("Severity breakdown:")
from collections import Counter
sev_count = Counter(e['sev'] for e in ERROR_DEFINITIONS)
for sev in sorted(sev_count):
    name = SEVERITY_LEVELS[sev]['name']
    print(f"  Level {sev} ({name:10s}): {sev_count[sev]} codes")

# ─── 5. P-VALUE INSTANCE GENERATOR ────────────────────────────────────────────
# Generate realistic observed parameter values for each error code instance
# Values are fault-aware: faults push params toward/beyond limits

def gen_pval(param_key, severity, is_fault_param=True):
    """Generate a realistic observed p-value given severity and whether this
    param is the primary fault indicator."""
    p = PARAMETERS[param_key]
    lo, hi = p['normal_min'], p['normal_max']
    clo, chi = p['critical_min'], p['critical_max']

    if not is_fault_param:
        # Secondary param: within normal range
        return round(random.uniform(lo, hi), 3)

    # Primary fault param: push toward limits based on severity
    if severity == 1:   # CRITICAL — beyond normal, near critical
        margin = (chi - hi) * random.uniform(0.7, 0.99)
        val = hi + margin
    elif severity == 2: # MAJOR — above normal limit
        margin = (chi - hi) * random.uniform(0.4, 0.7)
        val = hi + margin
    elif severity == 3: # SERIOUS — at/above normal limit
        margin = (hi - lo) * random.uniform(0.85, 1.05)
        val = lo + margin
    elif severity == 4: # MODERATE — upper normal zone
        val = random.uniform(lo + (hi-lo)*0.7, hi)
    elif severity in (5, 6): # MINOR/WARNING — mid to upper normal
        val = random.uniform(lo + (hi-lo)*0.5, lo + (hi-lo)*0.85)
    else:               # NOTICE/ADVISORY — lower normal
        val = random.uniform(lo + (hi-lo)*0.1, lo + (hi-lo)*0.5)

    # Clamp to critical bounds
    val = max(clo, min(chi, val))

    # Round based on unit type
    if p['unit'] in ['RPM','block']:
        return int(val)
    elif p['unit'] in ['%', 'slot']:
        return round(val, 1)
    else:
        return round(val, 3)


def build_pvalue_record(error_def, instance_id, machine="M01",
                        operation="OP01", run_id=None):
    """Build a full p-value observation record for one error code instance."""
    sev = error_def['sev']
    params = error_def['params']

    pvals = {}
    for i, pk in enumerate(params):
        is_primary = (i == 0)  # first param is always the primary fault indicator
        pvals[pk] = gen_pval(pk, sev, is_fault_param=is_primary)

    # Also add a selection of non-primary context params (always normal)
    context_params = [k for k in list(PARAMETERS.keys())[:6] if k not in params]
    for pk in context_params[:2]:
        pvals[pk] = gen_pval(pk, severity=7, is_fault_param=False)

    return {
        "instance_id"      : instance_id,
        "error_code"       : error_def['code'],
        "severity_level"   : sev,
        "severity_name"    : SEVERITY_LEVELS[sev]['name'],
        "subsystem_code"   : error_def['sub'],
        "subsystem_name"   : SUBSYSTEMS[error_def['sub']]['name'],
        "mid"              : SUBSYSTEMS[error_def['sub']]['mid'],
        "fault_category"   : error_def['fault'],
        "machine"          : machine,
        "operation_code"   : operation,
        "run_id"           : run_id or f"{machine}_{operation}_inst{instance_id:04d}",
        "title"            : error_def['title'],
        "primary_param"    : params[0],
        "primary_param_name": PARAMETERS[params[0]]['name'],
        "primary_param_unit": PARAMETERS[params[0]]['unit'],
        "primary_value"    : pvals[params[0]],
        "normal_min"       : PARAMETERS[params[0]]['normal_min'],
        "normal_max"       : PARAMETERS[params[0]]['normal_max'],
        "critical_min"     : PARAMETERS[params[0]]['critical_min'],
        "critical_max"     : PARAMETERS[params[0]]['critical_max'],
        "all_pvalues_json" : json.dumps(pvals),
        "recommended_action": SEVERITY_LEVELS[sev]['action'],
        "related_codes"    : "|".join(error_def['related']),
    }


# ─── 6. GENERATE FULL ERROR CODE MASTER TABLE ─────────────────────────────────
import pandas as pd, json

# Load fault events to cross-reference
fault_df = pd.read_csv("/home/claude/equipmentiq/processed/fault_events.csv")

# Build master error code catalogue (one row per code, full documentation)
catalogue = []
for ed in ERROR_DEFINITIONS:
    sub = SUBSYSTEMS[ed['sub']]
    sev = SEVERITY_LEVELS[ed['sev']]
    params_detail = []
    for pk in ed['params']:
        p = PARAMETERS[pk]
        params_detail.append(
            f"{pk} | {p['name']} [{p['unit']}] | normal: {p['normal_min']}–{p['normal_max']} | critical: {p['critical_min']}–{p['critical_max']}"
        )
    catalogue.append({
        "error_code"       : ed['code'],
        "severity_level"   : ed['sev'],
        "severity_name"    : sev['name'],
        "severity_color"   : sev['color'],
        "required_action"  : sev['action'],
        "max_downtime_min" : sev['max_downtime_min'],
        "subsystem_code"   : ed['sub'],
        "subsystem_name"   : sub['name'],
        "mid"              : sub['mid'],
        "fault_category"   : ed['fault'],
        "title"            : ed['title'],
        "description"      : ed['desc'],
        "probable_cause"   : ed['cause'],
        "diagnostic_steps" : " | ".join(ed['diag']) if ed['diag'] else "Advisory — no diagnostic required",
        "remedy"           : ed['remedy'],
        "parameters"       : " || ".join(params_detail),
        "related_codes"    : " | ".join(ed['related']) if ed['related'] else "",
        "num_params"       : len(ed['params']),
    })

cat_df = pd.DataFrame(catalogue)
cat_df.to_csv("/home/claude/equipmentiq/processed/error_code_catalogue.csv", index=False)
print(f"Error catalogue: {len(cat_df)} codes × {len(cat_df.columns)} columns")

# ─── 7. GENERATE P-VALUE OBSERVATION INSTANCES ────────────────────────────────
# For each fault event in Bosch dataset → generate matching error code instance(s)
# Plus additional synthetic instances to reach 500+ observations

observations = []
instance_id = 1

# Map fault categories to likely error codes
fault_to_codes = {
    "tool_wear":             ["SPN-MJ-003","SPN-SR-001","SPN-WN-001","SPN-WN-003","SPN-WN-004","SPN-MN-001","SPN-MD-001","VIB-MD-001"],
    "spindle_bearing_fault": ["SPN-CR-001","SPN-MJ-001","SPN-MJ-002","SPN-MJ-005","SPN-SR-003","VIB-MJ-001","VIB-SR-001","VIB-MN-001"],
    "chatter_vibration":     ["SPN-MJ-004","AXS-SR-001","VIB-SR-001","VIB-MJ-001","AXS-MN-002"],
    "actuator_fault":        ["AXS-CR-001","AXS-MJ-001","AXS-MJ-002","TCS-CR-001","TCS-MJ-001","LUB-CR-001","LUB-MJ-001"],
    "process_anomaly":       ["CNC-MJ-001","CNC-SR-001","CLS-CR-001","CLS-MJ-001","HYD-MJ-001"],
}

# Error code lookup
code_lookup = {ed['code']: ed for ed in ERROR_DEFINITIONS}

# Step A: Anchor fault events → real run_ids from Bosch
for _, frow in fault_df.iterrows():
    cat = frow['fault_category']
    codes = fault_to_codes.get(cat, ["SPN-MJ-002"])
    # Pick 1-3 codes per fault event
    n_codes = random.randint(1, min(3, len(codes)))
    chosen = random.sample(codes, n_codes)
    for code in chosen:
        if code not in code_lookup: continue
        obs = build_pvalue_record(
            code_lookup[code], instance_id,
            machine=frow['machine'],
            operation=frow['operation'],
            run_id=frow['run_id']
        )
        # Override with real sensor values where available
        if "x_rms" in frow.index:
            obs['real_x_rms']   = round(frow['x_rms'], 3)
            obs['real_y_rms']   = round(frow['y_rms'], 3)
            obs['real_z_rms']   = round(frow['z_rms'], 3)
            obs['real_crest']   = round(frow['x_crest'], 3)
            obs['real_kurtosis']= round(frow['x_kurtosis'], 3)
        obs['source'] = "bosch_real_fault"
        obs['complaint_case_id'] = frow['complaint_case_id']
        observations.append(obs)
        instance_id += 1

print(f"Generated {instance_id-1} observations from real Bosch fault events")

# Step B: Fill to 500+ with synthetic normal-operation observations
# (advisory, notice, warning — what the system sees during good runs)
good_ops = ["OP01","OP02","OP04","OP07","OP08","OP11","OP14"]
normal_codes = [ed for ed in ERROR_DEFINITIONS if ed['sev'] >= 6]

while instance_id <= 520:
    ed = random.choice(normal_codes)
    machine = random.choice(["M01","M02","M03"])
    op = random.choice(good_ops)
    obs = build_pvalue_record(ed, instance_id, machine=machine, operation=op)
    obs['source'] = "synthetic_normal"
    obs['complaint_case_id'] = ""
    obs.setdefault('real_x_rms', None)
    obs.setdefault('real_y_rms', None)
    obs.setdefault('real_z_rms', None)
    obs.setdefault('real_crest', None)
    obs.setdefault('real_kurtosis', None)
    observations.append(obs)
    instance_id += 1

obs_df = pd.DataFrame(observations)
obs_df.to_csv("/home/claude/equipmentiq/processed/error_observations.csv", index=False)

print(f"Total observations: {len(obs_df)}")
print(f"  Real Bosch-anchored: {(obs_df['source']=='bosch_real_fault').sum()}")
print(f"  Synthetic normal   : {(obs_df['source']=='synthetic_normal').sum()}")
print(f"\nObservations by severity:")
print(obs_df['severity_name'].value_counts().to_string())
print(f"\nObservations by fault category:")
print(obs_df['fault_category'].value_counts().to_string())

# ─── 8. GENERATE THE FULL ERROR CODE DOCUMENTATION JSON ───────────────────────
# This is what the RAG system indexes: rich structured text per error code

import os
os.makedirs("/home/claude/equipmentiq/processed/error_docs", exist_ok=True)

full_docs = {}
for ed in ERROR_DEFINITIONS:
    sub  = SUBSYSTEMS[ed['sub']]
    sev  = SEVERITY_LEVELS[ed['sev']]
    code = ed['code']

    # Build human-readable parameter table
    param_rows = []
    for pk in ed['params']:
        p = PARAMETERS[pk]
        param_rows.append({
            "param_id"   : pk,
            "pid"        : p['pid'],
            "name"       : p['name'],
            "unit"       : p['unit'],
            "normal_min" : p['normal_min'],
            "normal_max" : p['normal_max'],
            "critical_min": p['critical_min'],
            "critical_max": p['critical_max'],
            "subsystem"  : p['subsystem'],
        })

    # Sample p-value observations for this code
    obs_df = pd.read_csv("/home/claude/equipmentiq/processed/error_observations.csv")
    code_obs = obs_df[obs_df['error_code']==code][
        ['machine','operation_code','primary_value','primary_param_unit','source']
    ].head(5).to_dict('records')

    doc = {
        "error_code"        : code,
        "title"             : ed['title'],
        "severity_level"    : sev['name'],
        "severity_number"   : ed['sev'],
        "severity_color"    : sev['color'],
        "subsystem"         : sub['name'],
        "mid"               : sub['mid'],
        "fault_category"    : ed['fault'],
        "description"       : ed['desc'],
        "probable_cause"    : ed['cause'],
        "diagnostic_steps"  : ed['diag'],
        "remedy"            : ed['remedy'],
        "required_action"   : sev['action'],
        "max_downtime_min"  : sev['max_downtime_min'],
        "parameters"        : param_rows,
        "related_codes"     : ed['related'],
        "sample_observations": code_obs,
    }
    full_docs[code] = doc

    # Write individual JSON file per code (for RAG ingestion)
    fname = f"/home/claude/equipmentiq/processed/error_docs/{code}.json"
    with open(fname, 'w') as f:
        json.dump(doc, f, indent=2)

# Write master JSON
with open("/home/claude/equipmentiq/processed/error_code_master.json", 'w') as f:
    json.dump({
        "metadata": {
            "total_codes"    : len(ERROR_DEFINITIONS),
            "total_params"   : len(PARAMETERS),
            "total_subsystems": len(SUBSYSTEMS),
            "severity_levels": {str(k): v['name'] for k,v in SEVERITY_LEVELS.items()},
            "taxonomy_basis" : "Fagor CNC 8055 Error Manual + SAE J2012 MID/PID/FMI",
            "machine_type"   : "CNC Vertical Machining Centre (3-axis)",
            "dataset_link"   : "Bosch CNC Machining Dataset CC-BY-4.0",
        },
        "severity_levels" : SEVERITY_LEVELS,
        "subsystems"      : SUBSYSTEMS,
        "parameters"      : PARAMETERS,
        "error_codes"     : full_docs,
    }, f, indent=2)

print(f"Written {len(ERROR_DEFINITIONS)} individual JSON docs")
print(f"Written error_code_master.json")
print(f"\nSample code — SPN-CR-001:")
print(json.dumps(full_docs['SPN-CR-001'], indent=2)[:800], "...")
